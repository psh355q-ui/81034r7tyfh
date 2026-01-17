"""
sentence-transformers를 사용한 로컬 임베딩 서비스.
OpenAI 임베딩 API를 대체합니다.
"""
from sentence_transformers import SentenceTransformer
from typing import List
import logging
import os

# HuggingFace 다운로드 타임아웃 설정 (기본 10초 → 60초로 증가)
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '60'

logger = logging.getLogger(__name__)


class LocalEmbeddingService:
    """로컬 임베딩 서비스 (OpenAI 대체)"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', max_retries: int = 3):
        """
        로컬 임베딩 모델 초기화.

        Args:
            model_name: 사용할 모델 이름
                - all-MiniLM-L6-v2: 빠름, 영어 (384차원)
                - paraphrase-multilingual-MiniLM-L12-v2: 다국어 (384차원)
            max_retries: 다운로드 실패 시 재시도 횟수
        """
        import time

        self.model_name = model_name
        retry_count = 0

        while retry_count < max_retries:
            try:
                logger.info(f"Loading embedding model: {model_name} (attempt {retry_count + 1}/{max_retries})")
                # Increase timeout for model download
                self.model = SentenceTransformer(
                    model_name,
                    cache_folder=os.path.join(os.path.expanduser('~'), '.cache', 'huggingface', 'hub')
                )
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"✅ Embedding model loaded: {model_name} ({self.dimension} dimensions)")
                return
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to load embedding model after {max_retries} attempts: {e}")
                    # Fallback: create zero embeddings
                    self.dimension = 384  # Default for all-MiniLM-L6-v2
                    self.model = None
                    logger.warning("⚠️ Using zero embeddings as fallback")
                else:
                    wait_time = retry_count * 5
                    logger.warning(f"Retry {retry_count}/{max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
    
    def get_embedding(self, text: str) -> List[float]:
        """
        단일 텍스트의 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (리스트)
        """
        if self.model is None:
            logger.warning("⚠️ Model not loaded, returning zero embedding")
            return [0.0] * self.dimension

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # 빈 임베딩 반환 (기존 OpenAI 폴백과 동일)
            return [0.0] * self.dimension
    
    def get_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        여러 텍스트의 임베딩 배치 생성

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기

        Returns:
            임베딩 벡터 리스트
        """
        if self.model is None:
            logger.warning("⚠️ Model not loaded, returning zero embeddings")
            return [[0.0] * self.dimension for _ in texts]

        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10  # 10개 이상일 때만 진행률 표시
            )
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            # 빈 임베딩 리스트 반환
            return [[0.0] * self.dimension for _ in texts]


# 글로벌 인스턴스 (싱글톤 패턴)
_embedding_service = None


def get_embedding_service(model_name: str = 'all-MiniLM-L6-v2') -> LocalEmbeddingService:
    """
    임베딩 서비스 싱글톤 인스턴스 가져오기
    
    Args:
        model_name: 모델 이름 (첫 호출 시에만 사용)
        
    Returns:
        LocalEmbeddingService 인스턴스
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = LocalEmbeddingService(model_name)
    
    return _embedding_service
