"""
Multi-Strategy Orchestration API Router

Phase 0, Task T0.5

FastAPI router implementation based on:
- backend/contracts/strategy_contracts.py (API contract)
- backend/api/schemas/strategy_schemas.py (Request/Response schemas)
- backend/database/repository_multi_strategy.py (Data access)

Endpoints:
- /api/v1/strategies/* - 전략 관리
- /api/v1/positions/ownership/* - 포지션 소유권
- /api/v1/conflicts/* - 충돌 검사 및 로그

Usage:
    # In backend/main.py
    from backend.api.strategy_router import strategy_router, ownership_router, conflict_router

    app.include_router(strategy_router, prefix="/api/v1/strategies", tags=["strategies"])
    app.include_router(ownership_router, prefix="/api/v1/positions/ownership", tags=["ownership"])
    app.include_router(conflict_router, prefix="/api/v1/conflicts", tags=["conflicts"])
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from backend.database.repository import get_sync_session
from backend.database.repository_multi_strategy import (
    StrategyRepository,
    PositionOwnershipRepository,
    ConflictLogRepository
)
from backend.database.models import PositionOwnership
from backend.api.schemas.strategy_schemas import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    PositionOwnershipCreate,
    PositionOwnershipResponse,
    PositionOwnershipWithStrategy,
    ConflictLogResponse,
    ConflictCheckRequest,
    ConflictCheckResponse,
    ConflictDetail,
    ConflictResolution,
    BulkStrategyActivateRequest,
    BulkOperationResponse
)
from backend.core.cache import get_cache
import hashlib
import json


# ====================================
# Dependency: Database Session
# ====================================

def get_db() -> Session:
    """
    Database session dependency

    FastAPI will automatically close the session after request
    """
    with get_sync_session() as session:
        yield session


# ====================================
# Strategy Management Router
# ====================================

strategy_router = APIRouter()


@strategy_router.get("/", response_model=List[StrategyResponse])
def list_strategies(
    active_only: bool = Query(False, description="활성화된 전략만 조회"),
    db: Session = Depends(get_db)
):
    """
    전략 목록 조회

    - **active_only**: True면 활성 전략만 반환
    - Returns: 우선순위 내림차순으로 정렬된 전략 목록
    """
    import json

    repo = StrategyRepository(db)

    if active_only:
        strategies = repo.get_active_strategies()
    else:
        strategies = repo.get_all()

    # Parse config_metadata if it's a JSON string (PostgreSQL JSONB serialization issue)
    response_items = []
    for strategy in strategies:
        config_meta = strategy.config_metadata
        if isinstance(config_meta, str):
            try:
                config_meta = json.loads(config_meta)
            except Exception:
                config_meta = None

        response_items.append(StrategyResponse(
            id=strategy.id,
            name=strategy.name,
            display_name=strategy.display_name,
            persona_type=strategy.persona_type,
            priority=strategy.priority,
            time_horizon=strategy.time_horizon,
            is_active=strategy.is_active,
            config_metadata=config_meta,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        ))

    return response_items


@strategy_router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db)
):
    """
    새 전략 생성

    - **name**: 전략 시스템명 (unique, 영문자/숫자/언더스코어)
    - **priority**: 0-1000 (높을수록 우선)
    - Returns: 생성된 전략
    - Raises: 409 Conflict (이름 중복)
    """
    repo = StrategyRepository(db)

    try:
        new_strategy = repo.create(
            name=strategy.name,
            display_name=strategy.display_name,
            persona_type=strategy.persona_type.value,
            priority=strategy.priority,
            time_horizon=strategy.time_horizon.value,
            is_active=strategy.is_active,
            config_metadata=strategy.config_metadata
        )
        db.commit()
        return new_strategy

    except IntegrityError as e:
        db.rollback()
        if "uk_strategies_name" in str(e) or "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Strategy with name '{strategy.name}' already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}"
        )


@strategy_router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    전략 상세 조회

    - **strategy_id**: 전략 UUID
    - Returns: 전략 정보
    - Raises: 404 Not Found
    """
    repo = StrategyRepository(db)
    strategy = repo.get_by_id(strategy_id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found"
        )

    return strategy


