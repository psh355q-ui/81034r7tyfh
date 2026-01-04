
import os
from cryptography.fernet import Fernet
from pathlib import Path
import json
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """암호화된 시크릿 관리 클래스 (Singleton)"""

    def __init__(
        self,
        key_file: str = ".secrets.key",
        secrets_file: str = ".secrets.enc",
        base_dir: Optional[str] = None
    ):
        """
        초기화

        Args:
            key_file: 암호화 키 파일 이름
            secrets_file: 암호화된 시크릿 파일 이름
            base_dir: 기본 디렉토리 (없으면 프로젝트 루트 추론)
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # backend/config/secrets_manager.py 기준 프로젝트 루트 (../../)
            self.base_dir = Path(__file__).parent.parent.parent

        self.key_file = self.base_dir / key_file
        self.secrets_file = self.base_dir / secrets_file
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """암호화 키 로드 또는 생성"""
        if self.key_file.exists():
            return self.key_file.read_bytes()

        # 새 키 생성
        logger.warning(f"Creating new encryption key at {self.key_file}")
        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        # Windows에서는 chmod 600이 완벽히 동작하지 않지만 시도
        try:
            self.key_file.chmod(0o600)
        except Exception:
            pass

        return key

    def encrypt_secrets(self, secrets: Dict[str, str]) -> None:
        """시크릿 암호화 저장"""
        json_data = json.dumps(secrets, indent=2).encode('utf-8')
        encrypted_data = self.fernet.encrypt(json_data)
        
        self.secrets_file.write_bytes(encrypted_data)
        try:
            self.secrets_file.chmod(0o600)
        except Exception:
            pass
            
        logger.info(f"Encrypted {len(secrets)} secrets to {self.secrets_file}")

    def decrypt_secrets(self) -> Dict[str, str]:
        """시크릿 복호화 로드"""
        if not self.secrets_file.exists():
            # 파일이 없으면 빈 딕셔너리 반환 (또는 에러)
            return {}

        encrypted_data = self.secrets_file.read_bytes()
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode('utf-8'))

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """개별 시크릿 조회"""
        try:
            secrets = self.decrypt_secrets()
            return secrets.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get secret '{key}': {e}")
            return default

# Global Instance
_secrets_manager: Optional[SecretsManager] = None

def get_secrets_manager() -> SecretsManager:
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Helper function to get secret"""
    # 1. Try environment variable first (for compatibility/override)
    env_val = os.getenv(key)
    if env_val is not None:
        return env_val
        
    # 2. Try encrypted secrets
    return get_secrets_manager().get_secret(key, default)
