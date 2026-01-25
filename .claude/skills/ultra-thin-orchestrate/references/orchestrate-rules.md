# Ultra-Thin Orchestrate 상세 실행 규칙

## 1. 핵심 원칙: 최소 컨텍스트 유지

### 1.1 메인 에이전트 컨텍스트 제한

메인 에이전트(오케스트레이터)는 다음 정보**만** 유지합니다:

```
유지할 정보 (태스크당 ~190 토큰):
├── task_id: "T1.3"
├── phase: 1
├── status: "in_progress"
├── depends_on: ["T1.1", "T1.2"]
├── parallel_with: ["T1.4"]
└── retry_count: 0
```

```
유지하지 않는 정보:
├── 태스크 상세 설명
├── 서브에이전트 실행 로그
├── 에러 스택 트레이스
├── 생성된 코드 내용
└── 테스트 결과 상세
```

### 1.2 토큰 예산 계산

```
태스크당 예산: 190 토큰
├── task_id + phase: 20 토큰
├── status: 10 토큰
├── depends_on (평균 3개): 60 토큰
├── parallel_with (평균 2개): 40 토큰
├── retry_count + metadata: 30 토큰
└── JSON 구조 오버헤드: 30 토큰

200개 태스크 = 200 × 190 = 38,000 토큰
컨텍스트 여유분 포함 총합: ~50,000 토큰 (25% 버퍼)
```

---

## 2. 태스크 상태 머신

```
         ┌──────────┐
         │ pending  │
         └────┬─────┘
              │ 의존성 충족
              ▼
         ┌──────────┐
         │  ready   │
         └────┬─────┘
              │ 디스패치
              ▼
       ┌─────────────┐
       │ in_progress │
       └──────┬──────┘
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
┌──────────┐    ┌──────────┐
│completed │    │  failed  │
└──────────┘    └────┬─────┘
                     │ retry < 10
                     ▼
               ┌──────────┐
               │  ready   │ (재시도)
               └──────────┘
```

### 2.1 상태 전이 규칙

| 현재 상태 | 조건 | 다음 상태 |
|----------|------|----------|
| pending | 모든 depends_on이 completed | ready |
| ready | Task 도구로 디스패치됨 | in_progress |
| in_progress | DONE 신호 수신 | completed |
| in_progress | FAIL 신호 수신 & retry < 10 | ready |
| in_progress | FAIL 신호 수신 & retry >= 10 | failed |

---

## 3. 의존성 해결 알고리즘

### 3.1 Kahn's Algorithm (위상 정렬)

```python
def get_ready_tasks(tasks, completed):
    ready = []
    for task in tasks:
        if task.status == 'pending':
            deps_met = all(d in completed for d in task.depends_on)
            if deps_met:
                ready.append(task)
    return ready
```

### 3.2 순환 의존성 검출

```
TASKS.md 파싱 시점에 순환 의존성 검출
순환 발견 시: ERROR:CIRCULAR_DEP:{task_chain}
예: ERROR:CIRCULAR_DEP:T1.3->T1.4->T1.3
```

### 3.3 병렬 실행 그룹

```
parallel_with 속성이 있는 태스크들은 동시 디스패치 가능

예:
T1.3: parallel_with: [T1.4, T1.5]
→ T1.3, T1.4, T1.5를 동시에 Task 도구로 호출
```

---

## 4. 서브에이전트 디스패치 프로토콜

### 4.1 단일 태스크 디스패치

```
Task 도구:
  subagent_type: "general-purpose"  # 또는 specialist 타입
  prompt: |
    [ULTRA-THIN MODE]
    Task ID: T1.3
    Phase: 1

    TASKS.md에서 T1.3의 상세 내용을 읽고 실행하세요.
    파일 경로: docs/planning/TASKS.md (또는 docs/planning/06-tasks.md)

    완료 시 반드시 다음 형식으로 응답:
    - 성공: "DONE:T1.3"
    - 실패: "FAIL:T1.3:{간단한_에러_1줄}"

    상세 로그와 학습 내용은 .claude/memory/learnings.md에 기록하세요.
```

### 4.2 병렬 태스크 디스패치

의존성 없는 태스크들은 **단일 메시지에 여러 Task 도구 호출**:

```
메시지 내용:
[Task 도구 #1: T1.3 디스패치]
[Task 도구 #2: T1.4 디스패치]
[Task 도구 #3: T1.5 디스패치]
```

