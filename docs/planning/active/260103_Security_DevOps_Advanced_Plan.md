# Security, DevOps, Advanced Analytics 구현 계획

**작성일**: 2026-01-03
**카테고리**: Security, DevOps, Performance, Analytics, Cloud
**우선순위**: P1-P3 (High to Low Priority)
**상태**: 📋 Planning Phase

---

## Executive Summary

Claude Code Templates의 **13개 고급 컴포넌트**에 대한 구현 계획입니다. 보안 강화, DevOps 자동화, 성능 모니터링, 고급 분석, 클라우드 통합, 알림 시스템을 다룹니다.

**기존 계획 완료 문서:**
- ✅ [260103_Claude_Code_Templates_Implementation_Plan.md](260103_Claude_Code_Templates_Implementation_Plan.md) - 테스트 자동화, 프론트엔드 최적화, Git Hooks
- ✅ [260102_Database_Optimization_Plan.md](260102_Database_Optimization_Plan.md) - Database 최적화

**본 문서 범위:**
1. 🔒 Security Auditor Agent - API 키 암호화, OWASP 스캔
2. 🚀 DevOps Engineer Agent - CI/CD 파이프라인
3. ⚡ Performance Monitoring - 실시간 성능 추적
4. 📊 Data Scientist Agent - Shadow Trading 통계 분석
5. 🤖 NLP Engineer Agent - 로컬 임베딩, 티커 추출 개선
6. ☁️ AWS Integration - S3 백업, Lambda 백필
7. 📢 Discord/Slack Notifications - 실시간 알림

---

## 현재 시스템 상태 (2026-01-03 기준)

### 보안 현황
| 항목 | 현재 상태 | 문제점 | 목표 |
|------|-----------|--------|------|
| API 키 저장 | .env 평문 | 노출 위험 | 암호화 저장 |
| 보안 스캔 | 없음 | 취약점 미감지 | 자동 스캔 |
| OWASP Top 10 | 미검증 | 알 수 없음 | 100% 준수 |
| Secrets 검증 | Git hooks 없음 | 커밋 위험 | Pre-commit 차단 |

**최근 이슈:**
- ⚠️ OpenAI API 할당량 초과 (2026-01-02 이전)
- ✅ Kill Switch 구현 완료 (2026-01-02)

### DevOps 현황
| 항목 | 현재 상태 | 문제점 | 목표 |
|------|-----------|--------|------|
| CI/CD | GitHub Actions 기본 | 테스트 미실행 | 완전 자동화 |
| 배포 시간 | 수동 60분 | 느림 | 자동 5분 |
| 테스트 실행 | 수동 | 누락 위험 | PR마다 자동 |
| 롤백 | 수동 30분 | 복구 느림 | 자동 2분 |

**기존 인프라:**
- ✅ Docker Compose 구성 완료
- ✅ PostgreSQL TimescaleDB (포트 5433)
- ✅ Shadow Trading 모니터링 스크립트

### 성능 현황
| 항목 | 현재 값 | 목표 값 | 개선 여지 |
|------|---------|---------|----------|
| War Room MVP | 12.76초 | < 8초 | 병렬화 |
| 뉴스 백필 메모리 | 450MB | < 200MB | 배치 처리 |
| API 폴링 | 1,440 calls/hour | < 240 | WebSocket |

**2026-01-02 최적화 완료:**
- ✅ 복합 인덱스 5개 추가
- ✅ N+1 쿼리 제거 (ON CONFLICT)
- ✅ TTL 캐싱 구현

### 분석 현황
| 항목 | 현재 상태 | 문제점 | 목표 |
|------|-----------|--------|------|
| Shadow Trading 분석 | 수동 스크립트 | 비효율 | 자동 주간 리포트 |
| 백테스팅 메트릭 | 기본 (Win Rate, PF, MDD) | 부족 | 샤프/소르티노 비율 |
| 통계 검정 | 없음 | 유의성 불명 | p-value 계산 |

### NLP/AI 현황
| 항목 | 현재 상태 | 문제점 | 목표 |
|------|-----------|--------|------|
| 뉴스 임베딩 | OpenAI API | 비용 $20/month | 로컬 모델 $0 |
| 티커 추출 | Regex 기반 | 정확도 ~60% | NER 모델 90% |
| 감성 분석 | Gemini API | 할당량 제한 | 안정적 운영 |

---

## Part 1: Security & Compliance (보안 및 규정 준수)

### 목표
- API 키 노출 위험 100% 제거
- OWASP Top 10 자동 스캔
- Git 커밋 전 Secrets 차단
- 주간 보안 감사 자동화

---

### 1.1 Security Auditor Agent

**설치 방법:**
```bash
npx claude-code-templates@latest --agent security-auditor --yes
```

**주요 기능:**
1. API 키 암호화 저장
2. OWASP Top 10 취약점 스캔
3. SQL Injection 탐지
4. XSS 취약점 검사
5. 접근 제어 검증

---

#### Implementation 1-1: API 키 암호화 시스템

**현재 문제:**
```bash
# .env 파일 - 평문 저장 (위험!)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxx
KIS_APP_KEY=PSxxxxxxxxxxxxxxxx
KIS_APP_SECRET=xxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://user:password@localhost:5433/trading
TELEGRAM_BOT_TOKEN=7xxxxxxxxx:AAxxxxxxxxxxxxxxxxxxxxxxxxx
```

**해결책: Fernet 암호화**

**파일 1**: `backend/config/secrets_manager.py` (신규 생성)

```python
"""
Secrets Manager - 환경 변수 암호화 저장

Features:
- Fernet 대칭키 암호화
- 파일 권한 제한 (0o600)
- Git 추적 방지
- 런타임 복호화

Date: 2026-01-03
Author: AI Trading System Team
"""
import os
from cryptography.fernet import Fernet
from pathlib import Path
import json
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """암호화된 시크릿 관리 클래스"""

    def __init__(
        self,
        key_file: str = ".secrets.key",
        secrets_file: str = ".secrets.enc"
    ):
        """
        초기화

        Args:
            key_file: 암호화 키 파일 경로
            secrets_file: 암호화된 시크릿 파일 경로
        """
        self.key_file = Path(key_file)
        self.secrets_file = Path(secrets_file)
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """
        암호화 키 로드 또는 생성

        Returns:
            암호화 키 (bytes)
        """
        if self.key_file.exists():
            logger.info(f"Loading existing key from {self.key_file}")
            return self.key_file.read_bytes()

        # 새 키 생성
        logger.warning(f"Creating new encryption key at {self.key_file}")
        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        self.key_file.chmod(0o600)  # 소유자만 읽기/쓰기 가능

        return key

    def encrypt_secrets(self, secrets: Dict[str, str]) -> None:
        """
        시크릿 암호화 저장

        Args:
            secrets: 키-값 딕셔너리

        Example:
            manager.encrypt_secrets({
                'OPENAI_API_KEY': 'sk-proj-xxx',
                'DATABASE_URL': 'postgresql://...'
            })
        """
        # JSON 직렬화
        json_data = json.dumps(secrets, indent=2).encode('utf-8')

        # Fernet 암호화
        encrypted_data = self.fernet.encrypt(json_data)

        # 파일 저장
        self.secrets_file.write_bytes(encrypted_data)
        self.secrets_file.chmod(0o600)

        logger.info(f"Encrypted {len(secrets)} secrets to {self.secrets_file}")

    def decrypt_secrets(self) -> Dict[str, str]:
        """
        시크릿 복호화 로드

        Returns:
            복호화된 시크릿 딕셔너리

        Raises:
            FileNotFoundError: 암호화 파일 없음
            InvalidToken: 복호화 실패
        """
        if not self.secrets_file.exists():
            raise FileNotFoundError(
                f"Encrypted secrets file not found: {self.secrets_file}"
            )

        # 암호화 데이터 로드
        encrypted_data = self.secrets_file.read_bytes()

        # Fernet 복호화
        decrypted_data = self.fernet.decrypt(encrypted_data)

        # JSON 역직렬화
        secrets = json.loads(decrypted_data.decode('utf-8'))

        logger.debug(f"Decrypted {len(secrets)} secrets")
        return secrets

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        개별 시크릿 조회

        Args:
            key: 시크릿 키
            default: 기본값 (없을 경우)

        Returns:
            시크릿 값 또는 기본값
        """
        try:
            secrets = self.decrypt_secrets()
            return secrets.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get secret '{key}': {e}")
            return default

    def update_secret(self, key: str, value: str) -> None:
        """
        개별 시크릿 업데이트

        Args:
            key: 시크릿 키
            value: 새 값
        """
        secrets = self.decrypt_secrets()
        secrets[key] = value
        self.encrypt_secrets(secrets)

        logger.info(f"Updated secret '{key}'")

    def delete_secret(self, key: str) -> None:
        """
        개별 시크릿 삭제

        Args:
            key: 삭제할 키
        """
        secrets = self.decrypt_secrets()
        if key in secrets:
            del secrets[key]
            self.encrypt_secrets(secrets)
            logger.info(f"Deleted secret '{key}'")

    def list_keys(self) -> list:
        """
        저장된 시크릿 키 목록

        Returns:
            키 리스트 (값은 노출하지 않음)
        """
        secrets = self.decrypt_secrets()
        return list(secrets.keys())


# 글로벌 인스턴스 (싱글톤 패턴)
_secrets_manager_instance: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """
    SecretsManager 싱글톤 인스턴스 반환

    Returns:
        SecretsManager 인스턴스
    """
    global _secrets_manager_instance

    if _secrets_manager_instance is None:
        _secrets_manager_instance = SecretsManager()

    return _secrets_manager_instance


# 편의 함수
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    시크릿 조회 편의 함수

    Args:
        key: 시크릿 키
        default: 기본값

    Returns:
        시크릿 값

    Example:
        >>> openai_key = get_secret('OPENAI_API_KEY')
    """
    return get_secrets_manager().get_secret(key, default)
```

**파일 2**: `scripts/migrate_secrets.py` (마이그레이션 스크립트)

```python
#!/usr/bin/env python3
"""
.env → 암호화된 secrets 마이그레이션 스크립트

Usage:
    python scripts/migrate_secrets.py

Steps:
1. .env 파일 읽기
2. 모든 환경 변수 추출
3. SecretsManager로 암호화 저장
4. 백업 생성
5. .env 삭제 안내

Date: 2026-01-03
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.secrets_manager import SecretsManager


def migrate():
    """마이그레이션 실행"""
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file not found!")
        return

    # 1. 기존 .env 로드
    print("📂 Loading .env file...")
    load_dotenv()

    # 2. 환경 변수 추출
    secrets = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "KIS_APP_KEY": os.getenv("KIS_APP_KEY"),
        "KIS_APP_SECRET": os.getenv("KIS_APP_SECRET"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    }

    # None 값 제거
    secrets = {k: v for k, v in secrets.items() if v is not None}

    if not secrets:
        print("❌ No secrets found in .env file!")
        return

    print(f"✅ Found {len(secrets)} secrets:")
    for key in secrets.keys():
        print(f"   - {key}")

    # 3. 암호화 저장
    print("\n🔐 Encrypting secrets...")
    manager = SecretsManager()
    manager.encrypt_secrets(secrets)

    print(f"✅ Secrets encrypted to .secrets.enc")

    # 4. .env 백업
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f".env.backup_{timestamp}"
    shutil.copy(env_file, backup_file)
    print(f"💾 Backup created: {backup_file}")

    # 5. 안내 메시지
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT NEXT STEPS:")
    print("=" * 60)
    print("\n1. Verify encrypted secrets:")
    print("   python -c 'from backend.config.secrets_manager import get_secret; print(get_secret(\"OPENAI_API_KEY\")[:20])'")
    print("\n2. Update .gitignore:")
    print("   .secrets.key")
    print("   .secrets.enc")
    print("   .env.backup_*")
    print("\n3. Backup .secrets.key securely (NOT in Git!)")
    print("   - Store in password manager")
    print("   - Save to secure location")
    print("\n4. Update application code to use SecretsManager:")
    print("   from backend.config.secrets_manager import get_secret")
    print("   openai_key = get_secret('OPENAI_API_KEY')")
    print("\n5. Test the application")
    print("\n6. Delete .env file:")
    print("   rm .env")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    migrate()
```

**파일 3**: `.gitignore` 업데이트

```bash
# Secrets (암호화)
.secrets.key
.secrets.enc
.env.backup_*

# 기존
.env
*.pyc
__pycache__/
```

**사용 예시:**

```python
# Before: .env 파일 직접 접근
import os
openai_key = os.getenv("OPENAI_API_KEY")

# After: SecretsManager 사용
from backend.config.secrets_manager import get_secret
openai_key = get_secret("OPENAI_API_KEY")
```

