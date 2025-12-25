"""
Tax Engine - 미국 배당 세금 계산

Phase 21: Dividend Intelligence Module - Step 1.5
Date: 2025-12-25

Features:
- 미국 원천징수 15% 계산
- 한국 금융소득세 15.4% (14% + 1.4% 지방세)
- 종합과세 경고 (연 2천만원 초과)
"""

from typing import Dict, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class TaxEngine:
    """미국 배당 세금 계산"""
    
    # 세율 상수
    US_WITHHOLDING = 0.15  # 미국 원천징수 15%
    KR_COMPREHENSIVE_THRESHOLD = 20_000_000  # 종합과세 기준 (연 2천만원)
    KR_FINANCIAL_INCOME_TAX = 0.154  # 금융소득 세율 (15.4% = 14% + 1.4% 지방세)
    
    # 종합과세 구간별 세율 (참고용)
    KR_COMPREHENSIVE_TAX_BRACKETS = [
        {"min": 0, "max": 14_000_000, "rate": 0.06, "deduction": 0},
        {"min": 14_000_000, "max": 50_000_000, "rate": 0.15, "deduction": 1_260_000},
        {"min": 50_000_000, "max": 88_000_000, "rate": 0.24, "deduction": 5_760_000},
        {"min": 88_000_000, "max": 150_000_000, "rate": 0.35, "deduction": 15_440_000},
        {"min": 150_000_000, "max": 300_000_000, "rate": 0.38, "deduction": 19_940_000},
        {"min": 300_000_000, "max": 500_000_000, "rate": 0.40, "deduction": 25_940_000},
        {"min": 500_000_000, "max": float('inf'), "rate": 0.45, "deduction": 35_940_000}
    ]
    
    async def calculate_net_dividend(
        self,
        gross_usd: float,
        exchange_rate: float,
        annual_financial_income_krw: float = 0
    ) -> Dict:
        """
        세후 배당금 계산
        
        Args:
            gross_usd: 세전 배당금 (USD)
            exchange_rate: 환율 (KRW/USD)
            annual_financial_income_krw: 연간 금융소득 (KRW, 이자 + 배당)
        
        Returns:
            {
                "gross_usd": 1000,
                "us_withholding_usd": 150,  # 미국 원천징수
                "after_us_tax_usd": 850,
                "gross_krw": 1300000,
                "kr_tax_krw": 130900,  # 한국 세금
                "net_krw": 1105000,
                "effective_tax_rate": 15.0,
                "comprehensive_tax_warning": false,
                "comprehensive_tax_info": {...}  # 종합과세 대상 시
            }
        """
        
        # 1. 미국 원천징수
        us_tax_usd = gross_usd * self.US_WITHHOLDING
        after_us_usd = gross_usd - us_tax_usd
        
        # 2. 원화 환산
        gross_krw = gross_usd * exchange_rate
        after_us_krw = after_us_usd * exchange_rate
        us_tax_krw = us_tax_usd * exchange_rate
        
        # 3. 한국 세금
        kr_tax_krw = 0
        comprehensive_warning = False
        comprehensive_info = None
        
        if annual_financial_income_krw > self.KR_COMPREHENSIVE_THRESHOLD:
            # 종합과세 대상
            comprehensive_warning = True
            
            # 종합과세 예상 세율 계산 (간소화)
            # 실제로는 각 개인의 총 소득에 따라 다름
            comprehensive_info = {
                "is_comprehensive": True,
                "financial_income_krw": annual_financial_income_krw,
                "threshold_krw": self.KR_COMPREHENSIVE_THRESHOLD,
                "excess_krw": annual_financial_income_krw - self.KR_COMPREHENSIVE_THRESHOLD,
                "message": "연간 금융소득이 2천만원을 초과하여 종합과세 대상입니다. 실제 세율은 개인의 총 소득에 따라 6~45%입니다.",
                "warning": "세무사 상담을 권장합니다."
            }
            
            logger.warning(f"Comprehensive tax warning: {annual_financial_income_krw:,} KRW > threshold")
        
        # 금융소득세 (분리과세) 15.4%
        kr_tax_krw = after_us_krw * self.KR_FINANCIAL_INCOME_TAX
        
        # 4. 최종 세후 금액
        net_krw = after_us_krw - kr_tax_krw
        
        # 5. 실효 세율
        total_tax_krw = us_tax_krw + kr_tax_krw
        effective_rate = (total_tax_krw / gross_krw) * 100 if gross_krw > 0 else 0
        
        result = {
            "gross_usd": round(gross_usd, 2),
            "us_withholding_usd": round(us_tax_usd, 2),
            "after_us_tax_usd": round(after_us_usd, 2),
            "gross_krw": round(gross_krw),
            "us_tax_krw": round(us_tax_krw),
            "kr_tax_krw": round(kr_tax_krw),
            "total_tax_krw": round(total_tax_krw),
            "net_krw": round(net_krw),
            "effective_tax_rate": round(effective_rate, 2),
            "comprehensive_tax_warning": comprehensive_warning
        }
        
        if comprehensive_info:
            result['comprehensive_tax_info'] = comprehensive_info
        
        return result
    
    def calculate_comprehensive_tax_estimate(self, total_income_krw: float, financial_income_krw: float) -> Dict:
        """
        종합과세 예상 세금 계산 (참고용)
        
        Args:
            total_income_krw: 총 소득 (근로소득 + 금융소득 등)
            financial_income_krw: 금융소득 (이자 + 배당)
        
        Returns:
            {
                "total_income_krw": 100000000,
                "financial_income_krw": 30000000,
                "tax_bracket": "35%",
                "estimated_tax_krw": 35000000,
                "effective_rate": 35.0
            }
        """
        
        # 세율 구간 찾기
        bracket = None
        for b in self.KR_COMPREHENSIVE_TAX_BRACKETS:
            if b['min'] <= total_income_krw < b['max']:
                bracket = b
                break
        
        if not bracket:
            bracket = self.KR_COMPREHENSIVE_TAX_BRACKETS[-1]
        
        # 세금 계산
        estimated_tax = total_income_krw * bracket['rate'] - bracket['deduction']
        estimated_tax = max(0, estimated_tax)
        
        effective_rate = (estimated_tax / total_income_krw) * 100 if total_income_krw > 0 else 0
        
        return {
            "total_income_krw": total_income_krw,
            "financial_income_krw": financial_income_krw,
            "tax_bracket": f"{bracket['rate'] * 100:.0f}%",
            "estimated_tax_krw": round(estimated_tax),
            "effective_rate": round(effective_rate, 2),
            "warning": "이것은 예상치입니다. 정확한 세금은 세무사와 상담하세요."
        }


