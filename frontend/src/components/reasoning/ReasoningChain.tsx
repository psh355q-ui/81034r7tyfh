
import React from 'react';
import { ReasoningStep } from '../../types/ReasoningTypes';

interface Props {
    steps: ReasoningStep[];
}

const ReasoningChain: React.FC<Props> = ({ steps }) => {
    // Defensive check: handle undefined or empty steps
    if (!steps || steps.length === 0) {
        return (
            <div className="mt-8 text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                <p className="text-gray-500">No reasoning trace available</p>
            </div>
        );
    }

    return (
        <div className="mt-8">
            <h3 className="text-xl font-bold text-gray-800 mb-4">🧠 Chain of Thought Trace</h3>
            <div className="space-y-4">
                {steps.map((step) => (
                    <div key={step.step_number} className="relative flex items-start">
                        {/* Connecting Line */}
                        {step.step_number !== steps.length && (
                            <div className="absolute left-6 top-10 bottom-0 w-0.5 bg-gray-200" style={{ height: 'calc(100% + 1rem)' }}></div>
                        )}

                        {/* Step Number Bubble */}
                        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-lg border-4 border-white shadow-sm z-10">
                            {step.step_number}
                        </div>

                        {/* Content Card */}
                        <div className="ml-4 flex-grow bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Premise (Fact)</span>
                                    <p className="text-sm text-gray-800 mt-1">{step.premise}</p>
                                </div>
                                <div className="border-l border-gray-100 pl-4">
                                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Inference (Logic)</span>
                                    <p className="text-sm text-blue-800 mt-1">{step.inference}</p>
                                </div>
                                <div className="border-l border-gray-100 pl-4">
                                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Conclusion</span>
                                    <p className="text-sm text-purple-800 mt-1 font-medium">{step.conclusion}</p>
                                </div>
                            </div>
                            <div className="mt-2 text-right">
                                <span className="text-xs text-gray-400">Confidence: {(step.confidence * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ReasoningChain;
