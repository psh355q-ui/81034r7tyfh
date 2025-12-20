# Quick Amendment Mode integration script
import re

# Read check_integrity.py
with open('backend/constitution/check_integrity.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find verify_on_startup function and inject amendment check
old_function = '''def verify_on_startup() -> bool:
    """
    시스템 시작 시 헌법 무결성 검증
    
    변조 감지 시 SystemFreeze 예외 발생
    
    Returns:
        검증 성공 여부
    """
    # 개발 모드 체크 (해시가 하나도 설정되지 않았으면 개발 모드)
    if all(not h for h in EXPECTED_HASHES.values()):
        print("⚠️ 개발 모드: 헌법 무결성 검증 스킵")
        print("   (프로덕션 배포 전 update_expected_hashes() 실행 필요)\\n")
        return True
    
    is_valid, violations = verify_constitution_integrity()'''

new_function = '''def verify_on_startup() -> bool:
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
        print("   (프로덕션 배포 전 update_expected_hashes() 실행 필요)\\n")
        return True
    
    is_valid, violations = verify_constitution_integrity()'''

content = content.replace(old_function, new_function)

# Write back
with open('backend/constitution/check_integrity.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Amendment Mode integrated into check_integrity.py")
