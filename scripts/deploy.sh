#!/bin/bash

# ============================================================================
# AI Trading System - Deployment Script
# ============================================================================
#
# 사용법:
#   ./scripts/deploy.sh [환경] [옵션]
#
# 환경:
#   - staging: 스테이징 서버 배포
#   - production: 프로덕션 서버 배포
#
# 옵션:
#   --skip-tests: 테스트 건너뛰기
#   --force: 확인 없이 강제 배포
#
# 예시:
#   ./scripts/deploy.sh staging
#   ./scripts/deploy.sh production --force
#
# ============================================================================

set -e  # 오류 발생 시 즉시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경 확인
if [ -z "$1" ]; then
    log_error "환경을 지정해주세요: staging 또는 production"
    exit 1
fi

ENVIRONMENT=$1
SKIP_TESTS=false
FORCE=false

# 옵션 파싱
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            exit 1
            ;;
    esac
done

log_info "배포 시작: $ENVIRONMENT 환경"

# ============================================================================
# 1. 사전 검사
# ============================================================================

log_info "Step 1: 사전 검사 중..."

# Git 상태 확인
if [[ $(git status --porcelain) ]]; then
    log_warning "커밋되지 않은 변경사항이 있습니다."
    if [ "$FORCE" = false ]; then
        read -p "계속하시겠습니까? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "배포 중단됨"
            exit 1
        fi
    fi
fi

# 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)

if [ "$ENVIRONMENT" = "production" ]; then
    if [ "$CURRENT_BRANCH" != "main" ]; then
        log_error "Production 배포는 main 브랜치에서만 가능합니다. 현재: $CURRENT_BRANCH"
        exit 1
    fi
elif [ "$ENVIRONMENT" = "staging" ]; then
    if [ "$CURRENT_BRANCH" != "develop" ] && [ "$CURRENT_BRANCH" != "main" ]; then
        log_warning "Staging 배포는 develop 또는 main 브랜치에서 권장됩니다. 현재: $CURRENT_BRANCH"
    fi
fi

log_success "사전 검사 완료"

# ============================================================================
# 2. 테스트 실행
# ============================================================================

if [ "$SKIP_TESTS" = false ]; then
    log_info "Step 2: 테스트 실행 중..."

    # Backend 테스트
    log_info "Backend 테스트..."
    if [ -f "backend/requirements.txt" ]; then
        # 가상환경이 있으면 활성화
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi

        pytest backend/tests/ -v || {
            log_error "Backend 테스트 실패"
            exit 1
        }
    fi

    # Frontend 테스트
    log_info "Frontend 테스트..."
    if [ -d "frontend" ]; then
        cd frontend
        npm test -- --watchAll=false || {
            log_error "Frontend 테스트 실패"
            cd ..
            exit 1
        }
        cd ..
    fi

    log_success "모든 테스트 통과"
else
    log_warning "테스트 건너뜀 (--skip-tests)"
fi

# ============================================================================
# 3. Docker 이미지 빌드
# ============================================================================

log_info "Step 3: Docker 이미지 빌드 중..."

# 이미지 태그 생성 (commit hash + timestamp)
GIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="${ENVIRONMENT}-${GIT_HASH}-${TIMESTAMP}"

log_info "이미지 태그: $IMAGE_TAG"

# Backend 이미지 빌드
docker build \
    -t ai-trading-backend:${IMAGE_TAG} \
    -t ai-trading-backend:${ENVIRONMENT}-latest \
    -f backend/Dockerfile \
    . || {
    log_error "Backend 이미지 빌드 실패"
    exit 1
}

# Frontend 이미지 빌드
docker build \
    -t ai-trading-frontend:${IMAGE_TAG} \
    -t ai-trading-frontend:${ENVIRONMENT}-latest \
    -f frontend/Dockerfile \
    frontend/ || {
    log_error "Frontend 이미지 빌드 실패"
    exit 1
}

log_success "Docker 이미지 빌드 완료"

# ============================================================================
# 4. 환경 설정 로드
# ============================================================================

log_info "Step 4: 환경 설정 로드 중..."

# .env 파일 확인
ENV_FILE=".env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    log_error "환경 설정 파일을 찾을 수 없습니다: $ENV_FILE"
    exit 1
fi

# 환경 변수 로드
export $(cat $ENV_FILE | grep -v '^#' | xargs)

log_success "환경 설정 로드 완료"

# ============================================================================
# 5. 데이터베이스 백업 (Production만)
# ============================================================================

