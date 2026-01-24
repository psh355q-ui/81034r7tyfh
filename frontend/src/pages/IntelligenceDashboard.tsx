/**
 * Intelligence Dashboard
 *
 * Market Intelligence v2.0 Dashboard
 *
 * Features:
 * - Contrarian Signal analysis (crowding detection)
 * - Enhanced News Pipeline processing
 * - Chart generation visualization
 * - Component statistics
 *
 * Author: AI Trading System Team
 * Date: 2026-01-19
 * Reference: docs/planning/260118_market_intelligence_roadmap.md
 */

import React, { useState } from "react";
import {
    Card,
    Row,
    Col,
    Button,
    Input,
    Select,
    Typography,
    Divider,
    Tag,
    Space,
    Alert,
    Statistic,
    Progress,
    Steps,
    Badge,
    Spin,
    Empty
} from "antd";
import {
    LineChartOutlined,
    BarChartOutlined,
    BulbOutlined,
    ThunderboltOutlined,
    EyeOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    DownloadOutlined,
    RocketOutlined,
    SafetyCertificateOutlined,
    GlobalOutlined,
    ReadOutlined
} from "@ant-design/icons";
import axios from "axios";

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

// Helper function to convert backend file path to full URL
const getChartUrl = (filePath: string): string => {
    if (!filePath) return "";

    // Normalize path: replace backslashes with forward slashes
    // filePath can be: "tmp\charts\filename.png" or "/static/charts/filename.png"
    let normalizedPath = filePath.replace(/\\/g, '/');

    // Ensure path starts with /
    if (!normalizedPath.startsWith('/')) {
        normalizedPath = '/' + normalizedPath;
    }

    // Backend static files are served at http://localhost:8001
    return `http://localhost:8001${normalizedPath}`;
};


// ============================================================================
// Types
// ============================================================================

interface ContrarySignalData {
    symbol: string;
    crowding_level: string;
    flow_z_score: number;
    sentiment_extreme: boolean;
    sentiment_direction: string;
    position_skew: number;
    contrarian_action: string;
    reasoning: string;
    confidence: number;
}

interface PipelineResult {
    success: boolean;
    final_insight: string | null;
    contrarian_view: {
        bull_case: string | null;
        bear_case: string | null;
        key_risks: string[];
        confidence: number;
    } | null;
    invalidation_conditions: string[];
    failure_triggers: string[];
    processing_time_ms: number;
    stages: Record<string, {
        success: boolean;
        data: Record<string, unknown>;
        reasoning: string;
    }>;
}

interface ChartResult {
    success: boolean;
    chart_type: string;
    file_path: string;
    metadata: Record<string, unknown>;
}

interface Statistics {
    contrary_signal: {
        total_analyses: number;
        extreme_signals: number;
        extreme_signal_rate: number;
    };
    pipeline: {
        total_processed: number;
        early_terminations: number;
        component_failures: Record<string, number>;
    };
    chart_generator: {
        total_charts: number;
        theme_bubble_count: number;
        timeline_count: number;
        sector_performance_count: number;
    };
}

// ============================================================================
// Helper Functions
// ============================================================================


// ============================================================================
// Components
// ============================================================================

