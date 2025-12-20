"""
URLSecurityValidator - URL 보안 검증 시스템

2025년 URL 기반 공격 방어:
- Phishing URL 탐지
- Data Exfiltration 차단
- webhook.site 등 의심 도메인 차단
- URL Shortener 차단

작성일: 2025-12-03
"""

import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class URLThreat:
    """URL 위협 정보"""
    threat_type: str
    severity: str
    url: str
    description: str


class URLSecurityValidator:
    """
    URL Security Validator

    악의적 URL 차단:
    1. Data Exfiltration 도메인 (webhook.site, pipedream.com 등)
    2. URL Shortener (bit.ly, tinyurl.com 등)
    3. Phishing 패턴
    4. 허용되지 않은 도메인
    """

    # Data Exfiltration에 자주 사용되는 도메인
    EXFILTRATION_DOMAINS = [
        "webhook.site",
        "pipedream.com",
        "requestcatcher.com",
        "beeceptor.com",
        "mocky.io",
        "mockbin.org",
        "httpbin.org",
        "postb.in",
        "requestbin.com",
    ]

    # URL Shortener (실제 목적지 숨김)
    URL_SHORTENERS = [
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "goo.gl",
        "ow.ly",
        "is.gd",
        "buff.ly",
        "adf.ly",
    ]

    # 허용된 금융/뉴스 도메인 (Whitelist)
    ALLOWED_DOMAINS = [
        "investing.com",
        "finance.yahoo.com",
        "bloomberg.com",
        "reuters.com",
        "cnbc.com",
        "marketwatch.com",
        "seekingalpha.com",
        "benzinga.com",
        "barrons.com",
        "wsj.com",
        "ft.com",
        "nasdaq.com",
        "sec.gov",
        "nvidia.com",
        "amd.com",
        "intel.com",
        "tsmc.com",
        "broadcom.com",
        "google.com",
        "microsoft.com",
        "openai.com",
        "anthropic.com",
    ]

    def __init__(self, enforce_whitelist: bool = False):
        """
        Args:
            enforce_whitelist: True이면 허용 목록에 없는 도메인 모두 차단
        """
        self.enforce_whitelist = enforce_whitelist
        logger.info(f"URLSecurityValidator initialized (whitelist={enforce_whitelist})")

    def validate_url(self, url: str) -> Tuple[bool, List[URLThreat]]:
        """
        URL 보안 검증

        Args:
            url: 검증할 URL

        Returns:
            (is_safe, threats)
        """
        threats: List[URLThreat] = []

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # 1. Data Exfiltration 도메인 체크
            if self._is_exfiltration_domain(domain):
                threats.append(URLThreat(
                    threat_type="DATA_EXFILTRATION",
                    severity="CRITICAL",
                    url=url,
                    description=f"Data exfiltration domain detected: {domain}"
                ))

            # 2. URL Shortener 체크
            if self._is_url_shortener(domain):
                threats.append(URLThreat(
                    threat_type="URL_SHORTENER",
                    severity="HIGH",
                    url=url,
                    description=f"URL shortener detected: {domain}"
                ))

            # 3. Phishing 패턴 체크
            phishing_threat = self._check_phishing_patterns(url, domain)
            if phishing_threat:
                threats.append(phishing_threat)

            # 4. Whitelist 강제 (옵션)
            if self.enforce_whitelist:
                if not self._is_allowed_domain(domain):
                    threats.append(URLThreat(
                        threat_type="UNAUTHORIZED_DOMAIN",
                        severity="MEDIUM",
                        url=url,
                        description=f"Domain not in whitelist: {domain}"
                    ))

            is_safe = len(threats) == 0

            if not is_safe:
                logger.warning(f"URL threats detected: {url}")

            return is_safe, threats

        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False, [URLThreat(
                threat_type="INVALID_URL",
                severity="HIGH",
                url=url,
                description=f"Invalid URL: {str(e)}"
            )]

    def _is_exfiltration_domain(self, domain: str) -> bool:
        """Data Exfiltration 도메인 체크"""
        for blocked in self.EXFILTRATION_DOMAINS:
            if blocked in domain:
                return True
        return False

    def _is_url_shortener(self, domain: str) -> bool:
        """URL Shortener 체크"""
        for shortener in self.URL_SHORTENERS:
            if shortener in domain:
                return True
        return False

    def _is_allowed_domain(self, domain: str) -> bool:
        """허용 도메인 체크"""
        for allowed in self.ALLOWED_DOMAINS:
            if allowed in domain:
                return True
        return False

    def _check_phishing_patterns(self, url: str, domain: str) -> Optional[URLThreat]:
        """Phishing 패턴 체크"""
        # 1. 도메인에 @가 있으면 의심 (credential injection)
        if '@' in domain:
            return URLThreat(
                threat_type="PHISHING",
                severity="CRITICAL",
                url=url,
                description="Suspicious @ character in domain"
            )

        # 2. 도메인에 여러 개의 - 또는 . 연속
        if '--' in domain or '..' in domain:
            return URLThreat(
                threat_type="PHISHING",
                severity="MEDIUM",
                url=url,
                description="Suspicious repeated characters in domain"
            )

        # 3. 유명 브랜드 typosquatting 체크
        typo_patterns = [
            r'g[o0][o0]gl[e3]',     # google 변형
            r'[a@]m[a@]z[o0]n',     # amazon 변형
            r'm[i1]cr[o0]s[o0]ft',  # microsoft 변형
            r'[a@]ppl[e3]',         # apple 변형
        ]

        for pattern in typo_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return URLThreat(
                    threat_type="TYPOSQUATTING",
                    severity="HIGH",
                    url=url,
                    description=f"Possible typosquatting: {domain}"
                )

        return None


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("URLSecurityValidator Test")
    print("=" * 70)

    validator = URLSecurityValidator(enforce_whitelist=False)

    # Test 1: 정상 URL
    print("\n=== Test 1: Normal URL ===")
    url1 = "https://investing.com/news/nvidia-q3-earnings"
    is_safe1, threats1 = validator.validate_url(url1)
    print(f"URL: {url1}")
    print(f"Safe: {is_safe1}")
    print(f"Threats: {len(threats1)}")

    # Test 2: Data Exfiltration (webhook.site)
    print("\n=== Test 2: Data Exfiltration (webhook.site) ===")
    url2 = "https://webhook.site/abc123"
    is_safe2, threats2 = validator.validate_url(url2)
    print(f"URL: {url2}")
    print(f"Safe: {is_safe2}")
    if threats2:
        print(f"Threat: {threats2[0].description}")

    # Test 3: URL Shortener
    print("\n=== Test 3: URL Shortener ===")
    url3 = "https://bit.ly/3abc123"
    is_safe3, threats3 = validator.validate_url(url3)
    print(f"URL: {url3}")
    print(f"Safe: {is_safe3}")
    if threats3:
        print(f"Threat: {threats3[0].description}")

    # Test 4: Phishing (@)
    print("\n=== Test 4: Phishing (@ character) ===")
    url4 = "https://admin@evil.com/phishing"
    is_safe4, threats4 = validator.validate_url(url4)
    print(f"URL: {url4}")
    print(f"Safe: {is_safe4}")
    if threats4:
        print(f"Threat: {threats4[0].description}")

    # Test 5: Typosquatting
    print("\n=== Test 5: Typosquatting ===")
    url5 = "https://g00gle.com/search"
    is_safe5, threats5 = validator.validate_url(url5)
    print(f"URL: {url5}")
    print(f"Safe: {is_safe5}")
    if threats5:
        print(f"Threat: {threats5[0].description}")

    # Test 6: Whitelist 강제 모드
    print("\n=== Test 6: Whitelist Enforcement ===")
    validator_strict = URLSecurityValidator(enforce_whitelist=True)
    url6 = "https://random-news-site.com/article"
    is_safe6, threats6 = validator_strict.validate_url(url6)
    print(f"URL: {url6}")
    print(f"Safe: {is_safe6}")
    if threats6:
        print(f"Threat: {threats6[0].description}")

    print("\n=== Test PASSED! ===")
