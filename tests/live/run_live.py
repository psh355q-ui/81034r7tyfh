"""
실전 사용 가이드: Constitutional AI Trading System
간단한 대화형 인터페이스

사용법:
  python run_live.py

작성일: 2025-12-15
"""

import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.constitution import Constitution
from backend.data.collectors.api_clients.yahoo_client import YahooFinanceClient


def print_header():
    """헤더 출력"""
    print("\n" + "="*70)
    print(" "*15 + "🏛️ Constitutional AI Trading System")
    print(" "*20 + "실전 투자 도우미")
    print("="*70 + "\n")


def get_user_input():
    """사용자 입력 받기"""
    print("📝 투자 아이디어를 입력하세요:\n")
    
    # 종목
    ticker = input("  종목 코드 (예: AAPL, MSFT, NVDA): ").strip().upper()
    if not ticker:
        ticker = "AAPL"
    
    # 뉴스/이유
    print(f"\n  {ticker}을(를) 고려하는 이유:")
    reason = input("  (예: AI 칩 기술 돌파구, 실적 호조 등): ").strip()
    if not reason:
        reason = "관심 종목"
    
    # 액션
    print("\n  예상 액션:")
    print("    1. BUY (매수)")
    print("    2. SELL (매도)")
    print("    3. HOLD (보유)")
    action_input = input("  선택 (1-3, 기본: 1): ").strip()
    
    action_map = {"1": "BUY", "2": "SELL", "3": "HOLD", "": "BUY"}
    action = action_map.get(action_input, "BUY")
    
    return {
        'ticker': ticker,
        'reason': reason,
        'action': action
    }


def get_market_data(ticker: str):
    """실시간 시장 데이터"""
    print(f"\n{'='*70}")
    print(f"📊 {ticker} 실시간 데이터 조회 중...")
    print(f"{'='*70}\n")
    
    try:
        yahoo = YahooFinanceClient()
        data = yahoo.get_etf_data(ticker, period="5d")
        
        if data and data.get('price'):
            price = data['price'][-1]
            volume = data['volume'][-1] if data.get('volume') else 0
            
            prev_price = data['price'][-2] if len(data['price']) > 1 else price
            change_pct = ((price - prev_price) / prev_price) * 100
            
            print(f"✅ 데이터 수집 완료:")
            print(f"  현재가: ${price:.2f}")
            print(f"  변동: {change_pct:+.2f}%")
            print(f"  거래량: {volume:,}")
            
            return price, change_pct, volume
        else:
            print(f"⚠️ {ticker} 데이터를 가져올 수 없습니다.")
            return None, None, None
            
    except Exception as e:
        print(f"⚠️ 에러: {e}")
        return None, None, None


def analyze_with_constitution(ticker: str, action: str, price: float, reason: str):
    """헌법 검증"""
    print(f"\n{'='*70}")
    print(f"🏛️ 헌법 검증")
    print(f"{'='*70}\n")
    
    constitution = Constitution()
    
    # 간단한 포트폴리오 가정
    total_capital = 100_000  # $100K
    order_value = total_capital * 0.10  # 10%
    
    proposal = {
        'ticker': ticker,
        'action': action,
        'target_price': price,
        'position_value': order_value,
        'order_value_usd': order_value,
        'is_approved': True,  # 사용자가 직접 입력했으므로 승인된 것으로 간주
        'reasoning': reason
    }
    
    context = {
        'total_capital': total_capital,
        'current_allocation': {'stock': 0.70, 'cash': 0.30},
        'market_regime': 'risk_on',
        'daily_trades': 0,
        'weekly_trades': 1,
        'daily_volume_usd': 10_000_000,
        'vix': 20
    }
    
    print(f"제안 내용:")
    print(f"  종목: {ticker}")
    print(f"  액션: {action}")
    print(f"  가격: ${price:.2f}")
    print(f"  주문 금액: ${order_value:,.0f} ({order_value/total_capital:.0%})")
    print(f"  이유: {reason}")
    
    # 검증
    is_valid, violations, violated_articles = constitution.validate_proposal(
        proposal, context
    )
    
    print(f"\n검증 결과:")
    if is_valid:
        print(f"  ✅ 헌법 준수 - 거래 가능")
    else:
        print(f"  ❌ 헌법 위반 - 거래 불가")
        if violations:
            print(f"\n위반 사항:")
            for v in violations[:3]:
                print(f"    • {v}")
    
    return is_valid, violations


def provide_recommendation(ticker: str, action: str, price: float, is_valid: bool, violations: list):
    """최종 추천"""
    print(f"\n{'='*70}")
    print(f"💡 Constitutional AI 추천")
    print(f"{'='*70}\n")
    
    if is_valid:
        print(f"✅ 승인 가능 제안:")
        print(f"\n  {ticker} {action} @ ${price:.2f}")
        print(f"\n권장 사항:")
        print(f"  1. 헌법 기준을 충족합니다")
        print(f"  2. 포지션 크기를 준수합니다")
        print(f"  3. 리스크가 관리 가능합니다")
        print(f"\n⚠️ 주의:")
        print(f"  • 최종 결정은 본인이 하세요 (제3조)")
        print(f"  • 시장 상황을 계속 모니터링하세요")
        print(f"  • Stop Loss를 설정하세요")
    else:
        print(f"❌ 거부 권장 제안:")
        print(f"\n  {ticker} {action} @ ${price:.2f}")
        print(f"\n거부 이유:")
        if violations:
            for i, v in enumerate(violations[:3], 1):
                print(f"  {i}. {v}")
        print(f"\n대안:")
        print(f"  • 포지션 크기를 줄이세요")
        print(f"  • 시장 상황이 개선될 때까지 대기")
        print(f"  • 다른 종목을 고려하세요")
    
    print(f"\n{'='*70}")
    print(f"💎 '수익률이 아닌 안전을 우선합니다'")
    print(f"{'='*70}\n")


def main():
    """메인 실행"""
    print_header()
    
    print("이 시스템은 AI Constitutional Trading System을 실전에서 사용합니다.")
    print("모든 제안을 헌법 기준으로 검증하여 안전한 투자를 돕습니다.\n")
    
    while True:
        # 사용자 입력
        user_input = get_user_input()
        
        # 시장 데이터
        price, change_pct, volume = get_market_data(user_input['ticker'])
        
        if price is None:
            print("\n데이터를 가져올 수 없어 분석을 건너뜁니다.\n")
            retry = input("다시 시도하시겠습니까? (y/n): ").strip().lower()
            if retry != 'y':
                break
            continue
        
        # 헌법 검증
        is_valid, violations = analyze_with_constitution(
            user_input['ticker'],
            user_input['action'],
            price,
            user_input['reason']
        )
        
        # 추천
        provide_recommendation(
            user_input['ticker'],
            user_input['action'],
            price,
            is_valid,
            violations
        )
        
        # 계속 여부
        print("\n" + "-"*70 + "\n")
        another = input("다른 종목을 분석하시겠습니까? (y/n): ").strip().lower()
        if another != 'y':
            break
        print("\n")
    
    print("\n" + "="*70)
    print("감사합니다! Constitutional AI Trading System을 이용해주셔서 감사합니다.")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
