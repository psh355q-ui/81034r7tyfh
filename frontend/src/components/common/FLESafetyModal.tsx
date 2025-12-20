import React from 'react';
import './FLESafetyModal.css';

interface FLESafetyModalProps {
    fle: number;
    peak_fle: number;
    drawdown_pct: number;
    message: string;
    onClose: () => void;
    onPause: () => void;
}

const FLESafetyModal: React.FC<FLESafetyModalProps> = ({
    fle,
    peak_fle,
    drawdown_pct,
    message,
    onClose,
    onPause
}) => {
    const formatCurrency = (value: number): string => {
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW',
            maximumFractionDigits: 0
        }).format(value);
    };

    return (
        <div className="fle-safety-modal-overlay" onClick={onClose}>
            <div className="fle-safety-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <span className="warning-icon">🛑</span>
                    <h2>투자 현황 점검 시간입니다</h2>
                </div>

                <div className="modal-body">
                    <div className="fle-display">
                        <p className="fle-label">지금 전부 매도하면 손에 남는 돈</p>
                        <p className="fle-amount">{formatCurrency(fle)}</p>
                    </div>

                    <div className="drawdown-info">
                        <p className="drawdown-label">최고점 대비</p>
                        <p className="drawdown-amount">
                            {formatCurrency(peak_fle - fle)} 하락 ({(drawdown_pct * 100).toFixed(1)}%)
                        </p>
                    </div>

                    <div className="safety-message">
                        <div className="message-icon">💡</div>
                        <div className="message-content">
                            <p>{message}</p>
                            <p className="sub-message">
                                오늘은 여기서 멈추고 내일 다시 보는 것도 좋습니다.
                            </p>
                            <p className="quote">
                                잠시 쉬어가는 것도 전략의 일부입니다.
                            </p>
                        </div>
                    </div>

                    <div className="reminder-box">
                        <p className="reminder-title">기억하세요</p>
                        <ul className="reminder-list">
                            <li>시장은 언제나 다시 기회를 줍니다</li>
                            <li>당신의 건강이 수익률보다 중요합니다</li>
                            <li>하루 쉬었다고 기회가 사라지지 않습니다</li>
                        </ul>
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="btn btn-pause" onClick={onPause}>
                        오늘은 여기까지 (일시 중지)
                    </button>
                    <button className="btn btn-continue" onClick={onClose}>
                        계속 진행하기
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FLESafetyModal;
