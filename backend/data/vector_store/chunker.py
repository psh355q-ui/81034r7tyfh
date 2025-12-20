"""
TextChunker - Document chunking logic for embedding.

Supports:
- Token-based chunking with overlap
- Section-based chunking (for SEC filings)
- Paragraph-based chunking
"""

from typing import List, Dict
import re


class TextChunker:
    """
    Split long documents into chunks for embedding.
    
    Why chunking?
    - OpenAI embedding models support up to 8191 tokens
    - Smaller chunks (4000 tokens) produce better semantic coherence
    - Overlap helps preserve context across boundaries
    
    Usage:
        chunker = TextChunker()
        chunks = chunker.chunk_by_tokens(long_text, chunk_size=4000, overlap=200)
    """
    
    @staticmethod
    def chunk_by_tokens(
        text: str,
        chunk_size: int = 4000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks by approximate token count.
        
        Token estimation: 1 token ≈ 0.75 words (rough approximation)
        
        Args:
            text: Text to chunk
            chunk_size: Target tokens per chunk (default: 4000)
            overlap: Overlapping tokens between chunks (default: 200)
        
        Returns:
            List of text chunks
        
        Example:
            >>> text = "..." * 10000  # Long document
            >>> chunks = TextChunker.chunk_by_tokens(text, chunk_size=4000, overlap=200)
            >>> len(chunks)
            3
            >>> len(chunks[0].split())  # Approximately 4000/1.3 = ~3000 words
            3076
        """
        if not text or not text.strip():
            return []
        
        # Rough tokenization (1 token ≈ 1.3 words)
        words = text.split()
        tokens_per_word = 1.3
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(words):
            # Calculate end index
            end_idx = start_idx + int(chunk_size / tokens_per_word)
            chunk_words = words[start_idx:end_idx]
            
            if chunk_words:
                chunks.append(" ".join(chunk_words))
            
            # Move start with overlap
            overlap_words = int(overlap / tokens_per_word)
            start_idx = end_idx - overlap_words
            
            # Prevent infinite loop
            if start_idx <= 0 or end_idx >= len(words):
                break
        
        return chunks
    
    @staticmethod
    def chunk_by_sections(
        text: str,
        section_headers: List[str]
    ) -> List[Dict]:
        """
        Split SEC filing by sections (e.g., "Risk Factors", "MD&A").
        
        SEC 10-K/10-Q documents have standardized sections:
        - Item 1: Business
        - Item 1A: Risk Factors
        - Item 7: Management's Discussion and Analysis (MD&A)
        - Item 8: Financial Statements
        
        Args:
            text: Full SEC filing text
            section_headers: List of section headers to extract
        
        Returns:
            List of {"section": str, "content": str} dictionaries
        
        Example:
            >>> filing_text = load_10k("AAPL")
            >>> sections = TextChunker.chunk_by_sections(filing_text, [
            ...     "Risk Factors",
            ...     "Management's Discussion and Analysis"
            ... ])
            >>> sections[0]
            {"section": "Risk Factors", "content": "Our business is subject to..."}
        """
        chunks = []
        
        for i, header in enumerate(section_headers):
            # Find section start (case-insensitive, beginning of line)
            pattern = re.compile(rf"(?i)^.*{re.escape(header)}.*$", re.MULTILINE)
            match = pattern.search(text)
            
            if not match:
                continue
            
            start_idx = match.start()
            
            # Find next section (or end of document)
            if i + 1 < len(section_headers):
                next_pattern = re.compile(
                    rf"(?i)^.*{re.escape(section_headers[i+1])}.*$",
                    re.MULTILINE
                )
                next_match = next_pattern.search(text, start_idx + 1)
                end_idx = next_match.start() if next_match else len(text)
            else:
                end_idx = len(text)
            
            content = text[start_idx:end_idx].strip()
            
            if content:
                chunks.append({
                    "section": header,
                    "content": content
                })
        
        return chunks
    
    @staticmethod
    def chunk_by_paragraphs(
        text: str,
        max_paragraphs: int = 10
    ) -> List[str]:
        """
        Split text into chunks by paragraphs.
        
        Useful for news articles or narrative documents.
        
        Args:
            text: Text to chunk
            max_paragraphs: Maximum paragraphs per chunk
        
        Returns:
            List of text chunks
        
        Example:
            >>> article = "Paragraph 1\\n\\nParagraph 2\\n\\nParagraph 3..."
            >>> chunks = TextChunker.chunk_by_paragraphs(article, max_paragraphs=2)
            >>> len(chunks)
            2
        """
        # Split by double newline (paragraph separator)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        
        for i in range(0, len(paragraphs), max_paragraphs):
            chunk_paragraphs = paragraphs[i:i + max_paragraphs]
            chunks.append("\n\n".join(chunk_paragraphs))
        
        return chunks
    
    @staticmethod
    def smart_chunk(
        text: str,
        doc_type: str,
        max_tokens: int = 4000
    ) -> List[Dict]:
        """
        Automatically choose best chunking strategy based on document type.
        
        Strategy selection:
        - SEC filings (10-K, 10-Q): Section-based chunking
        - News articles: Paragraph-based chunking
        - Other: Token-based chunking
        
        Args:
            text: Text to chunk
            doc_type: Document type ('10K', '10Q', 'news', etc.)
            max_tokens: Maximum tokens per chunk
        
        Returns:
            List of {"content": str, "metadata": dict} dictionaries
        
        Example:
            >>> chunks = TextChunker.smart_chunk(text, doc_type='10K')
            >>> chunks[0]
            {
                "content": "Risk Factors section content...",
                "metadata": {"section": "Risk Factors", "method": "section"}
            }
        """
        if doc_type in ['10K', '10Q', '8K']:
            # SEC filings: Extract standard sections
            section_headers = [
                "Business",
                "Risk Factors",
                "Management's Discussion and Analysis",
                "Financial Statements",
                "Controls and Procedures"
            ]
            
            sections = TextChunker.chunk_by_sections(text, section_headers)
            
            # Convert to standard format
            return [
                {
                    "content": section["content"],
                    "metadata": {
                        "section": section["section"],
                        "method": "section"
                    }
                }
                for section in sections
            ]
        
        elif doc_type == 'news':
            # News: Paragraph-based
            chunks = TextChunker.chunk_by_paragraphs(text, max_paragraphs=5)
            
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "chunk_index": i,
                        "method": "paragraph"
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        
        else:
            # Default: Token-based
            chunks = TextChunker.chunk_by_tokens(text, chunk_size=max_tokens, overlap=200)
            
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "chunk_index": i,
                        "method": "token"
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.
        
        Uses rough approximation: 1 token ≈ 1.3 words
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        
        Example:
            >>> TextChunker.estimate_tokens("Hello world this is a test")
            8  # 6 words * 1.3 ≈ 8 tokens
        """
        words = len(text.split())
        return int(words * 1.3)


if __name__ == "__main__":
    # Example usage
    
    # Test 1: Token-based chunking
    long_text = " ".join([f"Sentence {i}." for i in range(10000)])
    chunks = TextChunker.chunk_by_tokens(long_text, chunk_size=4000, overlap=200)
    print(f"✅ Token chunking: {len(chunks)} chunks")
    print(f"   First chunk: {len(chunks[0].split())} words")
    print(f"   Estimated tokens: {TextChunker.estimate_tokens(chunks[0])}")
    
    # Test 2: Section-based chunking
    sec_filing = """
    Item 1. Business
    
    We are a technology company...
    
    Item 1A. Risk Factors
    
    Our business faces several risks...
    
    Item 7. Management's Discussion and Analysis
    
    The following discussion should be read...
    """
    
    sections = TextChunker.chunk_by_sections(sec_filing, [
        "Business",
        "Risk Factors",
        "Management's Discussion"
    ])
    print(f"\n✅ Section chunking: {len(sections)} sections")
    for section in sections:
        print(f"   - {section['section']}: {len(section['content'])} chars")
    
    # Test 3: Smart chunking
    smart_chunks = TextChunker.smart_chunk(sec_filing, doc_type='10K')
    print(f"\n✅ Smart chunking: {len(smart_chunks)} chunks")
    print(f"   Method: {smart_chunks[0]['metadata']['method']}")
