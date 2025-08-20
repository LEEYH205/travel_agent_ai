#!/bin/bash

# ========================================
# Travel Agent AI - 프로덕션 배포 스크립트
# ========================================

set -e  # 오류 발생 시 스크립트 중단

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

# 환경 변수 로드
if [ -f ".env" ]; then
    log_info "환경 변수 파일 로드 중..."
    export $(cat .env | grep -v '^#' | xargs)
else
    log_error ".env 파일을 찾을 수 없습니다."
    exit 1
fi

# 기본 설정
PROJECT_NAME="travel_agent_ai"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="/var/backups/${PROJECT_NAME}"
LOG_DIR="/var/log/${PROJECT_NAME}"

# 함수 정의

# 시스템 요구사항 확인
check_requirements() {
    log_info "시스템 요구사항 확인 중..."
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    # 디스크 공간 확인
    DISK_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [ "$DISK_SPACE" -lt 1048576 ]; then  # 1GB 미만
        log_warning "디스크 공간이 부족합니다. (현재: ${DISK_SPACE}KB)"
    fi
    
    log_success "시스템 요구사항 확인 완료"
}

# 백업 생성
create_backup() {
    log_info "백업 생성 중..."
    
    BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    # 백업 디렉토리 생성
    sudo mkdir -p "${BACKUP_DIR}"
    
    # 현재 상태 백업
    docker-compose ps > "${BACKUP_DIR}/current_status.txt" 2>/dev/null || true
    
    # 볼륨 데이터 백업
    if [ -d "cache" ]; then
        tar -czf "${BACKUP_FILE}" cache/ logs/ 2>/dev/null || true
        log_success "백업 생성 완료: ${BACKUP_FILE}"
    else
        log_warning "백업할 데이터가 없습니다."
    fi
}

# 이전 배포 정리
cleanup_previous() {
    log_info "이전 배포 정리 중..."
    
    # 이전 컨테이너 정리
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 사용하지 않는 이미지 정리
    docker image prune -f
    
    # 사용하지 않는 볼륨 정리
    docker volume prune -f
    
    log_success "이전 배포 정리 완료"
}

# 새 이미지 빌드
build_images() {
    log_info "Docker 이미지 빌드 중..."
    
    # 백엔드 이미지 빌드
    log_info "백엔드 이미지 빌드 중..."
    docker-compose build backend
    
    # 프론트엔드 이미지 빌드
    log_info "프론트엔드 이미지 빌드 중..."
    docker-compose build frontend
    
    log_success "이미지 빌드 완료"
}

# 서비스 시작
start_services() {
    log_info "서비스 시작 중..."
    
    # 백그라운드에서 서비스 시작
    docker-compose up -d
    
    # 서비스 상태 확인
    log_info "서비스 상태 확인 중..."
    sleep 10
    
    # 헬스 체크
    check_health
    
    log_success "서비스 시작 완료"
}

# 헬스 체크
check_health() {
    log_info "헬스 체크 실행 중..."
    
    # 백엔드 헬스 체크
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "백엔드 서비스 정상"
    else
        log_error "백엔드 서비스 비정상"
        return 1
    fi
    
    # 프론트엔드 헬스 체크
    if curl -f http://localhost:8501 > /dev/null 2>&1; then
        log_success "프론트엔드 서비스 정상"
    else
        log_error "프론트엔드 서비스 비정상"
        return 1
    fi
    
    # Nginx 헬스 체크
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Nginx 서비스 정상"
    else
        log_warning "Nginx 서비스 비정상 (설정 확인 필요)"
    fi
}

# 로그 설정
setup_logging() {
    log_info "로깅 설정 중..."
    
    # 로그 디렉토리 생성
    sudo mkdir -p "${LOG_DIR}"
    sudo chown -R $USER:$USER "${LOG_DIR}"
    
    # 로그 로테이션 설정
    if [ ! -f "/etc/logrotate.d/${PROJECT_NAME}" ]; then
        sudo tee "/etc/logrotate.d/${PROJECT_NAME}" > /dev/null <<EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose restart backend frontend
    endscript
}
EOF
        log_success "로그 로테이션 설정 완료"
    fi
}

# 모니터링 설정
setup_monitoring() {
    log_info "모니터링 설정 중..."
    
    # Prometheus 설정
    if [ ! -d "monitoring" ]; then
        mkdir -p monitoring
        log_warning "monitoring 디렉토리가 없습니다. 수동으로 설정해주세요."
    fi
    
    # Grafana 대시보드 설정
    if [ ! -d "monitoring/grafana" ]; then
        mkdir -p monitoring/grafana/dashboards
        mkdir -p monitoring/grafana/datasources
        log_warning "Grafana 설정 디렉토리가 없습니다. 수동으로 설정해주세요."
    fi
}

