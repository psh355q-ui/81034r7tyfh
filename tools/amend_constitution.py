"""
Constitutional Amendment Tool - 헌법 개정 도구

헌법 개정을 자동화하여 휴먼 에러 제거

사용법:
    python tools/amend_constitution.py \
        --file trading_constraints.py \
        --reason "MAX_VOLUME_PARTICIPATION 1% → 5%" \
        --version 2.0.2 \
        --author developer

작성일: 2025-12-16
버전: 1.0.0
"""

import hashlib
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


def calculate_file_hash(filepath: Path) -> str:
    """
    파일의 SHA256 해시 계산
    
    Args:
        filepath: 대상 파일 경로
        
    Returns:
        SHA256 해시 (hex)
    """
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def update_expected_hash(filename: str, new_hash: str) -> bool:
    """
    check_integrity.py의 EXPECTED_HASHES 자동 업데이트
    
    Args:
        filename: 파일명 (예: trading_constraints.py)
        new_hash: 새 SHA256 해시
        
    Returns:
        성공 여부
    """
    check_file = Path("backend/constitution/check_integrity.py")
    
    if not check_file.exists():
        print(f"❌ {check_file} 파일을 찾을 수 없습니다")
        return False
    
    content = check_file.read_text(encoding='utf-8')
    
    # 정규표현식으로 해시 교체
    pattern = f'"{filename}": "([a-f0-9]{{64}})"'
    replacement = f'"{filename}": "{new_hash}"'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content == content:
        print(f"⚠️ {filename}에 대한 해시를 찾을 수 없습니다")
        return False
    
    check_file.write_text(new_content, encoding='utf-8')
    print(f"✅ check_integrity.py 업데이트 완료")
    
    return True


def log_amendment(
    file: str,
    reason: str,
    version: str,
    author: str,
    old_hash: str,
    new_hash: str
) -> bool:
    """
    헌법 개정 기록을 CONSTITUTION_CHANGELOG.md에 추가
    
    Args:
        file: 수정된 파일명
        reason: 개정 이유
        version: 새 버전
        author: 개정자
        old_hash: 이전 해시
        new_hash: 새 해시
        
    Returns:
        성공 여부
    """
    log_file = Path("backend/constitution/CONSTITUTION_CHANGELOG.md")
    
    entry = f"""
## v{version} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**개정자**: {author}  
**파일**: `{file}`  
**이유**: {reason}

**해시 변경**:
- Before: `{old_hash[:16]}...`
- After: `{new_hash[:16]}...`

---
"""
    
    # 기존 내용이 있으면 앞에 추가, 없으면 새로 생성
    if log_file.exists():
        existing = log_file.read_text(encoding='utf-8')
        log_file.write_text(entry + existing, encoding='utf-8')
    else:
        header = f"""# Constitutional Amendment Changelog

헌법 개정 기록

---
"""
        log_file.write_text(header + entry, encoding='utf-8')
    
    print(f"✅ CONSTITUTION_CHANGELOG.md 업데이트 완료")
    
    return True


def get_current_hash(filename: str) -> Optional[str]:
    """
    check_integrity.py에서 현재 해시 추출
    
    Args:
        filename: 파일명
        
    Returns:
        현재 해시 (없으면 None)
    """
    check_file = Path("backend/constitution/check_integrity.py")
    
    if not check_file.exists():
        return None
    
    content = check_file.read_text(encoding='utf-8')
    
    pattern = f'"{filename}": "([a-f0-9]{{64}})"'
    match = re.search(pattern, content)
    
    if match:
        return match.group(1)
    
    return None


def amend_constitution(
    file: str,
    reason: str,
    version: str,
    author: str = "system"
) -> bool:
    """
    헌법 개정 수행
    
    Args:
        file: 수정된 파일명 (예: trading_constraints.py)
        reason: 개정 이유
        version: 새 버전 (예: 2.0.2)
        author: 개정자
        
    Returns:
        성공 여부
        
    Example:
        >>> amend_constitution(
        ...     file="trading_constraints.py",
        ...     reason="MAX_VOLUME_PARTICIPATION 1% → 5%",
        ...     version="2.0.2",
        ...     author="developer"
        ... )
    """
    print("\n" + "="*70)
    print(" "*20 + "🏛️ Constitutional Amendment")
    print("="*70 + "\n")
    
    # 1. 파일 존재 확인
    file_path = Path(f"backend/constitution/{file}")
    
    if not file_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return False
    
    print(f"📄 파일: {file}")
    
    # 2. 이전 해시 가져오기
    old_hash = get_current_hash(file)
    
    if old_hash:
        print(f"🔒 이전 해시: {old_hash[:16]}...")
    else:
        print("⚠️ 이전 해시를 찾을 수 없습니다 (새 파일?)")
        old_hash = "0" * 64
    
    # 3. 새 해시 계산
    new_hash = calculate_file_hash(file_path)
    print(f"🔐 새 해시: {new_hash[:16]}...")
    
    # 4. 해시 변경 확인
    if old_hash == new_hash:
        print("\n⚠️ 파일이 변경되지 않았습니다!")
        print("   개정이 필요하지 않습니다.")
        return False
    
    # 5. check_integrity.py 업데이트
    print("\n📝 check_integrity.py 업데이트 중...")
    if not update_expected_hash(file, new_hash):
        return False
    
    # 6. 개정 기록
    print("\n📋 CONSTITUTION_CHANGELOG.md 기록 중...")
    if not log_amendment(file, reason, version, author, old_hash, new_hash):
        return False
    
    # 7. 완료
    print("\n" + "="*70)
    print("✅ 헌법 개정 완료!")
    print("="*70)
    print(f"\n📊 요약:")
    print(f"   버전: v{version}")
    print(f"   파일: {file}")
    print(f"   이유: {reason}")
    print(f"   개정자: {author}")
    print(f"\n💡 다음 단계:")
    print(f"   1. CONSTITUTION_CHANGELOG.md 확인")
    print(f"   2. 변경사항 커밋")
    print(f"   3. CONSTITUTION_MODE=NORMAL로 테스트")
    print()
    
    return True


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="Constitutional Amendment Tool - 헌법 개정 자동화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python tools/amend_constitution.py \\
      --file trading_constraints.py \\
      --reason "MAX_VOLUME_PARTICIPATION 1%% → 5%%" \\
      --version 2.0.2 \\
      --author developer
        """
    )
    
    parser.add_argument(
        "--file",
        required=True,
        help="수정된 헌법 파일명 (예: trading_constraints.py)"
    )
    
    parser.add_argument(
        "--reason",
        required=True,
        help="개정 이유 (자세하게 작성)"
    )
    
    parser.add_argument(
        "--version",
        required=True,
        help="새 헌법 버전 (예: 2.0.2)"
    )
    
    parser.add_argument(
        "--author",
        default="system",
        help="개정 승인자 (기본값: system)"
    )
    
    args = parser.parse_args()
    
    # 개정 수행
    success = amend_constitution(
        file=args.file,
        reason=args.reason,
        version=args.version,
        author=args.author
    )
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
