/**
 * War Room Page - AI 투자위원회 토론실
 * 
 * 여러 티커의 AI Agents 실시간 토론을 시각화
 */

import React from 'react';
import WarRoomList from '../components/war-room/WarRoomList';

const WarRoomPage: React.FC = () => {
    return (
        <div className="war-room-page">
            <div className="page-header" style={{
                textAlign: 'center',
                padding: '40px 20px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                marginBottom: '32px',
                borderRadius: '0 0 32px 32px',
                boxShadow: '0 10px 40px rgba(102, 126, 234, 0.3)',
                position: 'relative',
                overflow: 'hidden'
            }}>
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'url(/C:/Users/a/.gemini/antigravity/brain/ebfd4060-7097-4c3b-9596-8df013d8df38/war_room_hero_1765900477167.png)',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    opacity: 0.15,
                    zIndex: 0
                }} />
                <div style={{ position: 'relative', zIndex: 1 }}>
                    <h1 style={{
                        margin: '0 0 12px 0',
                        fontSize: '42px',
                        fontWeight: '900',
                        textShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
                    }}>
                        🎭 AI War Room
                    </h1>
                    <p style={{
                        margin: 0,
                        fontSize: '18px',
                        opacity: 0.95,
                        fontWeight: '600',
                        textShadow: '0 2px 10px rgba(0, 0, 0, 0.2)'
                    }}>
                        AI 투자 위원회 실시간 토론 - 5개 에이전트의 집단 지성
                    </p>
                </div>
            </div>

            <WarRoomList />
        </div>
    );
};

export default WarRoomPage;