# SSL 인증서 설정
setup_ssl() {
    log_info "SSL 인증서 설정 중..."
    
    if [ -n "$SSL_CERT_PATH" ] && [ -n "$SSL_KEY_PATH" ]; then
        if [ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ]; then
            log_success "SSL 인증서 파일 확인 완료"
            
            # Nginx SSL 설정 활성화
            if [ -f "nginx.conf" ]; then
                sed -i 's/# server {/server {/g' nginx.conf
                sed -i 's/# listen 443 ssl http2;/listen 443 ssl http2;/g' nginx.conf
                log_success "Nginx SSL 설정 활성화 완료"
            fi
        else
            log_warning "SSL 인증서 파일을 찾을 수 없습니다: $SSL_CERT_PATH, $SSL_KEY_PATH"
        fi
    else
        log_warning "SSL 인증서 경로가 설정되지 않았습니다."
    fi
}

# 방화벽 설정
setup_firewall() {
    log_info "방화벽 설정 중..."
    
    # UFW 사용 시
    if command -v ufw &> /dev/null; then
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw allow 8000/tcp
        sudo ufw allow 8501/tcp
        log_success "UFW 방화벽 설정 완료"
    # iptables 사용 시
    elif command -v iptables &> /dev/null; then
        sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
        sudo iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
        log_success "iptables 방화벽 설정 완료"
    else
        log_warning "방화벽 도구를 찾을 수 없습니다. 수동으로 설정해주세요."
    fi
}

# 성능 최적화
optimize_performance() {
    log_info "성능 최적화 중..."
    
    # 시스템 파라미터 최적화
    if [ -f "/etc/sysctl.conf" ]; then
        # 네트워크 성능 최적화
        echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
        echo "net.ipv4.tcp_max_syn_backlog = 65535" | sudo tee -a /etc/sysctl.conf
        echo "net.ipv4.tcp_fin_timeout = 30" | sudo tee -a /etc/sysctl.conf
        
        # 메모리 최적화
        echo "vm.swappiness = 10" | sudo tee -a /etc/sysctl.conf
        
        sudo sysctl -p
        log_success "시스템 파라미터 최적화 완료"
    fi
    
    # Docker 최적화
    if [ -f "/etc/docker/daemon.json" ]; then
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "max-concurrent-downloads": 10,
    "max-concurrent-uploads": 5,
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "3"
    }
}
EOF
        sudo systemctl restart docker
        log_success "Docker 최적화 완료"
    fi
}

# 배포 후 검증
post_deployment_check() {
    log_info "배포 후 검증 중..."
    
    # 서비스 상태 확인
    docker-compose ps
    
    # 로그 확인
    log_info "최근 로그 확인 중..."
    docker-compose logs --tail=20
    
    # 성능 메트릭 확인
    if curl -f http://localhost:8000/api/status > /dev/null 2>&1; then
        log_success "API 상태 확인 완료"
    else
        log_warning "API 상태 확인 실패"
    fi
    
    log_success "배포 후 검증 완료"
}

# 롤백 함수
rollback() {
    log_error "배포 실패. 롤백 중..."
    
    # 이전 백업 복원
    LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        log_info "백업 복원 중: $LATEST_BACKUP"
        tar -xzf "$LATEST_BACKUP" -C ./
    fi
    
    # 이전 컨테이너 재시작
    docker-compose down
    docker-compose up -d
    
    log_warning "롤백 완료. 이전 버전으로 복원되었습니다."
}

# 메인 배포 프로세스
main() {
    log_info "Travel Agent AI 프로덕션 배포 시작"
    
    # 트랩 설정 (오류 발생 시 롤백)
    trap rollback ERR
    
    # 1. 요구사항 확인
    check_requirements
    
    # 2. 백업 생성
    create_backup
    
    # 3. 이전 배포 정리
    cleanup_previous
    
    # 4. 새 이미지 빌드
    build_images
    
    # 5. 서비스 시작
    start_services
    
    # 6. 로깅 설정
    setup_logging
    
    # 7. 모니터링 설정
    setup_monitoring
    
    # 8. SSL 설정
    setup_ssl
    
    # 9. 방화벽 설정
    setup_firewall
    
    # 10. 성능 최적화
    optimize_performance
    
    # 11. 배포 후 검증
    post_deployment_check
    
    # 트랩 제거
    trap - ERR
    
    log_success "배포 완료! 🎉"
    log_info "서비스 URL:"
    log_info "  - 프론트엔드: http://localhost:8501"
    log_info "  - 백엔드 API: http://localhost:8000"
    log_info "  - API 문서: http://localhost:8000/docs"
    log_info "  - 모니터링: http://localhost:3000 (Grafana)"
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
