"""
Phase 10: Signal Backtest API Router
백테스트 실행 및 결과 조회 API 엔드포인트

엔드포인트:
- POST /api/backtest/run - 새 백테스트 실행
- GET /api/backtest/results - 백테스트 결과 목록
- GET /api/backtest/results/{id} - 특정 결과 상세
- POST /api/backtest/optimize - 파라미터 최적화
- GET /api/backtest/compare - 결과 비교
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid
import asyncio
from pathlib import Path

# Import backtest engine
from backend.backtesting.signal_backtest_engine import (
    SignalBacktestEngine,
    NewsAnalysis,
    BacktestResult
)

router = APIRouter(prefix="/backtest", tags=["backtest"])

# 결과 저장소 (실제로는 DB 사용)
RESULTS_DIR = Path("./backtest_results")
try:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Docker 환경에서 권한 문제 발생 시 /tmp 사용
    RESULTS_DIR = Path("/tmp/backtest_results")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class BacktestConfig(BaseModel):
    """백테스트 설정"""
    start_date: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")
    initial_capital: float = Field(default=100000.0, description="초기 자본금")
    
    # 거래 비용
    commission_rate: float = Field(default=0.00015, description="수수료율 (0.00015 = 0.015%)")
    slippage_bps: float = Field(default=1.0, description="슬리피지 (basis points)")
    
    # 포지션 관리
    max_holding_days: int = Field(default=5, description="최대 보유 기간")
    stop_loss_pct: float = Field(default=2.0, description="손절 퍼센트")
    take_profit_pct: float = Field(default=5.0, description="익절 퍼센트")
    
    # 시그널 생성 파라미터
    base_position_size: float = Field(default=0.05, description="기본 포지션 크기 (포트폴리오 비율)")
    max_position_size: float = Field(default=0.10, description="최대 포지션 크기")
    min_sentiment_threshold: float = Field(default=0.7, description="최소 감정 임계값")
    min_relevance_score: int = Field(default=70, description="최소 관련성 점수")
    
    # 검증 파라미터
    min_confidence: float = Field(default=0.7, description="최소 신뢰도")
    max_daily_trades: int = Field(default=10, description="일일 최대 거래 횟수")
    daily_loss_limit_pct: float = Field(default=2.0, description="일일 손실 제한 (%)")


class BacktestRunRequest(BaseModel):
    """백테스트 실행 요청"""
    config: BacktestConfig
    name: str = Field(default="Backtest", description="백테스트 이름")
    description: str = Field(default="", description="설명")
    use_real_data: bool = Field(default=True, description="실제 DB 데이터 사용 여부")


class BacktestRunResponse(BaseModel):
    """백테스트 실행 응답"""
    id: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED
    message: str
    created_at: str


class BacktestResultSummary(BaseModel):
    """백테스트 결과 요약"""
    id: str
    name: str
    status: str
    created_at: str
    
    # 주요 지표
    total_return_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None


class OptimizationRequest(BaseModel):
    """파라미터 최적화 요청"""
    base_config: BacktestConfig
    
    # 최적화할 파라미터 범위
    param_ranges: Dict[str, List[float]] = Field(
        default={
            "min_sentiment_threshold": [0.6, 0.7, 0.8],
            "stop_loss_pct": [1.5, 2.0, 2.5, 3.0],
            "take_profit_pct": [3.0, 5.0, 7.0, 10.0]
        },
        description="최적화할 파라미터와 테스트할 값들"
    )
    
    optimization_metric: str = Field(
        default="sharpe_ratio",
        description="최적화 기준 지표"
    )


class OptimizationResult(BaseModel):
    """최적화 결과"""
    best_params: Dict[str, float]
    best_score: float
    optimization_metric: str
    all_results: List[Dict[str, Any]]
    total_combinations: int
    completed_at: str


class ComparisonRequest(BaseModel):
    """백테스트 결과 비교 요청"""
    backtest_ids: List[str] = Field(..., description="비교할 백테스트 ID 목록")


class ComparisonResult(BaseModel):
    """백테스트 비교 결과"""
    backtests: List[Dict[str, Any]]
    best_by_metric: Dict[str, str]  # metric -> backtest_id
    analysis: Dict[str, Any]


# =============================================================================
# IN-MEMORY STATE (실제로는 Redis 또는 DB 사용)
# =============================================================================

backtest_jobs: Dict[str, Dict] = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_news_analyses_from_db() -> List[NewsAnalysis]:
    """DB에서 뉴스 분석 데이터 로드 (실제 구현 필요)"""
    # TODO: 실제 DB 쿼리 구현
    # 현재는 빈 목록 반환
    return []


def load_price_data_from_db(
    tickers: List[str],
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Dict[str, float]]:
    """DB에서 가격 데이터 로드 (실제 구현 필요)"""
    try:
        from backend.trading import kis_client
        from backend.trading import overseas_stock
        import time
        
        result = {}
        for ticker in tickers:
            ticker_data = {}
            
            # Domestic Stock (6 digits)
            if ticker.isdigit() and len(ticker) == 6:
                daily_prices = kis_client.inquire_daily_price(ticker, period="D")
                for dp in daily_prices:
                    date_str = dp.get("stck_bsop_date")
                    if date_str:
                        try:
                            dt_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                            dt_obj = datetime.strptime(dt_str, "%Y-%m-%d")
                            if start_date <= dt_obj <= end_date:
                                ticker_data[dt_str] = float(dp.get("stck_clpr", 0))
                        except Exception:
                            continue

            # Overseas Stock (Alphabet)
            else:
                # Try major exchanges
                for exc in ["NASD", "NYSE", "AMEX"]:
                    daily_prices = overseas_stock.get_daily_price(exc, ticker.upper(), period="D")
                    if daily_prices:
                        break
                
                for dp in daily_prices:
                    # Overseas fields: xymd (date), clos (close price)
                    date_str = dp.get("xymd")
                    if date_str:
                        try:
                            dt_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                            dt_obj = datetime.strptime(dt_str, "%Y-%m-%d")
                            if start_date <= dt_obj <= end_date:
                                # ovrs_nmix_prpr or clos check
                                price = float(dp.get("clos", dp.get("ovrs_nmix_prpr", 0)))
                                ticker_data[dt_str] = price
                        except Exception:
                            continue
            
            if ticker_data:
                result[ticker] = ticker_data
                print(f"  -> {ticker}: {len(ticker_data)} days loaded")
            else:
                print(f"  -> {ticker}: No data found")
            
            time.sleep(0.1)
            
        print(f"✅ Loaded real price data for {len(result)} tickers")
        return result
        
    except Exception as e:
        print(f"⚠️ Failed to load real price data: {e}")
        return {}


def generate_sample_data():
    """테스트용 샘플 데이터 생성"""
    import random
    random.seed(42)
    
    # 30일 샘플 뉴스 분석 데이터
    analyses = []
    tickers = ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL", "AMZN", "META"]
    
    start_date = datetime(2024, 1, 1)
    
    for i in range(20):  # 20개의 뉴스 분석
        day_offset = random.randint(0, 29)
        news_date = start_date + timedelta(days=day_offset)
        
        ticker = random.choice(tickers)
        
        # 랜덤 감정
        sentiment_value = random.gauss(0, 0.5)
        if sentiment_value > 0.3:
            sentiment = "POSITIVE"
        elif sentiment_value < -0.3:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        
        analyses.append(NewsAnalysis(
            id=f"analysis_{i:03d}",
            article_id=f"article_{i:03d}",
            crawled_at=news_date + timedelta(hours=random.randint(9, 16)),
            analyzed_at=news_date + timedelta(hours=random.randint(9, 16), minutes=10),
            sentiment_overall=sentiment,
            sentiment_score=abs(sentiment_value),
            sentiment_confidence=random.uniform(0.6, 0.95),
            urgency=random.choice(["IMMEDIATE", "SHORT_TERM", "LONG_TERM"]),
            impact_magnitude=random.uniform(0.3, 0.9),
            risk_category=random.choice(["LOW", "MEDIUM", "HIGH"]),
            key_facts=[f"Key fact {j}" for j in range(3)],
            related_tickers=[{
                "ticker_symbol": ticker,
                "relevance_score": random.randint(70, 95)
            }]
        ))
    
    # 30일 가격 데이터
    price_data = {}
    base_prices = {
        "AAPL": 180.0, "TSLA": 250.0, "MSFT": 350.0,
        "NVDA": 500.0, "GOOGL": 140.0, "AMZN": 150.0, "META": 350.0
    }
    
    for day in range(30):
        date = start_date + timedelta(days=day)
        date_str = date.strftime("%Y-%m-%d")
        
        price_data[date_str] = {}
        
        for ticker, base_price in base_prices.items():
            noise = random.gauss(0, 0.015)  # 1.5% 표준편차
            trend = 0.001 * day  # 일일 0.1% 상승
            price = base_price * (1 + trend + noise)
            price_data[date_str][ticker] = round(price, 2)
    
    return analyses, price_data, start_date, start_date + timedelta(days=29)


async def run_backtest_async(job_id: str, config: BacktestConfig, use_real_data: bool):
    """비동기 백테스트 실행"""
    
    try:
        backtest_jobs[job_id]["status"] = "RUNNING"
        backtest_jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # 데이터 로드
        if use_real_data:
            analyses = load_news_analyses_from_db()
            start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(config.end_date, "%Y-%m-%d")
            
            # 티커 추출
            tickers = set()
            for analysis in analyses:
                for ticker_info in analysis.related_tickers:
                    tickers.add(ticker_info.get("ticker_symbol"))
            
            price_data = load_price_data_from_db(list(tickers), start_date, end_date)
        else:
            # 샘플 데이터 사용
            analyses, price_data, start_date, end_date = generate_sample_data()
        
        # 백테스트 엔진 생성
        engine = SignalBacktestEngine(
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            slippage_bps=config.slippage_bps,
            max_holding_days=config.max_holding_days,
            stop_loss_pct=config.stop_loss_pct,
            take_profit_pct=config.take_profit_pct
        )
        
        # 시그널 생성기 설정
        engine.signal_generator.base_position_size = config.base_position_size
        engine.signal_generator.max_position_size = config.max_position_size
        engine.signal_generator.min_sentiment_threshold = config.min_sentiment_threshold
        engine.signal_generator.min_relevance_score = config.min_relevance_score
        
        # 검증기 설정
        engine.signal_validator.min_confidence = config.min_confidence
        engine.signal_validator.max_daily_trades = config.max_daily_trades
        engine.signal_validator.daily_loss_limit_pct = config.daily_loss_limit_pct
        
        # 백테스트 실행
        result = await engine.run(analyses, price_data, start_date, end_date)
        
        # 결과 저장
        result_dict = {
            "id": job_id,
            "name": backtest_jobs[job_id]["name"],
            "description": backtest_jobs[job_id]["description"],
            "config": config.dict(),
            "result": {
                "start_date": result.start_date,
                "end_date": result.end_date,
                "initial_capital": result.initial_capital,
                "final_value": result.final_value,
                "total_return_pct": result.total_return_pct,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown_pct": result.max_drawdown_pct,
                "win_rate": result.win_rate,
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "avg_win_pct": result.avg_win_pct,
                "avg_loss_pct": result.avg_loss_pct,
                "profit_factor": result.profit_factor,
                "total_signals": result.total_signals,
                "executed_signals": result.executed_signals,
                "rejected_signals": result.rejected_signals,
                "best_day_pct": result.best_day_pct,
                "worst_day_pct": result.worst_day_pct,
                "avg_daily_return_pct": result.avg_daily_return_pct,
                "parameters": result.parameters,
                "daily_values": result.daily_values,
                "trades": result.trades
            },
            "created_at": backtest_jobs[job_id]["created_at"],
            "completed_at": datetime.now().isoformat()
        }
        
        # 파일로 저장
        result_file = RESULTS_DIR / f"{job_id}.json"
        with open(result_file, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        # 상태 업데이트
        backtest_jobs[job_id]["status"] = "COMPLETED"
        backtest_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        backtest_jobs[job_id]["result_file"] = str(result_file)
        
    except Exception as e:
        backtest_jobs[job_id]["status"] = "FAILED"
        backtest_jobs[job_id]["error"] = str(e)
        backtest_jobs[job_id]["completed_at"] = datetime.now().isoformat()


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/run", response_model=BacktestRunResponse)
async def run_backtest(
    request: BacktestRunRequest,
    background_tasks: BackgroundTasks
):
    """
    새 백테스트 실행
    
    - 비동기로 실행되며, job_id를 반환
    - GET /results/{id}로 결과 확인
    """
    
    job_id = str(uuid.uuid4())
    
    # 작업 등록
    backtest_jobs[job_id] = {
        "id": job_id,
        "name": request.name,
        "description": request.description,
        "status": "PENDING",
        "config": request.config.dict(),
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "result_file": None,
        "error": None
    }
    
    # 백그라운드에서 실행
    background_tasks.add_task(
        run_backtest_async,
        job_id,
        request.config,
        request.use_real_data
    )
    
    return BacktestRunResponse(
        id=job_id,
        status="PENDING",
        message="Backtest job created. Check results with GET /results/{id}",
        created_at=backtest_jobs[job_id]["created_at"]
    )


@router.get("/results", response_model=List[BacktestResultSummary])
async def get_backtest_results():
    """
    모든 백테스트 결과 목록 조회
    """
    
    results = []
    
    for job_id, job in backtest_jobs.items():
        summary = BacktestResultSummary(
            id=job_id,
            name=job["name"],
            status=job["status"],
            created_at=job["created_at"]
        )
        
        # 완료된 경우 지표 추가
        if job["status"] == "COMPLETED" and job["result_file"]:
            try:
                with open(job["result_file"], "r") as f:
                    result_data = json.load(f)
                    result = result_data["result"]
                    
                    summary.total_return_pct = result["total_return_pct"]
                    summary.sharpe_ratio = result["sharpe_ratio"]
                    summary.max_drawdown_pct = result["max_drawdown_pct"]
                    summary.win_rate = result["win_rate"]
                    summary.total_trades = result["total_trades"]
            except Exception:
                pass
        
        results.append(summary)
    
    # 최신순 정렬
    results.sort(key=lambda x: x.created_at, reverse=True)
    
    return results


@router.get("/results/{job_id}")
async def get_backtest_result(job_id: str):
    """
    특정 백테스트 결과 상세 조회
    """
    
    if job_id not in backtest_jobs:
        raise HTTPException(status_code=404, detail=f"Backtest {job_id} not found")
    
    job = backtest_jobs[job_id]
    
    # 아직 완료되지 않은 경우
    if job["status"] in ["PENDING", "RUNNING"]:
        return {
            "id": job_id,
            "status": job["status"],
            "message": "Backtest is still running. Please wait.",
            "created_at": job["created_at"],
            "started_at": job.get("started_at")
        }
    
    # 실패한 경우
    if job["status"] == "FAILED":
        return {
            "id": job_id,
            "status": "FAILED",
            "error": job.get("error", "Unknown error"),
            "created_at": job["created_at"],
            "completed_at": job.get("completed_at")
        }
    
    # 완료된 경우 - 파일에서 결과 로드
    if job["result_file"]:
        try:
            with open(job["result_file"], "r") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load result: {str(e)}")
    
    raise HTTPException(status_code=500, detail="Result file not found")


@router.post("/optimize", response_model=OptimizationResult)
async def optimize_parameters(request: OptimizationRequest):
    """
    파라미터 최적화 실행
    
    Grid Search 방식으로 최적 파라미터 조합 탐색
    """
    
    from itertools import product
    
    # 파라미터 조합 생성
    param_names = list(request.param_ranges.keys())
    param_values = list(request.param_ranges.values())
    combinations = list(product(*param_values))
    
    results = []
    best_score = float('-inf') if request.optimization_metric != "max_drawdown_pct" else float('inf')
    best_params = {}
    
    # 각 조합에 대해 백테스트 실행
    for combo in combinations:
        # 설정 복사
        config = request.base_config.copy()
        
        # 파라미터 적용
        params = dict(zip(param_names, combo))
        for key, value in params.items():
            setattr(config, key, value)
        
        # 백테스트 실행 (샘플 데이터)
        analyses, price_data, start_date, end_date = generate_sample_data()
        
        engine = SignalBacktestEngine(
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            slippage_bps=config.slippage_bps,
            max_holding_days=config.max_holding_days,
            stop_loss_pct=config.stop_loss_pct,
            take_profit_pct=config.take_profit_pct
        )
        
        engine.signal_generator.base_position_size = config.base_position_size
        engine.signal_generator.max_position_size = config.max_position_size
        engine.signal_generator.min_sentiment_threshold = config.min_sentiment_threshold
        engine.signal_validator.min_confidence = config.min_confidence
        
        result = await engine.run(analyses, price_data, start_date, end_date)
        
        # 점수 추출
        score = getattr(result, request.optimization_metric, 0)
        
        # 결과 기록
        results.append({
            "params": params,
            "score": score,
            "total_return_pct": result.total_return_pct,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown_pct": result.max_drawdown_pct,
            "win_rate": result.win_rate,
            "total_trades": result.total_trades
        })
        
        # 최적값 업데이트
        if request.optimization_metric == "max_drawdown_pct":
            # Drawdown은 낮을수록 좋음 (덜 음수)
            if score > best_score:
                best_score = score
                best_params = params
        else:
            # 나머지는 높을수록 좋음
            if score > best_score:
                best_score = score
                best_params = params
    
    return OptimizationResult(
        best_params=best_params,
        best_score=best_score,
        optimization_metric=request.optimization_metric,
        all_results=results,
        total_combinations=len(combinations),
        completed_at=datetime.now().isoformat()
    )


@router.post("/compare", response_model=ComparisonResult)
async def compare_backtests(request: ComparisonRequest):
    """
    여러 백테스트 결과 비교
    """
    
    backtests = []
    
    for job_id in request.backtest_ids:
        if job_id not in backtest_jobs:
            continue
        
        job = backtest_jobs[job_id]
        
        if job["status"] != "COMPLETED" or not job["result_file"]:
            continue
        
        try:
            with open(job["result_file"], "r") as f:
                result_data = json.load(f)
                backtests.append({
                    "id": job_id,
                    "name": job["name"],
                    "result": result_data["result"],
                    "config": result_data["config"]
                })
        except Exception:
            continue
    
    if not backtests:
        raise HTTPException(status_code=404, detail="No valid backtests found")
    
    # 각 지표별 최고 백테스트 찾기
    metrics = ["total_return_pct", "sharpe_ratio", "win_rate", "profit_factor"]
    best_by_metric = {}
    
    for metric in metrics:
        best_id = max(backtests, key=lambda x: x["result"].get(metric, 0))["id"]
        best_by_metric[metric] = best_id
    
    # Max Drawdown은 낮을수록 좋음
    best_drawdown = max(backtests, key=lambda x: x["result"].get("max_drawdown_pct", -100))
    best_by_metric["max_drawdown_pct"] = best_drawdown["id"]
    
    # 종합 분석
    analysis = {
        "average_return": sum(b["result"]["total_return_pct"] for b in backtests) / len(backtests),
        "average_sharpe": sum(b["result"]["sharpe_ratio"] for b in backtests) / len(backtests),
        "average_win_rate": sum(b["result"]["win_rate"] for b in backtests) / len(backtests),
        "total_backtests": len(backtests),
        "recommendation": ""
    }
    
    # 추천
    best_overall = max(
        backtests,
        key=lambda x: (
            x["result"]["sharpe_ratio"] * 0.4 +
            x["result"]["total_return_pct"] * 0.3 +
            (1 + x["result"]["max_drawdown_pct"] / 100) * 0.3  # Drawdown은 음수이므로 조정
        )
    )
    analysis["recommendation"] = f"Best overall: {best_overall['name']} (ID: {best_overall['id']})"
    
    return ComparisonResult(
        backtests=[{
            "id": b["id"],
            "name": b["name"],
            "total_return_pct": b["result"]["total_return_pct"],
            "sharpe_ratio": b["result"]["sharpe_ratio"],
            "max_drawdown_pct": b["result"]["max_drawdown_pct"],
            "win_rate": b["result"]["win_rate"],
            "total_trades": b["result"]["total_trades"],
            "profit_factor": b["result"]["profit_factor"]
        } for b in backtests],
        best_by_metric=best_by_metric,
        analysis=analysis
    )


@router.delete("/results/{job_id}")
async def delete_backtest_result(job_id: str):
    """
    백테스트 결과 삭제
    """
    
    if job_id not in backtest_jobs:
        raise HTTPException(status_code=404, detail=f"Backtest {job_id} not found")
    
    job = backtest_jobs[job_id]
    
    # 파일 삭제
    if job.get("result_file"):
        try:
            Path(job["result_file"]).unlink(missing_ok=True)
        except Exception:
            pass
    
    # 메모리에서 삭제
    del backtest_jobs[job_id]
    
    return {"message": f"Backtest {job_id} deleted successfully"}


@router.get("/status/{job_id}")
async def get_backtest_status(job_id: str):
    """
    백테스트 작업 상태 확인
    """
    
    if job_id not in backtest_jobs:
        raise HTTPException(status_code=404, detail=f"Backtest {job_id} not found")
    
    job = backtest_jobs[job_id]
    
    return {
        "id": job_id,
        "status": job["status"],
        "created_at": job["created_at"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "error": job.get("error")
    }


# =============================================================================
# CONSENSUS BACKTEST ENDPOINTS
# =============================================================================

class ConsensusBacktestRequest(BaseModel):
    """Consensus 백테스트 요청"""
    tickers: List[str] = Field(default=["NVDA", "AMD", "AAPL"], description="테스트할 종목들")
    start_date: str = Field(default="2024-01-01", description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(default="2024-06-01", description="종료 날짜 (YYYY-MM-DD)")
    initial_capital: float = Field(default=100000.0, description="초기 자본금")
    consensus_threshold: float = Field(default=0.6, description="Consensus 승인 임계값 (0.6 = 60%)")
    use_mock_consensus: bool = Field(default=True, description="Mock Consensus 사용 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["NVDA", "AMD", "AAPL"],
                "start_date": "2024-01-01",
                "end_date": "2024-06-01",
                "initial_capital": 100000.0,
                "consensus_threshold": 0.6,
                "use_mock_consensus": True
            }
        }


consensus_backtest_jobs: Dict[str, Dict] = {}


async def run_consensus_backtest_async(job_id: str, request: ConsensusBacktestRequest):
    """비동기 Consensus 백테스트 실행"""
    
    try:
        consensus_backtest_jobs[job_id]["status"] = "RUNNING"
        consensus_backtest_jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        from backend.backtesting.consensus_backtest import ConsensusBacktest
        
        backtest = ConsensusBacktest(
            initial_capital=request.initial_capital,
            consensus_threshold=request.consensus_threshold,
            use_mock_consensus=request.use_mock_consensus
        )
        
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        result = backtest.run(
            tickers=request.tickers,
            start_date=start_date,
            end_date=end_date
        )
        
        # 결과 저장
        result_dict = {
            "id": job_id,
            "type": "consensus",
            "request": request.dict(),
            "result": result,
            "created_at": consensus_backtest_jobs[job_id]["created_at"],
            "completed_at": datetime.now().isoformat()
        }
        
        result_file = RESULTS_DIR / f"consensus_{job_id}.json"
        with open(result_file, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        consensus_backtest_jobs[job_id]["status"] = "COMPLETED"
        consensus_backtest_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        consensus_backtest_jobs[job_id]["result_file"] = str(result_file)
        consensus_backtest_jobs[job_id]["result"] = result
        
    except Exception as e:
        consensus_backtest_jobs[job_id]["status"] = "FAILED"
        consensus_backtest_jobs[job_id]["error"] = str(e)
        consensus_backtest_jobs[job_id]["completed_at"] = datetime.now().isoformat()


@router.post("/consensus")
async def run_consensus_backtest(
    request: ConsensusBacktestRequest,
    background_tasks: BackgroundTasks
):
    """
    Consensus 전략 백테스트 실행
    
    3-AI Consensus + DCA 전략을 히스토리컬 데이터로 테스트
    """
    
    job_id = str(uuid.uuid4())
    
    consensus_backtest_jobs[job_id] = {
        "id": job_id,
        "type": "consensus",
        "status": "PENDING",
        "request": request.dict(),
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "result_file": None,
        "result": None,
        "error": None
    }
    
    background_tasks.add_task(
        run_consensus_backtest_async,
        job_id,
        request
    )
    
    return {
        "id": job_id,
        "type": "consensus",
        "status": "PENDING",
        "message": "Consensus backtest job created. Check results with GET /backtest/consensus/{id}",
        "created_at": consensus_backtest_jobs[job_id]["created_at"]
    }


@router.get("/consensus/list")
async def list_consensus_backtests():
    """모든 Consensus 백테스트 결과 목록"""
    
    results = []
    for job_id, job in consensus_backtest_jobs.items():
        summary = {
            "id": job_id,
            "status": job["status"],
            "created_at": job["created_at"],
            "tickers": job["request"]["tickers"]
        }
        
        if job["status"] == "COMPLETED" and job.get("result"):
            result = job["result"]
            summary["total_return_pct"] = result.get("total_return_pct")
            summary["sharpe_ratio"] = result.get("sharpe_ratio")
            summary["win_rate"] = result.get("win_rate")
        
        results.append(summary)
    
    results.sort(key=lambda x: x["created_at"], reverse=True)
    return results


@router.get("/consensus/{job_id}")
async def get_consensus_backtest_result(job_id: str):
    """특정 Consensus 백테스트 결과 상세"""
    
    if job_id not in consensus_backtest_jobs:
        raise HTTPException(status_code=404, detail=f"Consensus backtest {job_id} not found")
    
    job = consensus_backtest_jobs[job_id]
    
    if job["status"] in ["PENDING", "RUNNING"]:
        return {
            "id": job_id,
            "status": job["status"],
            "message": "Backtest is still running. Please wait.",
            "created_at": job["created_at"],
            "started_at": job.get("started_at")
        }
    
    if job["status"] == "FAILED":
        return {
            "id": job_id,
            "status": "FAILED",
            "error": job.get("error", "Unknown error"),
            "created_at": job["created_at"],
            "completed_at": job.get("completed_at")
        }
    
    if job["result_file"]:
        try:
            with open(job["result_file"], "r") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load result: {str(e)}")
    
    return job


@router.get("/consensus/quick-test")
async def quick_consensus_test():
    """
    빠른 Consensus 백테스트 (동기 실행)
    
    샘플 데이터로 즉시 결과 반환
    """
    
    try:
        from backend.backtesting.consensus_backtest import ConsensusBacktest
        
        backtest = ConsensusBacktest(
            initial_capital=100000.0,
            consensus_threshold=0.6,
            use_mock_consensus=True
        )
        
        result = backtest.run(
            tickers=["NVDA", "AMD"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 2, 1)  # 1개월
        )
        
        return {
            "status": "COMPLETED",
            "type": "quick_test",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

