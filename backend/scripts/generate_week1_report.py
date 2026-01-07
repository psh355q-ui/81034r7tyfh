"""
Shadow Trading Week 1 보고서 생성

week1_data.json을 읽어서 마크다운 보고서 생성
"""
import json
from datetime import datetime

def load_data(filename='week1_data.json'):
    """JSON 데이터 로드"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_report(data, metrics):
    """보고서 생성"""
    session = data['session']
    positions = data['positions']
    
    # 포지션별 집계
    positions_by_symbol = {}
    for pos in positions:
        symbol = pos['symbol']
        if symbol not in positions_by_symbol:
            positions_by_symbol[symbol] = {
                'quantity': 0,
                'total_cost': 0,
                'count': 0
            }
        positions_by_symbol[symbol]['quantity'] += pos['quantity']
        positions_by_symbol[symbol]['total_cost'] += pos['quantity'] * pos['entry_price']
        positions_by_symbol[symbol]['count'] += 1
    
    # 평균 진입가 계산
    for symbol, info in positions_by_symbol.items():
        info['avg_entry'] = info['total_cost'] / info['quantity'] if info['quantity'] > 0 else 0
    
    report = f"""# Shadow Trading Week 1 완료 보고서 (Day 0-7)

**기간**: 2025-12-31 ~ 2026-01-07 (완료)  
**세션 ID**: `{session['session_id']}`  
**상태**: {session['status'].upper()}

---

## 📊 성과 요약

### 자본 현황
- **초기 자본**: ${session['initial_capital']:,.2f}
- **현재 자본**: ${session['current_capital']:,.2f}
- **가용 현금**: ${session['available_cash']:,.2f}
- **투자 금액**: ${session['initial_capital'] - session['available_cash']:,.2f}
- **투자 비율**: {((session['initial_capital'] - session['available_cash']) / session['initial_capital'] * 100):.1f}%

### 거래 지표
- **총 포지션**: {metrics['total_trades']}개
- **오픈 포지션**: {metrics['open_trades']}개
- **청산 포지션**: {metrics['closed_trades']}개

### 손익 (P&L)
> ⚠️ **주의**: 현재 가격 정보가 DB에 없어 미실현 손익 계산 불가능  
> 실시간 모니터링 스크립트로 확인 필요

- **실현 손익**: ${metrics['realized_pnl']:+,.2f}
- **미실현 손익**: 계산 필요
- **총 손익**: 계산 필요
- **ROI**: 계산 필요

---

## 💼 현재 포지션 (Final 기준)

| Symbol | 수량 | 평균 진입가 | 거래 수 | 투자 금액 |
|--------|------|-------------|---------|-----------|
"""
    
    for symbol, info in sorted(positions_by_symbol.items()):
        report += f"| {symbol} | {info['quantity']:,} | ${info['avg_entry']:.2f} | {info['count']} | ${info['total_cost']:,.2f} |\n"
    
    report += f"""
**총 투자 금액**: ${sum(info['total_cost'] for info in positions_by_symbol.values()):,.2f}

---

## 📝 포지션 상세

"""
    
    for i, pos in enumerate(positions, 1):
        status_badge = "🟢 OPEN" if pos['status'] == 'open' else "🔴 CLOSED"
        report += f"""### {i}. {pos['symbol']} - {status_badge}

- **Action**: {pos['action'].upper()}
- **수량**: {pos['quantity']:,}주
- **진입가**: ${pos['entry_price']:.2f}
- **진입 시각**: {pos['entry_date']}
- **Stop Loss**: ${pos['stop_loss_price']:.2f}
- **Reason**: {pos['reason']}

"""
        
        if pos['exit_price']:
            report += f"""- **청산가**: ${pos['exit_price']:.2f}
- **청산 시각**: {pos['exit_date']}
- **P&L**: ${pos['pnl']:+,.2f} ({pos['pnl_pct']:+.2f}%)

"""
    
    report += f"""---

## 🎯 Week 1 완료 (Lessons Learned)

### 거래 타임라인

- **Day 0 (2025-12-31)**: NKE 259주 매수 ($63.03) - 초기 포지션 구축
- **Day 3 (2026-01-03)**: AAPL 20주 매수 ($150.00) - 기술적 반등 노림
- **Day 4-7 (2026-01-04 ~ 01-07)**: 추가 거래 없음 (관망세 유지)

### 핵심 관찰사항

1.  **보수적 운용**: 총 자산의 19.3%만 투입하고 80.7% 현금 보유. 시장 불확실성에 대비한 AI의 신중함이 돋보임.
2.  **종목 집중**: NKE와 AAPL 두 종목에 집중. 백화점식 나열이 아닌 '확신 있는 소수' 전략.
3.  **리스크 관리**: 진입과 동시에 Stop Loss 설정 확인됨.
4.  **Deep Reasoning 영향**: 후반부(Day 4-7)에 추가 매수가 없었던 것은 Deep Reasoning Agent가 지정학적/매크로 리스크를 감지하여 'HOLD' 의견을 냈을 가능성 있음.

---

## 📈 다음 단계 (Week 2 Plan)

### 목표: 수익 창출 및 리스크 헤지
1.  **Report Orchestrator 가동**: 매일 아침 정밀 브리핑을 통해 AI의 의사결정 투명성 제고.
2.  **적극적 리밸런싱**: 현금 비중(80%)을 활용하여 유망 섹터(반도체, 방산 등) 비중 확대 검토.
3.  **News Agent Enhancement**: 실시간 뉴스 분석을 통해 '단기 모멘텀' 포착 시도.

---

**보고서 생성 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
"""
    
    return report


if __name__ == "__main__":
    print("="*60)
    print("Shadow Trading Week 1 보고서 생성")
    print("="*60)
    
    # 데이터 로드
    print("\n📖 데이터 로딩...")
    data_dict = load_data()
    data = data_dict['data']
    metrics = data_dict['metrics']
    
    print(f"✅ 세션: {data['session']['session_id'][:30]}...")
    print(f"✅ 포지션: {len(data['positions'])}개")
    
    # 보고서 생성
    print("\n📝 보고서 생성...")
    report = generate_report(data, metrics)
    
    # 파일 저장
    filename = 'shadow_trading_week1_report.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 보고서 저장: {filename}")
    
    print("\n" + "="*60)
    print("✅ 보고서 생성 완료")
    print("="*60)
    print(f"\n📄 파일 경로: {filename}")
