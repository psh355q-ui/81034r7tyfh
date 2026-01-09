"""
backend.ai.llm 패키지

로컬 LLM 및 임베딩 서비스
"""
from .local_embeddings import LocalEmbeddingService, get_embedding_service
from .ollama_client import OllamaClient, get_ollama_client

__all__ = [
    'LocalEmbeddingService',
    'get_embedding_service',
    'OllamaClient',
    'get_ollama_client',
]
