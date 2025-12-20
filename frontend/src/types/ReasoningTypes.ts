export interface ReasoningStep {
    step_number: number;
    premise: string;
    inference: string;
    conclusion: string;
    confidence: number;
    related_files?: string[];
}

export interface Contradiction {
    factor_a: string;
    factor_b: string;
    description: string;
    severity: "low" | "medium" | "high" | "critical";
    resolution_strategy: string;
}

export interface MarketThesis {
    ticker: string;
    direction: "BULLISH" | "BEARISH" | "NEUTRAL" | "UNCERTAIN";
    time_horizon: "SCALPING" | "DAY" | "SWING" | "LONG_TERM";

    summary: string;
    bull_case: string;
    bear_case: string;

    reasoning_trace: ReasoningStep[];
    contradictions: Contradiction[];

    key_risks: string[];
    catalysts: string[];

    final_confidence_score: number;
    generated_at: string;

    // Optional advanced analysis fields
    macro_warning?: string;
    macro_contradictions_count?: number;
    skeptic_challenge?: string;
    skeptic_recommendation?: string;
}

export interface AnalyzeRequest {
    ticker: string;
    news_context: string;
    technical_summary: {
        rsi?: number | string;
        macd?: string;
        ma_status?: string;
        price_action?: string;
    };
    use_mock?: boolean;
    enable_macro_check?: boolean;  // Optional: 매크로 정합성 체크
    enable_skeptic?: boolean;       // Optional: 반박논리추가
}