@strategy_router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(
    strategy_id: str,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """
    전략 수정

    - **strategy_id**: 전략 UUID
    - **strategy_update**: 수정할 필드 (partial update)
    - Returns: 수정된 전략
    - Raises: 404 Not Found
    - Note: config_metadata는 전체 교체 (merge 아님)
    """
    repo = StrategyRepository(db)

    # Build update dict (exclude None values)
    update_data = strategy_update.dict(exclude_none=True)

    # Convert Enum to string
    if "persona_type" in update_data:
        update_data["persona_type"] = update_data["persona_type"].value
    if "time_horizon" in update_data:
        update_data["time_horizon"] = update_data["time_horizon"].value

    updated_strategy = repo.update(strategy_id, **update_data)

    if not updated_strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found"
        )

    db.commit()
    return updated_strategy


@strategy_router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    전략 삭제

    - **strategy_id**: 전략 UUID
    - Returns: 204 No Content
    - Raises: 404 Not Found, 409 Conflict (소유권이 있으면 삭제 불가)

    주의: FK RESTRICT로 인해 position_ownership이 있으면 삭제 실패
    """
    repo = StrategyRepository(db)

    try:
        success = repo.delete(strategy_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )

        db.commit()
        return None  # 204 No Content

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete strategy with existing position ownerships. Release ownerships first."
        )


@strategy_router.post("/{strategy_id}/activate", response_model=StrategyResponse)
def activate_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    전략 활성화

    - **strategy_id**: 전략 UUID
    - Returns: 활성화된 전략
    - Raises: 404 Not Found
    """
    import json

    repo = StrategyRepository(db)

    success = repo.activate(strategy_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found"
        )

    db.commit()

    # Return updated strategy with parsed config_metadata
    strategy = repo.get_by_id(strategy_id)

    # Parse config_metadata if it's a JSON string
    config_meta = strategy.config_metadata
    if isinstance(config_meta, str):
        try:
            config_meta = json.loads(config_meta)
        except Exception:
            config_meta = None

    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        display_name=strategy.display_name,
        persona_type=strategy.persona_type,
        priority=strategy.priority,
        time_horizon=strategy.time_horizon,
        is_active=strategy.is_active,
        config_metadata=config_meta,
        created_at=strategy.created_at,
        updated_at=strategy.updated_at
    )


