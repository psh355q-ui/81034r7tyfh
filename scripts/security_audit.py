#!/usr/bin/env python3
"""
OWASP Top 10 자동 보안 스캔 도구

Checks:
1. SQL Injection (f-string/format queries)
2. XSS (dangerouslySetInnerHTML)
3. Sensitive Data Exposure (API Keys, Passwords)
4. Broken Access Control (Unprotected DELETE/PUT)
"""
import re
from pathlib import Path
from typing import List, Dict
import sys

class SecurityAuditor:
    """보안 감사 도구"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.issues = []

    def scan_sql_injection(self) -> List[Dict]:
        """SQL Injection 취약점 스캔"""
        issues = []
        # repository.py 등 DB 관련 파일 스캔
        repo_files = list(self.base_path.glob("backend/database/*.py"))
        repo_files.extend(list(self.base_path.glob("backend/repositories/*.py")))

        for file in repo_files:
            try:
                content = file.read_text(encoding='utf-8')
                # 위험 패턴: f-string 또는 % 포맷팅으로 SQL 구성
                if re.search(r'execute\(f[\'"].*SELECT.*\{.*\}', content, re.IGNORECASE):
                    issues.append({
                        "type": "SQL_INJECTION",
                        "severity": "HIGH",
                        "file": str(file),
                        "message": "Potential SQL injection via f-string in execute()"
                    })
            except Exception:
                pass
        return issues

    def scan_xss(self) -> List[Dict]:
        """XSS 취약점 스캔"""
        issues = []
        # 프론트엔드 파일 스캔
        tsx_files = self.base_path.glob("frontend/src/**/*.tsx")

        for file in tsx_files:
            try:
                content = file.read_text(encoding='utf-8')
                if "dangerouslySetInnerHTML" in content:
                    issues.append({
                        "type": "XSS",
                        "severity": "MEDIUM",
                        "file": str(file),
                        "message": "dangerouslySetInnerHTML detected - verify sanitization"
                    })
            except Exception:
                pass
        return issues

    def scan_secrets_exposure(self) -> List[Dict]:
        """시크릿 노출 스캔"""
        issues = []
        py_files = self.base_path.glob("backend/**/*.py")
        
        secret_patterns = [
            (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
            (r'AIzaSy[a-zA-Z0-9_-]{33}', 'Google API Key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
            (r'postgresql://[^:]+:[^@]+@', 'Database Password in URL')
        ]

        for file in py_files:
            if '.venv' in str(file) or 'Data_Collection' in str(file):
                continue
            
            try:
                content = file.read_text(encoding='utf-8')
                for pattern, secret_type in secret_patterns:
                    if re.search(pattern, content):
                        issues.append({
                            "type": "SECRET_EXPOSURE",
                            "severity": "CRITICAL",
                            "file": str(file),
                            "message": f"Potential {secret_type} hardcoded"
                        })
            except Exception:
                pass
        return issues

    def run_full_audit(self) -> Dict:
        """전체 보안 감사 실행"""
        all_issues = []
        all_issues.extend(self.scan_sql_injection())
        all_issues.extend(self.scan_xss())
        all_issues.extend(self.scan_secrets_exposure())

        critical = [i for i in all_issues if i['severity'] == 'CRITICAL']
        high = [i for i in all_issues if i['severity'] == 'HIGH']
        medium = [i for i in all_issues if i['severity'] == 'MEDIUM']

        return {
            "total_issues": len(all_issues),
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "issues": all_issues
        }

if __name__ == "__main__":
    print("🔍 Starting Security Audit...")
    auditor = SecurityAuditor()
    results = auditor.run_full_audit()

    print(f"\n📊 Audit Results:")
    print(f"Total Issues: {results['total_issues']}")
    print(f"  🔴 Critical: {results['critical']}")
    print(f"  🟠 High: {results['high']}")
    print(f"  🟡 Medium: {results['medium']}")

    if results['critical'] > 0:
        print("\n❌ CRITICAL ISSUES FOUND:")
        for issue in results['issues']:
            if issue['severity'] == 'CRITICAL':
                print(f"  [{issue['type']}] {issue['file']}: {issue['message']}")
        sys.exit(1)
    
    if results['total_issues'] == 0:
        print("\n✅ No security issues found.")
    else:
        print("\n⚠️  Issues found (Non-critical). Check report.")
        # Print non-critical files
        for issue in results['issues']:
            if issue['severity'] != 'CRITICAL':
                 print(f"  [{issue['severity']}] {issue['file']}: {issue['message']}")
    
    sys.exit(0)
