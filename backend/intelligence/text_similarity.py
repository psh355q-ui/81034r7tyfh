"""
텍스트 유사도 유틸리티
뉴스 기사 간 유사도 측정
"""
from typing import List, Set
import re
from collections import Counter
import math


def tokenize(text: str) -> List[str]:
    """
    텍스트를 토큰화
    
    Args:
        text: 입력 텍스트
    
    Returns:
        소문자 단어 리스트
    """
    # 알파벳과 숫자만 남기고 토큰화
    text = text.lower()
    tokens = re.findall(r'\b\w+\b', text)
    return tokens


def cosine_similarity(text1: str, text2: str) -> float:
    """
    코사인 유사도 계산
    
    Args:
        text1, text2: 비교할 텍스트
    
    Returns:
        0.0 (완전 다름) ~ 1.0 (완전 동일)
    """
    if not text1 or not text2:
        return 0.0
    
    # 토큰화
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # 빈도 카운터
    counter1 = Counter(tokens1)
    counter2 = Counter(tokens2)
    
    # 공통 단어
    common_words = set(counter1.keys()) & set(counter2.keys())
    
    # 내적 (dot product)
    dot_product = sum(counter1[word] * counter2[word] for word in common_words)
    
    # 크기 (magnitude)
    magnitude1 = math.sqrt(sum(count ** 2 for count in counter1.values()))
    magnitude2 = math.sqrt(sum(count ** 2 for count in counter2.values()))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    # 코사인 유사도
    similarity = dot_product / (magnitude1 * magnitude2)
    
    return similarity


def jaccard_similarity(text1: str, text2: str) -> float:
    """
    자카드 유사도 계산
    
    Args:
        text1, text2: 비교할 텍스트
    
    Returns:
        0.0 (완전 다름) ~ 1.0 (완전 동일)
    """
    if not text1 or not text2:
        return 0.0
    
    # 토큰 집합
    set1 = set(tokenize(text1))
    set2 = set(tokenize(text2))
    
    if not set1 or not set2:
        return 0.0
    
    # 교집합과 합집합
    intersection = set1 & set2
    union = set1 | set2
    
    if not union:
        return 0.0
    
    # 자카드 유사도
    similarity = len(intersection) / len(union)
    
    return similarity


def pairwise_similarities(
    texts: List[str], 
    method: str = 'cosine'
) -> List[float]:
    """
    여러 텍스트 간 쌍별 유사도 계산
    
    Args:
        texts: 텍스트 리스트
        method: 'cosine' 또는 'jaccard'
    
    Returns:
        유사도 리스트
    """
    similarities = []
    
    sim_func = cosine_similarity if method == 'cosine' else jaccard_similarity
    
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = sim_func(texts[i], texts[j])
            similarities.append(sim)
    
    return similarities


def average_similarity(texts: List[str], method: str = 'cosine') -> float:
    """
    평균 유사도 계산
    
    Args:
        texts: 텍스트 리스트
        method: 'cosine' 또는 'jaccard'
    
    Returns:
        평균 유사도
    """
    if len(texts) < 2:
        return 0.0
    
    similarities = pairwise_similarities(texts, method)
    
    if not similarities:
        return 0.0
    
    return sum(similarities) / len(similarities)