### 4.3 전문가 에이전트 매핑

| specialist 값 | subagent_type |
|--------------|---------------|
| backend-specialist | general-purpose |
| frontend-specialist | general-purpose |
| database-specialist | general-purpose |
| test-specialist | general-purpose |
| 그 외 | general-purpose |

---

## 5. 응답 파싱 규칙

### 5.1 성공 신호

```
정규표현식: DONE:(T\d+\.\d+)
예: "DONE:T1.3"
처리: task.status = "completed"
```

### 5.2 실패 신호

```
정규표현식: FAIL:(T\d+\.\d+):(.+)
예: "FAIL:T1.3:TypeError - 타입 불일치"
처리:
  task.retry_count += 1
  if task.retry_count < 10:
    task.status = "ready"
  else:
    task.status = "failed"
```

### 5.3 응답에 신호가 없는 경우

```
서브에이전트 응답에 DONE/FAIL 신호가 없으면:
1. 경고 로그 기록
2. 태스크를 "ready" 상태로 복귀
3. 재시도 카운터 증가
```

---

## 6. Phase 실행 규칙

### 6.1 Phase 0 (프로젝트 셋업)

```
특성:
- Git Worktree 불필요
- main 브랜치에서 직접 작업
- 순차 실행 (병렬 불가)
```

### 6.2 Phase 1+ (기능 개발)

```
특성:
- Git Worktree 필수
- TDD 사이클 적용 (RED → GREEN → REFACTOR)
- 병렬 실행 가능 (parallel_with 명시 시)

Worktree 명령:
git worktree add ../project-phase{N}-{feature} -b phase/{N}-{feature}
```

### 6.3 Phase 간 전환

```
Phase N 완료 조건:
- 모든 Phase N 태스크가 completed 또는 failed
- failed 태스크는 10회 재시도 완료

Phase N+1 시작 조건:
- Phase N 완료
- Phase N의 성공률 >= 90% (또는 사용자 확인 후 강제 진행)
```

---

## 7. 상태 파일 관리

### 7.1 저장 시점

```
상태 파일 저장 시점:
- 태스크 상태 변경 시
- Phase 전환 시
- 에러 발생 시
- 30초마다 자동 저장 (heartbeat)
```

### 7.2 백업

```
저장 전 백업 생성:
cp .claude/orchestrate-state.json .claude/orchestrate-state.json.bak
```

### 7.3 복구

```
상태 파일 손상 시:
1. 백업에서 복구 시도
2. 복구 실패 시: TASKS.md에서 [x] 체크된 태스크를 completed로 재구성
```

---

## 8. 로깅 규칙

### 8.1 메인 에이전트 로그 (최소)

```
[ULTRA-THIN] Phase 1 시작
[DISPATCH] T1.3, T1.4, T1.5 → 병렬 실행
[DONE] T1.3
[DONE] T1.4
[FAIL] T1.5:TypeError (retry 1/10)
[DISPATCH] T1.5 → 재시도
[DONE] T1.5
[ULTRA-THIN] Phase 1 완료 (3/3 성공)
```

### 8.2 상세 로그 위치

```
서브에이전트 상세 로그: .claude/memory/learnings.md
실행 기록 전체: .claude/orchestrate.log
```

---

## 9. 비상 탈출 (Emergency Exit)

### 9.1 사용자 중단

```
사용자가 Ctrl+C 또는 "중단" 요청 시:
1. 현재 상태 즉시 저장
2. in_progress 태스크를 ready로 복귀
3. 재개 방법 안내
```

### 9.2 연속 실패 감지

```
동일 태스크 3회 연속 같은 에러 시:
1. 해당 태스크 일시 중단
2. 사용자에게 수동 개입 요청
3. 다른 태스크 계속 진행
```

### 9.3 컨텍스트 포화 예방

```
컨텍스트 사용량 모니터링:
- 70% 도달: 경고 로그
- 80% 도달: 상태 저장 + 사용자 안내
- 90% 도달: 자동 중단 + 재개 안내
```

---

## 10. 슬랙 알림 (선택)

### 10.1 알림 시점

```
알림 전송 시점:
- Phase 완료
- 전체 완료
- 연속 실패 발생 (3회 이상)
```

### 10.2 웹훅 호출

```bash
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "🎉 Phase 1 완료!\n├── 프로젝트: my-app\n├── 완료: 12개\n└── 소요: 45분"
  }'
```