@strategy_router.post("/{strategy_id}/deactivate", response_model=StrategyResponse)
def deactivate_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    전략 비활성화

    - **strategy_id**: 전략 UUID
    - Returns: 비활성화된 전략
    - Raises: 404 Not Found

    Side Effect: 기존 소유권은 유지됨 (locked_until 만료 시 자동 해제)
    """
    import json

    repo = StrategyRepository(db)

    success = repo.deactivate(strategy_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found"
        )

    db.commit()

    # Return updated strategy with parsed config_metadata
    strategy = repo.get_by_id(strategy_id)

    # Parse config_metadata if it's a JSON string
    config_meta = strategy.config_metadata
    if isinstance(config_meta, str):
        try:
            config_meta = json.loads(config_meta)
        except Exception:
            config_meta = None

    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        display_name=strategy.display_name,
        persona_type=strategy.persona_type,
        priority=strategy.priority,
        time_horizon=strategy.time_horizon,
        is_active=strategy.is_active,
        config_metadata=config_meta,
        created_at=strategy.created_at,
        updated_at=strategy.updated_at
    )


@strategy_router.post("/bulk/activate", response_model=BulkOperationResponse)
def bulk_activate_strategies(
    request: BulkStrategyActivateRequest,
    db: Session = Depends(get_db)
):
    """
    전략 일괄 활성화/비활성화

    - **strategy_ids**: 전략 ID 목록
    - **is_active**: 활성화 여부
    - Returns: 성공/실패 건수 및 오류 목록
    """
    repo = StrategyRepository(db)

    success_count = 0
    failed_count = 0
    errors = []

    for strategy_id in request.strategy_ids:
        try:
            if request.is_active:
                success = repo.activate(strategy_id)
            else:
                success = repo.deactivate(strategy_id)

            if success:
                success_count += 1
            else:
                failed_count += 1
                errors.append(f"{strategy_id}: Not found")

        except Exception as e:
            failed_count += 1
            errors.append(f"{strategy_id}: {str(e)}")

    db.commit()

    return BulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        errors=errors
    )


# ====================================
# Position Ownership Router
# ====================================

ownership_router = APIRouter()


@ownership_router.get("/")
async def list_ownerships(
    ticker: Optional[str] = Query(None, description="종목 코드 필터"),
    strategy_id: Optional[str] = Query(None, description="전략 ID 필터"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1-100)"),
    db: Session = Depends(get_db)
):
    """
    포지션 소유권 목록 조회 (Phase 5, T5.2)

    **페이지네이션 파라미터**:
    - **page**: 페이지 번호 (1부터 시작, default=1)
    - **page_size**: 페이지당 항목 수 (1-100, default=20)

    **필터 파라미터**:
    - **ticker**: 종목 코드 필터 (optional)
    - **strategy_id**: 전략 ID 필터 (optional)

    **Returns**:
    - **total**: 전체 항목 수
    - **page**: 현재 페이지
    - **page_size**: 페이지 크기
    - **total_pages**: 전체 페이지 수
    - **items**: 소유권 목록 (strategy 정보 포함)
    
    **Caching**: 3s TTL for dashboard polling optimization
    """
    # Generate cache key
    cache_params = {
        'ticker': ticker,
        'strategy_id': strategy_id,
        'page': page,
        'page_size': page_size
    }
    cache_key_str = json.dumps(cache_params, sort_keys=True)
    cache_key = f"ownership:list:{hashlib.md5(cache_key_str.encode()).hexdigest()}"
    
    # Check cache
    cache = await get_cache()
    cached_data = await cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    repo = PositionOwnershipRepository(db)

    # Build base query with eager loading to prevent N+1 queries
    base_query = db.query(PositionOwnership).options(
        joinedload(PositionOwnership.strategy)
    )
    
    if ticker:
        # Filter by ticker
        query = base_query.filter(
            PositionOwnership.ticker == ticker.upper()
        )
    elif strategy_id:
        # Filter by strategy
        query = base_query.filter(
            PositionOwnership.strategy_id == strategy_id
        )
    else:
        # Get all
        query = base_query

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    ownerships = query.order_by(
        PositionOwnership.created_at.desc()
    ).offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # Convert to response models with parsed config_metadata
    items = []
    for o in ownerships:
        # Parse config_metadata if it's a JSON string
        strategy_data = None
        if o.strategy:
            config_meta = o.strategy.config_metadata
            if isinstance(config_meta, str):
                try:
                    config_meta = json.loads(config_meta)
                except Exception:
                    config_meta = None

            strategy_data = StrategyResponse(
                id=o.strategy.id,
                name=o.strategy.name,
                display_name=o.strategy.display_name,
                persona_type=o.strategy.persona_type,
                priority=o.strategy.priority,
                time_horizon=o.strategy.time_horizon,
                is_active=o.strategy.is_active,
                config_metadata=config_meta,
                created_at=o.strategy.created_at,
                updated_at=o.strategy.updated_at
            )

        items.append(PositionOwnershipWithStrategy(
            id=o.id,
            ticker=o.ticker,
            strategy_id=o.strategy_id,
            position_id=o.position_id,
            ownership_type=o.ownership_type,
            locked_until=o.locked_until,
            reasoning=o.reasoning,
            created_at=o.created_at,
            strategy=strategy_data
        ))

    response_data = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": [item.dict() for item in items]
    }

    # Cache for 3 seconds
    await cache.set(cache_key, response_data, ttl=3)

    return response_data


@ownership_router.get("/{ticker}/primary", response_model=PositionOwnershipResponse)
def get_primary_owner(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    종목의 primary 소유권 조회

    - **ticker**: 종목 코드
    - Returns: Primary 소유권
    - Raises: 404 Not Found (소유권 없으면)
    """
    repo = PositionOwnershipRepository(db)
    ownership = repo.get_primary_ownership(ticker.upper())

    if not ownership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No primary ownership found for ticker {ticker}"
        )

    return ownership


