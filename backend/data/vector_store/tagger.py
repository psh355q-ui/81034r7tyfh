"""
AutoTagger - AI-powered automatic tag generation for documents.

Generates multi-dimensional tags:
- Ticker tags: Stock symbols mentioned
- Sector tags: Industry sectors
- Topic tags: Key themes (supply_chain, regulatory_risk, etc.)
- Entity tags: Named entities (CEO names, products, regions)
- Geographic tags: Geographic regions
"""

from typing import List, Dict, Optional
import re
from anthropic import AsyncAnthropic


class AutoTagger:
    """
    Automatic tag generation for documents using hybrid approach:
    - Rule-based for tickers and basic topics (fast, $0)
    - AI-based for sectors and entities (accurate, low cost)
    
    Cost optimization:
    - Use Claude Haiku ($0.25/1M tokens) instead of Sonnet
    - Only use AI for ambiguous cases
    - Cache common patterns
    
    Usage:
        tagger = AutoTagger(claude_client, use_ai=True)
        tags = await tagger.generate_tags(content, ticker="AAPL", doc_type="10K")
    """
    
    # Predefined taxonomies
    SECTORS = [
        "Technology", "Healthcare", "Financials", "Consumer Discretionary",
        "Communication Services", "Industrials", "Consumer Staples",
        "Energy", "Utilities", "Real Estate", "Materials"
    ]
    
    TOPICS = [
        "supply_chain", "regulatory_risk", "legal_risk", "labor_dispute",
        "AI_adoption", "cybersecurity", "ESG", "M&A", "earnings_miss",
        "product_launch", "leadership_change", "market_expansion",
        "debt_restructuring", "dividend_change", "buyback",
        "patent_litigation", "antitrust", "data_breach"
    ]
    
    # Topic keyword mapping (for rule-based detection)
    TOPIC_KEYWORDS = {
        "supply_chain": ["supply chain", "supplier", "logistics", "shortage", "inventory", "procurement"],
        "regulatory_risk": ["regulation", "compliance", "FDA", "SEC", "antitrust", "regulatory"],
        "legal_risk": ["lawsuit", "litigation", "settlement", "penalty", "investigation", "legal action"],
        "labor_dispute": ["strike", "union", "labor", "workforce", "employee relations", "collective bargaining"],
        "AI_adoption": ["artificial intelligence", "machine learning", "AI", "automation", "neural network"],
        "cybersecurity": ["cyber", "data breach", "hack", "security incident", "ransomware"],
        "ESG": ["environmental", "sustainability", "carbon", "ESG", "climate", "renewable"],
        "M&A": ["merger", "acquisition", "takeover", "buyout", "consolidation"],
        "earnings_miss": ["earnings miss", "revenue below", "guidance cut", "disappointing results"],
        "product_launch": ["new product", "launch", "release", "unveil", "introduce"],
        "leadership_change": ["CEO", "CFO", "resignation", "appointed", "successor", "executive change"],
        "market_expansion": ["expansion", "new market", "international", "geographic", "entering"],
        "debt_restructuring": ["debt", "restructuring", "refinancing", "covenant", "default"],
        "dividend_change": ["dividend", "payout", "yield", "distribution"],
        "buyback": ["buyback", "repurchase", "share repurchase"],
        "patent_litigation": ["patent", "intellectual property", "IP", "infringement"],
        "antitrust": ["antitrust", "monopoly", "competition", "DOJ", "FTC"],
        "data_breach": ["data breach", "privacy", "GDPR", "personal information"]
    }
    
    def __init__(
        self,
        claude_client: Optional[AsyncAnthropic] = None,
        use_ai: bool = True,
        claude_model: str = "claude-haiku-4-20250514"
    ):
        """
        Initialize AutoTagger.
        
        Args:
            claude_client: Anthropic Claude client (optional)
            use_ai: Whether to use AI for ambiguous cases
            claude_model: Claude model to use (default: Haiku for low cost)
        """
        self.claude = claude_client
        self.use_ai = use_ai and claude_client is not None
        self.claude_model = claude_model
        
        # Stats
        self.total_tags_generated = 0
        self.ai_calls_made = 0
        self.total_ai_cost = 0.0
    
    async def generate_tags(
        self,
        content: str,
        primary_ticker: str,
        doc_type: str,
        max_tags: int = 20
    ) -> List[Dict]:
        """
        Generate comprehensive tags for a document.
        
        Args:
            content: Document text
            primary_ticker: Primary stock ticker
            doc_type: Document type ('10K', '10Q', 'news', etc.)
            max_tags: Maximum tags to generate
        
        Returns:
            List of {"type": str, "value": str, "confidence": float} dictionaries
        
        Example:
            >>> tags = await tagger.generate_tags(
            ...     content="Apple reports supply chain issues in China...",
            ...     primary_ticker="AAPL",
            ...     doc_type="news"
            ... )
            >>> tags
            [
                {"type": "ticker", "value": "AAPL", "confidence": 1.0},
                {"type": "sector", "value": "Technology", "confidence": 0.95},
                {"type": "topic", "value": "supply_chain", "confidence": 0.87},
                {"type": "geographic", "value": "China", "confidence": 0.92}
            ]
        """
        tags = []
        
        # 1. Primary ticker (always confidence 1.0)
        tags.append({
            "type": "ticker",
            "value": primary_ticker,
            "confidence": 1.0
        })
        
        # 2. Extract additional ticker mentions
        ticker_tags = self._extract_ticker_tags(content, primary_ticker)
        tags.extend(ticker_tags)
        
        # 3. Extract sector (AI-based if enabled)
        sector_tags = await self._extract_sector_tags(content, primary_ticker)
        tags.extend(sector_tags)
        
        # 4. Extract topics (rule-based)
        topic_tags = self._extract_topic_tags(content)
        tags.extend(topic_tags)
        
        # 5. Extract entities (AI-based if enabled)
        if self.use_ai:
            entity_tags = await self._extract_entity_tags(content)
            tags.extend(entity_tags)
        
        # 6. Extract geographic regions (rule-based + AI)
        geo_tags = self._extract_geographic_tags(content)
        tags.extend(geo_tags)
        
        # Deduplicate and limit
        unique_tags = self._deduplicate_tags(tags)
        self.total_tags_generated += len(unique_tags)
        
        return unique_tags[:max_tags]
    
    def _extract_ticker_tags(self, content: str, primary_ticker: str) -> List[Dict]:
        """Extract stock ticker mentions from text."""
        tags = []
        
        # Regex for ticker symbols (1-5 uppercase letters)
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        mentioned_tickers = set(re.findall(ticker_pattern, content))
        
        # Filter out common false positives
        exclude_words = {
            "CEO", "CFO", "SEC", "FDA", "USA", "NYSE", "NASDAQ", "ETF",
            "IPO", "LLC", "INC", "CORP", "LTD", "THE", "AND", "FOR"
        }
        mentioned_tickers = mentioned_tickers - exclude_words - {primary_ticker}
        
        # Only keep tickers that appear with context (near "stock", "shares", etc.)
        context_pattern = r'(?:stock|shares|equity|ticker|symbol)\s+([A-Z]{1,5})'
        context_tickers = set(re.findall(context_pattern, content, re.IGNORECASE))
        
        for ticker in mentioned_tickers:
            confidence = 0.9 if ticker in context_tickers else 0.6
            tags.append({
                "type": "ticker",
                "value": ticker,
                "confidence": confidence
            })
        
        return tags
    
    async def _extract_sector_tags(self, content: str, ticker: str) -> List[Dict]:
        """Extract sector tags (AI-based if enabled, else rule-based)."""
        if not self.use_ai:
            # Rule-based fallback: keyword matching
            for sector in self.SECTORS:
                if sector.lower() in content.lower():
                    return [{
                        "type": "sector",
                        "value": sector,
                        "confidence": 0.75
                    }]
            return []
        
        # AI-based sector classification
        prompt = f"""Classify this document into ONE primary sector from this list:
{', '.join(self.SECTORS)}

Document excerpt (first 2000 chars):
{content[:2000]}

Respond with ONLY the sector name from the list above. Nothing else."""

        try:
            response = await self.claude.messages.create(
                model=self.claude_model,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            
            sector = response.content[0].text.strip()
            
            # Track AI cost (rough estimate)
            tokens_used = 2000 * 1.3  # Approximate
            cost = (tokens_used / 1_000_000) * 0.25  # Haiku: $0.25/1M tokens
            self.total_ai_cost += cost
            self.ai_calls_made += 1
            
            if sector in self.SECTORS:
                return [{
                    "type": "sector",
                    "value": sector,
                    "confidence": 0.95
                }]
        
        except Exception as e:
            print(f"  ⚠️  Sector classification error: {e}")
        
        return []
    
    def _extract_topic_tags(self, content: str) -> List[Dict]:
        """Extract topic tags using keyword matching."""
        tags = []
        content_lower = content.lower()
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            
            if matches > 0:
                # Confidence based on number of matching keywords
                confidence = min(0.7 + (matches * 0.05), 0.95)
                
                tags.append({
                    "type": "topic",
                    "value": topic,
                    "confidence": confidence
                })
        
        return tags
    
    async def _extract_entity_tags(self, content: str) -> List[Dict]:
        """Extract named entities using Claude API."""
        if not self.use_ai:
            return []
        
        prompt = f"""Extract important named entities from this document.
Focus on:
- Executive names (CEO, CFO, etc.)
- Product names
- Company names (excluding the primary company)
- Key people

Document excerpt (first 2000 chars):
{content[:2000]}

Respond with ONLY a comma-separated list of entities. Maximum 10 entities.
Example: Tim Cook, iPhone 15, Tesla, Elon Musk"""

        try:
            response = await self.claude.messages.create(
                model=self.claude_model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            entities_text = response.content[0].text.strip()
            entities = [e.strip() for e in entities_text.split(",") if e.strip()]
            
            # Track AI cost
            tokens_used = 2200 * 1.3
            cost = (tokens_used / 1_000_000) * 0.25
            self.total_ai_cost += cost
            self.ai_calls_made += 1
            
            tags = []
            for entity in entities[:10]:  # Limit to top 10
                tags.append({
                    "type": "entity",
                    "value": entity,
                    "confidence": 0.85
                })
            
            return tags
        
        except Exception as e:
            print(f"  ⚠️  Entity extraction error: {e}")
            return []
    
    def _extract_geographic_tags(self, content: str) -> List[Dict]:
        """Extract geographic regions (rule-based)."""
        tags = []
        
        # Common geographic regions
        regions = {
            "China": ["china", "chinese", "beijing", "shanghai"],
            "United States": ["usa", "united states", "america", "us "],
            "Europe": ["europe", "european", "eu "],
            "Asia": ["asia", "asian"],
            "India": ["india", "indian"],
            "Japan": ["japan", "japanese", "tokyo"],
            "South Korea": ["korea", "korean", "seoul"],
            "Latin America": ["latin america", "brazil", "mexico"],
            "Middle East": ["middle east", "saudi", "uae"]
        }
        
        content_lower = content.lower()
        
        for region, keywords in regions.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append({
                    "type": "geographic",
                    "value": region,
                    "confidence": 0.85
                })
        
        return tags
    
    def _deduplicate_tags(self, tags: List[Dict]) -> List[Dict]:
        """Remove duplicate tags, keeping highest confidence."""
        unique = {}
        
        for tag in tags:
            key = (tag["type"], tag["value"])
            
            if key not in unique or tag["confidence"] > unique[key]["confidence"]:
                unique[key] = tag
        
        return list(unique.values())
    
    def get_stats(self) -> Dict:
        """Get tagging statistics."""
        return {
            "total_tags_generated": self.total_tags_generated,
            "ai_calls_made": self.ai_calls_made,
            "total_ai_cost_usd": round(self.total_ai_cost, 6),
            "avg_cost_per_call": round(
                self.total_ai_cost / max(self.ai_calls_made, 1), 6
            )
        }


if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    from anthropic import AsyncAnthropic
    
    async def test():
        # Test without AI (rule-based only)
        tagger_basic = AutoTagger(use_ai=False)
        
        sample_text = """
        Apple Inc. (AAPL) reported supply chain disruptions in China affecting 
        iPhone production. CEO Tim Cook mentioned ongoing challenges with 
        component shortages. The company is expanding operations in India 
        as part of its diversification strategy.
        """
        
        tags_basic = await tagger_basic.generate_tags(
            content=sample_text,
            primary_ticker="AAPL",
            doc_type="news"
        )
        
        print("✅ Rule-based tagging:")
        for tag in tags_basic:
            print(f"   {tag['type']:12} {tag['value']:20} (confidence: {tag['confidence']:.2f})")
        
        # Test with AI (if API key available)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            claude = AsyncAnthropic(api_key=api_key)
            tagger_ai = AutoTagger(claude_client=claude, use_ai=True)
            
            tags_ai = await tagger_ai.generate_tags(
                content=sample_text,
                primary_ticker="AAPL",
                doc_type="news"
            )
            
            print("\n✅ AI-enhanced tagging:")
            for tag in tags_ai:
                print(f"   {tag['type']:12} {tag['value']:20} (confidence: {tag['confidence']:.2f})")
            
            stats = tagger_ai.get_stats()
            print(f"\n📊 AI Stats:")
            print(f"   AI calls: {stats['ai_calls_made']}")
            print(f"   Total cost: ${stats['total_ai_cost_usd']:.6f}")
    
    asyncio.run(test())
