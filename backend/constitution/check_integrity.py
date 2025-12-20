"""
Check Integrity - 헌법 무결성 검증

SHA256 해시를 사용한 헌법 파일 변조 감지

작성일: 2025-12-15
헌법: 제5조 (헌법 개정은 인간 승인 필요)
"""

import hashlib
from pathlib import Path
from typing import Dict, Tuple, List


# ========================================
# 예상 해시 (Expected Hashes)
# ========================================
# 프로덕션 배포 시 헌법 파일의 SHA256 해시
# 파일 변조 시 시스템 자동 동결

EXPECTED_HASHES: Dict[str, str] = {
    "risk_limits.py": "0c029c14d56346085fc63d6900f0412a9378f453ed57da5f133f3120425056e0",
    "allocation_rules.py": "4a43a70df5f06d1161d09788f65de02d3bcbed907de81dd31c3d265ae58b9cf3",
    "trading_constraints.py": "cbcb43598c260f85ff49876ba8832b0cd784fd78335867b9d2ce75f097f0b617",
    "constitution.py": "385fdfecdf31f53ed7695454c877608a528fd01bdcdcd217f68c5b1a77cb0ba1",
}


def calculate_file_hash(filepath: Path) -> str:
    """
    파일의 SHA256 해시 계산
    
    Args:
        filepath: 파일 경로
        
    Returns:
        SHA256 해시 (hex)
    """
    sha256 = hashlib.sha256()
    
    try:
        with open(filepath, 'rb') as f:
            # 4KB 청크로 읽어서 메모리 효율적으로 처리
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"⚠️ 파일 해시 계산 실패: {filepath} - {e}")
        return ""


def verify_constitution_integrity() -> Tuple[bool, List[str]]:
    """
    헌법 파일들의 무결성 검증
    
    Returns:
        (is_valid, violations)
    """
    constitution_dir = Path(__file__).parent
    violations = []
    
    for filename, expected_hash in EXPECTED_HASHES.items():
        # 해시가 설정되지 않은 경우 스킵 (개발 중)
        if not expected_hash:
            continue
        
        filepath = constitution_dir / filename
        
        if not filepath.exists():
            violations.append(f"❌ {filename}: 파일이 존재하지 않습니다")
            continue
        
        current_hash = calculate_file_hash(filepath)
        
        if current_hash != expected_hash:
            violations.append(
                f"⚠️ {filename} 변조 감지!\n"
                f"   Expected: {expected_hash[:16]}...\n"
                f"   Current:  {current_hash[:16]}..."
            )
    
    is_valid = len(violations) == 0
    
    return is_valid, violations


def update_expected_hashes():
    """
    현재 파일들의 해시를 계산하여 출력
    
    개발 중에 헌법 파일을 수정한 후
    이 함수를 실행하여 새로운 해시값을 얻습니다.
    """
    constitution_dir = Path(__file__).parent
    
    print("# 업데이트된 해시값 (check_integrity.py에 복사):")
    print("\nEXPECTED_HASHES = {")
    
    for filename in EXPECTED_HASHES.keys():
        filepath = constitution_dir / filename
        
        if filepath.exists():
            file_hash = calculate_file_hash(filepath)
            print(f'    "{filename}": "{file_hash}",')
        else:
            print(f'    "{filename}": "",  # 파일 없음')
    
    print("}")


def verify_on_startup() -> bool:
    """
    시스템 시작 시 헌법 무결성 검증
    
    CONSTITUTION_MODE 환경변수에 따라:
    - NORMAL (기본): 엄격한 무결성 검증
    - AMENDMENT: 개정 모드, 검증 스킵
    
    Returns:
        검증 성공 여부
    """
    # Amendment Mode 확인
    try:
        from .amendment_mode import allow_amendment
        
        if allow_amendment():
            logger.warning("⚠️ AMENDMENT MODE: 헌법 무결성 검증 스킵")
            logger.warning("   개정 작업 완료 후 NORMAL 모드로 전환하십시오")
            return True
    except ImportError:
        pass  # amendment_mode.py 없으면 기본 동작

    # 개발 모드 체크 (해시가 하나도 설정되지 않았으면 개발 모드)
    if all(not h for h in EXPECTED_HASHES.values()):
        print("⚠️ 개발 모드: 헌법 무결성 검증 스킵")
        print("   (프로덕션 배포 전 update_expected_hashes() 실행 필요)\n")
        return True
    
    is_valid, violations = verify_constitution_integrity()
    
    if not is_valid:
        print("\n" + "="*60)
        print(" "*15 + "🚨 시스템 동결 (System Freeze) 🚨")
        print("="*60)
        print("\n헌법 무결성 검증 실패!")
        print("\n위반 사항:")
        
        for v in violations:
            print(f"  {v}\n")
        
        print("="*60)
        print("\n시스템을 시작할 수 없습니다.")
        print("헌법 파일이 변조되었거나 손상되었습니다.")
        print("\n조치:")
        print("1. 백업에서 헌법 파일 복구")
        print("2. 또는 의도적 수정이면 update_expected_hashes() 실행")
        print("="*60 + "\n")
        
        raise SystemFreeze("헌법 무결성 검증 실패")
    
    print("✅ 헌법 무결성 검증 성공\n")
    return True


class SystemFreeze(Exception):
    """
    헌법 위반으로 인한 시스템 동결
    
    헌법 파일이 변조되었을 때 발생하는 예외
    시스템의 모든 작동을 중단시킵니다.
    """
    pass


if __name__ == "__main__":
    print("=== Constitution Integrity Check ===\n")
    
    # 개발 모드: 현재 해시 출력
    print("[모드: 개발]\n")
    update_expected_hashes()
    
    print("\n" + "-"*60 + "\n")
    
    # 검증 테스트
    print("[검증 테스트]\n")
    
    try:
        is_valid = verify_on_startup()
        
        if is_valid:
            print("✅ 시스템 시작 가능")
        
    except SystemFreeze as e:
        print(f"❌ 시스템 동결: {e}")
    
    print("\n" + "="*60)
    print("📝 참고:")
    print("  - 프로덕션 배포 전: update_expected_hashes() 실행")
    print("  - EXPECTED_HASHES에 해시값 복사")
    print("  - 이후 헌법 수정 시 자동 감지됨")
    print("="*60)