**예상 효과:**
- ✅ API 키 노출 위험: 100% → 0%
- ✅ Git 커밋 안전: 평문 키 차단
- ✅ 운영 환경 보안: 암호화 파일만 배포

---

#### Implementation 1-2: OWASP Top 10 자동 스캔

**파일**: `scripts/security_audit.py` (신규 생성)

```python
#!/usr/bin/env python3
"""
OWASP Top 10 자동 보안 스캔

Checks:
1. SQL Injection (A03:2021)
2. XSS - Cross-Site Scripting (A03:2021)
3. Broken Authentication (A07:2021)
4. Sensitive Data Exposure (A02:2021)
5. Broken Access Control (A01:2021)
6. Security Misconfiguration (A05:2021)
7. Insecure Deserialization (A08:2021)
8. Using Components with Known Vulnerabilities (A06:2021)
9. Insufficient Logging & Monitoring (A09:2021)
10. Server-Side Request Forgery (A10:2021)

Date: 2026-01-03
Author: AI Trading System Team
"""
import re
from pathlib import Path
from typing import List, Dict, Set
import json
from datetime import datetime


class SecurityAuditor:
    """보안 감사 도구"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.issues: List[Dict] = []
        self.scanned_files: Set[Path] = set()

    def scan_sql_injection(self) -> List[Dict]:
        """
        A03:2021 - SQL Injection 취약점 스캔

        Patterns:
        - f-string in SQL query
        - % formatting in SQL
        - Direct string concatenation
        """
        issues = []

        # Python 파일 스캔
        py_files = list(self.base_path.glob("backend/**/*.py"))

        for file in py_files:
            if self._should_skip(file):
                continue

            self.scanned_files.add(file)
            content = file.read_text(encoding='utf-8', errors='ignore')

            # 위험 패턴 1: f-string in SELECT
            if re.search(r'f".*?SELECT.*?\{.*?\}"', content, re.IGNORECASE):
                issues.append(self._create_issue(
                    type="SQL_INJECTION",
                    severity="CRITICAL",
                    file=file,
                    message="Potential SQL injection via f-string in SELECT statement",
                    line=self._find_line_number(content, r'f".*?SELECT.*?\{.*?\}"')
                ))

            # 위험 패턴 2: % formatting
            if re.search(r'%.*?SELECT|INSERT|UPDATE|DELETE', content, re.IGNORECASE):
                issues.append(self._create_issue(
                    type="SQL_INJECTION",
                    severity="HIGH",
                    file=file,
                    message="Potential SQL injection via % formatting",
                    line=self._find_line_number(content, r'%.*?SELECT')
                ))

            # 위험 패턴 3: String concatenation
            if re.search(r'\+.*?(SELECT|INSERT|UPDATE|DELETE)', content, re.IGNORECASE):
                issues.append(self._create_issue(
                    type="SQL_INJECTION",
                    severity="MEDIUM",
                    file=file,
                    message="Potential SQL injection via string concatenation",
                    line=self._find_line_number(content, r'\+.*?SELECT')
                ))

        return issues

    def scan_xss(self) -> List[Dict]:
        """
        A03:2021 - XSS 취약점 스캔

        Checks:
        - dangerouslySetInnerHTML in React
        - Unescaped user input in templates
        """
        issues = []

        # TypeScript/React 파일 스캔
        tsx_files = list(self.base_path.glob("frontend/src/**/*.tsx"))

        for file in tsx_files:
            self.scanned_files.add(file)
            content = file.read_text(encoding='utf-8', errors='ignore')

            # dangerouslySetInnerHTML 사용
            if "dangerouslySetInnerHTML" in content:
                issues.append(self._create_issue(
                    type="XSS",
                    severity="HIGH",
                    file=file,
                    message="dangerouslySetInnerHTML detected - verify sanitization with DOMPurify",
                    line=self._find_line_number(content, "dangerouslySetInnerHTML")
                ))

            # Unescaped innerHTML
            if re.search(r'\.innerHTML\s*=', content):
                issues.append(self._create_issue(
                    type="XSS",
                    severity="MEDIUM",
                    file=file,
                    message="Direct innerHTML assignment - XSS risk",
                    line=self._find_line_number(content, r'\.innerHTML\s*=')
                ))

        return issues

    def scan_secrets_exposure(self) -> List[Dict]:
        """
        A02:2021 - Sensitive Data Exposure

        Patterns:
        - API keys in code
        - Passwords in code
        - Database credentials
        """
        issues = []

        # 모든 코드 파일 스캔
        code_files = list(self.base_path.glob("**/*.py"))
        code_files.extend(self.base_path.glob("**/*.tsx"))
        code_files.extend(self.base_path.glob("**/*.ts"))

        secret_patterns = [
            (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
            (r'AIzaSy[a-zA-Z0-9_-]{33}', 'Google/Gemini API Key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
            (r'[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com', 'Google OAuth'),
            (r'postgresql://[^:]+:[^@]+@', 'PostgreSQL Password in URL'),
            (r'mysql://[^:]+:[^@]+@', 'MySQL Password in URL'),
            (r'mongodb://[^:]+:[^@]+@', 'MongoDB Password in URL'),
        ]

        for file in code_files:
            if self._should_skip(file):
                continue

            self.scanned_files.add(file)
            content = file.read_text(encoding='utf-8', errors='ignore')

            for pattern, secret_type in secret_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    issues.append(self._create_issue(
                        type="SECRET_EXPOSURE",
                        severity="CRITICAL",
                        file=file,
                        message=f"Potential {secret_type} hardcoded in source",
                        line=self._find_line_number(content, pattern)
                    ))

        return issues

    def scan_broken_access_control(self) -> List[Dict]:
        """
        A01:2021 - Broken Access Control

        Checks:
        - DELETE endpoints without authentication
        - Admin routes without authorization
        - Direct object references
        """
        issues = []

        # API 라우터 스캔
        router_files = list(self.base_path.glob("backend/api/*_router.py"))

        for file in router_files:
            self.scanned_files.add(file)
            content = file.read_text(encoding='utf-8', errors='ignore')

            # DELETE without auth
            delete_routes = re.findall(
                r'@router\.delete\([^)]+\)\s*async def ([a-z_]+)',
                content,
                re.IGNORECASE
            )

            for route in delete_routes:
                # Check if Depends(get_current_user) exists
                if 'Depends(get_current_user)' not in content:
                    issues.append(self._create_issue(
                        type="BROKEN_ACCESS_CONTROL",
                        severity="CRITICAL",
                        file=file,
                        message=f"DELETE endpoint '{route}' without authentication",
                        line=self._find_line_number(content, f'def {route}')
                    ))

            # Admin routes
            if '/admin' in content or 'admin' in str(file):
                if 'is_admin' not in content and 'require_admin' not in content:
                    issues.append(self._create_issue(
                        type="BROKEN_ACCESS_CONTROL",
                        severity="HIGH",
                        file=file,
                        message="Admin route without authorization check",
                        line=1
                    ))

        return issues

    def scan_security_misconfiguration(self) -> List[Dict]:
        """
        A05:2021 - Security Misconfiguration

        Checks:
        - DEBUG mode in production
        - Default credentials
        - Unnecessary services
        """
        issues = []

        # Check main.py for debug mode
        main_file = self.base_path / "backend" / "main.py"
        if main_file.exists():
            content = main_file.read_text(encoding='utf-8')

            if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
                issues.append(self._create_issue(
                    type="SECURITY_MISCONFIGURATION",
                    severity="HIGH",
                    file=main_file,
                    message="DEBUG mode enabled - should be False in production",
                    line=self._find_line_number(content, r'debug\s*=\s*True')
                ))

        # Check docker-compose for default passwords
        docker_compose = self.base_path / "docker-compose.yml"
        if docker_compose.exists():
            content = docker_compose.read_text(encoding='utf-8')

            if 'POSTGRES_PASSWORD: trading123' in content:
                issues.append(self._create_issue(
                    type="SECURITY_MISCONFIGURATION",
                    severity="MEDIUM",
                    file=docker_compose,
                    message="Default database password detected",
                    line=self._find_line_number(content, 'POSTGRES_PASSWORD')
                ))

        return issues

    def scan_insufficient_logging(self) -> List[Dict]:
        """
        A09:2021 - Insufficient Logging & Monitoring

        Checks:
        - Exception handling without logging
        - Security events without audit trail
        """
        issues = []

        py_files = list(self.base_path.glob("backend/**/*.py"))

        for file in py_files:
            if self._should_skip(file):
                continue

            content = file.read_text(encoding='utf-8', errors='ignore')

            # Bare except without logging
            bare_excepts = re.findall(
                r'except:[\s\S]{0,200}?pass',
                content
            )

            if bare_excepts and 'logger' not in content:
                issues.append(self._create_issue(
                    type="INSUFFICIENT_LOGGING",
                    severity="MEDIUM",
                    file=file,
                    message="Exception handling without logging",
                    line=self._find_line_number(content, r'except:')
                ))

        return issues

    def run_full_audit(self) -> Dict:
        """전체 보안 감사 실행"""
        print("🔍 Starting Security Audit...")
        print("=" * 60)

        all_issues = []

        # Run all scans
        print("1️⃣  Scanning for SQL Injection...")
        all_issues.extend(self.scan_sql_injection())

        print("2️⃣  Scanning for XSS vulnerabilities...")
        all_issues.extend(self.scan_xss())

        print("3️⃣  Scanning for exposed secrets...")
        all_issues.extend(self.scan_secrets_exposure())

        print("4️⃣  Scanning for broken access control...")
        all_issues.extend(self.scan_broken_access_control())

        print("5️⃣  Scanning for security misconfiguration...")
        all_issues.extend(self.scan_security_misconfiguration())

        print("6️⃣  Scanning for insufficient logging...")
        all_issues.extend(self.scan_insufficient_logging())

        # Categorize by severity
        critical = [i for i in all_issues if i['severity'] == 'CRITICAL']
        high = [i for i in all_issues if i['severity'] == 'HIGH']
        medium = [i for i in all_issues if i['severity'] == 'MEDIUM']
        low = [i for i in all_issues if i['severity'] == 'LOW']

        result = {
            "scan_date": datetime.now().isoformat(),
            "scanned_files": len(self.scanned_files),
            "total_issues": len(all_issues),
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
            "issues": all_issues
        }

        return result

    def _should_skip(self, file: Path) -> bool:
        """스캔 제외 파일 판단"""
        skip_patterns = [
            '.venv',
            'node_modules',
            '__pycache__',
            '.git',
            'migrations',
            'test_',
            '.pyc'
        ]

        return any(pattern in str(file) for pattern in skip_patterns)

    def _create_issue(
        self,
        type: str,
        severity: str,
        file: Path,
        message: str,
        line: int = 1
    ) -> Dict:
        """이슈 객체 생성"""
        return {
            "type": type,
            "severity": severity,
            "file": str(file.relative_to(self.base_path)),
            "line": line,
            "message": message
        }

    def _find_line_number(self, content: str, pattern: str) -> int:
        """패턴이 위치한 라인 번호 찾기"""
        try:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    return i
        except:
            pass
        return 1

    def generate_report(self, result: Dict, output_file: str = "security_audit_report.json"):
        """감사 리포트 생성"""
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print("\n" + "=" * 60)
        print("📊 Security Audit Report")
        print("=" * 60)
        print(f"Scanned Files: {result['scanned_files']}")
        print(f"Total Issues: {result['total_issues']}")
        print(f"  🔴 Critical: {result['critical']}")
        print(f"  🟠 High: {result['high']}")
        print(f"  🟡 Medium: {result['medium']}")
        print(f"  ⚪ Low: {result['low']}")
        print("=" * 60)

        if result['critical'] > 0:
            print("\n❌ CRITICAL ISSUES:")
            for issue in result['issues']:
                if issue['severity'] == 'CRITICAL':
                    print(f"  {issue['file']}:{issue['line']}")
                    print(f"    {issue['message']}")

        print(f"\n💾 Full report saved to: {output_file}")


# CLI 실행
if __name__ == "__main__":
    auditor = SecurityAuditor()
    results = auditor.run_full_audit()
    auditor.generate_report(results)

    # Exit with error code if critical issues found
    if results['critical'] > 0:
        exit(1)
```

**실행:**
```bash
# 전체 스캔
python scripts/security_audit.py

# 출력:
# 🔍 Starting Security Audit...
# ============================================================
# 1️⃣  Scanning for SQL Injection...
# 2️⃣  Scanning for XSS vulnerabilities...
# 3️⃣  Scanning for exposed secrets...
# 4️⃣  Scanning for broken access control...
# 5️⃣  Scanning for security misconfiguration...
# 6️⃣  Scanning for insufficient logging...
#
# ============================================================
# 📊 Security Audit Report
# ============================================================
# Scanned Files: 127
# Total Issues: 5
#   🔴 Critical: 1
#   🟠 High: 2
#   🟡 Medium: 2
#   ⚪ Low: 0
# ============================================================
#
# ❌ CRITICAL ISSUES:
#   backend/api/war_room_router.py:42
#     DELETE endpoint 'delete_session' without authentication
#
# 💾 Full report saved to: security_audit_report.json
```

