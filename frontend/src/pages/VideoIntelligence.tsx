import React from 'react';

export const VideoIntelligence: React.FC = () => {
    return (
        <div className="space-y-6 p-6">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                Video Market Intelligence
            </h1>
            <p className="text-muted-foreground text-gray-500">
                Real-time Thinking Layer & Signal Mapping (Powered by Streamlit)
            </p>

            {/* Embed Streamlit Dashboard */}
            <div className="h-[calc(100vh-200px)] min-h-[800px] border border-gray-200 dark:border-gray-800 rounded-xl shadow-sm overflow-hidden bg-white dark:bg-gray-950">
                <iframe
                    src="http://localhost:8501"
                    className="w-full h-full border-0"
                    title="Streamlit Intelligence Dashboard"
                />
            </div>
        </div>
    );
};
