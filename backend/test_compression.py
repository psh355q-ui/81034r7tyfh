"""
Test LLMLingua-2 Compression

Quick test to verify compression module works correctly.
"""

import asyncio
from backend.ai.compression import get_compressor


async def test_compression():
    """Test LLMLingua-2 compression on sample SEC text"""
    
    # Sample SEC filing text (boilerplate-heavy)
    sample_text = """
    UNITED STATES SECURITIES AND EXCHANGE COMMISSION
    Washington, D.C. 20549
    
    FORM 10-Q
    
    QUARTERLY REPORT PURSUANT TO SECTION 13 OR 15(d)
    OF THE SECURITIES EXCHANGE ACT OF 1934
    
    For the quarterly period ended September 30, 2024
    
    The Company's revenue for the third quarter of 2024 was $1.2 billion, 
    representing a 15% increase compared to the same period last year. 
    This growth was primarily driven by strong demand for our cloud services 
    and enterprise software solutions.
    
    Operating expenses for the quarter totaled $850 million, up from $780 million 
    in the prior year period. The increase was largely attributable to higher 
    research and development costs as we continue to invest in AI and machine 
    learning capabilities.
    
    Risk Factors:
    
    We face intense competition in the technology sector. Our competitors may have 
    greater financial resources or more established market positions. If we are 
    unable to compete effectively, our business could be materially harmed.
    
    Changes in economic conditions could negatively impact demand for our products. 
    A recession or economic downturn could lead to reduced IT spending by our customers.
    
    Cybersecurity threats continue to evolve. Despite our security measures, 
    we may be vulnerable to data breaches that could damage our reputation and 
    result in significant costs.
    
    [Additional 500 words of standard legal boilerplate and disclosures...]
    """ * 3  # Simulate longer filing
    
    print("🧪 Testing LLMLingua-2 Compression")
    print("=" * 60)
    
    # Get compressor
    compressor = get_compressor()
    
    # Test SEC filing compression
    print("\n📄 Compressing SEC filing text...")
    result = compressor.compress_sec_filing(
        filing_text=sample_text,
        query="What are the key risks and revenue trends?"
    )
    
    print(f"\n📊 Compression Results:")
    print(f"  Original tokens: {result['original_tokens']:,}")
    print(f"  Compressed tokens: {result['compressed_tokens']:,}")
    print(f"  Compression ratio: {result['compression_ratio']:.1%}")
    print(f"  Token savings: {result['savings']:.1%}")
    
    print(f"\n✂️ Original length: {len(sample_text):,} characters")
    print(f"  Compressed length: {len(result['compressed_prompt']):,} characters")
    
    print(f"\n💰 Cost Impact (estimated):")
    # Claude Sonnet: ~$3/1M input tokens
    original_cost = (result['original_tokens'] / 1_000_000) * 3.00
    compressed_cost = (result['compressed_tokens'] / 1_000_000) * 3.00
    savings = original_cost - compressed_cost
    
    print(f"  Original cost: ${original_cost:.4f}")
    print(f"  Compressed cost: ${compressed_cost:.4f}")
    print(f"  💸 Savings: ${savings:.4f} ({result['savings']:.1%})")
    
    # Show compressed sample
    print(f"\n📝 Compressed text sample (first 300 chars):")
    print(f"  {result['compressed_prompt'][:300]}...")
    
    print("\n✅ Compression test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_compression())
