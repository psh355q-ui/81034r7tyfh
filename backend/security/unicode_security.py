"""
UnicodeSecurityChecker - 유니코드 공격 탐지 시스템

2025년 유니코드 보안 위협 대응:
- Homograph Attack 탐지 (유사 문자 치환)
- Invisible Characters 탐지
- Right-to-Left Override 공격 차단
- Zero-Width Characters 탐지

참고:
- https://www.cttsonline.com/2025/10/03/how-a-unicode-security-vulnerability-lets-hackers-disguise-dangerous-websites/

작성일: 2025-12-03
"""

import logging
import unicodedata
from typing import List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UnicodeThreat:
    """유니코드 위협 정보"""
    threat_type: str
    severity: str
    character: str
    position: int
    description: str


class UnicodeSecurityChecker:
    """
    Unicode Security Checker

    유니코드를 이용한 공격 탐지:
    1. Homograph Attack: 비슷하게 생긴 문자 치환 (예: a → а)
    2. Invisible Characters: 보이지 않는 문자
    3. RTL Override: 텍스트 방향 조작
    4. Zero-Width Characters: 너비 0 문자
    """

    # 위험한 유니코드 범위
    DANGEROUS_RANGES = [
        (0x200B, 0x200F),  # Zero-width characters, RTL/LTR marks
        (0x202A, 0x202E),  # Directional formatting
        (0x2060, 0x2064),  # Invisible characters
        (0xFEFF, 0xFEFF),  # Zero Width No-Break Space
        (0x180E, 0x180E),  # Mongolian Vowel Separator
        (0xFFF9, 0xFFFB),  # Interlinear annotation characters
    ]

    # Homograph 공격에 자주 사용되는 Cyrillic 문자 (라틴 문자와 비슷)
    CYRILLIC_LOOKALIKES = {
        'а': 'a',  # Cyrillic 'a' → Latin 'a'
        'е': 'e',  # Cyrillic 'e' → Latin 'e'
        'о': 'o',  # Cyrillic 'o' → Latin 'o'
        'р': 'p',  # Cyrillic 'р' → Latin 'p'
        'с': 'c',  # Cyrillic 'с' → Latin 'c'
        'у': 'y',  # Cyrillic 'у' → Latin 'y'
        'х': 'x',  # Cyrillic 'х' → Latin 'x'
    }

    # Greek 유사 문자
    GREEK_LOOKALIKES = {
        'α': 'a',  # Greek alpha → Latin 'a'
        'ο': 'o',  # Greek omicron → Latin 'o'
        'ρ': 'p',  # Greek rho → Latin 'p'
        'ν': 'v',  # Greek nu → Latin 'v'
    }

    # 일본어 유사 문자 (Booking.com 피싱 사례)
    JAPANESE_LOOKALIKES = {
        'ノ': '/',  # Katakana 'no' → forward slash
        '一': '-',  # Kanji 'one' → hyphen
        'ー': '-',  # Katakana prolonged sound → hyphen
    }

    def __init__(self):
        """UnicodeSecurityChecker 초기화"""
        self.all_lookalikes = {
            **self.CYRILLIC_LOOKALIKES,
            **self.GREEK_LOOKALIKES,
            **self.JAPANESE_LOOKALIKES
        }

        logger.info("UnicodeSecurityChecker initialized")

    def check_text(self, text: str) -> Tuple[bool, List[UnicodeThreat]]:
        """
        텍스트의 유니코드 위협 체크

        Args:
            text: 검사할 텍스트

        Returns:
            (is_safe, threats)
        """
        threats: List[UnicodeThreat] = []

        # 1. Invisible characters 탐지
        invisible_threats = self._check_invisible(text)
        threats.extend(invisible_threats)

        # 2. RTL Override 탐지
        rtl_threats = self._check_rtl_override(text)
        threats.extend(rtl_threats)

        # 3. Zero-width characters 탐지
        zw_threats = self._check_zero_width(text)
        threats.extend(zw_threats)

        # 4. Homograph 공격 탐지
        homograph_threats = self._check_homograph(text)
        threats.extend(homograph_threats)

        is_safe = len(threats) == 0

        if not is_safe:
            logger.warning(f"Unicode threats detected: {len(threats)} issues")

        return is_safe, threats

    def sanitize_text(self, text: str) -> str:
        """
        위험한 유니코드 문자 제거

        Args:
            text: 원본 텍스트

        Returns:
            정제된 텍스트
        """
        sanitized = []

        for i, char in enumerate(text):
            codepoint = ord(char)

            # 위험한 범위 체크
            is_dangerous = any(
                start <= codepoint <= end
                for start, end in self.DANGEROUS_RANGES
            )

            if is_dangerous:
                logger.debug(f"Removed dangerous character at position {i}: U+{codepoint:04X}")
                continue

            # Homograph 변환
            if char in self.all_lookalikes:
                replacement = self.all_lookalikes[char]
                logger.debug(f"Replaced lookalike '{char}' → '{replacement}' at position {i}")
                sanitized.append(replacement)
            else:
                sanitized.append(char)

        return ''.join(sanitized)

    def _check_invisible(self, text: str) -> List[UnicodeThreat]:
        """보이지 않는 문자 탐지"""
        threats = []

        for i, char in enumerate(text):
            codepoint = ord(char)

            # 위험한 범위에 속하는지 확인
            for start, end in self.DANGEROUS_RANGES:
                if start <= codepoint <= end:
                    threats.append(UnicodeThreat(
                        threat_type="INVISIBLE_CHARACTER",
                        severity="HIGH",
                        character=f"U+{codepoint:04X}",
                        position=i,
                        description=f"Invisible/control character detected"
                    ))
                    break

        return threats

    def _check_rtl_override(self, text: str) -> List[UnicodeThreat]:
        """RTL Override 공격 탐지"""
        threats = []

        # RTL override 문자들
        rtl_chars = [
            '\u202E',  # RIGHT-TO-LEFT OVERRIDE
            '\u202D',  # LEFT-TO-RIGHT OVERRIDE
        ]

        for i, char in enumerate(text):
            if char in rtl_chars:
                threats.append(UnicodeThreat(
                    threat_type="RTL_OVERRIDE",
                    severity="CRITICAL",
                    character=f"U+{ord(char):04X}",
                    position=i,
                    description="Bidirectional text override detected"
                ))

        return threats

    def _check_zero_width(self, text: str) -> List[UnicodeThreat]:
        """Zero-width 문자 탐지"""
        threats = []

        zero_width_chars = [
            '\u200B',  # ZERO WIDTH SPACE
            '\u200C',  # ZERO WIDTH NON-JOINER
            '\u200D',  # ZERO WIDTH JOINER
            '\uFEFF',  # ZERO WIDTH NO-BREAK SPACE
        ]

        for i, char in enumerate(text):
            if char in zero_width_chars:
                threats.append(UnicodeThreat(
                    threat_type="ZERO_WIDTH",
                    severity="MEDIUM",
                    character=f"U+{ord(char):04X}",
                    position=i,
                    description="Zero-width character detected"
                ))

        return threats

    def _check_homograph(self, text: str) -> List[UnicodeThreat]:
        """Homograph 공격 탐지"""
        threats = []

        for i, char in enumerate(text):
            if char in self.all_lookalikes:
                replacement = self.all_lookalikes[char]
                category = self._get_lookalike_category(char)

                threats.append(UnicodeThreat(
                    threat_type="HOMOGRAPH",
                    severity="HIGH",
                    character=char,
                    position=i,
                    description=f"{category} lookalike: '{char}' resembles '{replacement}'"
                ))

        return threats

    def _get_lookalike_category(self, char: str) -> str:
        """유사 문자의 카테고리 반환"""
        if char in self.CYRILLIC_LOOKALIKES:
            return "Cyrillic"
        elif char in self.GREEK_LOOKALIKES:
            return "Greek"
        elif char in self.JAPANESE_LOOKALIKES:
            return "Japanese"
        else:
            return "Unknown"

    def check_url(self, url: str) -> Tuple[bool, List[UnicodeThreat]]:
        """
        URL의 유니코드 위협 체크

        Booking.com 피싱 사례 등을 탐지
        """
        # URL을 IDN (Internationalized Domain Name) 디코딩
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc

            # 도메인 체크
            is_safe, threats = self.check_text(domain)

            if not is_safe:
                logger.warning(f"Unicode threats in URL domain: {domain}")

            return is_safe, threats

        except Exception as e:
            logger.error(f"URL check error: {e}")
            return False, [UnicodeThreat(
                threat_type="INVALID_URL",
                severity="MEDIUM",
                character="",
                position=-1,
                description=f"URL parsing error: {str(e)}"
            )]


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("UnicodeSecurityChecker Test")
    print("=" * 70)

    checker = UnicodeSecurityChecker()

    # Test 1: 정상 텍스트
    print("\n=== Test 1: Normal Text ===")
    text1 = "NVIDIA announces new GPU"
    is_safe1, threats1 = checker.check_text(text1)
    print(f"Text: {text1}")
    print(f"Safe: {is_safe1}")
    print(f"Threats: {len(threats1)}")

    # Test 2: Cyrillic Homograph (а → a)
    print("\n=== Test 2: Cyrillic Homograph ===")
    text2 = "Googlе.com"  # 'е' is Cyrillic, not Latin
    is_safe2, threats2 = checker.check_text(text2)
    print(f"Text: {text2}")
    print(f"Safe: {is_safe2}")
    if threats2:
        for threat in threats2:
            print(f"  Threat: {threat.description} at position {threat.position}")

    sanitized2 = checker.sanitize_text(text2)
    print(f"Sanitized: {sanitized2}")

    # Test 3: Zero-width characters
    print("\n=== Test 3: Zero-Width Characters ===")
    text3 = "NVI\u200BDIA"  # ZERO WIDTH SPACE
    is_safe3, threats3 = checker.check_text(text3)
    print(f"Text (with hidden char): {text3}")
    print(f"Safe: {is_safe3}")
    if threats3:
        for threat in threats3:
            print(f"  Threat: {threat.description}")

    sanitized3 = checker.sanitize_text(text3)
    print(f"Sanitized: {sanitized3}")

    # Test 4: RTL Override
    print("\n=== Test 4: RTL Override ===")
    text4 = "test\u202Emalicious"  # RIGHT-TO-LEFT OVERRIDE
    is_safe4, threats4 = checker.check_text(text4)
    print(f"Text: {repr(text4)}")
    print(f"Safe: {is_safe4}")
    if threats4:
        for threat in threats4:
            print(f"  Threat: {threat.threat_type} - {threat.description}")

    # Test 5: Japanese lookalike (Booking.com 사례)
    print("\n=== Test 5: Japanese Lookalike (Booking.com Phishing) ===")
    text5 = "bookingノcom"  # ノ looks like /
    is_safe5, threats5 = checker.check_text(text5)
    print(f"Text: {text5}")
    print(f"Safe: {is_safe5}")
    if threats5:
        for threat in threats5:
            print(f"  Threat: {threat.description}")

    sanitized5 = checker.sanitize_text(text5)
    print(f"Sanitized: {sanitized5}")

    # Test 6: URL 체크
    print("\n=== Test 6: URL Check ===")
    url6 = "https://googlе.com/search"  # Cyrillic 'е'
    is_safe6, threats6 = checker.check_url(url6)
    print(f"URL: {url6}")
    print(f"Safe: {is_safe6}")
    if threats6:
        for threat in threats6:
            print(f"  Threat: {threat.description}")

    print("\n=== Test PASSED! ===")
