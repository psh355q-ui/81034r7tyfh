import React, { useEffect, useRef, useState } from 'react';
import { Card } from '../common/Card';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { getGNNGraph } from '../../services/api';

interface Node {
    id: string;
    group: string;
    value?: number; // Size/Importance
}

interface Link {
    source: string;
    target: string;
    value: number; // Weight
}

interface GraphData {
    nodes: Node[];
    links: Link[];
}

interface GNNGraphProps {
    ticker?: string;
    width?: number;
    height?: number;
}

export const GNNGraph: React.FC<GNNGraphProps> = ({ ticker, width = 600, height = 400 }) => {
    const [data, setData] = useState<GraphData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);

    // Fetch Graph Data
    useEffect(() => {
        const fetchGraph = async () => {
            setLoading(true);
            try {
                // In real app: fetch from /api/shadow/graph?ticker={ticker}
                // Mocking for now as per plan
                await new Promise(r => setTimeout(r, 800));

                // Mock Data Generator centered on ticker
                const center = ticker || 'NVDA';
                const related = ['AMD', 'INTC', 'TSM', 'MSFT', 'GOOGL'];
                const nodes = [
                    { id: center, group: 'Target', value: 20 },
                    ...related.map(r => ({ id: r, group: 'Related', value: 10 + Math.random() * 10 }))
                ];
                const links = related.map(r => ({
                    source: center,
                    target: r,
                    value: Math.random()
                }));

                // Add some cross links
                links.push({ source: 'AMD', target: 'INTC', value: 0.8 });
                links.push({ source: 'MSFT', target: 'GOOGL', value: 0.6 });

                setData({ nodes, links });
                setError(null);
            } catch (err) {
                setError('Failed to load knowledge graph');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchGraph();
    }, [ticker]);

    // Simple Force-Directed Layout Simulation (Simplified)
    // For a robust implementation, usage of d3-force is recommended, 
    // but here we use a simple circular layout with the target in center for stability and lightness.

    if (loading) return <div className="h-64 flex items-center justify-center"><LoadingSpinner /></div>;
    if (error) return <div className="h-64 flex items-center justify-center text-red-500">{error}</div>;
    if (!data) return null;

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 3;

    // Calculate Positions
    const nodePositions = new Map<string, { x: number, y: number }>();

    // Center node
    const targetNode = data.nodes.find(n => n.group === 'Target') || data.nodes[0];
    if (targetNode) {
        nodePositions.set(targetNode.id, { x: centerX, y: centerY });
    }

    // Related nodes in a circle
    const relatedNodes = data.nodes.filter(n => n.id !== targetNode?.id);
    const angleStep = (2 * Math.PI) / relatedNodes.length;

    relatedNodes.forEach((node, index) => {
        const angle = index * angleStep - Math.PI / 2; // Start from top
        nodePositions.set(node.id, {
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle)
        });
    });

    return (
        <Card title={`Reference Graph: ${ticker || 'Market'}`}>
            <div className="relative bg-slate-900 rounded-lg overflow-hidden border border-slate-700" style={{ height }}>
                <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
                    <defs>
                        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
                        </marker>
                    </defs>

                    {/* Links */}
                    {data.links.map((link, i) => {
                        const start = nodePositions.get(link.source);
                        const end = nodePositions.get(link.target);
                        if (!start || !end) return null;

                        return (
                            <g key={i}>
                                <line
                                    x1={start.x} y1={start.y}
                                    x2={end.x} y2={end.y}
                                    stroke="#475569"
                                    strokeWidth={1 + link.value * 2}
                                    strokeOpacity={0.6}
                                />
                                {/* Relationship Score Label */}
                                <text
                                    x={(start.x + end.x) / 2}
                                    y={(start.y + end.y) / 2}
                                    fill="#94a3b8"
                                    fontSize="10"
                                    textAnchor="middle"
                                    dy="-5"
                                >
                                    {(link.value).toFixed(2)}
                                </text>
                            </g>
                        );
                    })}

                    {/* Nodes */}
                    {data.nodes.map((node) => {
                        const pos = nodePositions.get(node.id);
                        if (!pos) return null;
                        const isHovered = hoveredNode === node.id;
                        const isTarget = node.group === 'Target';

                        return (
                            <g
                                key={node.id}
                                transform={`translate(${pos.x},${pos.y})`}
                                onMouseEnter={() => setHoveredNode(node.id)}
                                onMouseLeave={() => setHoveredNode(null)}
                                style={{ cursor: 'pointer' }}
                            >
                                <circle
                                    r={isTarget ? 30 : 20}
                                    fill={isTarget ? '#3b82f6' : '#64748b'}
                                    stroke={isHovered ? '#fff' : 'none'}
                                    strokeWidth={2}
                                    className="transition-all duration-300 ease-in-out"
                                />
                                <text
                                    dy=".35em"
                                    textAnchor="middle"
                                    fill="white"
                                    fontWeight="bold"
                                    fontSize={isTarget ? 14 : 12}
                                    pointerEvents="none"
                                >
                                    {node.id}
                                </text>

                                {/* Tooltip on hover */}
                                {isHovered && (
                                    <g transform="translate(0, -40)">
                                        <rect x="-60" y="-20" width="120" height="40" rx="4" fill="rgba(0,0,0,0.8)" />
                                        <text y="0" textAnchor="middle" fill="white" fontSize="11">
                                            Influence: {(node.value || 0).toFixed(1)}
                                        </text>
                                        <text y="12" textAnchor="middle" fill="#cbd5e1" fontSize="10">
                                            {node.group} Group
                                        </text>
                                    </g>
                                )}
                            </g>
                        );
                    })}
                </svg>

                <div className="absolute bottom-4 right-4 text-xs text-slate-500 bg-slate-800/80 px-2 py-1 rounded">
                    Current GNN Layout v2.0
                </div>
            </div>
        </Card>
    );
};
