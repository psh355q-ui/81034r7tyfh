"""
LLMLingua-2 Intelligent Prompt Compressor

Reduces prompt token count by 2-5x while preserving semantic meaning.
Uses Microsoft's LLMLingua-2 model for data-distillation based compression.

Reference: https://github.com/microsoft/LLMLingua
"""

import logging
from typing import Optional, List
from llmlingua import PromptCompressor

logger = logging.getLogger(__name__)


class IntelligentPromptCompressor:
    """
    Compress prompts using LLMLingua-2 before LLM calls
    
    Achieves 2-5x compression with minimal quality loss.
    Ideal for:
    - Long news articles
    - SEC filing text
    - Community reports from GraphRAG
    - Historical context
    
    Example:
        >>> compressor = IntelligentPromptCompressor()
        >>> compressed = compressor.compress_context(
        ...     context_text="[Long SEC filing text...]",
        ...     user_query="What are the main risks?",
        ...     compression_rate=0.33
        ... )
        >>> # Returns 33% of original tokens, preserving key info
    """
    
    def __init__(self, model_name: str = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"):
        """
        Initialize prompt compressor
        
        Args:
            model_name: LLMLingua-2 model to use
                - xlm-roberta-large-meetingbank: Multilingual, high quality
                - bert-base-multilingual: Faster, good for most tasks
        """
        logger.info(f"Initializing LLMLingua-2 compressor with model: {model_name}")
        
        try:
            self.compressor = PromptCompressor(
                model_name=model_name,
                use_llmlingua2=True  # Use LLMLingua-2 (not v1)
            )
            logger.info("✅ LLMLingua-2 compressor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLMLingua-2: {e}")
            raise
    
    def compress_context(
        self,
        context_text: str,
        user_query: str,
        compression_rate: float = 0.33,
        instruction: Optional[str] = None,
        force_tokens: Optional[List[str]] = None
    ) -> dict:
        """
        Compress context to preserve only essential information
        
        Args:
            context_text: Long text to compress (news, filings, reports)
            user_query: User's question (helps preserve relevant info)
            compression_rate: Target compression (0.33 = keep 33% of tokens)
            instruction: Optional custom instruction for compression
            force_tokens: Tokens to always preserve (e.g., financial symbols)
        
        Returns:
            dict with:
                - compressed_prompt: Compressed text
                - original_tokens: Original token count
                - compressed_tokens: Compressed token count
                - compression_ratio: Actual compression achieved
                - savings: Token cost savings estimate
        
        Example:
            >>> result = compressor.compress_context(
            ...     context_text=long_sec_filing,
            ...     user_query="What are the revenue trends?",
            ...     compression_rate=0.33
            ... )
            >>> print(f"Saved {result['savings']:.1%} tokens")
        """
        if not context_text or not context_text.strip():
            logger.warning("Empty context_text provided, skipping compression")
            return {
                "compressed_prompt": "",
                "original_tokens": 0,
                "compressed_tokens": 0,
                "compression_ratio": 1.0,
                "savings": 0.0
            }
        
        # Default instruction for financial/investment context
        if instruction is None:
            instruction = (
                "Preserve core financial information, numerical data, "
                "risk factors, and key business insights. "
                "Remove redundant phrases and filler words."
            )
        
        # Default force tokens for financial context
        if force_tokens is None:
            force_tokens = ['\n', '?', '$', '%', 'M', 'B', 'Q1', 'Q2', 'Q3', 'Q4']
        
        try:
            logger.debug(f"Compressing {len(context_text)} characters (target rate: {compression_rate:.0%})")
            
            compressed_result = self.compressor.compress_prompt(
                context_text,
                instruction=instruction,
                question=user_query,
                rate=compression_rate,
                force_tokens=force_tokens
            )
            
            # Calculate savings metrics
            original_tokens = compressed_result.get('origin_tokens', len(context_text.split()))
            compressed_tokens = compressed_result.get('compressed_tokens', len(compressed_result['compressed_prompt'].split()))
            actual_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
            savings = 1.0 - actual_ratio
            
            logger.info(
                f"✅ Compression complete: {original_tokens} → {compressed_tokens} tokens "
                f"({actual_ratio:.1%} retained, {savings:.1%} saved)"
            )
            
            return {
                "compressed_prompt": compressed_result['compressed_prompt'],
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
                "compression_ratio": actual_ratio,
                "savings": savings
            }
            
        except Exception as e:
            logger.error(f"❌ Compression failed: {e}")
            # Fallback: return original text
            return {
                "compressed_prompt": context_text,
                "original_tokens": len(context_text.split()),
                "compressed_tokens": len(context_text.split()),
                "compression_ratio": 1.0,
                "savings": 0.0,
                "error": str(e)
            }
    
    def compress_news_article(self, article_text: str, query: str = "Summarize key market impacts") -> dict:
        """
        Specialized compression for news articles
        
        Args:
            article_text: News article content
            query: Analysis question (default: market impact summary)
        
        Returns:
            Compression result dict
        """
        return self.compress_context(
            context_text=article_text,
            user_query=query,
            compression_rate=0.40,  # Keep 40% for news (more aggressive)
            instruction="Preserve key events, market impacts, stock tickers, and numerical data. Remove filler and background context.",
            force_tokens=['\n', '$', '%', 'CEO', 'Fed', 'Q1', 'Q2', 'Q3', 'Q4']
        )
    
    def compress_sec_filing(self, filing_text: str, query: str = "Extract key risks and opportunities") -> dict:
        """
        Specialized compression for SEC filings
        
        Args:
            filing_text: SEC filing content (10-K, 10-Q, 8-K)
            query: Analysis question
        
        Returns:
            Compression result dict
        """
        return self.compress_context(
            context_text=filing_text,
            user_query=query,
            compression_rate=0.30,  # Keep 30% for SEC (very aggressive, lots of boilerplate)
            instruction="Preserve risk factors, financial metrics, material changes, and forward-looking statements. Remove legal boilerplate.",
            force_tokens=['\n', '$', '%', 'Risk', 'Material', 'million', 'billion']
        )
    
    def compress_graphrag_community(self, community_text: str, query: str) -> dict:
        """
        Specialized compression for GraphRAG community reports
        
        Args:
            community_text: Community report text
            query: User's query
        
        Returns:
            Compression result dict
        """
        return self.compress_context(
            context_text=community_text,
            user_query=query,
            compression_rate=0.35,  # Keep 35% for community reports
            instruction="Preserve key entities, relationships, and insights relevant to the query. Remove redundant descriptions.",
            force_tokens=['\n', ':', '-', 'entity', 'relationship']
        )


# Singleton instance for application-wide use
_compressor_instance: Optional[IntelligentPromptCompressor] = None


def get_compressor() -> IntelligentPromptCompressor:
    """
    Get singleton compressor instance
    
    Returns:
        Initialized IntelligentPromptCompressor
    """
    global _compressor_instance
    
    if _compressor_instance is None:
        _compressor_instance = IntelligentPromptCompressor()
    
    return _compressor_instance