**예상 소요:** 4시간
**예상 효과:** OWASP Top 10 취약점 자동 탐지

---

#### Implementation 1-3: `/check-security` Command 통합

**설치:**
```bash
npx claude-code-templates@latest --command check-security --yes
```

**사용:**
```bash
# 전체 코드베이스 스캔
/check-security

# 특정 파일만 스캔
/check-security backend/api/war_room_router.py

# 리포트 생성
/check-security --report
```

**GitHub Actions 통합:**

**파일**: `.github/workflows/security-scan.yml` (신규)

```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 0'  # 매주 일요일 오전 2시

jobs:
  security-audit:
    name: OWASP Security Audit
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install cryptography

      - name: Run security audit
        run: |
          python scripts/security_audit.py

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-audit-report
          path: security_audit_report.json

      - name: Fail on critical issues
        run: |
          CRITICAL=$(jq '.critical' security_audit_report.json)
          if [ "$CRITICAL" -gt 0 ]; then
            echo "❌ Found $CRITICAL critical security issues!"
            exit 1
          fi
```

**예상 효과:** PR마다 자동 보안 검사, Critical 이슈 시 머지 차단

---

### 1.2 구현 로드맵 (Security)

**Week 1: Secrets 암호화**
- [ ] Day 1-2: SecretsManager 클래스 구현
- [ ] Day 3: 마이그레이션 스크립트 작성
- [ ] Day 4: .env → .secrets.enc 전환
- [ ] Day 5: 백엔드 코드 업데이트 (get_secret 사용)
- [ ] Day 6-7: 테스트 및 검증

**Week 2: 보안 감사 자동화**
- [ ] Day 1-3: SecurityAuditor 구현 (6개 스캔)
- [ ] Day 4: GitHub Actions 워크플로우 작성
- [ ] Day 5: `/check-security` 명령 설치 및 테스트
- [ ] Day 6-7: 발견된 취약점 수정

**Week 3: 지속적 모니터링**
- [ ] Day 1-2: 주간 보안 스캔 스케줄 설정
- [ ] Day 3-4: Telegram 알림 통합 (Critical 이슈)
- [ ] Day 5-7: 보안 대시보드 구축 (선택)

**예상 효과:**
- ✅ API 키 노출 위험: 100% → 0%
- ✅ OWASP Top 10 준수: 0% → 90%
- ✅ 보안 취약점 발견: 수동 → 자동 (주간)
- ✅ Critical 이슈 차단: PR 머지 방지

---

## Part 2: DevOps & CI/CD (배포 자동화)

### 목표
- CI/CD 파이프라인 구축
- 배포 시간 60분 → 5분
- 테스트 자동 실행 (PR마다)
- Blue-Green 배포 및 자동 롤백

---

### 2.1 DevOps Engineer Agent

**설치 방법:**
```bash
npx claude-code-templates@latest --agent devops-engineer --yes
```

**주요 기능:**
1. GitHub Actions CI/CD 설정
2. Docker 멀티스테이지 빌드
3. 자동 테스트 실행
4. Staging/Production 분리 배포
5. Blue-Green 배포 전략
6. 자동 롤백

---

#### Implementation 2-1: GitHub Actions CI/CD 파이프라인

**현재 상태:**
```yaml
# .github/workflows/ci.yml - 기본만 존재
# 테스트 실행 안 함 ❌
```

**목표 파이프라인:**
```
코드 푸시 → Lint → Test → Build → Security Scan → Deploy
```

