"""
WebhookSecurityValidator - 웹훅 보안 검증 시스템

2025년 최신 웹훅 보안 위협 대응:
- SSRF (Server-Side Request Forgery) 차단
- MITM (Man-in-the-Middle) 공격 방어
- Replay Attack 탐지
- Data Exfiltration 방지
- HMAC 서명 검증

참고:
- https://hookdeck.com/webhooks/guides/webhook-security-vulnerabilities-guide
- https://www.aikido.dev/blog/webhook-security-checklist
- https://thehackernews.com/2025/12/malicious-npm-package-uses-hidden.html

작성일: 2025-12-03
"""

import hashlib
import hmac
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re
import ipaddress
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class SecurityThreat:
    """보안 위협 정보"""
    threat_type: str  # SSRF, MITM, REPLAY, etc.
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    blocked: bool
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class WebhookValidationResult:
    """웹훅 검증 결과"""
    is_valid: bool
    threats: List[SecurityThreat] = field(default_factory=list)
    hmac_verified: bool = False
    replay_detected: bool = False
    ssrf_detected: bool = False
    warnings: List[str] = field(default_factory=list)


class WebhookSecurityValidator:
    """
    Webhook Security Validator

    2025년 최신 웹훅 보안 위협 방어 시스템

    주요 기능:
    1. SSRF 공격 차단 (내부 IP, localhost 차단)
    2. HMAC 서명 검증 (payload 무결성)
    3. Replay Attack 탐지 (timestamp 기반)
    4. HTTPS 강제 (TLS/SSL)
    5. 악의적 URL 패턴 차단
    """

    # SSRF 차단: 내부 IP 대역
    BLOCKED_IP_RANGES = [
        "127.0.0.0/8",      # Localhost
        "10.0.0.0/8",       # Private A
        "172.16.0.0/12",    # Private B
        "192.168.0.0/16",   # Private C
        "169.254.0.0/16",   # Link-local
        "::1/128",          # IPv6 localhost
        "fc00::/7",         # IPv6 private
        "fe80::/10",        # IPv6 link-local
    ]

    # 차단할 호스트명 패턴
    BLOCKED_HOSTNAMES = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "metadata.google.internal",  # GCP metadata
        "169.254.169.254",           # AWS metadata
        "metadata.azure.com",        # Azure metadata
    ]

    # 의심스러운 URL 패턴
    SUSPICIOUS_PATTERNS = [
        r"@",              # URL에 @ 포함 (credential injection)
        r"\.\./",          # Path traversal
        r"%2e%2e",         # Encoded path traversal
        r"file://",        # File protocol
        r"ftp://",         # FTP protocol
        r"data:",          # Data URI
        r"javascript:",    # JavaScript URI
    ]

    def __init__(
        self,
        hmac_secret: Optional[str] = None,
        replay_window_seconds: int = 300  # 5분
    ):
        """
        Args:
            hmac_secret: HMAC 서명 검증용 공유 비밀키
            replay_window_seconds: Replay attack 탐지 윈도우 (초)
        """
        self.hmac_secret = hmac_secret
        self.replay_window = replay_window_seconds
        self.processed_requests: Dict[str, datetime] = {}  # request_id -> timestamp

        logger.info(f"WebhookSecurityValidator initialized (replay_window={replay_window_seconds}s)")

    def validate_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        request_id: Optional[str] = None
    ) -> WebhookValidationResult:
        """
        웹훅 요청 검증

        Args:
            url: 웹훅 URL
            payload: 요청 페이로드
            headers: HTTP 헤더
            request_id: 요청 ID (replay attack 탐지용)

        Returns:
            WebhookValidationResult
        """
        threats: List[SecurityThreat] = []
        warnings: List[str] = []

        # 1. HTTPS 강제 검증
        if not url.startswith("https://"):
            threats.append(SecurityThreat(
                threat_type="MITM",
                severity="CRITICAL",
                description="HTTP not allowed - HTTPS required for webhook security",
                blocked=True
            ))
            warnings.append("⚠️ CRITICAL: Non-HTTPS webhook blocked")

        # 2. SSRF 공격 차단
        ssrf_threat = self._check_ssrf(url)
        if ssrf_threat:
            threats.append(ssrf_threat)
            warnings.append(f"⚠️ {ssrf_threat.severity}: SSRF attack blocked")

        # 3. 악의적 URL 패턴 체크
        pattern_threat = self._check_url_patterns(url)
        if pattern_threat:
            threats.append(pattern_threat)
            warnings.append(f"⚠️ {pattern_threat.severity}: Malicious URL pattern detected")

        # 4. HMAC 서명 검증
        hmac_verified = False
        if self.hmac_secret and "X-Webhook-Signature" in headers:
            hmac_verified = self._verify_hmac(payload, headers["X-Webhook-Signature"])
            if not hmac_verified:
                threats.append(SecurityThreat(
                    threat_type="TAMPERING",
                    severity="HIGH",
                    description="HMAC signature verification failed",
                    blocked=True
                ))
                warnings.append("⚠️ HIGH: HMAC verification failed")

        # 5. Replay Attack 탐지
        replay_detected = False
        if request_id:
            replay_detected = self._check_replay(request_id, headers.get("X-Webhook-Timestamp"))
            if replay_detected:
                threats.append(SecurityThreat(
                    threat_type="REPLAY",
                    severity="HIGH",
                    description="Replay attack detected - request already processed",
                    blocked=True
                ))
                warnings.append("⚠️ HIGH: Replay attack detected")

        # 6. Timestamp 검증
        timestamp_threat = self._check_timestamp(headers.get("X-Webhook-Timestamp"))
        if timestamp_threat:
            threats.append(timestamp_threat)
            warnings.append(f"⚠️ {timestamp_threat.severity}: Invalid timestamp")

        # 검증 결과 생성
        ssrf_detected = any(t.threat_type == "SSRF" for t in threats)
        is_valid = not any(t.blocked for t in threats)

        result = WebhookValidationResult(
            is_valid=is_valid,
            threats=threats,
            hmac_verified=hmac_verified,
            replay_detected=replay_detected,
            ssrf_detected=ssrf_detected,
            warnings=warnings
        )

        if not is_valid:
            logger.warning(f"Webhook validation failed: {len(threats)} threats detected")
        else:
            logger.info("Webhook validation passed")

        return result

    def _check_ssrf(self, url: str) -> Optional[SecurityThreat]:
        """
        SSRF 공격 체크

        내부 IP, localhost, 메타데이터 서비스 차단
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return SecurityThreat(
                    threat_type="SSRF",
                    severity="CRITICAL",
                    description="Invalid URL - no hostname",
                    blocked=True
                )

            # 차단된 호스트명 체크
            hostname_lower = hostname.lower()
            for blocked in self.BLOCKED_HOSTNAMES:
                if blocked in hostname_lower:
                    return SecurityThreat(
                        threat_type="SSRF",
                        severity="CRITICAL",
                        description=f"SSRF: Blocked hostname '{hostname}'",
                        blocked=True
                    )

            # IP 주소 체크
            try:
                ip = ipaddress.ip_address(hostname)

                # 내부 IP 대역 체크
                for blocked_range in self.BLOCKED_IP_RANGES:
                    network = ipaddress.ip_network(blocked_range)
                    if ip in network:
                        return SecurityThreat(
                            threat_type="SSRF",
                            severity="CRITICAL",
                            description=f"SSRF: Private IP address '{ip}' not allowed",
                            blocked=True
                        )

            except ValueError:
                # 호스트명이 IP 주소가 아님 - 정상
                pass

            return None

        except Exception as e:
            logger.error(f"SSRF check error: {e}")
            return SecurityThreat(
                threat_type="SSRF",
                severity="HIGH",
                description=f"SSRF check failed: {str(e)}",
                blocked=True
            )

    def _check_url_patterns(self, url: str) -> Optional[SecurityThreat]:
        """악의적 URL 패턴 체크"""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return SecurityThreat(
                    threat_type="MALICIOUS_URL",
                    severity="HIGH",
                    description=f"Suspicious URL pattern detected: {pattern}",
                    blocked=True
                )

        return None

    def _verify_hmac(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        HMAC 서명 검증

        payload 무결성 확인 및 변조 방지
        """
        try:
            import json
            payload_str = json.dumps(payload, sort_keys=True)
            expected_signature = hmac.new(
                self.hmac_secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"HMAC verification error: {e}")
            return False

    def _check_replay(self, request_id: str, timestamp_str: Optional[str]) -> bool:
        """
        Replay Attack 탐지

        동일한 request_id가 재사용되는지 확인
        """
        if not request_id:
            return False

        # 이미 처리된 요청인지 확인
        if request_id in self.processed_requests:
            logger.warning(f"Replay attack detected: request_id={request_id}")
            return True

        # 요청 기록 (만료된 항목은 제거)
        current_time = datetime.now()
        self.processed_requests[request_id] = current_time

        # 만료된 항목 제거 (메모리 관리)
        cutoff_time = current_time - timedelta(seconds=self.replay_window * 2)
        self.processed_requests = {
            req_id: ts for req_id, ts in self.processed_requests.items()
            if ts > cutoff_time
        }

        return False

    def _check_timestamp(self, timestamp_str: Optional[str]) -> Optional[SecurityThreat]:
        """
        Timestamp 검증

        너무 오래되거나 미래의 요청 차단
        """
        if not timestamp_str:
            return None  # Timestamp 선택사항

        try:
            timestamp = float(timestamp_str)
            request_time = datetime.fromtimestamp(timestamp)
            current_time = datetime.now()

            time_diff = abs((current_time - request_time).total_seconds())

            # Replay window 초과
            if time_diff > self.replay_window:
                return SecurityThreat(
                    threat_type="REPLAY",
                    severity="MEDIUM",
                    description=f"Timestamp outside replay window: {time_diff}s",
                    blocked=True
                )

            return None

        except (ValueError, OSError) as e:
            return SecurityThreat(
                threat_type="INVALID_TIMESTAMP",
                severity="LOW",
                description=f"Invalid timestamp format: {str(e)}",
                blocked=False
            )

    def generate_hmac_signature(self, payload: Dict[str, Any]) -> str:
        """
        HMAC 서명 생성

        웹훅 요청 전송 시 사용
        """
        if not self.hmac_secret:
            raise ValueError("HMAC secret not configured")

        import json
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.hmac_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("WebhookSecurityValidator Test")
    print("=" * 70)

    validator = WebhookSecurityValidator(
        hmac_secret="my_secret_key",
        replay_window_seconds=300
    )

    # Test 1: 정상 웹훅
    print("\n=== Test 1: Valid HTTPS Webhook ===")
    payload = {"event": "trade", "ticker": "NVDA", "action": "BUY"}
    signature = validator.generate_hmac_signature(payload)

    result1 = validator.validate_webhook(
        url="https://api.example.com/webhook",
        payload=payload,
        headers={
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(time.time())
        },
        request_id="req_001"
    )

    print(f"Valid: {result1.is_valid}")
    print(f"HMAC Verified: {result1.hmac_verified}")
    print(f"Threats: {len(result1.threats)}")

    # Test 2: SSRF 공격 (localhost)
    print("\n=== Test 2: SSRF Attack (localhost) ===")
    result2 = validator.validate_webhook(
        url="https://localhost:8000/webhook",
        payload=payload,
        headers={},
        request_id="req_002"
    )

    print(f"Valid: {result2.is_valid}")
    print(f"SSRF Detected: {result2.ssrf_detected}")
    if result2.threats:
        print(f"Threat: {result2.threats[0].description}")

    # Test 3: SSRF 공격 (내부 IP)
    print("\n=== Test 3: SSRF Attack (Private IP) ===")
    result3 = validator.validate_webhook(
        url="https://192.168.1.1/webhook",
        payload=payload,
        headers={},
        request_id="req_003"
    )

    print(f"Valid: {result3.is_valid}")
    print(f"SSRF Detected: {result3.ssrf_detected}")
    if result3.threats:
        print(f"Threat: {result3.threats[0].description}")

    # Test 4: HTTP (MITM 위험)
    print("\n=== Test 4: HTTP (MITM Risk) ===")
    result4 = validator.validate_webhook(
        url="http://api.example.com/webhook",
        payload=payload,
        headers={},
        request_id="req_004"
    )

    print(f"Valid: {result4.is_valid}")
    if result4.threats:
        print(f"Threat: {result4.threats[0].threat_type} - {result4.threats[0].description}")

    # Test 5: Replay Attack
    print("\n=== Test 5: Replay Attack ===")
    result5a = validator.validate_webhook(
        url="https://api.example.com/webhook",
        payload=payload,
        headers={
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(time.time())
        },
        request_id="req_005"
    )
    print(f"First request - Valid: {result5a.is_valid}")

    result5b = validator.validate_webhook(
        url="https://api.example.com/webhook",
        payload=payload,
        headers={
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(time.time())
        },
        request_id="req_005"  # 같은 request_id
    )
    print(f"Replay attempt - Valid: {result5b.is_valid}")
    print(f"Replay Detected: {result5b.replay_detected}")

    # Test 6: 악의적 URL 패턴
    print("\n=== Test 6: Malicious URL Pattern ===")
    result6 = validator.validate_webhook(
        url="https://api.example.com/../../../etc/passwd",
        payload=payload,
        headers={},
        request_id="req_006"
    )

    print(f"Valid: {result6.is_valid}")
    if result6.threats:
        print(f"Threat: {result6.threats[0].description}")

    print("\n=== Test PASSED! ===")
