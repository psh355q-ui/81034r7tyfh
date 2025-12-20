#!/bin/bash

# =============================================================================
# AI Trading System - NAS 배포 스크립트
# =============================================================================

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# 1. 환경 확인
# =============================================================================

log_info "환경 확인 중..."

if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되어 있지 않습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

log_info "✓ Docker: $(docker --version)"
log_info "✓ Docker Compose: $(docker-compose --version)"

# =============================================================================
# 2. .env 파일 확인
# =============================================================================

log_info ".env 파일 확인 중..."

if [ ! -f .env ]; then
    log_warn ".env 파일이 없습니다. .env.example을 복사합니다."

    if [ -f .env.example ]; then
        cp .env.example .env
        log_warn "⚠️  .env 파일을 편집하여 환경 변수를 설정하세요!"
        log_warn "    필수 항목: DATABASE_URL, POSTGRES_PASSWORD, API_KEY 등"

        read -p "지금 편집하시겠습니까? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        else
            log_error ".env 파일 설정 후 다시 실행하세요."
            exit 1
        fi
    else
        log_error ".env.example 파일이 없습니다."
        exit 1
    fi
fi

log_info "✓ .env 파일 존재"

# =============================================================================
# 3. 기존 컨테이너 정리 (선택적)
# =============================================================================

log_info "기존 컨테이너 상태 확인..."

if [ "$(docker ps -q -f name=ai-trading)" ]; then
    log_warn "기존 컨테이너가 실행 중입니다."
    read -p "기존 컨테이너를 중지하고 재배포하시겠습니까? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "기존 컨테이너 중지 중..."
        docker-compose -f docker-compose.prod.yml down
        log_info "✓ 컨테이너 중지 완료"
    else
        log_info "배포를 취소합니다."
        exit 0
    fi
fi

# =============================================================================
# 4. 이미지 빌드
# =============================================================================

log_info "Docker 이미지 빌드 중..."
log_info "⏳ 이 작업은 5-10분 정도 소요될 수 있습니다..."

docker-compose -f docker-compose.prod.yml build

log_info "✓ 이미지 빌드 완료"

# =============================================================================
# 5. 컨테이너 실행
# =============================================================================

log_info "컨테이너 실행 중..."

docker-compose -f docker-compose.prod.yml up -d

log_info "⏳ 컨테이너 시작 대기 중... (30초)"
sleep 30

# =============================================================================
# 6. 헬스 체크
# =============================================================================

log_info "헬스 체크 수행 중..."

# PostgreSQL 체크
log_info "PostgreSQL 연결 확인..."
if docker exec ai-trading-postgres-prod pg_isready -U ai_trading_user &> /dev/null; then
    log_info "✓ PostgreSQL 정상"
else
    log_error "✗ PostgreSQL 연결 실패"
fi

# Redis 체크
log_info "Redis 연결 확인..."
if docker exec ai-trading-redis-prod redis-cli ping &> /dev/null; then
    log_info "✓ Redis 정상"
else
    log_error "✗ Redis 연결 실패"
fi

# Backend 체크
log_info "Backend API 확인..."
if docker exec ai-trading-backend-prod curl -f http://localhost:8000/health &> /dev/null; then
    log_info "✓ Backend API 정상"
else
    log_warn "✗ Backend API 응답 없음 (로그 확인 필요)"
fi

# =============================================================================
# 7. 데이터베이스 초기화 (필요 시)
# =============================================================================

log_info "데이터베이스 테이블 확인 중..."

TABLE_COUNT=$(docker exec ai-trading-postgres-prod psql -U ai_trading_user -d ai_trading -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

if [ "$TABLE_COUNT" -eq "0" ]; then
    log_warn "데이터베이스 테이블이 없습니다."
    read -p "데이터베이스를 초기화하시겠습니까? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "데이터베이스 초기화 중..."
        docker exec ai-trading-backend-prod python scripts/init_database.py
        log_info "✓ 데이터베이스 초기화 완료"
    fi
else
    log_info "✓ 데이터베이스 테이블 $TABLE_COUNT 개 존재"
fi

# =============================================================================
# 8. 배포 결과 출력
# =============================================================================

echo
log_info "======================================================================"
log_info "                    배포 완료!"
log_info "======================================================================"
echo

log_info "실행 중인 컨테이너:"
docker-compose -f docker-compose.prod.yml ps

echo
log_info "접속 정보:"
log_info "  - 프론트엔드:        http://localhost"
log_info "  - API 문서:          http://localhost/docs"
log_info "  - Grafana:           http://localhost:3001"
log_info "  - Prometheus:        http://localhost:9090"

echo
log_info "유용한 명령어:"
log_info "  로그 확인:           docker-compose -f docker-compose.prod.yml logs -f"
log_info "  컨테이너 재시작:     docker-compose -f docker-compose.prod.yml restart backend"
log_info "  컨테이너 중지:       docker-compose -f docker-compose.prod.yml down"
log_info "  백업:                docker exec ai-trading-postgres-prod pg_dump -U ai_trading_user ai_trading > backup.sql"

echo
log_info "⚠️  중요 사항:"
log_info "  1. Grafana 기본 계정: admin / admin (최초 접속 시 변경)"
log_info "  2. 정기 백업 설정을 권장합니다."
log_info "  3. .env 파일은 절대 Git에 커밋하지 마세요!"

echo
log_info "======================================================================"