**파일**: `.github/workflows/ci-cd-pipeline.yml` (신규 생성)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============================================================
  # Stage 1: Lint & Format Check
  # ============================================================
  lint:
    name: 🔍 Code Linting
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Python dependencies
        run: |
          cd backend
          pip install flake8 black mypy
          pip install -r requirements.txt

      - name: Lint with flake8
        run: |
          cd backend
          # Stop build if syntax errors or undefined names
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # Exit-zero treats all errors as warnings
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Check formatting with black
        run: |
          cd backend
          black --check --diff .

      - name: Type check with mypy
        continue-on-error: true
        run: |
          cd backend
          mypy --ignore-missing-imports --no-strict-optional .

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Lint frontend
        run: |
          cd frontend
          npm run lint

  # ============================================================
  # Stage 2: Backend Tests
  # ============================================================
  test-backend:
    name: 🧪 Backend Tests
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: timescale/timescaledb:latest-pg15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: trading_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-mock

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/trading_test
          TESTING: true
        run: |
          cd backend
          pytest --cov=. --cov-report=xml --cov-report=term --cov-report=html -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend
          name: backend-coverage

      - name: Upload coverage HTML
        uses: actions/upload-artifact@v3
        with:
          name: backend-coverage-html
          path: backend/htmlcov/

  # ============================================================
  # Stage 3: Frontend Tests
  # ============================================================
  test-frontend:
    name: 🎨 Frontend Tests
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false

      - name: Build
        run: |
          cd frontend
          npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: frontend-build
          path: frontend/dist/

  # ============================================================
  # Stage 4: Security Scan
  # ============================================================
  security-scan:
    name: 🔒 Security Scan
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install cryptography

      - name: Run OWASP security audit
        run: |
          python scripts/security_audit.py

      - name: Check for critical issues
        run: |
          CRITICAL=$(jq '.critical' security_audit_report.json)
          if [ "$CRITICAL" -gt 0 ]; then
            echo "❌ Found $CRITICAL critical security issues!"
            exit 1
          fi

      - name: Upload security report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-audit-report
          path: security_audit_report.json

  # ============================================================
  # Stage 5: Build Docker Images
  # ============================================================
  build-images:
    name: 🐳 Build Docker Images
    runs-on: ubuntu-latest
    needs: [security-scan]
    if: github.event_name == 'push'

    steps:
      - uses: checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels)
        id: meta-backend
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend

      - name: Build and push backend image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta-backend.outputs.tags }}
          labels: ${{ steps.meta-backend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Extract metadata for frontend
        id: meta-frontend
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend

      - name: Build and push frontend image
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta-frontend.outputs.tags }}
          labels: ${{ steps.meta-frontend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================================
  # Stage 6: Deploy to Staging
  # ============================================================
  deploy-staging:
    name: 🚀 Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build-images]
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.trading.example.com

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to staging server
        run: |
          echo "🚀 Deploying to Staging..."
          # SSH to staging server and pull new images
          # ssh staging "cd /app && docker-compose pull && docker-compose up -d"

      - name: Health check
        run: |
          sleep 10
          curl -f https://staging.trading.example.com/health || exit 1

      - name: Notify Telegram
        if: success()
        run: |
          curl -X POST https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage \
            -d chat_id=${{ secrets.TELEGRAM_CHAT_ID }} \
            -d text="✅ Staging deployment successful - ${{ github.sha }}"

  # ============================================================
  # Stage 7: Deploy to Production
  # ============================================================
  deploy-production:
    name: 🎯 Deploy to Production
    runs-on: ubuntu-latest
    needs: [build-images]
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://trading.example.com

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production (Blue-Green)
        run: |
          echo "🎯 Deploying to Production (Blue-Green)..."
          # 1. Start new containers (Green)
          # 2. Health check
          # 3. Switch traffic
          # 4. Stop old containers (Blue)

      - name: Health check
        run: |
          sleep 15
          curl -f https://trading.example.com/health || exit 1

      - name: Rollback on failure
        if: failure()
        run: |
          echo "❌ Deployment failed, rolling back..."
          # Switch back to Blue

      - name: Notify Telegram
        if: always()
        run: |
          STATUS="${{ job.status }}"
          if [ "$STATUS" = "success" ]; then
            MSG="✅ Production deployment successful"
          else
            MSG="❌ Production deployment FAILED - rolled back"
          fi
          curl -X POST https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage \
            -d chat_id=${{ secrets.TELEGRAM_CHAT_ID }} \
            -d text="$MSG - ${{ github.sha }}"
```

**예상 효과:**
- ✅ 자동 테스트 실행 (PR마다)
- ✅ 보안 스캔 자동화
- ✅ Staging 자동 배포 (develop 브랜치)
- ✅ Production 배포 (main 브랜치)
- ✅ 배포 실패 시 자동 롤백

---

#### Implementation 2-2: Docker 멀티스테이지 빌드

**파일**: `backend/Dockerfile` (최적화)

```dockerfile
# ============================================================
# Stage 1: Builder
# ============================================================
FROM python:3.11-slim as builder

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 빌드 (레이어 캐싱)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================
# Stage 2: Runtime
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Builder stage에서 Python 패키지 복사
COPY --from=builder /root/.local /root/.local

# PATH 업데이트
ENV PATH=/root/.local/bin:$PATH

# 애플리케이션 코드 복사
COPY . .

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 비루트 사용자 생성
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**예상 효과:**
- 이미지 크기: 1.2GB → 400MB
- 빌드 시간: 5분 → 2분 (캐시 활용)
- 보안: 비루트 사용자 실행

---

**파일**: `frontend/Dockerfile` (최적화)

```dockerfile
# ============================================================
# Stage 1: Build
# ============================================================
FROM node:18-alpine as build

WORKDIR /app

# 의존성 설치 (레이어 캐싱)
COPY package*.json ./
RUN npm ci --only=production

# 소스 복사 및 빌드
COPY . .
RUN npm run build

# ============================================================
# Stage 2: Production with Nginx
# ============================================================
FROM nginx:alpine

# Nginx 설정
COPY nginx.conf /etc/nginx/nginx.conf

# 빌드 결과물만 복사
COPY --from=build /app/dist /usr/share/nginx/html

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**파일**: `frontend/nginx.conf` (신규)

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    server {
        listen 80;
        server_name _;

        root /usr/share/nginx/html;
        index index.html;

        # SPA routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API proxy
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

**예상 효과:**
- 이미지 크기: 800MB → 50MB
- Production-ready Nginx
- SPA 라우팅 지원

---

### 2.2 구현 로드맵 (DevOps)

**Week 1: CI 파이프라인 구축**
- [ ] Day 1-2: GitHub Actions 워크플로우 작성
- [ ] Day 3: Lint/Test 단계 구성 및 테스트
- [ ] Day 4-5: 커버리지 리포트 Codecov 통합
- [ ] Day 6-7: Security scan 단계 추가

**Week 2: CD 파이프라인 구축**
- [ ] Day 1-2: Docker 이미지 빌드 자동화
- [ ] Day 3-4: Staging 배포 스크립트 작성
- [ ] Day 5: Production Blue-Green 배포 구현
- [ ] Day 6-7: 롤백 메커니즘 테스트

**Week 3: Docker 최적화**
- [ ] Day 1-2: Backend Dockerfile 멀티스테이지 빌드
- [ ] Day 3-4: Frontend Dockerfile + Nginx 설정
- [ ] Day 5: docker-compose.yml 헬스체크 추가
- [ ] Day 6-7: 이미지 크기 및 빌드 시간 측정

**Week 4: 모니터링 및 알림**
- [ ] Day 1-2: Telegram 배포 알림 통합
- [ ] Day 3-4: 에러 추적 시스템 (Sentry 연동)
- [ ] Day 5-7: 성능 모니터링 대시보드 (선택)

**예상 효과:**
- ✅ 배포 시간: 60분 → 5분 (92% 개선)
- ✅ 테스트 커버리지: 자동 측정 및 리포트
- ✅ 롤백 시간: 수동 30분 → 자동 2분
- ✅ 배포 신뢰도: 수동 → 자동 (Zero-downtime)

---

## Part 3: Performance & Monitoring (성능 및 모니터링)

### 목표
- War Room MVP 응답 시간 단축 (12.76초 → 7.5초)
- 실시간 성능 모니터링 및 알림
- 병목 지점 자동 탐지
- 메모리 사용 최적화 (450MB → 200MB)

---

### 3.1 `/performance-audit` Command

**설치 방법:**
```bash
npx claude-code-templates@latest --command performance-audit --yes
```

**주요 기능:**
1. 함수 실행 시간 프로파일링
2. 메모리 사용량 분석
3. 병목 지점 자동 탐지
4. 최적화 권장사항 제공

---

#### Implementation 3-1: War Room MVP 병렬화

**현재 문제:**
```python
# backend/ai/mvp/war_room_mvp.py
# 순차 실행 - 8.2초 소요
trader_result = self.trader_agent.analyze(...)  # 2.8초
risk_result = self.risk_agent.analyze(...)      # 2.7초
analyst_result = self.analyst_agent.analyze(...)  # 2.7초
# 총 8.2초 + PM Agent 1.5초 = 9.7초
```

**해결책: ThreadPoolExecutor 병렬화**

**파일**: `backend/ai/mvp/war_room_mvp.py` (수정)

```python
"""
War Room MVP - 병렬 처리 최적화

Date: 2026-01-03
Optimization: Parallel agent execution
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class WarRoomMVP:
    """War Room MVP - 3 Agent + PM 구조"""

    def __init__(self):
        self.trader_agent = TraderAgentMVP()
        self.risk_agent = RiskAgentMVP()
        self.analyst_agent = AnalystAgentMVP()
        self.pm_agent = PMAgentMVP()

        # ThreadPool 생성 (재사용)
        self.executor = ThreadPoolExecutor(max_workers=3)

    def deliberate(
        self,
        symbol: str,
        action_context: str = "new_position",
        market_data: Dict = None,
        portfolio_state: Dict = None,
        additional_data: Dict = None
    ) -> Dict[str, Any]:
        """
        전쟁실 심의 - 병렬 처리 버전

        Args:
            symbol: 종목 심볼
            action_context: 액션 컨텍스트
            market_data: 시장 데이터
            portfolio_state: 포트폴리오 상태
            additional_data: 추가 데이터

        Returns:
            최종 의사결정 결과
        """
        start_time = time.time()

        # 1. 3개 Agent 병렬 실행
        logger.info(f"Starting parallel agent execution for {symbol}")

        futures = {
            'trader': self.executor.submit(
                self.trader_agent.analyze,
                symbol=symbol,
                price_data=market_data.get('price_data'),
                technical_data=market_data.get('technical_data')
            ),
            'risk': self.executor.submit(
                self.risk_agent.analyze,
                symbol=symbol,
                price_data=market_data.get('price_data'),
                portfolio_state=portfolio_state
            ),
            'analyst': self.executor.submit(
                self.analyst_agent.analyze,
                symbol=symbol,
                news_data=market_data.get('news_data'),
                macro_data=market_data.get('macro_data')
            )
        }

        # 2. 결과 수집 (as_completed로 먼저 끝나는 순서대로)
        agent_opinions = {}
        for agent_name, future in futures.items():
            try:
                result = future.result(timeout=10)  # 10초 타임아웃
                agent_opinions[agent_name] = result
                logger.debug(f"{agent_name} completed: {result.get('action')}")
            except Exception as e:
                logger.error(f"{agent_name} failed: {e}")
                agent_opinions[agent_name] = {
                    'action': 'PASS',
                    'confidence': 0.0,
                    'reasoning': f'Agent error: {str(e)}'
                }

        agent_time = time.time() - start_time
        logger.info(f"Agents completed in {agent_time:.2f}s (parallel)")

        # 3. PM Agent 최종 결정
        pm_start = time.time()

        final_decision = self.pm_agent.make_final_decision(
            symbol=symbol,
            trader_opinion=agent_opinions.get('trader'),
            risk_opinion=agent_opinions.get('risk'),
            analyst_opinion=agent_opinions.get('analyst'),
            portfolio_state=portfolio_state
        )

        pm_time = time.time() - pm_start
        total_time = time.time() - start_time

        logger.info(
            f"War Room completed: {total_time:.2f}s "
            f"(agents: {agent_time:.2f}s, PM: {pm_time:.2f}s)"
        )

        return {
            'symbol': symbol,
            'final_decision': final_decision,
            'agent_opinions': agent_opinions,
            'pm_decision': final_decision,
            'performance': {
                'total_time': total_time,
                'agent_time': agent_time,
                'pm_time': pm_time,
                'speedup': '3x' if agent_time < 4.0 else '1x'
            }
        }

    def __del__(self):
        """Clean up thread pool"""
        self.executor.shutdown(wait=False)
```

**예상 효과:**
- Agent 실행 시간: 8.2초 → 2.8초 (병렬화)
- 전체 응답 시간: 12.76초 → 7.5초 (41% 개선)
- 리소스 사용: CPU 활용도 3배 증가

---

#### Implementation 3-2: 뉴스 백필 메모리 최적화

**현재 문제:**
```python
# backend/data/processors/news_processor.py
def process_articles(self, articles: List[Article]):
    # 20개 기사 전부 메모리 로드 (120MB)
    embeddings = [self.get_embedding(a.content) for a in articles]  # 280MB
    # 총 450MB 메모리 스파이크
```

**해결책: 배치 처리 + 제너레이터**

**파일**: `backend/data/processors/news_processor.py` (수정)

```python
"""
News Processor - 메모리 최적화

Date: 2026-01-03
Optimization: Batch processing with generator
"""
import gc
from typing import List, Generator
import logging

logger = logging.getLogger(__name__)


class NewsProcessor:
    """뉴스 처리 파이프라인 - 메모리 최적화 버전"""

    def __init__(self, batch_size: int = 5):
        """
        초기화

        Args:
            batch_size: 배치 크기 (메모리 제한에 따라 조절)
        """
        self.batch_size = batch_size
        self.embedding_model = LocalEmbeddingModel()  # 로컬 모델 사용

    def process_articles_batched(
        self,
        articles: List[Article]
    ) -> Generator[Dict, None, None]:
        """
        배치 단위 기사 처리 (제너레이터)

        Args:
            articles: 처리할 기사 리스트

        Yields:
            처리된 기사 데이터
        """
        total = len(articles)
        logger.info(f"Processing {total} articles in batches of {self.batch_size}")

        for i in range(0, total, self.batch_size):
            batch = articles[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size

            logger.debug(f"Processing batch {batch_num}/{total_batches}")

            # 배치 처리
            processed_batch = self._process_batch(batch)

            # 개별 기사 yield
            for article_data in processed_batch:
                yield article_data

            # 명시적 메모리 해제
            del batch
            del processed_batch
            gc.collect()

    def _process_batch(self, batch: List[Article]) -> List[Dict]:
        """
        단일 배치 처리

        Args:
            batch: 기사 배치

        Returns:
            처리된 데이터 리스트
        """
        # 1. 텍스트 추출
        texts = [article.content for article in batch]

        # 2. 배치 임베딩 (단일 API 호출)
        embeddings = self.embedding_model.get_embeddings_batch(texts)

        # 3. 데이터 조합
        processed = []
        for article, embedding in zip(batch, embeddings):
            processed.append({
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'embedding': embedding,
                'processed_at': datetime.now()
            })

        return processed

    def save_processed_articles(self, articles: List[Article]):
        """
        처리 및 저장 (메모리 효율적)

        Args:
            articles: 기사 리스트
        """
        from backend.database.repository import NewsRepository

        repo = NewsRepository()
        saved_count = 0

        # 제너레이터로 순회 (메모리 절약)
        for article_data in self.process_articles_batched(articles):
            try:
                repo.save_article_with_embedding(article_data)
                saved_count += 1

                if saved_count % 10 == 0:
                    logger.info(f"Saved {saved_count} articles")

            except Exception as e:
                logger.error(f"Failed to save article {article_data['id']}: {e}")

        logger.info(f"✅ Saved {saved_count}/{len(articles)} articles")


# 사용 예시
if __name__ == "__main__":
    processor = NewsProcessor(batch_size=5)

    # 20개 기사 처리
    articles = fetch_recent_articles(limit=20)

    # Before: 450MB 메모리
    # After: 100MB 메모리 (5개씩 배치 처리)
    processor.save_processed_articles(articles)
```

**예상 효과:**
- 메모리 사용: 450MB → 100MB (78% 감소)
- 처리 속도: 동일 유지
- OOM 에러 방지

---

### 3.2 Performance Monitor Hook

**설치 방법:**
```bash
npx claude-code-templates@latest --hook performance-monitor --yes
```

**구현:**

**파일**: `backend/monitoring/performance_monitor.py` (신규 생성)

```python
"""
Performance Monitor - 실시간 성능 추적

Features:
- 함수 실행 시간 모니터링
- 메모리 사용량 추적
- 임계값 초과 시 자동 알림
- 성능 메트릭 수집

Date: 2026-01-03
Author: AI Trading System Team
"""
import time
import psutil
from functools import wraps
from typing import Callable, Dict, List
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """성능 모니터링 데코레이터 및 유틸리티"""

    def __init__(self, threshold_seconds: float = 5.0):
        """
        초기화

        Args:
            threshold_seconds: 알림 임계값 (초)
        """
        self.threshold = threshold_seconds
        self.metrics: List[Dict] = []
        self.max_metrics = 1000  # 최대 1000개 메트릭 저장

    def monitor(self, func: Callable):
        """
        함수 실행 시간 및 메모리 모니터링 데코레이터

        Usage:
            @perf_monitor.monitor
            async def my_function():
                ...
        """
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 시작 메트릭
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # 종료 메트릭
                elapsed = time.time() - start_time
                end_memory = process.memory_info().rss / 1024 / 1024
                memory_delta = end_memory - start_memory

                # 메트릭 기록
                metric = {
                    'function': func.__name__,
                    'elapsed': elapsed,
                    'memory_mb': end_memory,
                    'memory_delta': memory_delta,
                    'timestamp': datetime.now().isoformat(),
                    'threshold_exceeded': elapsed > self.threshold
                }

                self._record_metric(metric)

                # 임계값 초과 시 알림
                if elapsed > self.threshold:
                    await self._send_alert(metric)

                # 로깅
                log_level = logging.WARNING if elapsed > self.threshold else logging.DEBUG
                logger.log(
                    log_level,
                    f"{func.__name__} took {elapsed:.2f}s "
                    f"(mem: {end_memory:.1f}MB, delta: {memory_delta:+.1f}MB)"
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 동기 함수 버전
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                end_memory = process.memory_info().rss / 1024 / 1024
                memory_delta = end_memory - start_memory

                metric = {
                    'function': func.__name__,
                    'elapsed': elapsed,
                    'memory_mb': end_memory,
                    'memory_delta': memory_delta,
                    'timestamp': datetime.now().isoformat(),
                    'threshold_exceeded': elapsed > self.threshold
                }

                self._record_metric(metric)

                if elapsed > self.threshold:
                    # 동기 함수에서는 blocking 알림
                    logger.warning(
                        f"⚠️  Performance Alert: {func.__name__} took {elapsed:.2f}s "
                        f"(threshold: {self.threshold}s)"
                    )

                logger.debug(
                    f"{func.__name__} took {elapsed:.2f}s "
                    f"(mem: {end_memory:.1f}MB, delta: {memory_delta:+.1f}MB)"
                )

        # 비동기/동기 함수 구분
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def _record_metric(self, metric: Dict):
        """메트릭 기록 (순환 버퍼)"""
        self.metrics.append(metric)

        # 최대 개수 초과 시 오래된 메트릭 제거
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]

    async def _send_alert(self, metric: Dict):
        """성능 알림 전송"""
        try:
            from backend.notifications.telegram_notifier import create_telegram_notifier

            telegram = create_telegram_notifier()
            await telegram.send_message(
                f"⚠️ Performance Alert\n\n"
                f"Function: {metric['function']}\n"
                f"Time: {metric['elapsed']:.2f}s (threshold: {self.threshold}s)\n"
                f"Memory: {metric['memory_mb']:.1f}MB (delta: {metric['memory_delta']:+.1f}MB)\n"
                f"Timestamp: {metric['timestamp']}"
            )
        except Exception as e:
            logger.error(f"Failed to send performance alert: {e}")

    def get_metrics(
        self,
        function_name: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        메트릭 조회

        Args:
            function_name: 함수명 필터 (None이면 전체)
            limit: 최대 개수

        Returns:
            메트릭 리스트 (최신순)
        """
        if function_name:
            filtered = [m for m in self.metrics if m['function'] == function_name]
        else:
            filtered = self.metrics

        return sorted(filtered, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def get_summary(self) -> Dict:
        """
        성능 요약 통계

        Returns:
            요약 통계 딕셔너리
        """
        if not self.metrics:
            return {'message': 'No metrics collected yet'}

        # 함수별 그룹화
        by_function = {}
        for metric in self.metrics:
            fname = metric['function']
            if fname not in by_function:
                by_function[fname] = []
            by_function[fname].append(metric['elapsed'])

        # 통계 계산
        summary = {}
        for fname, times in by_function.items():
            summary[fname] = {
                'calls': len(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'threshold_exceeded': sum(1 for t in times if t > self.threshold)
            }

        return summary


# 글로벌 모니터 인스턴스
perf_monitor = PerformanceMonitor(threshold_seconds=5.0)


# 편의 함수
def get_performance_summary() -> Dict:
    """성능 요약 조회"""
    return perf_monitor.get_summary()
```

**적용 예시:**

```python
# backend/ai/mvp/war_room_mvp.py
from backend.monitoring.performance_monitor import perf_monitor

class WarRoomMVP:
    @perf_monitor.monitor
    def deliberate(self, symbol, ...):
        """
        5초 초과 시 자동 Telegram 알림
        """
        ...

# backend/data/processors/news_processor.py
from backend.monitoring.performance_monitor import perf_monitor

class NewsProcessor:
    @perf_monitor.monitor
    def process_articles_batched(self, articles):
        """
        처리 시간 자동 추적
        """
        ...
```

**API 엔드포인트:**

**파일**: `backend/api/monitoring_router.py` (신규 생성)

```python
"""
Monitoring API Router

Date: 2026-01-03
"""
from fastapi import APIRouter
from backend.monitoring.performance_monitor import get_performance_summary

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/performance/summary")
async def performance_summary():
    """성능 메트릭 요약"""
    return get_performance_summary()


@router.get("/performance/metrics/{function_name}")
async def performance_metrics(function_name: str, limit: int = 10):
    """함수별 성능 메트릭"""
    from backend.monitoring.performance_monitor import perf_monitor
    return perf_monitor.get_metrics(function_name, limit)
```

**예상 효과:**
- ✅ 실시간 성능 모니터링
- ✅ 5초 초과 함수 자동 알림
- ✅ 성능 히스토리 추적
- ✅ 병목 지점 자동 탐지

---

### 3.3 구현 로드맵 (Performance)

**Week 1: 성능 감사 도구**
- [ ] Day 1: `/performance-audit` 설치 및 테스트
- [ ] Day 2-3: War Room MVP 병렬화 구현
- [ ] Day 4-5: 뉴스 백필 메모리 최적화
- [ ] Day 6-7: 성능 테스트 및 검증

**Week 2: 실시간 모니터링**
- [ ] Day 1-2: PerformanceMonitor 클래스 구현
- [ ] Day 3-4: 주요 함수에 데코레이터 적용
- [ ] Day 5: Telegram 알림 통합
- [ ] Day 6-7: API 엔드포인트 추가

**Week 3: 대시보드 (선택)**
- [ ] Day 1-3: 성능 메트릭 시각화
- [ ] Day 4-5: 히스토리 차트
- [ ] Day 6-7: 자동 리포트 생성

**예상 효과:**
- ✅ War Room MVP: 12.76초 → 7.5초 (41% 개선)
- ✅ 메모리 사용: 450MB → 100MB (78% 감소)
- ✅ 성능 저하 감지: 수동 → 자동 (실시간)

---

## Part 4: Advanced Analytics (고급 분석)

### 목표
- Shadow Trading 통계 분석 고도화
- 샤프/소르티노 비율 자동 계산
- 로컬 임베딩 모델 도입 (비용 절감)
- 티커 추출 정확도 향상 (60% → 90%)

---

### 4.1 Data Scientist Agent

**설치 방법:**
```bash
npx claude-code-templates@latest --agent data-scientist --yes
```

**주요 기능:**
1. Shadow Trading 고급 통계 분석
2. 샤프/소르티노/칼마 비율 계산
3. 연승/연패 분석
4. 통계적 유의성 검정

---

#### Implementation 4-1: Shadow Trading 통계 분석

**파일**: `backend/analytics/shadow_trading_analyzer.py` (신규 생성)

```python
"""
Shadow Trading 통계 분석

Features:
- 샤프 비율 (Sharpe Ratio)
- 소르티노 비율 (Sortino Ratio)
- 칼마 비율 (Calmar Ratio)
- 연승/연패 분석
- 통계적 유의성 검정

Date: 2026-01-03
Author: AI Trading System Team
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ShadowTradingAnalyzer:
    """Shadow Trading 성과 통계 분석"""

    def __init__(self, trades: List[Dict]):
        """
        초기화

        Args:
            trades: 거래 리스트
                [
                    {
                        'symbol': 'AAPL',
                        'action': 'BUY',
                        'entry_price': 150.0,
                        'exit_price': 155.0,
                        'pnl': 500.0,
                        'pnl_pct': 0.033,
                        'created_at': '2026-01-01'
                    },
                    ...
                ]
        """
        self.trades_df = pd.DataFrame(trades)

        if not self.trades_df.empty:
            self.trades_df['created_at'] = pd.to_datetime(self.trades_df['created_at'])
            self.trades_df = self.trades_df.sort_values('created_at')

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        샤프 비율 계산 (연율화)

        Args:
            risk_free_rate: 무위험 수익률 (연율)

        Returns:
            샤프 비율
        """
        if len(self.trades_df) < 2:
            return 0.0

        returns = self.trades_df['pnl_pct'].values

        # 일별 무위험 수익률
        daily_rf = risk_free_rate / 252

        # 초과 수익률
        excess_returns = returns - daily_rf

        if np.std(excess_returns) == 0:
            return 0.0

        # 연율화 (252 거래일 가정)
        sharpe = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252)

        return sharpe

    def calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        소르티노 비율 (하방 리스크만 고려)

        Args:
            risk_free_rate: 무위험 수익률

        Returns:
            소르티노 비율
        """
        returns = self.trades_df['pnl_pct'].values
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf

        # 하방 수익률만 추출
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0

        # 연율화
        sortino = (np.mean(excess_returns) / downside_std) * np.sqrt(252)

        return sortino

    def calculate_calmar_ratio(self) -> float:
        """
        칼마 비율 (연간 수익률 / 최대 낙폭)

        Returns:
            칼마 비율
        """
        if len(self.trades_df) == 0:
            return 0.0

        # 연간 수익률 추정
        annual_return = self.trades_df['pnl_pct'].mean() * 252

        # 최대 낙폭
        mdd = self.calculate_max_drawdown()

        if mdd == 0:
            return 0.0

        return annual_return / abs(mdd)

    def calculate_max_drawdown(self) -> float:
        """
        최대 낙폭 (Maximum Drawdown)

        Returns:
            MDD (음수)
        """
        if len(self.trades_df) == 0:
            return 0.0

        # 누적 수익률
        cumulative = (1 + self.trades_df['pnl_pct']).cumprod()

        # 누적 최대값
        running_max = cumulative.cummax()

        # Drawdown
        drawdown = (cumulative - running_max) / running_max

        return drawdown.min()

    def analyze_win_streaks(self) -> Dict:
        """
        연승/연패 분석

        Returns:
            연승/연패 통계
        """
        if len(self.trades_df) == 0:
            return {
                'max_win_streak': 0,
                'max_loss_streak': 0,
                'current_streak': 0,
                'current_streak_type': 'NONE'
            }

        wins = (self.trades_df['pnl'] > 0).astype(int).values

        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0

        for win in wins:
            if win == 1:
                # 승리
                current_streak = current_streak + 1 if current_streak > 0 else 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                # 손실
                current_streak = current_streak - 1 if current_streak < 0 else -1
                max_loss_streak = max(max_loss_streak, abs(current_streak))

        return {
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'current_streak': abs(current_streak),
            'current_streak_type': 'WIN' if current_streak > 0 else 'LOSS' if current_streak < 0 else 'NONE'
        }

    def statistical_significance_test(self) -> Dict:
        """
        통계적 유의성 검정 (Win Rate > 50%?)

        Returns:
            검정 결과
        """
        if len(self.trades_df) == 0:
            return {
                'win_rate': 0.0,
                'p_value': 1.0,
                'significant': False,
                'confidence_level': 0.0
            }

        wins = len(self.trades_df[self.trades_df['pnl'] > 0])
        total = len(self.trades_df)

        win_rate = wins / total if total > 0 else 0.0

        # 이항 검정 (H0: p = 0.5, H1: p > 0.5)
        p_value = stats.binom_test(wins, total, 0.5, alternative='greater')

        return {
            'win_rate': win_rate,
            'total_trades': total,
            'wins': wins,
            'losses': total - wins,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'confidence_level': (1 - p_value) * 100
        }

    def generate_report(self) -> Dict:
        """
        종합 통계 리포트

        Returns:
            전체 분석 결과
        """
        if len(self.trades_df) == 0:
            return {'error': 'No trades to analyze'}

        return {
            'basic_metrics': {
                'total_trades': len(self.trades_df),
                'win_rate': len(self.trades_df[self.trades_df['pnl'] > 0]) / len(self.trades_df),
                'avg_pnl': float(self.trades_df['pnl'].mean()),
                'total_pnl': float(self.trades_df['pnl'].sum()),
                'avg_pnl_pct': float(self.trades_df['pnl_pct'].mean()),
                'best_trade': float(self.trades_df['pnl'].max()),
                'worst_trade': float(self.trades_df['pnl'].min())
            },
            'risk_metrics': {
                'sharpe_ratio': float(self.calculate_sharpe_ratio()),
                'sortino_ratio': float(self.calculate_sortino_ratio()),
                'calmar_ratio': float(self.calculate_calmar_ratio()),
                'max_drawdown': float(self.calculate_max_drawdown())
            },
            'streak_analysis': self.analyze_win_streaks(),
            'statistical_test': self.statistical_significance_test(),
            'generated_at': datetime.now().isoformat()
        }


# CLI 사용 예시
if __name__ == "__main__":
    # Shadow Trading 데이터 로드
    from backend.execution.shadow_trading import ShadowTradingEngine

    engine = ShadowTradingEngine()
    trades = engine.get_trade_history()

    analyzer = ShadowTradingAnalyzer(trades)
    report = analyzer.generate_report()

    print("📊 Shadow Trading Statistical Analysis")
    print("=" * 60)
    print(f"Total Trades: {report['basic_metrics']['total_trades']}")
    print(f"Win Rate: {report['basic_metrics']['win_rate']:.1%}")
    print(f"Sharpe Ratio: {report['risk_metrics']['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {report['risk_metrics']['sortino_ratio']:.2f}")
    print(f"Calmar Ratio: {report['risk_metrics']['calmar_ratio']:.2f}")
    print(f"Max Drawdown: {report['risk_metrics']['max_drawdown']:.2%}")
    print(f"\nStatistical Significance: {report['statistical_test']['significant']}")
    print(f"P-value: {report['statistical_test']['p_value']:.4f}")
```

**API 엔드포인트:**

**파일**: `backend/api/analytics_router.py` (신규 생성)

```python
"""
Analytics API Router

Date: 2026-01-03
"""
from fastapi import APIRouter
from backend.analytics.shadow_trading_analyzer import ShadowTradingAnalyzer
from backend.execution.shadow_trading import ShadowTradingEngine

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/shadow-trading/report")
async def shadow_trading_report():
    """Shadow Trading 통계 리포트"""
    engine = ShadowTradingEngine()
    trades = engine.get_trade_history()

    analyzer = ShadowTradingAnalyzer(trades)
    return analyzer.generate_report()


@router.get("/shadow-trading/metrics")
async def shadow_trading_metrics():
    """주요 메트릭만 반환"""
    engine = ShadowTradingEngine()
    trades = engine.get_trade_history()

    analyzer = ShadowTradingAnalyzer(trades)
    report = analyzer.generate_report()

    return {
        'win_rate': report['basic_metrics']['win_rate'],
        'sharpe_ratio': report['risk_metrics']['sharpe_ratio'],
        'sortino_ratio': report['risk_metrics']['sortino_ratio'],
        'max_drawdown': report['risk_metrics']['max_drawdown'],
        'statistical_significance': report['statistical_test']['significant']
    }
```

**예상 효과:**
- ✅ 샤프 비율 자동 계산
- ✅ 주간 통계 리포트 자동 생성
- ✅ 통계적 유의성 검증

---

### Component 4.2: NLP Engineer Agent - 로컬 임베딩 및 티커 추출 고도화

**현재 상태:**
- OpenAI API 사용 (text-embedding-ada-002): $0.0001/1K tokens
- 월간 임베딩 비용: ~$15-30
- 티커 추출: 정규표현식 기반 (정확도 ~85%)
- spaCy 미사용
- Custom NER 모델 없음

**목표:**
- OpenAI 임베딩 → 로컬 임베딩 전환 (비용 $0)
- 티커 추출 정확도: 85% → 95%+
- 금융 도메인 NER 모델 구축
- 뉴스 sentiment 분석 고도화

---

#### 4.2.1 로컬 임베딩 전환 (Sentence Transformers)

**목표:**
- OpenAI API 의존성 제거
- 비용 절감 (월 $30 → $0)
- 속도 개선 (네트워크 I/O 제거)

**구현:**

**파일:** `backend/ai/embeddings/local_embedder.py` (신규)

```python
"""
로컬 임베딩 모델 구현 (Sentence Transformers)

Date: 2026-01-03
Component: NLP Engineer Agent - Local Embeddings
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class LocalEmbedder:
    """
    Sentence Transformers 기반 로컬 임베딩

    Models:
    - all-MiniLM-L6-v2: 384 dim, 빠름 (80MB)
    - all-mpnet-base-v2: 768 dim, 정확함 (420MB) - 권장
    """

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Args:
            model_name: HuggingFace 모델명
        """
        self.model_name = model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        logger.info(f"Loading embedding model: {model_name} on {self.device}")
        self.model = SentenceTransformer(model_name, device=self.device)

        # 모델 정보
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        텍스트 리스트를 임베딩 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            show_progress: 진행률 표시

        Returns:
            (N, embedding_dim) numpy array
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # 코사인 유사도용 정규화
        )

        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """단일 텍스트 임베딩"""
        return self.encode([text])[0]

    @lru_cache(maxsize=1000)
    def encode_cached(self, text: str) -> tuple:
        """
        캐시된 임베딩 (자주 사용되는 쿼리용)

        Note: lru_cache는 hashable 타입만 지원하므로 tuple 반환
        """
        embedding = self.encode_single(text)
        return tuple(embedding.tolist())

    def similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간 코사인 유사도"""
        emb1 = self.encode_single(text1)
        emb2 = self.encode_single(text2)

        # 이미 정규화됨 → 내적 = 코사인 유사도
        similarity = np.dot(emb1, emb2)
        return float(similarity)

    def find_similar(
        self,
        query: str,
        corpus: List[str],
        top_k: int = 5
    ) -> List[tuple]:
        """
        쿼리와 유사한 상위 K개 텍스트 찾기

        Returns:
            List of (index, similarity_score, text)
        """
        query_emb = self.encode_single(query)
        corpus_embs = self.encode(corpus)

        # 코사인 유사도 계산
        similarities = corpus_embs @ query_emb  # (N,) array

        # 상위 K개
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [
            (int(idx), float(similarities[idx]), corpus[idx])
            for idx in top_indices
        ]

        return results


# Singleton instance
_embedder_instance: Optional[LocalEmbedder] = None


def get_embedder(model_name: str = 'all-mpnet-base-v2') -> LocalEmbedder:
    """싱글톤 임베더 인스턴스"""
    global _embedder_instance

    if _embedder_instance is None:
        _embedder_instance = LocalEmbedder(model_name)

    return _embedder_instance
```

**마이그레이션 스크립트:** `backend/scripts/migrate_embeddings.py` (신규)

```python
"""
OpenAI 임베딩 → 로컬 임베딩 마이그레이션

Usage:
    python backend/scripts/migrate_embeddings.py --batch-size 100
"""

import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import NewsArticle
from backend.ai.embeddings.local_embedder import get_embedder
from tqdm import tqdm
import numpy as np


def migrate_embeddings(batch_size: int = 100, dry_run: bool = False):
    """기존 뉴스 기사 임베딩 재계산"""

    # DB 연결
    from backend.config import settings
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 로컬 임베더 로드
    embedder = get_embedder()
    print(f"✅ Embedder loaded: {embedder.model_name} (dim={embedder.embedding_dim})")

    # OpenAI 임베딩이 있는 기사 조회
    articles = session.query(NewsArticle).filter(
        NewsArticle.embedding.isnot(None)
    ).all()

    print(f"📊 Total articles to migrate: {len(articles)}")

    if dry_run:
        print("🔍 DRY RUN - No changes will be made")
        return

    # 배치 처리
    for i in tqdm(range(0, len(articles), batch_size), desc="Migrating"):
        batch = articles[i:i+batch_size]

        # 텍스트 추출
        texts = [
            f"{article.title}\n{article.content[:500]}"
            for article in batch
        ]

        # 로컬 임베딩 생성
        embeddings = embedder.encode(texts, batch_size=batch_size)

        # DB 업데이트
        for article, embedding in zip(batch, embeddings):
            # PostgreSQL ARRAY로 저장 (pgvector 사용 시 vector 타입)
            article.embedding = embedding.tolist()

        session.commit()

    print("✅ Migration completed!")

    # 통계
    avg_similarity = verify_migration(session, embedder, sample_size=10)
    print(f"📈 Avg similarity (OpenAI vs Local): {avg_similarity:.3f}")


def verify_migration(session, embedder, sample_size: int = 10):
    """마이그레이션 검증 (샘플링)"""
    import random

    articles = session.query(NewsArticle).limit(sample_size).all()

    similarities = []
    for article in articles:
        # 로컬 임베딩 재계산
        text = f"{article.title}\n{article.content[:500]}"
        new_emb = embedder.encode_single(text)

        # 기존 임베딩과 비교
        old_emb = np.array(article.embedding)

        # 정규화
        old_emb = old_emb / np.linalg.norm(old_emb)

        # 코사인 유사도
        sim = np.dot(old_emb, new_emb)
        similarities.append(sim)

    return np.mean(similarities)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    migrate_embeddings(args.batch_size, args.dry_run)
```

**Repository 업데이트:** `backend/database/repository.py`

```python
# Lines 90-105: add_article() 메서드 수정

from backend.ai.embeddings.local_embedder import get_embedder

class NewsRepository:
    def __init__(self, session):
        self.session = session
        self.embedder = get_embedder()  # 로컬 임베더

    def add_article(self, article_data: dict) -> NewsArticle:
        # ... 기존 로직

        # 임베딩 생성 (OpenAI 대신 로컬)
        text = f"{article_data['title']}\n{article_data['content'][:500]}"
        embedding = self.embedder.encode_single(text)

        article = NewsArticle(
            **article_data,
            embedding=embedding.tolist()  # numpy → list
        )

        self.session.add(article)
        self.session.commit()

        return article
```

**예상 효과:**
- ✅ 비용 절감: $30/월 → $0
- ✅ 속도 개선: 200ms/article → 50ms/article (4배 고속화)
- ✅ 오프라인 작동 가능
- ⚠️ 초기 모델 다운로드: ~420MB

**설치:**
```bash
pip install sentence-transformers
```

---

#### 4.2.2 금융 도메인 NER (Named Entity Recognition)

**목표:**
- 티커 추출 정확도: 85% → 95%+
- 회사명 → 티커 매핑
- 금융 용어 인식 (IPO, M&A, earnings, etc.)

**구현:**

**파일:** `backend/ai/ner/ticker_extractor.py` (신규)

```python
"""
금융 도메인 NER - 티커 및 회사명 추출

Date: 2026-01-03
Component: NLP Engineer Agent - Ticker Extraction
"""

import re
import spacy
from typing import List, Dict, Set, Tuple
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class TickerExtractor:
    """
    티커 심볼 및 회사명 추출

    Methods:
    1. 정규표현식 (기본)
    2. spaCy NER (회사명)
    3. 커스텀 사전 (NASDAQ/NYSE 매핑)
    """

    def __init__(self):
        # spaCy 모델 로드
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None

        # 티커 → 회사명 매핑
        self.ticker_to_company = self._load_ticker_mapping()

        # 회사명 → 티커 역방향 매핑
        self.company_to_ticker = {
            v.lower(): k for k, v in self.ticker_to_company.items()
        }

        # 알려진 티커 집합 (빠른 검색)
        self.known_tickers = set(self.ticker_to_company.keys())

    def _load_ticker_mapping(self) -> Dict[str, str]:
        """
        티커 → 회사명 매핑 로드

        TODO: DB에서 로드하거나 CSV 파일 사용
        """
        return {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'NVDA': 'NVIDIA Corporation',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'AMD': 'Advanced Micro Devices Inc.',
            'INTC': 'Intel Corporation',
            'QCOM': 'Qualcomm Incorporated',
            # ... 더 많은 매핑 필요 (현재 ~50개, 목표 500+개)
        }

    def extract_tickers_regex(self, text: str) -> List[str]:
        """
        정규표현식 기반 티커 추출 (기본 방법)

        패턴:
        - 대문자 1-5자 (예: AAPL, GOOGL)
        - $ 접두사 (예: $TSLA)
        - 괄호 내 (예: Apple (AAPL))
        """
        tickers = set()

        # 패턴 1: $TICKER
        pattern1 = r'\$([A-Z]{1,5})\b'
        tickers.update(re.findall(pattern1, text))

        # 패턴 2: (TICKER)
        pattern2 = r'\(([A-Z]{1,5})\)'
        tickers.update(re.findall(pattern2, text))

        # 패턴 3: TICKER (단어 경계)
        # 주의: USA, CEO 등 제외 필요
        pattern3 = r'\b([A-Z]{2,5})\b'
        candidates = re.findall(pattern3, text)

        # 알려진 티커만 포함
        for candidate in candidates:
            if candidate in self.known_tickers:
                tickers.add(candidate)

        return sorted(tickers)

    def extract_companies_ner(self, text: str) -> List[Tuple[str, str]]:
        """
        spaCy NER로 회사명 추출 후 티커 매핑

        Returns:
            List of (company_name, ticker)
        """
        if not self.nlp:
            return []

        doc = self.nlp(text)
        results = []

        for ent in doc.ents:
            if ent.label_ == 'ORG':  # Organization
                company_name = ent.text

                # 회사명 → 티커 매핑
                company_lower = company_name.lower()

                # 정확 매칭
                if company_lower in self.company_to_ticker:
                    ticker = self.company_to_ticker[company_lower]
                    results.append((company_name, ticker))
                else:
                    # 부분 매칭 (예: "Apple" → "Apple Inc.")
                    for full_name, ticker in self.company_to_ticker.items():
                        if company_lower in full_name or full_name in company_lower:
                            results.append((company_name, ticker))
                            break

        return results

    def extract_all(self, text: str) -> Dict[str, any]:
        """
        통합 추출 (정규표현식 + NER)

        Returns:
            {
                'tickers': ['AAPL', 'NVDA'],
                'companies': [('Apple Inc.', 'AAPL')],
                'confidence': 0.95
            }
        """
        # Method 1: 정규표현식
        tickers_regex = set(self.extract_tickers_regex(text))

        # Method 2: NER
        companies_ner = self.extract_companies_ner(text)
        tickers_ner = {ticker for _, ticker in companies_ner}

        # 결합
        all_tickers = tickers_regex | tickers_ner

        # 신뢰도 계산
        confidence = 1.0 if tickers_ner else 0.85  # NER 매칭 시 높은 신뢰도

        return {
            'tickers': sorted(all_tickers),
            'companies': companies_ner,
            'confidence': confidence,
            'methods': {
                'regex': sorted(tickers_regex),
                'ner': sorted(tickers_ner)
            }
        }


# Singleton
_extractor_instance = None


def get_ticker_extractor() -> TickerExtractor:
    """싱글톤 추출기"""
    global _extractor_instance

    if _extractor_instance is None:
        _extractor_instance = TickerExtractor()

    return _extractor_instance
```

**사용 예시:**

```python
from backend.ai.ner.ticker_extractor import get_ticker_extractor

extractor = get_ticker_extractor()

text = """
Apple (AAPL) reported record earnings today.
NVIDIA shares surged 5% on strong AI demand.
Tesla CEO Elon Musk announced $TSLA price cuts.
"""

result = extractor.extract_all(text)

print(result)
# {
#     'tickers': ['AAPL', 'NVDA', 'TSLA'],
#     'companies': [
#         ('Apple', 'AAPL'),
#         ('NVIDIA', 'NVDA'),
#         ('Tesla', 'TSLA')
#     ],
#     'confidence': 1.0,
#     'methods': {
#         'regex': ['AAPL', 'TSLA'],
#         'ner': ['AAPL', 'NVDA', 'TSLA']
#     }
# }
```

**Repository 통합:** `backend/database/repository.py`

```python
from backend.ai.ner.ticker_extractor import get_ticker_extractor

class NewsRepository:
    def __init__(self, session):
        self.session = session
        self.ticker_extractor = get_ticker_extractor()

    def add_article(self, article_data: dict) -> NewsArticle:
        # 티커 추출 (개선된 방법)
        text = f"{article_data['title']} {article_data['content']}"
        extraction = self.ticker_extractor.extract_all(text)

        article = NewsArticle(
            **article_data,
            tickers=extraction['tickers'],  # 추출된 티커 리스트
            companies=extraction['companies'],  # 회사명-티커 매핑
            ticker_confidence=extraction['confidence']  # 신뢰도
        )

        self.session.add(article)
        self.session.commit()

        return article
```

**예상 효과:**
- ✅ 티커 추출 정확도: 85% → 95%+
- ✅ 회사명 매핑 지원
- ✅ False positive 감소 (USA, CEO 등 제외)

**설치:**
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

---

#### 4.2.3 Sentiment 분석 고도화

**현재 상태:**
- 단순 키워드 기반 sentiment (positive/negative/neutral)
- 수동 규칙

**개선 방향:**
- FinBERT 모델 사용 (금융 도메인 특화)
- 감정 점수 (-1 ~ +1)
- 문장 단위 sentiment

**파일:** `backend/ai/sentiment/finbert_analyzer.py` (신규)

```python
"""
FinBERT 기반 Sentiment 분석

Date: 2026-01-03
Component: NLP Engineer Agent - Sentiment Analysis
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Dict
import numpy as np

class FinBERTAnalyzer:
    """
    FinBERT: 금융 도메인 Sentiment 분석

    Model: ProsusAI/finbert
    Labels: positive, negative, neutral
    """

    def __init__(self, model_name: str = 'ProsusAI/finbert'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()

        # Label mapping
        self.id2label = {0: 'positive', 1: 'negative', 2: 'neutral'}

    def analyze(self, text: str) -> Dict[str, any]:
        """
        Sentiment 분석

        Returns:
            {
                'label': 'positive',
                'score': 0.92,
                'scores': {'positive': 0.92, 'negative': 0.05, 'neutral': 0.03}
            }
        """
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0]

        # 최고 확률 레이블
        label_id = torch.argmax(probs).item()
        label = self.id2label[label_id]
        score = probs[label_id].item()

        return {
            'label': label,
            'score': score,
            'scores': {
                'positive': probs[0].item(),
                'negative': probs[1].item(),
                'neutral': probs[2].item()
            },
            'sentiment_score': probs[0].item() - probs[1].item()  # -1 ~ +1
        }
```

**예상 효과:**
- ✅ 금융 도메인 특화 sentiment
- ✅ 정량적 점수 제공
- ⚠️ 모델 크기: ~440MB

---

### 구현 로드맵 (NLP Engineer Agent)

**Week 1: 로컬 임베딩**
- [ ] Sentence Transformers 설치
- [ ] LocalEmbedder 구현
- [ ] 마이그레이션 스크립트 작성
- [ ] 기존 뉴스 재임베딩 (배치)

**Week 2: 티커 추출**
- [ ] spaCy 설치 및 모델 다운로드
- [ ] TickerExtractor 구현
- [ ] 티커 매핑 DB 구축 (500+ 티커)
- [ ] Repository 통합

**Week 3: Sentiment 분석**
- [ ] FinBERT 설치
- [ ] FinBERTAnalyzer 구현
- [ ] 기존 뉴스 sentiment 재계산
- [ ] API 엔드포인트 추가

**Week 4: 검증 및 튜닝**
- [ ] 정확도 측정 (수동 라벨링 샘플)
- [ ] 성능 벤치마크
- [ ] 문서화

**예상 효과:**
- 임베딩 비용: $30/월 → $0
- 티커 추출 정확도: 85% → 95%+
- Sentiment 정확도: 70% → 85%+

---

## Part 5: Cloud & Infrastructure - AWS Integration MCP

### Component 5.1: AWS Integration MCP - S3 백업 및 Lambda 백필

**현재 상태:**
- 로컬 파일 시스템 백업만 존재
- 클라우드 백업 없음
- 데이터 백필 수동 실행

**목표:**
- S3 자동 백업 (일일/주간)
- Lambda 데이터 백필 자동화
- 재해 복구 시스템 구축

---

#### 5.1.1 S3 백업 시스템

**구현:**

**파일:** `backend/cloud/s3_backup.py` (신규)

```python
"""
S3 자동 백업 시스템

Date: 2026-01-03
Component: AWS Integration MCP - S3 Backup
"""

import boto3
from datetime import datetime, timedelta
import gzip
import json
import logging
from pathlib import Path
from typing import Optional
import os

logger = logging.getLogger(__name__)


class S3BackupManager:
    """
    PostgreSQL 백업을 S3에 저장

    Backup Types:
    - Daily: 매일 자정
    - Weekly: 매주 일요일
    - Monthly: 매월 1일
    """

    def __init__(
        self,
        bucket_name: str = 'ai-trading-backups',
        region: str = 'us-east-1'
    ):
        self.bucket_name = bucket_name
        self.region = region

        # AWS 클라이언트
        self.s3 = boto3.client('s3', region_name=region)

        # 버킷 존재 확인 (없으면 생성)
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """S3 버킷 생성 (없으면)"""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ S3 bucket exists: {self.bucket_name}")
        except:
            logger.info(f"Creating S3 bucket: {self.bucket_name}")
            self.s3.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={'LocationConstraint': self.region}
            )

            # Lifecycle policy (90일 후 Glacier로 이동)
            self.s3.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'Id': 'MoveToGlacier',
                            'Status': 'Enabled',
                            'Transitions': [
                                {'Days': 90, 'StorageClass': 'GLACIER'}
                            ],
                            'Expiration': {'Days': 365}
                        }
                    ]
                }
            )

    def backup_database(self, backup_type: str = 'daily') -> str:
        """
        PostgreSQL 전체 백업

        Args:
            backup_type: daily|weekly|monthly

        Returns:
            S3 key (경로)
        """
        from backend.config import settings

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"/tmp/db_backup_{timestamp}.sql"

        # pg_dump 실행
        db_url = settings.DATABASE_URL
        # postgresql://user:pass@host:port/dbname 파싱
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        if not match:
            raise ValueError("Invalid DATABASE_URL format")

        user, password, host, port, dbname = match.groups()

        cmd = f"PGPASSWORD={password} pg_dump -h {host} -p {port} -U {user} -d {dbname} -F c -f {backup_file}"
        os.system(cmd)

        # Gzip 압축
        gzip_file = f"{backup_file}.gz"
        with open(backup_file, 'rb') as f_in:
            with gzip.open(gzip_file, 'wb') as f_out:
                f_out.writelines(f_in)

        # S3 업로드
        s3_key = f"backups/{backup_type}/{timestamp}/database.sql.gz"

        self.s3.upload_file(
            gzip_file,
            self.bucket_name,
            s3_key,
            ExtraArgs={'StorageClass': 'STANDARD_IA'}  # Infrequent Access
        )

        logger.info(f"✅ Backup uploaded: s3://{self.bucket_name}/{s3_key}")

        # 로컬 파일 삭제
        os.remove(backup_file)
        os.remove(gzip_file)

        return s3_key

    def backup_files(self, directory: Path, backup_type: str = 'daily') -> str:
        """
        파일 디렉토리 백업 (docs/, logs/ 등)

        Returns:
            S3 key prefix
        """
        import tarfile

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tar_file = f"/tmp/{directory.name}_{timestamp}.tar.gz"

        # Tar 압축
        with tarfile.open(tar_file, 'w:gz') as tar:
            tar.add(directory, arcname=directory.name)

        # S3 업로드
        s3_key = f"backups/{backup_type}/{timestamp}/{directory.name}.tar.gz"

        self.s3.upload_file(tar_file, self.bucket_name, s3_key)

        logger.info(f"✅ Files uploaded: s3://{self.bucket_name}/{s3_key}")

        os.remove(tar_file)

        return s3_key

    def list_backups(self, backup_type: Optional[str] = None) -> list:
        """백업 목록 조회"""
        prefix = f"backups/{backup_type}/" if backup_type else "backups/"

        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )

        backups = []
        for obj in response.get('Contents', []):
            backups.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            })

        return backups

    def restore_database(self, s3_key: str, target_db: str = 'ai_trading_restored'):
        """
        S3 백업에서 DB 복원

        Args:
            s3_key: S3 객체 키
            target_db: 복원할 데이터베이스명
        """
        # S3 다운로드
        local_file = "/tmp/restore.sql.gz"
        self.s3.download_file(self.bucket_name, s3_key, local_file)

        # 압축 해제
        sql_file = "/tmp/restore.sql"
        with gzip.open(local_file, 'rb') as f_in:
            with open(sql_file, 'wb') as f_out:
                f_out.write(f_in.read())

        # pg_restore 실행
        from backend.config import settings
        # ... (위와 동일한 파싱)

        cmd = f"PGPASSWORD={password} pg_restore -h {host} -p {port} -U {user} -d {target_db} -c {sql_file}"
        os.system(cmd)

        logger.info(f"✅ Database restored to: {target_db}")

        os.remove(local_file)
        os.remove(sql_file)


# 스케줄러
def schedule_daily_backup():
    """일일 백업 (Cron 또는 APScheduler)"""
    manager = S3BackupManager()

    # DB 백업
    manager.backup_database('daily')

    # Docs 백업
    manager.backup_files(Path('docs'), 'daily')

    # Logs 백업 (7일치만)
    manager.backup_files(Path('logs'), 'daily')
```

**Cron 설정:**
```bash
# crontab -e
0 0 * * * cd /opt/ai-trading-system && python -c "from backend.cloud.s3_backup import schedule_daily_backup; schedule_daily_backup()"
```

**예상 효과:**
- ✅ 재해 복구 가능
- ✅ 자동 백업 (매일)
- ✅ 스토리지 비용 최적화 (Glacier)
- 💰 월 비용: ~$5-10 (100GB 백업 기준)

---

#### 5.1.2 Lambda 데이터 백필 자동화

**목표:**
- 주간 자동 백필 (Yahoo Finance)
- 서버리스 실행 (비용 절감)

**Lambda 함수:** `lambda/backfill_weekly.py`

```python
"""
AWS Lambda - 주간 데이터 백필

Trigger: CloudWatch Events (매주 일요일 오전 2시)
"""

import json
import boto3
import requests
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """
    주간 데이터 백필 실행

    1. 전주 월~금 주가 데이터 백필
    2. 완료 후 Telegram 알림
    """

    # 백필 대상 기간
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_friday = last_monday + timedelta(days=4)

    start_date = last_monday.strftime('%Y-%m-%d')
    end_date = last_friday.strftime('%Y-%m-%d')

    # Tickers (S&P 500 상위 50개)
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META',
        # ... (생략)
    ]

    # API 호출 (EC2 백엔드)
    api_url = "https://api.ai-trading.com/api/backfill/prices"

    response = requests.post(api_url, json={
        'tickers': tickers,
        'start_date': start_date,
        'end_date': end_date,
        'interval': '1d'
    })

    if response.status_code == 200:
        job_id = response.json()['job_id']

        # Telegram 알림
        send_telegram_notification(
            f"✅ Weekly backfill started\n"
            f"Period: {start_date} ~ {end_date}\n"
            f"Job ID: {job_id}"
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'job_id': job_id})
        }
    else:
        return {
            'statusCode': 500,
            'body': 'Backfill failed'
        }


def send_telegram_notification(message: str):
    """Telegram 알림"""
    import os

    bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={'chat_id': chat_id, 'text': message})
```

**배포:**
```bash
# Lambda 함수 생성
aws lambda create-function \
  --function-name ai-trading-weekly-backfill \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler backfill_weekly.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --environment Variables="{TELEGRAM_BOT_TOKEN=xxx,TELEGRAM_CHAT_ID=yyy}"

# CloudWatch Events 트리거
aws events put-rule \
  --name weekly-backfill \
  --schedule-expression "cron(0 2 ? * SUN *)"  # 매주 일요일 오전 2시

aws events put-targets \
  --rule weekly-backfill \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:ai-trading-weekly-backfill"
```

**예상 효과:**
- ✅ 수동 백필 제거
- ✅ 서버리스 실행 (EC2 부하 없음)
- 💰 Lambda 비용: ~$0.20/월

---

## Part 6: Communication & Notifications - Discord/Slack Integration

### Component 6.1: Discord Notifications

**현재 상태:**
- Telegram만 지원
- Discord 미연동

**목표:**
- Discord Webhook 알림
- Embed 형식 메시지
- 채널별 분류 (거래, 알림, 에러)

**구현:**

**파일:** `backend/notifications/discord_notifier.py` (신규)

```python
"""
Discord Webhook 알림

Date: 2026-01-03
Component: Discord/Slack Integration
"""

import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """
    Discord Webhook 알림 클래스

    Channels:
    - #trading: 거래 신호 및 실행
    - #alerts: 중요 알림 (Kill Switch 등)
    - #errors: 시스템 에러
    """

    def __init__(
        self,
        webhook_url_trading: str,
        webhook_url_alerts: str,
        webhook_url_errors: str
    ):
        self.webhooks = {
            'trading': webhook_url_trading,
            'alerts': webhook_url_alerts,
            'errors': webhook_url_errors
        }

    def send_embed(
        self,
        channel: str,
        title: str,
        description: str,
        color: int = 0x00ff00,  # 녹색
        fields: Optional[list] = None
    ):
        """
        Discord Embed 메시지 전송

        Args:
            channel: trading|alerts|errors
            title: 제목
            description: 본문
            color: RGB 색상 (hex)
            fields: [{name, value, inline}] 리스트
        """
        webhook_url = self.webhooks.get(channel)
        if not webhook_url:
            logger.error(f"Unknown channel: {channel}")
            return

        embed = {
            'title': title,
            'description': description,
            'color': color,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {'text': 'AI Trading System'}
        }

        if fields:
            embed['fields'] = fields

        payload = {'embeds': [embed]}

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"✅ Discord notification sent: {channel}")
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")

    def send_trading_signal(self, signal: Dict):
        """거래 신호 알림"""
        self.send_embed(
            channel='trading',
            title=f"🔔 Trading Signal: {signal['ticker']}",
            description=f"Action: **{signal['action']}**",
            color=0x00ff00 if signal['action'] == 'BUY' else 0xff0000,
            fields=[
                {'name': 'Confidence', 'value': f"{signal['confidence']:.1%}", 'inline': True},
                {'name': 'Price', 'value': f"${signal['price']:.2f}", 'inline': True},
                {'name': 'Reasoning', 'value': signal['reasoning'][:200], 'inline': False}
            ]
        )

    def send_kill_switch_alert(self, reason: str, details: Dict):
        """Kill Switch 발동 알림"""
        self.send_embed(
            channel='alerts',
            title="🚨 KILL SWITCH ACTIVATED",
            description=f"Reason: **{reason}**",
            color=0xff0000,  # 빨간색
            fields=[
                {'name': 'Daily Loss', 'value': f"{details.get('daily_loss_pct', 0):.2f}%", 'inline': True},
                {'name': 'Threshold', 'value': f"{details.get('threshold_pct', 5):.2f}%", 'inline': True},
                {'name': 'Action', 'value': '**ALL TRADING HALTED**', 'inline': False}
            ]
        )

    def send_error(self, error_type: str, message: str):
        """시스템 에러 알림"""
        self.send_embed(
            channel='errors',
            title=f"❌ Error: {error_type}",
            description=message,
            color=0xffa500  # 주황색
        )
```

**환경 변수 (.env):**
```bash
DISCORD_WEBHOOK_TRADING=https://discord.com/api/webhooks/xxx/yyy
DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/xxx/zzz
DISCORD_WEBHOOK_ERRORS=https://discord.com/api/webhooks/xxx/www
```

**사용 예시:**

```python
from backend.notifications.discord_notifier import DiscordNotifier
from backend.config import settings

discord = DiscordNotifier(
    webhook_url_trading=settings.DISCORD_WEBHOOK_TRADING,
    webhook_url_alerts=settings.DISCORD_WEBHOOK_ALERTS,
    webhook_url_errors=settings.DISCORD_WEBHOOK_ERRORS
)

# 거래 신호
discord.send_trading_signal({
    'ticker': 'AAPL',
    'action': 'BUY',
    'confidence': 0.85,
    'price': 150.00,
    'reasoning': 'Strong earnings beat, positive momentum'
})

# Kill Switch
discord.send_kill_switch_alert('daily_loss', {
    'daily_loss_pct': 5.2,
    'threshold_pct': 5.0
})

# 에러
discord.send_error('API_ERROR', 'Yahoo Finance API timeout')
```

**예상 효과:**
- ✅ 실시간 알림 (Discord 모바일 앱)
- ✅ Rich formatting (Embed)
- ✅ 채널별 분류
- 💰 비용: $0 (무료)

---

### Component 6.2: Slack Integration (선택 사항)

**구현:** Discord와 유사한 패턴

```python
class SlackNotifier:
    """Slack Webhook 알림"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_message(self, text: str, blocks: Optional[list] = None):
        """Slack Block Kit 메시지"""
        payload = {'text': text}
        if blocks:
            payload['blocks'] = blocks

        requests.post(self.webhook_url, json=payload)
```

---

## Part 7: 전체 구현 타임라인

### Month 1: Security & DevOps (Foundation)

**Week 1: Security Hardening**
- [ ] SecretsManager 구현
- [ ] OWASP Top 10 스캐너 통합
- [ ] Pre-commit hooks 설정

**Week 2: CI/CD Pipeline**
- [ ] GitHub Actions 워크플로우 작성
- [ ] Docker 멀티 스테이지 빌드
- [ ] Codecov 통합

**Week 3: Blue-Green Deployment**
- [ ] Nginx 설정
- [ ] 배포 스크립트 작성
- [ ] Rollback 테스트

**Week 4: 검증 및 문서화**
- [ ] 전체 CI/CD 파이프라인 테스트
- [ ] 보안 감사 실행
- [ ] 문서 작성

---

### Month 2: Performance & Analytics

**Week 1: War Room MVP 병렬화**
- [ ] ThreadPoolExecutor 적용
- [ ] 성능 측정 (8s → 3s)
- [ ] 에러 처리 개선

**Week 2: Memory Optimization**
- [ ] Generator 패턴 적용
- [ ] 배치 처리 구현
- [ ] 메모리 프로파일링

**Week 3: Shadow Trading Analytics**
- [ ] ShadowTradingAnalyzer 구현
- [ ] Sharpe/Sortino/Calmar 계산
- [ ] 통계적 유의성 테스트

**Week 4: Performance Monitoring**
- [ ] PerformanceMonitor 데코레이터
- [ ] Telegram/Discord 알림
- [ ] 대시보드 구축

---

### Month 3: NLP & Cloud

**Week 1: Local Embeddings**
- [ ] Sentence Transformers 설치
- [ ] LocalEmbedder 구현
- [ ] 기존 뉴스 재임베딩

**Week 2: Ticker Extraction**
- [ ] spaCy NER 구현
- [ ] 티커 매핑 DB 구축
- [ ] Repository 통합

**Week 3: AWS S3 Backup**
- [ ] S3BackupManager 구현
- [ ] 일일 백업 스케줄
- [ ] 복원 테스트

**Week 4: Lambda Backfill**
- [ ] Lambda 함수 작성
- [ ] CloudWatch Events 설정
- [ ] 자동화 검증

---

### Month 4: Communication & Integration

**Week 1: Discord Integration**
- [ ] DiscordNotifier 구현
- [ ] Webhook 설정
- [ ] Embed 메시지 테스트

**Week 2: FinBERT Sentiment**
- [ ] FinBERT 설치
- [ ] Sentiment 분석 통합
- [ ] 기존 뉴스 재계산

**Week 3: System Integration**
- [ ] 모든 컴포넌트 통합 테스트
- [ ] 성능 벤치마크
- [ ] End-to-End 검증

**Week 4: 문서화 및 배포**
- [ ] 전체 시스템 문서화
- [ ] Production 배포
- [ ] 모니터링 및 튜닝

---

## 성공 기준 (Success Criteria)

### Security & Compliance
- [ ] 시크릿 암호화 100% (git에 노출 0건)
- [ ] OWASP Top 10 스캔 통과
- [ ] Pre-commit 검증 100% 적용
- [ ] 보안 감사 PASS

### DevOps & CI/CD
- [ ] GitHub Actions 파이프라인 100% 성공
- [ ] 배포 다운타임 < 1분
- [ ] Rollback 시간 < 5분
- [ ] 테스트 커버리지 > 90%

### Performance
- [ ] War Room MVP: 8.2s → 3s 이하
- [ ] News ingestion: 200ms → 50ms
- [ ] Shadow Trading 분석: < 1s
- [ ] 메모리 사용량 < 2GB

### Analytics
- [ ] Sharpe ratio 자동 계산
- [ ] 통계적 유의성 검증
- [ ] 주간 리포트 자동 생성
- [ ] 성능 메트릭 실시간 모니터링

### NLP
- [ ] 임베딩 비용: $30/월 → $0
- [ ] 티커 추출 정확도: 85% → 95%+
- [ ] Sentiment 정확도: 70% → 85%+
- [ ] NER 회사명 매핑 500+ 티커

### Cloud & Infrastructure
- [ ] S3 백업 자동화 (일일)
- [ ] Lambda 백필 자동화 (주간)
- [ ] 재해 복구 시간 < 4시간
- [ ] 스토리지 비용 < $10/월

### Communication
- [ ] Discord/Telegram 알림 100% 전달
- [ ] Embed 메시지 Rich formatting
- [ ] 채널별 분류 정확도 100%
- [ ] 알림 지연 < 5초

---

## 비용 분석 (Cost Analysis)

### 월간 운영 비용

| 항목 | 현재 | 구현 후 | 절감 |
|------|------|---------|------|
| OpenAI Embeddings | $30 | $0 | -$30 |
| AWS S3 (100GB) | $0 | $5 | +$5 |
| AWS Lambda | $0 | $0.20 | +$0.20 |
| Discord/Slack | $0 | $0 | $0 |
| **Total** | **$30** | **$5.20** | **-$24.80** |

**연간 절감: $297.60**

---

## 리스크 및 완화 전략 (Risk Mitigation)

### 기술적 리스크

**1. 로컬 임베딩 품질 저하**
- **리스크**: OpenAI보다 품질 낮을 수 있음
- **완화책**: A/B 테스트, 유사도 검증, 필요시 all-mpnet-base-v2 (더 큰 모델) 사용

**2. AWS 비용 초과**
- **리스크**: S3 스토리지 예상보다 많을 수 있음
- **완화책**: Lifecycle policy (90일 후 Glacier), 압축, 불필요한 백업 제거

**3. Lambda Cold Start**
- **리스크**: 첫 실행 시 지연
- **완화책**: Provisioned Concurrency, CloudWatch 예열 트리거

**4. CI/CD 파이프라인 실패**
- **리스크**: 배포 중 에러
- **완화책**: Blue-Green 배포, 자동 롤백, 충분한 테스트

### 운영 리스크

**1. 백업 복원 실패**
- **리스크**: 재해 복구 시 백업 손상
- **완화책**: 주간 복원 테스트, 다중 백업 (S3 + 로컬)

**2. 알림 누락**
- **리스크**: Discord/Telegram Webhook 실패
- **완화책**: 재시도 로직, 다중 채널, 로그 기록

**3. 성능 회귀**
- **리스크**: 최적화 후 예상치 못한 병목
- **완화책**: 성능 모니터링, 벤치마크, 단계적 배포

### 롤백 전략

**즉시 롤백 (< 5분):**
```bash
# Blue-Green 배포 롤백
sudo systemctl stop ai-trading-green
sudo systemctl start ai-trading-blue
sudo nginx -s reload

# 기존 버전 활성화
git checkout <previous-commit>
docker-compose restart
```

**데이터 롤백 (< 30분):**
```bash
# S3 백업에서 DB 복원
python -c "
from backend.cloud.s3_backup import S3BackupManager
manager = S3BackupManager()
manager.restore_database('backups/daily/20260102_000000/database.sql.gz')
"
```

---

## 관련 문서 (Related Documents)

1. **[260102_Claude_Code_Templates_Review.md](260102_Claude_Code_Templates_Review.md)** - Claude Code Templates 전체 리뷰
2. **[260103_Claude_Code_Templates_Implementation_Plan.md](260103_Claude_Code_Templates_Implementation_Plan.md)** - 테스트 자동화, 프론트엔드 최적화, Git Hooks 계획
3. **[260102_Database_Optimization_Plan.md](260102_Database_Optimization_Plan.md)** - Database Architect Agent 계획
4. **[260103_Remaining_Components_Implementation_Plan.md](260103_Remaining_Components_Implementation_Plan.md)** - 13개 남은 컴포넌트 개요
5. **[Work_Log_20260102.md](Work_Log_20260102.md)** - DB 최적화 Phase 1, Kill Switch 구현 완료 기록

---

## 메타데이터 (Metadata)

**작성일**: 2026-01-03
**작성자**: AI Trading System Development Team
**문서 버전**: 1.0
**상태**: 📋 Plan Complete - Ready for Implementation
**우선순위**: P2 (Medium-High - Advanced Features)
**예상 소요 시간**: 4개월 (Month 1-4)
**예상 비용 절감**: $297.60/년

**핵심 컴포넌트 (10개):**
1. ✅ Security Auditor Agent - 시크릿 암호화, OWASP 스캔
2. ✅ DevOps Engineer Agent - CI/CD 파이프라인, Blue-Green 배포
3. ✅ Performance Optimizer - War Room MVP 병렬화, 메모리 최적화
4. ✅ Data Scientist Agent - Shadow Trading 통계 분석 (Sharpe, Sortino, Calmar)
5. ✅ NLP Engineer Agent - 로컬 임베딩, 티커 추출, FinBERT Sentiment
6. ✅ AWS Integration MCP - S3 백업, Lambda 백필
7. ✅ Discord/Slack Notifications - Webhook 알림, Embed 메시지
8. ✅ Performance Monitor Hook - 자동 성능 추적, 알림
9. ✅ /check-security Command - 보안 스캔 자동화
10. ✅ /setup-ci-cd-pipeline Command - CI/CD 자동 구성

**다음 단계:**
1. 사용자 승인 대기
2. Month 1부터 단계적 구현
3. 주간 진행 상황 리포트
4. Production 배포 후 모니터링

---

**END OF DOCUMENT**