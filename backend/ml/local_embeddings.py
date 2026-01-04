"""
로컬 임베딩 모델 (Local Embedding Model)

Date: 2026-01-03
Phase: Optimization
Purpose:
    - HuggingFace의 SentenceTransformer를 사용하여 로컬에서 텍스트 임베딩 생성
    - OpenAI API 의존성 제거 및 비용 절감
    - 네트워크 지연 없는 빠른 추론
"""
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class LocalEmbeddingModel:
    """
    로컬 임베딩 생성기 (OpenAI 대체)
    모델: all-MiniLM-L6-v2 (384차원, 빠르고 가벼움)
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        # Lazy loading to avoid memory overhead if not used

    @property
    def model(self):
        if self._model is None:
            logger.info(f"📥 Loading local embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("✅ Model loaded successfully")
        return self._model

    def get_embedding(self, text: str) -> List[float]:
        """단일 텍스트 임베딩 (384차원)"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 임베딩 (여러 텍스트 처리 최적화)"""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간 코사인 유사도 계산"""
        emb1 = self.model.encode(text1, convert_to_numpy=True)
        emb2 = self.model.encode(text2, convert_to_numpy=True)

        return self._cosine_similarity(emb1, emb2)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 내부 함수"""
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return float(dot_product / (norm_a * norm_b))

# 글로벌 인스턴스
embedding_model = LocalEmbeddingModel()
