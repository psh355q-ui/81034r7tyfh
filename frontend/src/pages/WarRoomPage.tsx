/**
 * War Room Page - AI 투자위원회 토론실
 * 
 * 📊 Data Sources:
 *   - API: GET /api/war-room-mvp/history (AI Debate 세션)
 *   - API: POST /api/war-room-mvp/deliberate (새 토론 시작)
 *
 * 📝 Notes:
 *   - Dashboard와 동일한 Tailwind 스타일 적용
 *   - MVP 3+1 Agents: Trader (35%), Risk (35%), Analyst (30%), PM (+1)
 */

import React from 'react';
import WarRoomList from '../components/war-room/WarRoomList';

const WarRoomPage: React.FC = () => {
    return (
        <div className="space-y-6 p-6">
            {/* Header - Dashboard 스타일과 동일 */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">🎭 AI War Room</h1>
                <p className="text-gray-600 mt-1">AI 투자 위원회 실시간 토론 - MVP 3+1 에이전트 시스템</p>
            </div>

            {/* War Room List Component */}
            <WarRoomList />
        </div>
    );
};

export default WarRoomPage;