if [ "$ENVIRONMENT" = "production" ]; then
    log_info "Step 5: 데이터베이스 백업 중..."

    BACKUP_DIR="backups"
    mkdir -p $BACKUP_DIR

    BACKUP_FILE="${BACKUP_DIR}/backup-${TIMESTAMP}.sql"

    docker-compose exec -T postgres pg_dump \
        -U postgres \
        -d ai_trading \
        > $BACKUP_FILE || {
        log_warning "데이터베이스 백업 실패 (계속 진행)"
    }

    log_success "백업 완료: $BACKUP_FILE"
fi

# ============================================================================
# 6. 배포 실행
# ============================================================================

log_info "Step 6: 배포 실행 중..."

# docker-compose 파일 선택
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    log_warning "$COMPOSE_FILE이 없습니다. 기본 docker-compose.yml 사용"
    COMPOSE_FILE="docker-compose.yml"
fi

# 최종 확인
if [ "$FORCE" = false ]; then
    log_warning "다음 환경에 배포합니다: $ENVIRONMENT"
    read -p "계속하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "배포 중단됨"
        exit 1
    fi
fi

# 컨테이너 중지
log_info "기존 컨테이너 중지 중..."
docker-compose -f $COMPOSE_FILE down

# 새 컨테이너 시작
log_info "새 컨테이너 시작 중..."
docker-compose -f $COMPOSE_FILE up -d || {
    log_error "컨테이너 시작 실패"

    # 롤백 시도
    log_warning "이전 버전으로 롤백 시도 중..."
    docker-compose -f $COMPOSE_FILE up -d

    exit 1
}

# 데이터베이스 마이그레이션
log_info "데이터베이스 마이그레이션 실행 중..."
docker-compose -f $COMPOSE_FILE exec -T backend alembic upgrade head || {
    log_error "마이그레이션 실패"
    exit 1
}

log_success "배포 완료"

# ============================================================================
# 7. Health Check
# ============================================================================

log_info "Step 7: Health Check 중..."

# 서비스 시작 대기
sleep 10

# Backend health check
BACKEND_URL="http://localhost:8000/health"
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_URL="https://api.ai-trading-system.com/health"
elif [ "$ENVIRONMENT" = "staging" ]; then
    BACKEND_URL="https://staging-api.ai-trading-system.com/health"
fi

if curl --fail --silent $BACKEND_URL > /dev/null; then
    log_success "Backend 정상 작동 중"
else
    log_error "Backend Health Check 실패"

    # 로그 확인
    log_info "Backend 로그:"
    docker-compose -f $COMPOSE_FILE logs --tail=50 backend

    exit 1
fi

# Frontend health check
FRONTEND_URL="http://localhost:3000"
if [ "$ENVIRONMENT" = "production" ]; then
    FRONTEND_URL="https://ai-trading-system.com"
elif [ "$ENVIRONMENT" = "staging" ]; then
    FRONTEND_URL="https://staging.ai-trading-system.com"
fi

if curl --fail --silent $FRONTEND_URL > /dev/null; then
    log_success "Frontend 정상 작동 중"
else
    log_warning "Frontend Health Check 실패 (경고만 표시)"
fi

# ============================================================================
# 8. 배포 완료 알림
# ============================================================================

log_info "Step 8: 알림 발송 중..."

# Slack 알림 (선택사항)
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST \
        -H 'Content-type: application/json' \
        --data "{
            \"text\": \"✅ $ENVIRONMENT 배포 완료\",
            \"blocks\": [
                {
                    \"type\": \"section\",
                    \"text\": {
                        \"type\": \"mrkdwn\",
                        \"text\": \"*배포 완료* ✅\n*환경*: $ENVIRONMENT\n*브랜치*: $CURRENT_BRANCH\n*커밋*: $GIT_HASH\n*시간*: $(date)\"
                    }
                }
            ]
        }" \
        $SLACK_WEBHOOK_URL > /dev/null 2>&1 || {
        log_warning "Slack 알림 전송 실패"
    }
fi

# ============================================================================
# 완료
# ============================================================================

echo ""
log_success "========================================="
log_success "배포 성공!"
log_success "환경: $ENVIRONMENT"
log_success "이미지 태그: $IMAGE_TAG"
log_success "시간: $(date)"
log_success "========================================="
echo ""

# 다음 단계 안내
log_info "다음 단계:"
echo "  1. 로그 확인: docker-compose -f $COMPOSE_FILE logs -f"
echo "  2. 상태 확인: docker-compose -f $COMPOSE_FILE ps"
echo "  3. 모니터링: $FRONTEND_URL"
echo ""