@ownership_router.post("/acquire", response_model=PositionOwnershipResponse, status_code=status.HTTP_201_CREATED)
def acquire_ownership(
    request: PositionOwnershipCreate,
    db: Session = Depends(get_db)
):
    """
    소유권 획득

    - **request**: PositionOwnershipCreate
    - Returns: 생성된 소유권
    - Raises: 409 Conflict (primary 소유권 중복)
    """
    repo = PositionOwnershipRepository(db)

    try:
        ownership = repo.create(
            strategy_id=request.strategy_id,
            ticker=request.ticker.upper(),
            ownership_type=request.ownership_type.value,
            position_id=request.position_id,
            locked_until=request.locked_until,
            reasoning=request.reasoning
        )
        db.commit()
        return ownership

    except IntegrityError as e:
        db.rollback()
        if "uk_ownership_primary_ticker" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Primary ownership for {request.ticker} already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}"
        )


@ownership_router.post("/transfer", response_model=PositionOwnershipResponse)
def transfer_ownership(
    ticker: str,
    to_strategy_id: str,
    reasoning: str,
    db: Session = Depends(get_db)
):
    """
    소유권 이전

    - **ticker**: 종목 코드
    - **to_strategy_id**: 새 소유 전략 ID
    - **reasoning**: 이전 이유
    - Returns: 새 소유권
    - Raises: 404 (기존 소유권 없음), 409 (잠금 충돌)
    """
    repo = PositionOwnershipRepository(db)

    # Get current primary ownership
    current_ownership = repo.get_primary_ownership(ticker.upper())

    if not current_ownership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ownership found for {ticker}"
        )

    # Check if locked
    if repo.is_ticker_locked(ticker.upper()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{ticker} is locked until {current_ownership.locked_until}"
        )

    # Transfer
    success = repo.transfer_ownership(
        ticker=ticker.upper(),
        from_strategy_id=current_ownership.strategy_id,
        to_strategy_id=to_strategy_id,
        reasoning=reasoning
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ownership transfer failed"
        )

    db.commit()

    # Return new ownership
    return repo.get_primary_ownership(ticker.upper())


@ownership_router.delete("/{ownership_id}", status_code=status.HTTP_204_NO_CONTENT)
def release_ownership(
    ownership_id: str,
    db: Session = Depends(get_db)
):
    """
    소유권 해제 (삭제)

    - **ownership_id**: 소유권 UUID
    - Returns: 204 No Content
    - Raises: 404 Not Found
    """
    repo = PositionOwnershipRepository(db)

    success = repo.delete(ownership_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ownership {ownership_id} not found"
        )

    db.commit()
    return None


# ====================================
# Conflict Management Router
# ====================================

conflict_router = APIRouter()