# CLI 실행
async def main():
    """테스트 실행"""
    
    tax_engine = TaxEngine()
    
    print("=" * 70)
    print("Tax Engine Test")
    print("=" * 70)
    print()
    
    exchange_rate = 1300.0  # KRW/USD
    
    # 테스트 케이스 1: 일반적인 배당 (종합과세 X)
    print("1️⃣ 일반 배당 (종합과세 대상 아님)")
    print("-" * 70)
    result1 = await tax_engine.calculate_net_dividend(
        gross_usd=1000,
        exchange_rate=exchange_rate,
        annual_financial_income_krw=10_000_000  # 1천만원 (< 2천만원)
    )
    
    print(f"Gross: ${result1['gross_usd']} (₩{result1['gross_krw']:,})")
    print(f"US Tax: ${result1['us_withholding_usd']} (₩{result1['us_tax_krw']:,})")
    print(f"KR Tax: ₩{result1['kr_tax_krw']:,}")
    print(f"Net: ₩{result1['net_krw']:,}")
    print(f"Effective Tax Rate: {result1['effective_tax_rate']}%")
    print(f"Comprehensive Tax Warning: {result1['comprehensive_tax_warning']}")
    
    # 테스트 케이스 2: 고액 배당 (종합과세 O)
    print("\n2️⃣ 고액 배당 (종합과세 대상)")
    print("-" * 70)
    result2 = await tax_engine.calculate_net_dividend(
        gross_usd=5000,
        exchange_rate=exchange_rate,
        annual_financial_income_krw=30_000_000  # 3천만원 (> 2천만원)
    )
    
    print(f"Gross: ${result2['gross_usd']} (₩{result2['gross_krw']:,})")
    print(f"Net: ₩{result2['net_krw']:,}")
    print(f"Effective Tax Rate: {result2['effective_tax_rate']}%")
    print(f"⚠️ Comprehensive Tax Warning: {result2['comprehensive_tax_warning']}")
    
    if 'comprehensive_tax_info' in result2:
        info = result2['comprehensive_tax_info']
        print(f"   Financial Income: ₩{info['financial_income_krw']:,}")
        print(f"   Threshold: ₩{info['threshold_krw']:,}")
        print(f"   Excess: ₩{info['excess_krw']:,}")
        print(f"   Message: {info['message']}")
    
    # 테스트 케이스 3: 종합과세 예상 계산
    print("\n3️⃣ 종합과세 예상 계산")
    print("-" * 70)
    comprehensive = tax_engine.calculate_comprehensive_tax_estimate(
        total_income_krw=100_000_000,  # 총 소득 1억
        financial_income_krw=30_000_000  # 금융소득 3천만원
    )
    
    print(f"Total Income: ₩{comprehensive['total_income_krw']:,}")
    print(f"Financial Income: ₩{comprehensive['financial_income_krw']:,}")
    print(f"Tax Bracket: {comprehensive['tax_bracket']}")
    print(f"Estimated Tax: ₩{comprehensive['estimated_tax_krw']:,}")
    print(f"Effective Rate: {comprehensive['effective_rate']}%")
    print(f"Warning: {comprehensive['warning']}")
    
    print("\n" + "=" * 70)
    print("✅ Test completed")
    print("=" * 70)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
