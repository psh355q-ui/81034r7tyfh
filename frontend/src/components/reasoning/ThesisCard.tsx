
import React from 'react';
import { MarketThesis } from '../../types/ReasoningTypes';

interface Props {
    thesis: MarketThesis;
}

const ThesisCard: React.FC<Props> = ({ thesis }) => {
    const isBullish = thesis.direction === 'BULLISH';
    const isBearish = thesis.direction === 'BEARISH';

    const cardColor = isBullish ? 'bg-green-50 border-green-200' :
        isBearish ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200';

    const textColor = isBullish ? 'text-green-800' :
        isBearish ? 'text-red-800' : 'text-gray-800';

    return (
        <div className={`border rounded-lg p-6 shadow-sm ${cardColor}`}>
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">{thesis.ticker} Analysis</h2>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mt-2 ${isBullish ? 'bg-green-200 text-green-800' : isBearish ? 'bg-red-200 text-red-800' : 'bg-gray-200 text-gray-800'}`}>
                        {thesis.direction} ({thesis.time_horizon})
                    </span>
                </div>
                <div className="text-right">
                    <div className="text-sm text-gray-500">Confidence</div>
                    <div className={`text-3xl font-bold ${textColor}`}>
                        {(thesis.final_confidence_score * 100).toFixed(0)}%
                    </div>
                </div>
            </div>

            <p className="text-gray-700 text-lg mb-6 leading-relaxed">
                {thesis.summary}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-4 rounded border border-gray-200">
                    <h3 className="font-bold text-green-700 mb-2">🐂 Bull Case</h3>
                    <p className="text-sm text-gray-600">{thesis.bull_case}</p>
                </div>
                <div className="bg-white p-4 rounded border border-gray-200">
                    <h3 className="font-bold text-red-700 mb-2">🐻 Bear Case</h3>
                    <p className="text-sm text-gray-600">{thesis.bear_case}</p>
                </div>
            </div>

            {(thesis.contradictions && thesis.contradictions.length > 0) && (
                <div className="mt-6 bg-yellow-50 border border-yellow-200 p-4 rounded">
                    <h3 className="font-bold text-yellow-800 mb-2">⚠️ Contradictions Detected</h3>
                    <ul className="list-disc pl-5 text-sm text-yellow-700">
                        {thesis.contradictions.map((c, idx) => (
                            <li key={idx}>
                                <strong>{c.factor_a} vs {c.factor_b}:</strong> {c.description}
                                <br /><span className="text-xs text-gray-500">Resolution: {c.resolution_strategy}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default ThesisCard;
