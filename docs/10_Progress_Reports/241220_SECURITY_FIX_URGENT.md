# 🚨 긴급 보안 조치 가이드

**날짜**: 2024년 12월 20일  
**심각도**: 🔴 CRITICAL

---

## ⚠️ 노출된 API 키

**파일**: `docs/09_Troubleshooting/FIX_API_KEY.md`  
**라인**: 49  
**노출된 키**: `AIzaSyBgp8dhRSRnGcXmhE_fw3qef2DKv_tnCAI`

**GitHub 커밋**: 5aa2b87d (PHASE5_TASK1_COMPLETE.md)

---

## 📋 즉시 조치 사항 (순서대로)

### 1단계: API 키 즉시 폐기 ⚠️ (5분 이내)

```
📍 https://console.cloud.google.com/apis/credentials

1. Google Cloud Console 접속
2. API 및 서비스 → 사용자 인증 정보
3. "AIzaSyBgp8dhRSRnGcXmhE_fw3qef2DKv_tnCAI" 찾기
4. 🗑️ 삭제 또는 ⏸️ 비활성화
5. ✅ 새 API 키 생성
6. .env 파일에 새 키 저장
```

### 2단계: 파일에서 키 제거

```powershell
# FIX_API_KEY.md 수정
# 실제 키를 placeholder로 교체
```

### 3단계: Git History에서 완전 제거

#### Option A: BFG Repo-Cleaner (권장)

```powershell
# BFG 다운로드
# https://rtyley.github.io/bfg-repo-cleaner/

# 실행
java -jar bfg.jar --replace-text replacements.txt ai-trading-system

# replacements.txt 내용:
AIzaSyBgp8dhRSRnGcXmhE_fw3qef2DKv_tnCAI==>YOUR_API_KEY_HERE

# Git cleanup
cd ai-trading-system
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

#### Option B: git filter-branch

```powershell
cd d:\code\ai-trading-system

# 모든 커밋에서 키 제거
git filter-branch --force --index-filter `
  "git ls-files -z | xargs -0 sed -i 's/AIzaSyBgp8dhRSRnGcXmhE_fw3qef2DKv_tnCAI/YOUR_API_KEY_HERE/g'" `
  --prune-empty --tag-name-filter cat -- --all

# Cleanup
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
git push origin --force --tags
```

### 4단계: .gitignore 강화

```gitignore
# API Keys & Secrets
.env
.env.*
!.env.example
*_API_KEY*
*_SECRET*
*credentials*

# Docs with potential secrets
docs/**/FIX_*.md
```

---

## 🔍 추가 검색할 파일들

다음 파일에도 키가 있을 수 있습니다:

1. `docs/09_Troubleshooting/FIX_GEMINI_QUOTA.md` (line 11)
2. GitHub commits history

---

## ✅ 검증

모든 조치 후 확인:

```powershell
# 로컬에서 검색
grep -r "AIzaSyBgp8dhRSRnGcXmhE_fw3qef2DKv_tnCAI" .

# Git history에서 검색
git log -S "AIzaSyBgp8dhRSRnGcXmhE_fw3qef2DKv_tnCAI" --all

# 결과가 없어야 함!
```

---

## 📊 영향 범위

**노출 기간**: 커밋 시점 ~ 현재  
**접근 가능자**: GitHub repo 읽기 권한 있는 모든 사용자  
**위험도**: 
- API 할당량 소진
- 무단 사용
- 비용 청구 가능성

---

## 🎯 향후 방지책

1. **Pre-commit Hook 설치**
```bash
# .git/hooks/pre-commit
#!/bin/sh
if git diff --cached | grep -E "AIzaSy[a-zA-Z0-9_-]{33}"; then
    echo "❌ API Key detected! Commit blocked."
    exit 1
fi
```

2. **GitHub Secret Scanning 활성화** (이미 작동 중 ✅)

3. **문서 작성 시 주의**
   - 예시는 항상 `your_api_key_here` 사용
   - 실제 키는 절대 문서화하지 않기

---

## 📞 완료 후 체크리스트

- [ ] Google Cloud Console에서 키 폐기
- [ ] 새 API 키 발급 및 .env 저장
- [ ] FIX_API_KEY.md에서 키 제거
- [ ] Git history에서 키 제거
- [ ] Force push 완료
- [ ] 검증 완료 (grep 결과 없음)
- [ ] Pre-commit hook 설치
- [ ] GitHub 보안 경고 해결 확인

---

## ⏱️ 예상 소요 시간

- 키 폐기: 5분
- 파일 수정: 2분
- Git history 정리: 10분
- 검증: 5분
- **총계**: 약 20분