function ContrarianSignalPanel() {
    const [symbol, setSymbol] = useState("NVDA");
    const [days, setDays] = useState(30);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ContrarySignalData | null>(null);

    const analyzeSignal = async () => {
        setLoading(true);
        try {
            const response = await axios.post("/api/intelligence/contrary-signal", {
                symbol,
                days,
            });
            setResult(response.data);
        } catch (error: any) {
            console.error("Contrary signal analysis error:", error);
        } finally {
            setLoading(false);
        }
    };

    const getCrowdingPercent = (level: string) => {
        switch (level) {
            case "LOW": return 25;
            case "MEDIUM": return 50;
            case "HIGH": return 75;
            case "EXTREME": return 100;
            default: return 0;
        }
    };

    const getCrowdingColor = (level: string) => {
        switch (level) {
            case "LOW": return "#52c41a";
            case "MEDIUM": return "#1890ff";
            case "HIGH": return "#faad14";
            case "EXTREME": return "#f5222d";
            default: return "#d9d9d9";
        }
    };

    return (
        <Card
            title={
                <Space>
                    <ThunderboltOutlined style={{ color: "#faad14" }} />
                    <span style={{ fontWeight: 600 }}>Contrarian Signal</span>
                </Space>
            }
            bordered={false}
            style={{ height: "100%", boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}
        >
            <Space direction="vertical" style={{ width: "100%" }} size="middle">
                <Space.Compact style={{ width: "100%" }}>
                    <Input
                        placeholder="Symbol"
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                        style={{ width: "40%" }}
                        onPressEnter={analyzeSignal}
                    />
                    <Select value={days} onChange={setDays} style={{ width: "30%" }}>
                        <Option value={7}>7 Days</Option>
                        <Option value={14}>14 Days</Option>
                        <Option value={30}>30 Days</Option>
                        <Option value={90}>90 Days</Option>
                    </Select>
                    <Button type="primary" onClick={analyzeSignal} loading={loading} style={{ width: "30%" }}>
                        Scan
                    </Button>
                </Space.Compact>

                {result ? (
                    <div style={{ marginTop: 16 }}>
                        <div style={{ textAlign: "center", marginBottom: 24 }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>CROWDING LEVEL</Text>
                            <Progress
                                type="dashboard"
                                percent={getCrowdingPercent(result.crowding_level)}
                                format={() => result.crowding_level}
                                strokeColor={getCrowdingColor(result.crowding_level)}
                                width={120}
                            />
                        </div>

                        <Card
                            size="small"
                            style={{
                                textAlign: "center",
                                background: result.contrarian_action === "EXIT" ? "#fff1f0" :
                                    result.contrarian_action === "ACCUMULATE" ? "#f6ffed" : "#f0f5ff",
                                borderColor: result.contrarian_action === "EXIT" ? "#ffa39e" :
                                    result.contrarian_action === "ACCUMULATE" ? "#b7eb8f" : "#adc6ff"
                            }}
                        >
                            <Text type="secondary" style={{ fontSize: 12 }}>RECOMMENDED ACTION</Text>
                            <Title level={4} style={{ margin: "4px 0 0 0" }}>
                                {result.contrarian_action}
                            </Title>
                        </Card>

                        <Divider style={{ margin: "16px 0" }} />

                        <Row gutter={[8, 8]}>
                            <Col span={12}>
                                <Statistic
                                    title="Flow Z-Score"
                                    value={result.flow_z_score}
                                    precision={2}
                                    valueStyle={{ color: Math.abs(result.flow_z_score) > 2 ? "#cf1322" : "#3f8600" }}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title="Position Skew"
                                    value={result.position_skew}
                                    precision={2}
                                    suffix={result.position_skew > 0 ? "Long" : "Short"}
                                />
                            </Col>
                        </Row>

                        <Alert
                            message="Analysis Reasoning"
                            description={result.reasoning}
                            type="info"
                            style={{ marginTop: 16, fontSize: 13 }}
                        />
                    </div>
                ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Enter a symbol to scan for crowding" />
                )}
            </Space>
        </Card>
    );
}

function PipelinePanel() {
    const [title, setTitle] = useState("AI Infrastructure Stocks Rally on Government Spending");
    const [content, setContent] = useState("Major AI infrastructure companies saw significant gains...");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PipelineResult | null>(null);

    const processArticle = async () => {
        setLoading(true);
        try {
            const response = await axios.post("/api/intelligence/pipeline/process", {
                title,
                content,
                source: "Reuters",
                published_at: new Date().toISOString(),
            });
            setResult(response.data);
        } catch (error: any) {
            console.error("Pipeline processing error:", error);
        } finally {
            setLoading(false);
        }
    };

    const getStageStatus = (stages: PipelineResult["stages"], stageName: string) => {
        if (!stages) return "wait";
        if (!stages[stageName]) return "wait";
        return stages[stageName].success ? "finish" : "error";
    };

    return (
        <Card
            title={
                <Space>
                    <RocketOutlined style={{ color: "#722ed1" }} />
                    <span style={{ fontWeight: 600 }}>Enhanced News Pipeline</span>
                </Space>
            }
            bordered={false}
            style={{ height: "100%", boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}
        >
            {result ? (
                <Row gutter={[24, 24]}>
                    <Col span={24}>
                        <Steps
                            size="small"
                            items={[
                                { title: "Filter", status: getStageStatus(result.stages, "filter"), icon: <ReadOutlined /> },
                                { title: "Narrative", status: getStageStatus(result.stages, "narrative"), icon: <BulbOutlined /> },
                                { title: "Fact Check", status: getStageStatus(result.stages, "fact_check"), icon: <SafetyCertificateOutlined /> },
                                { title: "Market", status: getStageStatus(result.stages, "market_confirm"), icon: <LineChartOutlined /> },
                                { title: "Horizon", status: getStageStatus(result.stages, "horizon"), icon: <ClockCircleOutlined /> },
                                { title: "Policy", status: getStageStatus(result.stages, "policy"), icon: <GlobalOutlined /> },
                            ]}
                        />
                    </Col>
                    <Col span={16}>
                        <Card title="Final Insight" size="small" type="inner" extra={<Tag color="purple">{(result.processing_time_ms / 1000).toFixed(2)}s</Tag>}>
                            <Paragraph style={{ fontSize: 15 }}>{result.final_insight}</Paragraph>
                        </Card>
                        {result.contrarian_view && (
                            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                                <Col span={12}>
                                    <Alert
                                        message="Bull Case"
                                        description={result.contrarian_view.bull_case || "N/A"}
                                        type="success"
                                        showIcon
                                    />
                                </Col>
                                <Col span={12}>
                                    <Alert
                                        message="Bear Case"
                                        description={result.contrarian_view.bear_case || "N/A"}
                                        type="error"
                                        showIcon
                                    />
                                </Col>
                            </Row>
                        )}
                    </Col>
                    <Col span={8}>
                        <Card size="small" title="Pipeline Diagnostics" style={{ height: "100%" }}>
                            <Space direction="vertical" style={{ width: "100%" }}>
                                <div>
                                    <Text type="secondary">Invalidation Conditions</Text>
                                    <Paragraph style={{ marginTop: 4 }}>
                                        {result.invalidation_conditions.length > 0 ?
                                            result.invalidation_conditions.map((c, i) => <Tag color="warning" key={i} style={{ marginBottom: 4 }}>{c}</Tag>) :
                                            <Tag color="success">None</Tag>
                                        }
                                    </Paragraph>
                                </div>
                                <Divider style={{ margin: "8px 0" }} />
                                <div>
                                    <Text type="secondary">Key Risks</Text>
                                    <Paragraph style={{ marginTop: 4 }}>
                                        {result.contrarian_view?.key_risks.map((r, i) => <Tag color="red" key={i} style={{ marginBottom: 4 }}>{r}</Tag>)}
                                    </Paragraph>
                                </div>
                            </Space>
                        </Card>
                    </Col>
                </Row>
            ) : (
                <div style={{ textAlign: "center", padding: "40px 0" }}>
                    <Input.TextArea
                        rows={2}
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Enter news headline..."
                        style={{ marginBottom: 16, fontSize: 16, fontWeight: 500 }}
                    />
                    <Button type="primary" size="large" icon={<RocketOutlined />} onClick={processArticle} loading={loading}>
                        Process Pipeline
                    </Button>
                </div>
            )}
        </Card>
    );
}

function ChartPanel() {
    const [chartType, setChartType] = useState("THEME_BUBBLE");
    const [title, setTitle] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ChartResult | null>(null);

    const generateChart = async () => {
        setLoading(true);
        try {
            let requestBody: any = {
                chart_type: chartType,
                title: title,
                themes: ["AI", "Defense", "Bio", "Chip"], // Default sample data
                metrics: { x: [0.8, 0.6, 0.4, 0.2], y: [0.7, 0.5, 0.3, 0.9], size: [100, 80, 60, 40] }
            };

            const response = await axios.post("/api/intelligence/chart/generate", requestBody);
            setResult(response.data);
        } catch (error: any) {
            console.error("Chart generation error:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card
            title={
                <Space>
                    <BarChartOutlined style={{ color: "#1890ff" }} />
                    <span style={{ fontWeight: 600 }}>Chart Generator</span>
                </Space>
            }
            bordered={false}
            style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}
        >
            <Row gutter={[24, 24]}>
                <Col span={6}>
                    <Space direction="vertical" style={{ width: "100%" }}>
                        <Text strong>Configuration</Text>
                        <Select value={chartType} onChange={setChartType} style={{ width: "100%" }}>
                            <Option value="THEME_BUBBLE">Theme Bubble</Option>
                            <Option value="GEOPOLITICAL_TIMELINE">Timeline</Option>
                            <Option value="SECTOR_PERFORMANCE">Sector Bar</Option>
                        </Select>
                        <Input
                            placeholder="Chart Title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                        <Button
                            type="primary"
                            icon={<BarChartOutlined />}
                            onClick={generateChart}
                            loading={loading}
                            block
                        >
                            Generate Chart
                        </Button>
                    </Space>
                </Col>
                <Col span={18} style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 300, background: "#fafafa", borderRadius: 8 }}>
                    {loading ? (
                        <Spin size="large" tip="Generating..." />
                    ) : result && result.success ? (
                        <div style={{ textAlign: "center", width: "100%" }}>
                            <img
                                src={getChartUrl(result.file_path)}
                                alt="Generated Chart"
                                style={{ maxWidth: "100%", maxHeight: 400, boxShadow: "0 4px 12px rgba(0,0,0,0.1)", borderRadius: 8 }}
                            />
                            <div style={{ marginTop: 16 }}>
                                <Button href={getChartUrl(result.file_path)} download icon={<DownloadOutlined />}>
                                    Download Image
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <Empty description="No chart generated" />
                    )}
                </Col>
            </Row>
        </Card>
    );
}

function StatisticsPanel({ statistics }: { statistics: Statistics | null }) {
    if (!statistics) return <Spin />;

    return (
        <Row gutter={[16, 16]}>
            <Col span={8}>
                <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}>
                    <Statistic
                        title="Market Crises Detected"
                        value={statistics.contrary_signal.extreme_signal_rate * 100}
                        precision={1}
                        valueStyle={{ color: '#cf1322' }}
                        prefix={<ThunderboltOutlined />}
                        suffix="%"
                    />
                    <Progress
                        percent={statistics.contrary_signal.extreme_signal_rate * 100}
                        showInfo={false}
                        strokeColor="#cf1322"
                        size="small"
                        status="active"
                    />
                    <div style={{ marginTop: 8, fontSize: 12, color: "#8c8c8c" }}>
                        {statistics.contrary_signal.total_analyses} Total Scans
                    </div>
                </Card>
            </Col>
            <Col span={8}>
                <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}>
                    <Statistic
                        title="Pipeline Efficiency"
                        value={100 - ((statistics.pipeline.component_failures.narrative || 0) / (statistics.pipeline.total_processed || 1) * 100)}
                        precision={1}
                        valueStyle={{ color: '#3f8600' }}
                        prefix={<CheckCircleOutlined />}
                        suffix="%"
                    />
                    <Progress
                        percent={100 - ((statistics.pipeline.component_failures.narrative || 0) / (statistics.pipeline.total_processed || 1) * 100)}
                        showInfo={false}
                        strokeColor="#3f8600"
                        size="small"
                        status="active"
                    />
                    <div style={{ marginTop: 8, fontSize: 12, color: "#8c8c8c" }}>
                        {statistics.pipeline.total_processed} Articles Processed
                    </div>
                </Card>
            </Col>
            <Col span={8}>
                <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}>
                    <Statistic
                        title="Charts Generated"
                        value={statistics.chart_generator.total_charts}
                        prefix={<BarChartOutlined />}
                        valueStyle={{ color: '#1890ff' }}
                    />
                    <Progress
                        percent={(statistics.chart_generator.total_charts % 100)}
                        showInfo={false}
                        strokeColor="#1890ff"
                        size="small"
                    />
                    <div style={{ marginTop: 8, fontSize: 12, color: "#8c8c8c" }}>
                        Active Visualization Engine
                    </div>
                </Card>
            </Col>
        </Row>
    );
}

// ============================================================================
// Main Page
// ============================================================================

export default function IntelligenceDashboard() {
    const [statistics, setStatistics] = useState<Statistics | null>(null);

    React.useEffect(() => {
        axios.get("/api/intelligence/statistics")
            .then(res => setStatistics(res.data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div style={{ padding: 24, background: "#f0f2f5", minHeight: "100vh" }}>
            <div style={{ marginBottom: 24 }}>
                <Title level={2} style={{ marginBottom: 8 }}>Market Intelligence Center</Title>
                <Text type="secondary">AI-Powered Market Crowding Detection & Enhanced News Analytics</Text>
            </div>

            <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <StatisticsPanel statistics={statistics} />

                <Row gutter={[24, 24]}>
                    <Col span={8} style={{ display: 'flex' }}>
                        <ContrarianSignalPanel />
                    </Col>
                    <Col span={16} style={{ display: 'flex' }}>
                        <PipelinePanel />
                    </Col>
                </Row>

                <ChartPanel />
            </Space>
        </div>
    );
}
