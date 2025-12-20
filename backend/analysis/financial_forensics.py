"""
Financial Red Flags Detector

재무제표 분석을 통한 회계 조작 의혹 감지

Based on Michael Burry's analysis of NVIDIA (Nov 2025):
1. Receivables Explosion - 매출채권 급증
2. Inventory Buildup - 미판매 재고 증가
3. DSO Increase - 외상값 회수 지연
4. OCF/NI Ratio - 현금흐름 vs 이익 괴리

Author: AI Trading System
Date: 2025-11-21
Phase: 14 (Financial Forensics)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class RedFlagSeverity(Enum):
    """Red Flag 심각도"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RedFlagResult:
    """Red Flag 검사 결과"""
    flag_name: str
    severity: RedFlagSeverity
    current_value: float
    threshold: float
    is_triggered: bool
    description: str
    recommendation: str
    
    def to_dict(self) -> dict:
        return {
            'flag_name': self.flag_name,
            'severity': self.severity.name,
            'current_value': round(self.current_value, 4),
            'threshold': self.threshold,
            'is_triggered': self.is_triggered,
            'description': self.description,
            'recommendation': self.recommendation
        }


@dataclass
class FinancialForensicsReport:
    """재무 포렌식 분석 리포트"""
    ticker: str
    analysis_date: datetime
    red_flags: List[RedFlagResult]
    overall_verdict: str  # CLEAN, SUSPICIOUS, HIGH_RISK, CRITICAL
    confidence_score: float  # 0.0 ~ 1.0
    recommendation: str  # BUY, HOLD, SELL, SHORT
    summary: str
    
    @property
    def critical_count(self) -> int:
        return sum(1 for flag in self.red_flags if flag.severity == RedFlagSeverity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        return sum(1 for flag in self.red_flags if flag.severity == RedFlagSeverity.HIGH)
    
    def to_dict(self) -> dict:
        return {
            'ticker': self.ticker,
            'analysis_date': self.analysis_date.isoformat(),
            'red_flags': [flag.to_dict() for flag in self.red_flags],
            'overall_verdict': self.overall_verdict,
            'confidence_score': round(self.confidence_score, 2),
            'recommendation': self.recommendation,
            'summary': self.summary,
            'critical_count': self.critical_count,
            'high_count': self.high_count
        }


# ============================================================================
# Financial Data Fetcher
# ============================================================================

class FinancialDataFetcher:
    """재무제표 데이터 수집"""
    
    @staticmethod
    def get_financial_data(ticker: str) -> Optional[Dict]:
        """
        Yahoo Finance에서 재무제표 데이터 수집
        
        Args:
            ticker: 종목 티커
            
        Returns:
            재무 데이터 딕셔너리
        """
        try:
            stock = yf.Ticker(ticker)
            
            # 재무제표 가져오기
            income_stmt = stock.income_stmt  # 손익계산서
            balance_sheet = stock.balance_sheet  # 재무상태표
            cash_flow = stock.cash_flow  # 현금흐름표
            
            if income_stmt.empty or balance_sheet.empty or cash_flow.empty:
                logger.error(f"No financial data available for {ticker}")
                return None
            
            # 최근 2개 분기 데이터 (현재 + 이전)
            current_period = income_stmt.columns[0]
            previous_period = income_stmt.columns[1] if len(income_stmt.columns) > 1 else None
            
            # 데이터 추출
            data = {
                'ticker': ticker,
                'period': current_period,
                
                # 손익계산서
                'revenue': FinancialDataFetcher._safe_get(income_stmt, 'Total Revenue', current_period),
                'revenue_prev': FinancialDataFetcher._safe_get(income_stmt, 'Total Revenue', previous_period) if previous_period else None,
                'net_income': FinancialDataFetcher._safe_get(income_stmt, 'Net Income', current_period),
                'cogs': FinancialDataFetcher._safe_get(income_stmt, 'Cost Of Revenue', current_period),
                
                # 재무상태표
                'receivables': FinancialDataFetcher._safe_get(balance_sheet, 'Accounts Receivable', current_period),
                'receivables_prev': FinancialDataFetcher._safe_get(balance_sheet, 'Accounts Receivable', previous_period) if previous_period else None,
                'inventory': FinancialDataFetcher._safe_get(balance_sheet, 'Inventory', current_period),
                'inventory_prev': FinancialDataFetcher._safe_get(balance_sheet, 'Inventory', previous_period) if previous_period else None,
                'total_assets': FinancialDataFetcher._safe_get(balance_sheet, 'Total Assets', current_period),
                'cash': FinancialDataFetcher._safe_get(balance_sheet, 'Cash And Cash Equivalents', current_period),
                
                # 현금흐름표
                'operating_cash_flow': FinancialDataFetcher._safe_get(cash_flow, 'Operating Cash Flow', current_period),
                'capex': FinancialDataFetcher._safe_get(cash_flow, 'Capital Expenditure', current_period),
                'free_cash_flow': FinancialDataFetcher._safe_get(cash_flow, 'Free Cash Flow', current_period),
            }
            
            # None 값 처리
            for key, value in data.items():
                if value is None and key not in ['ticker', 'period', 'revenue_prev', 'receivables_prev', 'inventory_prev']:
                    logger.warning(f"Missing data for {ticker}.{key}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching financial data for {ticker}: {e}")
            return None
    
    @staticmethod
    def _safe_get(df: pd.DataFrame, key: str, period) -> Optional[float]:
        """DataFrame에서 안전하게 값 추출"""
        try:
            if period is None:
                return None
            if key in df.index:
                value = df.loc[key, period]
                return float(value) if pd.notna(value) else None
            return None
        except:
            return None


# ============================================================================
# Red Flag Calculators
# ============================================================================

class RedFlagCalculator:
    """Red Flag 계산기"""
    
    @staticmethod
    def check_receivables_explosion(data: Dict) -> RedFlagResult:
        """
        Red Flag 1: 매출채권 급증
        
        매출채권 증가율이 매출 증가율보다 20% 이상 높으면 위험
        (고객이 돈을 안 갚고 있거나, 가짜 매출일 가능성)
        
        NVIDIA Case: 매출채권 +89% vs 매출 +94% (정상 범위)
        """
        revenue = data.get('revenue')
        revenue_prev = data.get('revenue_prev')
        receivables = data.get('receivables')
        receivables_prev = data.get('receivables_prev')
        
        if not all([revenue, revenue_prev, receivables, receivables_prev]):
            return RedFlagResult(
                flag_name="RECEIVABLES_EXPLOSION",
                severity=RedFlagSeverity.NONE,
                current_value=0.0,
                threshold=1.2,
                is_triggered=False,
                description="Insufficient data to calculate",
                recommendation="N/A"
            )
        
        # 증가율 계산
        revenue_growth = (revenue - revenue_prev) / revenue_prev
        receivables_growth = (receivables - receivables_prev) / receivables_prev
        
        # 비율 (1.0 이하면 정상, 1.2 이상이면 위험)
        ratio = receivables_growth / revenue_growth if revenue_growth > 0 else 0
        
        # 판단
        is_triggered = ratio > 1.2
        
        if ratio > 1.5:
            severity = RedFlagSeverity.CRITICAL
            recommendation = "SHORT - Possible fake revenue"
        elif ratio > 1.2:
            severity = RedFlagSeverity.HIGH
            recommendation = "SELL - Receivables growing faster than revenue"
        else:
            severity = RedFlagSeverity.NONE
            recommendation = "CLEAN"
        
        return RedFlagResult(
            flag_name="RECEIVABLES_EXPLOSION",
            severity=severity,
            current_value=ratio,
            threshold=1.2,
            is_triggered=is_triggered,
            description=f"Receivables growth ({receivables_growth*100:.1f}%) vs Revenue growth ({revenue_growth*100:.1f}%)",
            recommendation=recommendation
        )
    
    @staticmethod
    def check_inventory_buildup(data: Dict) -> RedFlagResult:
        """
        Red Flag 2: 재고 증가
        
        재고자산/매출 비율이 30% 이상이면 미판매 재고 과다
        (수요가 줄어들고 있거나, 재고를 못 팔고 있음)
        
        NVIDIA Case: 198억 / 350억 = 56% (위험!)
        """
        inventory = data.get('inventory')
        revenue = data.get('revenue')
        
        if not inventory or not revenue:
            return RedFlagResult(
                flag_name="INVENTORY_BUILDUP",
                severity=RedFlagSeverity.NONE,
                current_value=0.0,
                threshold=0.3,
                is_triggered=False,
                description="Insufficient data",
                recommendation="N/A"
            )
        
        # 재고/매출 비율
        ratio = inventory / revenue
        
        # 판단
        is_triggered = ratio > 0.3
        
        if ratio > 0.5:
            severity = RedFlagSeverity.CRITICAL
            recommendation = "SHORT - Excessive unsold inventory"
        elif ratio > 0.3:
            severity = RedFlagSeverity.HIGH
            recommendation = "SELL - High inventory levels"
        else:
            severity = RedFlagSeverity.NONE
            recommendation = "CLEAN"
        
        return RedFlagResult(
            flag_name="INVENTORY_BUILDUP",
            severity=severity,
            current_value=ratio,
            threshold=0.3,
            is_triggered=is_triggered,
            description=f"Inventory/Revenue ratio: {ratio*100:.1f}%",
            recommendation=recommendation
        )
    
    @staticmethod
    def check_dso_increase(data: Dict) -> RedFlagResult:
        """
        Red Flag 3: DSO (Days Sales Outstanding) 증가
        
        외상값 회수 기간이 60일 이상이면 위험
        DSO = (매출채권 / 일일 매출)
        
        NVIDIA Case: 53일 (경고 수준)
        """
        receivables = data.get('receivables')
        revenue = data.get('revenue')
        
        if not receivables or not revenue:
            return RedFlagResult(
                flag_name="DSO_INCREASE",
                severity=RedFlagSeverity.NONE,
                current_value=0.0,
                threshold=60.0,
                is_triggered=False,
                description="Insufficient data",
                recommendation="N/A"
            )
        
        # 일일 매출 (분기 매출 / 90일)
        daily_revenue = revenue / 90
        
        # DSO 계산
        dso = receivables / daily_revenue
        
        # 판단
        is_triggered = dso > 60
        
        if dso > 75:
            severity = RedFlagSeverity.CRITICAL
            recommendation = "SHORT - Payment delays are severe"
        elif dso > 60:
            severity = RedFlagSeverity.HIGH
            recommendation = "SELL - Customers delaying payments"
        elif dso > 45:
            severity = RedFlagSeverity.MEDIUM
            recommendation = "HOLD - Watch DSO trend"
        else:
            severity = RedFlagSeverity.NONE
            recommendation = "CLEAN"
        
        return RedFlagResult(
            flag_name="DSO_INCREASE",
            severity=severity,
            current_value=dso,
            threshold=60.0,
            is_triggered=is_triggered,
            description=f"Days Sales Outstanding: {dso:.1f} days",
            recommendation=recommendation
        )
    
    @staticmethod
    def check_ocf_to_ni_ratio(data: Dict) -> RedFlagResult:
        """
        Red Flag 4: 영업현금흐름 / 순이익 비율
        
        이익은 났는데 현금이 안 들어오면 가짜 이익
        OCF/NI < 0.8 이면 위험
        
        NVIDIA Case: 확인 필요
        """
        ocf = data.get('operating_cash_flow')
        net_income = data.get('net_income')
        
        if not ocf or not net_income or net_income <= 0:
            return RedFlagResult(
                flag_name="OCF_TO_NI_RATIO",
                severity=RedFlagSeverity.NONE,
                current_value=0.0,
                threshold=0.8,
                is_triggered=False,
                description="Insufficient data or negative income",
                recommendation="N/A"
            )
        
        # OCF/NI 비율
        ratio = ocf / net_income
        
        # 판단
        is_triggered = ratio < 0.8
        
        if ratio < 0.5:
            severity = RedFlagSeverity.CRITICAL
            recommendation = "SHORT - Profit without cash (fake earnings)"
        elif ratio < 0.8:
            severity = RedFlagSeverity.HIGH
            recommendation = "SELL - Low quality earnings"
        else:
            severity = RedFlagSeverity.NONE
            recommendation = "CLEAN"
        
        return RedFlagResult(
            flag_name="OCF_TO_NI_RATIO",
            severity=severity,
            current_value=ratio,
            threshold=0.8,
            is_triggered=is_triggered,
            description=f"Operating Cash Flow / Net Income: {ratio:.2f}",
            recommendation=recommendation
        )


# ============================================================================
# Main Forensics Analyzer
# ============================================================================

class FinancialForensicsAnalyzer:
    """재무 포렌식 분석기"""
    
    def __init__(self):
        self.fetcher = FinancialDataFetcher()
        self.calculator = RedFlagCalculator()
    
    def analyze(self, ticker: str) -> Optional[FinancialForensicsReport]:
        """
        종목 재무 포렌식 분석
        
        Args:
            ticker: 종목 티커
            
        Returns:
            분석 리포트
        """
        logger.info(f"Starting financial forensics analysis for {ticker}")
        
        # 1. 재무 데이터 수집
        data = self.fetcher.get_financial_data(ticker)
        if not data:
            logger.error(f"Failed to fetch financial data for {ticker}")
            return None
        
        # 2. 모든 Red Flag 검사
        red_flags = [
            self.calculator.check_receivables_explosion(data),
            self.calculator.check_inventory_buildup(data),
            self.calculator.check_dso_increase(data),
            self.calculator.check_ocf_to_ni_ratio(data)
        ]
        
        # 3. 종합 판단
        verdict, confidence, recommendation, summary = self._assess_overall_risk(red_flags)
        
        # 4. 리포트 생성
        report = FinancialForensicsReport(
            ticker=ticker,
            analysis_date=datetime.now(),
            red_flags=red_flags,
            overall_verdict=verdict,
            confidence_score=confidence,
            recommendation=recommendation,
            summary=summary
        )
        
        logger.info(
            f"Analysis complete for {ticker}: {verdict} "
            f"(Critical: {report.critical_count}, High: {report.high_count})"
        )
        
        return report
    
    def _assess_overall_risk(
        self,
        red_flags: List[RedFlagResult]
    ) -> Tuple[str, float, str, str]:
        """
        Red Flag들을 종합하여 전체 리스크 평가
        
        Returns:
            (verdict, confidence, recommendation, summary)
        """
        critical_count = sum(1 for f in red_flags if f.severity == RedFlagSeverity.CRITICAL)
        high_count = sum(1 for f in red_flags if f.severity == RedFlagSeverity.HIGH)
        medium_count = sum(1 for f in red_flags if f.severity == RedFlagSeverity.MEDIUM)
        
        # Critical 2개 이상 = 즉시 Short
        if critical_count >= 2:
            return (
                "CRITICAL",
                0.95,
                "SHORT",
                f"Multiple critical accounting red flags detected ({critical_count} critical, {high_count} high). "
                "High probability of accounting manipulation or severe business deterioration."
            )
        
        # Critical 1개 + High 1개 이상 = High Risk
        if critical_count >= 1 and high_count >= 1:
            return (
                "HIGH_RISK",
                0.85,
                "SELL",
                f"Serious accounting concerns ({critical_count} critical, {high_count} high). "
                "Recommend exiting position."
            )
        
        # Critical 1개 또는 High 2개 이상 = Suspicious
        if critical_count >= 1 or high_count >= 2:
            return (
                "SUSPICIOUS",
                0.70,
                "SELL",
                f"Financial health concerns ({critical_count} critical, {high_count} high). "
                "Revenue quality may be deteriorating."
            )
        
        # High 1개 또는 Medium 2개 이상 = 관찰 필요
        if high_count >= 1 or medium_count >= 2:
            return (
                "SUSPICIOUS",
                0.50,
                "HOLD",
                f"Some warning signs detected ({high_count} high, {medium_count} medium). "
                "Monitor closely."
            )
        
        # 정상
        return (
            "CLEAN",
            0.90,
            "BUY",
            "No significant accounting red flags detected. Financial statements appear healthy."
        )


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # NVIDIA 분석
    analyzer = FinancialForensicsAnalyzer()
    report = analyzer.analyze("NVDA")
    
    if report:
        print("\n" + "="*60)
        print(f"Financial Forensics Report: {report.ticker}")
        print("="*60)
        print(f"Verdict: {report.overall_verdict}")
        print(f"Confidence: {report.confidence_score*100:.0f}%")
        print(f"Recommendation: {report.recommendation}")
        print(f"\nSummary: {report.summary}")
        print(f"\nRed Flags Detected:")
        
        for flag in report.red_flags:
            if flag.is_triggered:
                print(f"\n  🚨 {flag.flag_name} ({flag.severity.name})")
                print(f"     {flag.description}")
                print(f"     → {flag.recommendation}")
        
        print("\n" + "="*60)
