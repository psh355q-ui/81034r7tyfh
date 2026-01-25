#!/usr/bin/env python3
"""
의존성 분석기 - Ultra-Thin Orchestrate용

태스크 의존성을 분석하고 실행 순서를 결정합니다.
Kahn's Algorithm (위상 정렬)을 사용합니다.

사용법:
    python dependency_resolver.py --state .claude/orchestrate-state.json --action next
    python dependency_resolver.py --state .claude/orchestrate-state.json --action update --task T1.3 --status completed
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def load_state(state_path: str) -> dict:
    """상태 파일 로드"""
    path = Path(state_path)
    if not path.exists():
        print(f"ERROR:STATE_NOT_FOUND:{state_path}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR:STATE_CORRUPT:{e}", file=sys.stderr)
        sys.exit(1)


def save_state(state: dict, state_path: str):
    """상태 파일 저장 (백업 포함)"""
    path = Path(state_path)

    # 백업 생성
    if path.exists():
        backup_path = path.with_suffix(".json.bak")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    # 업데이트 시간 갱신
    state["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # 저장
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def get_ready_tasks(state: dict) -> list:
    """
    의존성이 충족된 태스크 목록 반환 (Kahn's Algorithm)

    Returns:
        실행 가능한 태스크 ID 목록
    """
    completed = set(state["tasks"]["completed"])
    pending = state["tasks"]["pending"]
    task_details = state.get("task_details", {})

    ready = []
    remaining_pending = []

    for task_id in pending:
        details = task_details.get(task_id, {})
        deps = details.get("depends_on", [])

        # 모든 의존성이 완료되었는지 확인
        if all(d in completed for d in deps):
            ready.append(task_id)
        else:
            remaining_pending.append(task_id)

    # 상태 업데이트
    state["tasks"]["ready"] = ready
    state["tasks"]["pending"] = remaining_pending

    return ready


def get_parallel_group(state: dict, task_id: str) -> list:
    """
    병렬 실행 가능한 태스크 그룹 반환

    Returns:
        task_id와 함께 병렬 실행 가능한 태스크 목록
    """
    task_details = state.get("task_details", {})
    details = task_details.get(task_id, {})
    parallel_with = details.get("parallel_with", [])

    ready = set(state["tasks"]["ready"])
    group = [task_id]

    for parallel_id in parallel_with:
        if parallel_id in ready:
            group.append(parallel_id)

    # 병렬 제한 적용
    parallel_limit = state.get("execution", {}).get("parallel_limit", 5)
    return group[:parallel_limit]


def update_task_status(state: dict, task_id: str, new_status: str,
                       error_summary: Optional[str] = None):
    """
    태스크 상태 업데이트

    Args:
        state: 상태 딕셔너리
        task_id: 태스크 ID
        new_status: 새 상태 (completed, failed, ready, in_progress)
        error_summary: 에러 요약 (실패 시)
    """
    tasks = state["tasks"]

    # 현재 상태에서 제거
    for status_list in ["pending", "ready", "in_progress", "completed", "failed"]:
        if task_id in tasks[status_list]:
            tasks[status_list].remove(task_id)

    # 새 상태에 추가
    if new_status in tasks:
        tasks[new_status].append(task_id)

    # 실패 시 에러 로그 기록 및 재시도 카운터 증가
    if new_status == "failed" or (new_status == "ready" and error_summary):
        retry_counts = state.setdefault("retry_counts", {})
        retry_counts[task_id] = retry_counts.get(task_id, 0) + 1

        error_log = state.setdefault("error_log", [])
        error_log.append({
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error_summary": (error_summary or "Unknown error")[:100],
            "retry_number": retry_counts[task_id]
        })

        # 에러 로그 최대 50개 유지
        if len(error_log) > 50:
            state["error_log"] = error_log[-50:]

        # 10회 재시도 후 failed로 전환
        if retry_counts[task_id] >= 10:
            if task_id in tasks["ready"]:
                tasks["ready"].remove(task_id)
            tasks["failed"].append(task_id)

    # 통계 업데이트
    stats = state["stats"]
    stats["completed"] = len(tasks["completed"])
    stats["failed"] = len(tasks["failed"])
    total = stats["total"]
    if total > 0:
        stats["success_rate"] = len(tasks["completed"]) / total


def dispatch_tasks(state: dict, max_dispatch: int = 5) -> list:
    """
    다음 실행할 태스크 디스패치

    Args:
        state: 상태 딕셔너리
        max_dispatch: 최대 디스패치 수

    Returns:
        디스패치할 태스크 목록 (태스크 ID와 specialist 정보 포함)
    """
    ready = state["tasks"]["ready"]
    in_progress = state["tasks"]["in_progress"]
    task_details = state.get("task_details", {})

    # 이미 진행 중인 태스크 수 고려
    available_slots = max_dispatch - len(in_progress)
    if available_slots <= 0:
        return []

    dispatch_list = []
    dispatched_ids = []

    for task_id in ready[:available_slots]:
        details = task_details.get(task_id, {})

        # 병렬 실행 그룹 확인
        parallel_group = get_parallel_group(state, task_id)

        for group_task in parallel_group:
            if group_task not in dispatched_ids and len(dispatch_list) < available_slots:
                dispatch_list.append({
                    "task_id": group_task,
                    "phase": details.get("phase", 0),
                    "specialist": details.get("specialist", "general-purpose")
                })
                dispatched_ids.append(group_task)

    # ready에서 in_progress로 이동
    for item in dispatch_list:
        task_id = item["task_id"]
        if task_id in state["tasks"]["ready"]:
            state["tasks"]["ready"].remove(task_id)
        if task_id not in state["tasks"]["in_progress"]:
            state["tasks"]["in_progress"].append(task_id)

    return dispatch_list


def check_phase_completion(state: dict) -> dict:
    """
    현재 Phase 완료 여부 확인

    Returns:
        {
            "phase": 현재 Phase,
            "completed": 완료 여부,
            "stats": {
                "total": Phase 내 전체 태스크,
                "completed": 완료된 태스크,
                "failed": 실패한 태스크,
                "remaining": 남은 태스크
            }
        }
    """
    current_phase = state.get("execution", {}).get("current_phase", 0)
    task_details = state.get("task_details", {})

    phase_tasks = {
        tid for tid, details in task_details.items()
        if details.get("phase") == current_phase
    }

    completed = phase_tasks & set(state["tasks"]["completed"])
    failed = phase_tasks & set(state["tasks"]["failed"])
    remaining = phase_tasks - completed - failed

    is_completed = len(remaining) == 0

    return {
        "phase": current_phase,
        "completed": is_completed,
        "stats": {
            "total": len(phase_tasks),
            "completed": len(completed),
            "failed": len(failed),
            "remaining": len(remaining)
        }
    }


def advance_phase(state: dict) -> bool:
    """
    다음 Phase로 진행

    Returns:
        성공 여부
    """
    task_details = state.get("task_details", {})
    all_phases = sorted(set(d.get("phase", 0) for d in task_details.values()))

    current_phase = state.get("execution", {}).get("current_phase", 0)

    try:
        current_idx = all_phases.index(current_phase)
        if current_idx + 1 < len(all_phases):
            next_phase = all_phases[current_idx + 1]
            state["execution"]["current_phase"] = next_phase
            state["stats"]["phases_completed"] = state.get("stats", {}).get("phases_completed", 0) + 1
            return True
    except ValueError:
        pass

    return False


def format_status_summary(state: dict) -> str:
    """상태 요약 문자열 생성"""
    tasks = state["tasks"]
    stats = state["stats"]

    lines = [
        f"📊 실행 상태:",
        f"   ├── 전체: {stats['total']}개",
        f"   ├── 완료: {stats['completed']}개 ({stats.get('success_rate', 0)*100:.1f}%)",
        f"   ├── 실패: {stats['failed']}개",
        f"   ├── 진행중: {len(tasks['in_progress'])}개",
        f"   ├── 대기: {len(tasks['ready'])}개",
        f"   └── 미시작: {len(tasks['pending'])}개",
    ]

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="의존성 분석기 - Ultra-Thin Orchestrate용")
    parser.add_argument("--state", "-s", required=True, help="상태 파일 경로")
    parser.add_argument("--action", "-a", required=True,
                       choices=["next", "update", "status", "phase-check", "advance"],
                       help="수행할 액션")
    parser.add_argument("--task", "-t", help="태스크 ID (update 액션용)")
    parser.add_argument("--status", help="새 상태 (update 액션용)")
    parser.add_argument("--error", help="에러 요약 (update 액션용)")
    parser.add_argument("--max-dispatch", type=int, default=5, help="최대 디스패치 수")

    args = parser.parse_args()

    state = load_state(args.state)

    if args.action == "next":
        # 다음 실행할 태스크 찾기
        get_ready_tasks(state)
        dispatch_list = dispatch_tasks(state, args.max_dispatch)
        save_state(state, args.state)

        if dispatch_list:
            print(json.dumps(dispatch_list, ensure_ascii=False))
        else:
            print("[]")

    elif args.action == "update":
        if not args.task or not args.status:
            print("ERROR: --task와 --status 필수", file=sys.stderr)
            sys.exit(1)

        update_task_status(state, args.task, args.status, args.error)
        get_ready_tasks(state)  # 의존성 재계산
        save_state(state, args.state)
        print(f"OK: {args.task} → {args.status}")

    elif args.action == "status":
        print(format_status_summary(state))

    elif args.action == "phase-check":
        result = check_phase_completion(state)
        print(json.dumps(result, ensure_ascii=False))

    elif args.action == "advance":
        if advance_phase(state):
            save_state(state, args.state)
            print(f"OK: Phase {state['execution']['current_phase']}로 진행")
        else:
            print("WARN: 마지막 Phase입니다")


if __name__ == "__main__":
    main()
