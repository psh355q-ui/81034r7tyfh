"""
Shadow Trading Daily Monitoring Script

Day 3 시작 - 매일 실행하여 포지션 모니터링 및 성과 추적

기능:
1. 현재 포지션 조회
2. 실시간 가격 업데이트
3. Stop Loss 체크
4. Daily P&L 계산
5. 알림 발송 (필요시)
"""
import os
import sys
import requests
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Config
BASE_URL = "http://localhost:8001"
TELEGRAM_ENABLED = False  # 나중에 활성화

def get_shadow_status():
    """Shadow Trading 현재 상태 조회"""
    try:
        response = requests.get(f"{BASE_URL}/api/war-room-mvp/shadow/status", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Status API returned {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching status: {e}")
        return None

def check_positions(status):
    """포지션 상태 확인 및 Stop Loss 체크"""
    import sys
    
    if not status or 'info' not in status:
        print("⚠️  No status data")
        return
    
    info = status['info']
    
    print(f"\n{'='*80}")
    print(f"📊 Shadow Trading - Daily Monitor")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Session: {info.get('status', 'N/A')}")
    print(f"Day: {info.get('days_running', 'N/A')}\n")
    sys.stdout.flush()
    
    # Capital Overview
    print(f"💰 Capital Overview:")
    print(f"  Initial:    ${info.get('initial_capital', 0):,.2f}")
    print(f"  Current:    ${info.get('current_capital', 0):,.2f}")
    print(f"  Available:  ${info.get('available_cash', 0):,.2f}")
    invested = info.get('initial_capital', 0) - info.get('available_cash', 0)
    print(f"  Invested:   ${invested:,.2f} ({invested/info.get('initial_capital', 1)*100:.1f}%)\n")
    sys.stdout.flush()
    
    # Open Positions with Details
    open_positions = status.get('open_positions', [])
    open_count = len(open_positions)
    
    if open_count == 0:
        print("📭 No open positions")
        print("\n✅ Portfolio safe with no active trades\n")
    else:
        print(f"📈 Open Positions ({open_count}):")
        print(f"{'Symbol':<8} {'Qty':>6} {'Entry':>10} {'Current':>10} {'P&L':>12} {'Stop Loss':>10} {'Status':<12}")
        print("-" * 90)
        sys.stdout.flush()
        
        total_pnl = 0
        stop_loss_warnings = []
        
        for pos in open_positions:
            symbol = pos.get('symbol', 'N/A')
            quantity = pos.get('quantity', 0)
            entry_price = pos.get('entry_price', 0)
            current_price = pos.get('current_price', entry_price)
            current_pnl = pos.get('current_pnl', 0)
            stop_loss = pos.get('stop_loss', 0)
            
            # P&L 계산
            if current_price and entry_price:
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                pnl_dollar = (current_price - entry_price) * quantity
            else:
                pnl_pct = 0
                pnl_dollar = current_pnl if current_pnl else 0
            
            total_pnl += pnl_dollar
            
            # Stop Loss 체크
            if stop_loss and current_price:
                distance_to_sl = ((current_price - stop_loss) / current_price) * 100
                if distance_to_sl <= 2.0:  # 2% 이내
                    status_text = "⚠️ NEAR SL"
                    stop_loss_warnings.append({
                        'symbol': symbol,
                        'distance': distance_to_sl,
                        'current': current_price,
                        'stop_loss': stop_loss
                    })
                elif current_price <= stop_loss:
                    status_text = "🚨 SL HIT"
                else:
                    status_text = "✅ Safe  "
            else:
                status_text = "N/A      "
            
            print(f"{symbol:<8} {quantity:>6} ${entry_price:>9.2f} ${current_price:>9.2f} "
                  f"${pnl_dollar:>10.2f} ${stop_loss:>9.2f} {status_text:<12}")
        
        print("-" * 90)
        print(f"{'Total P&L':<8} {'':<6} {'':<10} {'':<10} ${total_pnl:>10.2f}\n")
        sys.stdout.flush()
        
        # Stop Loss Warnings
        if stop_loss_warnings:
            print(f"\n⚠️  STOP LOSS ALERTS:")
            for warning in stop_loss_warnings:
                print(f"  {warning['symbol']}: ${warning['current']:.2f} is {warning['distance']:.1f}% "
                      f"above Stop Loss (${warning['stop_loss']:.2f})")
            print()
            sys.stdout.flush()
    
    # Performance
    print(f"\n{'='*80}")
    print(f"📊 Performance Metrics")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    perf = status.get('performance', {})
    print(f"  Total Trades:    {perf.get('total_trades', 0)}")
    print(f"  Winning Trades:  {perf.get('winning_trades', 0)}")
    print(f"  Losing Trades:   {perf.get('losing_trades', 0)}")
    print(f"  Win Rate:        {perf.get('win_rate', 0)*100:.1f}%")
    print(f"  Profit Factor:   {perf.get('profit_factor', 0):.2f}")
    print(f"  Total P&L:       ${perf.get('total_pnl', 0):,.2f} ({perf.get('total_pnl_pct', 0):.2f}%)")
    print(f"  Max Drawdown:    {perf.get('max_drawdown', 0):.2f}%")
    print(f"  Sharpe Ratio:    {perf.get('sharpe_ratio', 0):.2f}")
    
    print(f"\n{'='*80}\n")

def send_telegram_alert(alerts):
    """Telegram 알림 발송 (나중에 구현)"""
    if not TELEGRAM_ENABLED:
        return
    
    # TODO: Telegram Bot API integration
    pass

def main():
    """Daily monitoring main"""
    print("\n🚀 Shadow Trading Daily Monitor")
    print(f"   Timestamp: {datetime.now()}\n")
    
    # 1. Get current status
    status = get_shadow_status()
    if not status:
        print("❌ Failed to fetch Shadow Trading status")
        print("💡 Make sure backend is running on port 8001")
        return
    
    # 2. Check positions and alerts
    check_positions(status)
    
    print("✅ Daily monitoring complete!\n")
    print("📝 Next steps:")
    print("  - Run this script daily to track positions")
    print("  - Check for Stop Loss alerts")
    print("  - Review performance metrics")
    print()

if __name__ == "__main__":
    main()
