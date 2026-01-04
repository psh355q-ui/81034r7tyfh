"""
Shadow Trading Week 1 데이터 수집

기간: 2025-12-31 ~ 2026-01-07
세션 ID: shadow_2025-12-31T13:37:42.235264
"""
import psycopg2
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from decimal import Decimal

# Load environment
load_dotenv()

# DATABASE_URL에서 asyncpg 제거 (psycopg2용)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ai_trading')
DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
SESSION_ID = 'shadow_2025-12-31T13:37:42.235264'


def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def collect_trading_data():
    """거래 데이터 수집"""
    print("="*60)
    print("Shadow Trading Week 1 데이터 수집")
    print("="*60)
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. 세션 정보
    print("\n📊 세션 정보 조회...")
    cursor.execute("""
        SELECT 
            session_id,
            initial_capital,
            available_cash,
            current_capital,
            status,
            created_at
        FROM shadow_trading_sessions
        WHERE session_id = %s
    """, (SESSION_ID,))
    
    session = cursor.fetchone()
    
    if not session:
        print(f"❌ 세션을 찾을 수 없습니다: {SESSION_ID}")
        return None
    
    session_info = {
        'session_id': session[0],
        'initial_capital': float(session[1]),
        'available_cash': float(session[2]),
        'current_capital': float(session[3]),
        'status': session[4],
        'created_at': session[5].isoformat() if session[5] else None
    }
    
    print(f"✅ 세션: {session_info['session_id']}")
    print(f"   초기 자본: ${session_info['initial_capital']:,.2f}")
    print(f"   현재 자본: ${session_info['current_capital']:,.2f}")
    print(f"   가용 현금: ${session_info['available_cash']:,.2f}")
    print(f"   상태: {session_info['status']}")
    
    # 2. 모든 포지션 조회
    print("\n📋 포지션 조회...")
    cursor.execute("""
        SELECT 
            id,
            symbol,
            action,
            quantity,
            entry_price,
            exit_price,
            entry_date,
            exit_date,
            pnl,
            pnl_pct,
            stop_loss_price,
            reason
        FROM shadow_trading_positions
        WHERE session_id = %s
        ORDER BY entry_date
    """, (SESSION_ID,))
    
    positions_raw = cursor.fetchall()
    
    positions = []
    for p in positions_raw:
        is_open = p[7] is None  # exit_date가 None이면 open
        positions.append({
            'id': p[0],
            'symbol': p[1],
            'action': p[2],
            'quantity': int(p[3]),
            'entry_price': float(p[4]),
            'exit_price': float(p[5]) if p[5] else None,
            'entry_date': p[6].isoformat() if p[6] else None,
            'exit_date': p[7].isoformat() if p[7] else None,
            'pnl': float(p[8]) if p[8] else 0.0,
            'pnl_pct': float(p[9]) if p[9] else 0.0,
            'stop_loss_price': float(p[10]) if p[10] else None,
            'reason': p[11],
            'status': 'open' if is_open else 'closed'
        })
    
    print(f"✅ 포지션 개수: {len(positions)}개")
    
    # 3. 포지션 상세 출력
    print("\n📌 포지션 상세:")
    for i, pos in enumerate(positions, 1):
        status_emoji = "🟢" if pos['status'] == 'open' else "🔴"
        print(f"\n{i}. {status_emoji} {pos['symbol']} ({pos['action'].upper()})")
        print(f"   수량: {pos['quantity']}주")
        print(f"   진입가: ${pos['entry_price']:.2f}")
        if pos['exit_price']:
            print(f"   청산가: ${pos['exit_price']:.2f}")
        print(f"   P&L: ${pos['pnl']:+.2f} ({pos['pnl_pct']:+.2f}%)")
        print(f"   상태: {pos['status']}")
        if pos['entry_date']:
            print(f"   진입: {pos['entry_date']}")
        if pos['exit_date']:
            print(f"   청산: {pos['exit_date']}")
    
    cursor.close()
    conn.close()
    
    return {
        'session': session_info,
        'positions': positions,
        'collected_at': datetime.utcnow().isoformat()
    }


def calculate_metrics(data):
    """성과 지표 계산"""
    print("\n" + "="*60)
    print("성과 지표 계산")
    print("="*60)
    
    positions = data['positions']
    session = data['session']
    
    # 진입 시간 기준 정렬
    open_positions = [p for p in positions if p['status'] == 'open']
    closed_positions = [p for p in positions if p['status'] == 'closed']
    
    print(f"\n📊 포지션 상태:")
    print(f"   오픈: {len(open_positions)}개")
    print(f"   청산: {len(closed_positions)}개")
    
    # Win Rate (청산된 포지션 기준)
    if closed_positions:
        wins = [p for p in closed_positions if p['pnl'] > 0]
        losses = [p for p in closed_positions if p['pnl'] < 0]
        win_rate = len(wins) / len(closed_positions)
        
        # Profit Factor
        total_profit = sum(p['pnl'] for p in wins)
        total_loss = abs(sum(p['pnl'] for p in losses))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Average P&L
        avg_pnl = sum(p['pnl'] for p in closed_positions) / len(closed_positions)
    else:
        win_rate = 0
        profit_factor = 0
        avg_pnl = 0
        wins = []
        losses = []
    
    # Unrealized P&L (오픈 포지션)
    unrealized_pnl = sum(p['pnl'] for p in open_positions)
    
    # Total P&L
    realized_pnl = sum(p['pnl'] for p in closed_positions)
    total_pnl = realized_pnl + unrealized_pnl
    
    # ROI
    initial_capital = session['initial_capital']
    roi_pct = (total_pnl / initial_capital) * 100
    
    metrics = {
        'total_trades': len(positions),
        'open_trades': len(open_positions),
        'closed_trades': len(closed_positions),
        'winning_trades': len(wins),
        'losing_trades': len(losses),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_pnl': avg_pnl,
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl,
        'total_pnl': total_pnl,
        'roi_pct': roi_pct
    }
    
    # 출력
    print(f"\n✅ 핵심 지표:")
    print(f"   총 거래: {metrics['total_trades']}건")
    print(f"   청산 거래: {metrics['closed_trades']}건")
    print(f"   오픈 포지션: {metrics['open_trades']}건")
    
    if closed_positions:
        print(f"\n📈 청산 거래 성과:")
        print(f"   Win Rate: {metrics['win_rate']*100:.1f}%")
        print(f"   승리: {metrics['winning_trades']}건")
        print(f"   손실: {metrics['losing_trades']}건")
        print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"   평균 P&L: ${metrics['avg_pnl']:,.2f}")
    
    print(f"\n💰 손익:")
    print(f"   실현 손익: ${metrics['realized_pnl']:+,.2f}")
    print(f"   미실현 손익: ${metrics['unrealized_pnl']:+,.2f}")
    print(f"   총 손익: ${metrics['total_pnl']:+,.2f}")
    print(f"   ROI: {metrics['roi_pct']:+.2f}%")
    
    return metrics


def save_to_json(data, metrics, filename='week1_data.json'):
    """데이터를 JSON 파일로 저장"""
    output = {
        'data': data,
        'metrics': metrics
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=decimal_to_float)
    
    print(f"\n💾 데이터 저장: {filename}")


if __name__ == "__main__":
    try:
        # 데이터 수집
        data = collect_trading_data()
        
        if data:
            # 지표 계산
            metrics = calculate_metrics(data)
            
            # JSON 저장
            save_to_json(data, metrics)
            
            print("\n" + "="*60)
            print("✅ 데이터 수집 완료")
            print("="*60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