@conflict_router.post("/check", response_model=ConflictCheckResponse)
def check_conflict(
    request: ConflictCheckRequest,
    db: Session = Depends(get_db)
):
    """
    충돌 검사 (Dry Run)

    - **request**: ConflictCheckRequest (strategy_id, ticker, action, quantity)
    - Returns: ConflictCheckResponse (has_conflict, resolution, can_proceed, reasoning)

    충돌 검사 로직:
    1. 해당 종목의 primary 소유권 조회
    2. 소유권 없음 → ALLOWED
    3. 같은 전략 → ALLOWED
    4. 다른 전략 → 우선순위 비교
       - 요청 전략 우선순위 > 소유 전략 → PRIORITY_OVERRIDE (허용)
       - 요청 전략 우선순위 <= 소유 전략 → BLOCKED (차단)
    """
    ownership_repo = PositionOwnershipRepository(db)
    strategy_repo = StrategyRepository(db)

    # 요청 전략 조회
    requesting_strategy = strategy_repo.get_by_id(request.strategy_id)
    if not requesting_strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {request.strategy_id} not found"
        )

    # Primary 소유권 조회
    ownership = ownership_repo.get_primary_ownership(request.ticker)

    # 소유권 없음 → 충돌 없음
    if not ownership:
        return ConflictCheckResponse(
            has_conflict=False,
            resolution=ConflictResolution.ALLOWED,
            can_proceed=True,
            reasoning=f"No ownership exists for {request.ticker}. Order allowed."
        )

    # 같은 전략 → 충돌 없음
    if ownership.strategy_id == request.strategy_id:
        return ConflictCheckResponse(
            has_conflict=False,
            resolution=ConflictResolution.ALLOWED,
            can_proceed=True,
            reasoning=f"Same strategy owns {request.ticker}. Order allowed."
        )

    # 다른 전략 → 우선순위 비교
    owning_strategy = ownership.strategy

    # 잠금 확인
    is_locked = ownership_repo.is_ticker_locked(request.ticker)

    if requesting_strategy.priority > owning_strategy.priority:
        # 우선순위 높음 → Override 가능
        return ConflictCheckResponse(
            has_conflict=True,
            resolution=ConflictResolution.PRIORITY_OVERRIDE,
            can_proceed=True,
            conflict_detail=ConflictDetail(
                owning_strategy_id=owning_strategy.id,
                owning_strategy_name=owning_strategy.name,
                owning_strategy_priority=owning_strategy.priority,
                ownership_type=ownership.ownership_type,
                locked_until=ownership.locked_until,
                reasoning=f"Requesting strategy '{requesting_strategy.name}' (priority={requesting_strategy.priority}) has higher priority than owning strategy '{owning_strategy.name}' (priority={owning_strategy.priority}). Override allowed."
            ),
            reasoning=f"Priority override: {requesting_strategy.name} ({requesting_strategy.priority}) > {owning_strategy.name} ({owning_strategy.priority})"
        )
    else:
        # 우선순위 낮음 → 차단
        return ConflictCheckResponse(
            has_conflict=True,
            resolution=ConflictResolution.BLOCKED,
            can_proceed=False,
            conflict_detail=ConflictDetail(
                owning_strategy_id=owning_strategy.id,
                owning_strategy_name=owning_strategy.name,
                owning_strategy_priority=owning_strategy.priority,
                ownership_type=ownership.ownership_type,
                locked_until=ownership.locked_until,
                reasoning=f"Owning strategy '{owning_strategy.name}' (priority={owning_strategy.priority}) has higher or equal priority. Order blocked."
            ),
            reasoning=f"Conflict blocked: {owning_strategy.name} ({owning_strategy.priority}) >= {requesting_strategy.name} ({requesting_strategy.priority})"
        )


@conflict_router.get("/logs", response_model=List[ConflictLogResponse])
def list_conflict_logs(
    ticker: Optional[str] = Query(None, description="종목 코드 필터"),
    days: int = Query(7, ge=1, le=90, description="조회 기간 (일)"),
    db: Session = Depends(get_db)
):
    """
    충돌 로그 조회

    - **ticker**: 종목 필터 (optional)
    - **days**: 조회 기간 (1-90일)
    - Returns: 충돌 로그 목록 (최신순)
    """
    repo = ConflictLogRepository(db)

    if ticker:
        logs = repo.get_by_ticker(ticker.upper(), days=days)
    else:
        logs = repo.get_recent_conflicts(days=days)

    return logs
