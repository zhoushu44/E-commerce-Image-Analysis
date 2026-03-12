#!/bin/bash

# 推送 Docker 镜像到 Docker Hub
# 使用方法: bash push-to-dockerhub.sh

set -e

# 配置变量（请修改这些变量）
DOCKER_USERNAME="your-dockerhub-username"  # 你的 Docker Hub 用户名（必须小写）
DOCKER_IMAGE_NAME="image-analysis"           # 镜像名称
DOCKER_TAG="latest"                         # 镜像标签（latest, v1.0.0 等）

# 完整镜像名称
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装，请先安装 Docker"
    fi
    info "Docker 已安装"
}

# 检查 Dockerfile 是否存在
check_dockerfile() {
    if [ ! -f "Dockerfile" ]; then
        error "Dockerfile 文件不存在，请确保在项目根目录运行此脚本"
    fi
    info "Dockerfile 已找到"
}

# 配置参数
configure_params() {
    echo ""
    echo "=========================================="
    echo "  配置 Docker Hub 参数"
    echo "=========================================="
    echo ""
    
    read -p "Docker Hub 用户名 [${DOCKER_USERNAME}]: " input_username
    DOCKER_USERNAME=${input_username:-$DOCKER_USERNAME}
    
    read -p "镜像名称 [${DOCKER_IMAGE_NAME}]: " input_image_name
    DOCKER_IMAGE_NAME=${input_image_name:-$DOCKER_IMAGE_NAME}
    
    read -p "镜像标签 [${DOCKER_TAG}]: " input_tag
    DOCKER_TAG=${input_tag:-$DOCKER_TAG}
    
    FULL_IMAGE_NAME="${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
    
    echo ""
    success "配置已更新！"
    echo ""
    info "镜像名称: ${FULL_IMAGE_NAME}"
    echo ""
    read -p "按 Enter 继续..."
}

# 构建镜像
build_image() {
    echo ""
    info "开始构建 Docker 镜像..."
    echo ""
    info "镜像名称: ${FULL_IMAGE_NAME}"
    echo ""
    
    docker build -t ${FULL_IMAGE_NAME} .
    
    if [ $? -eq 0 ]; then
        success "镜像构建成功！"
        echo ""
        docker images | grep ${DOCKER_IMAGE_NAME}
    else
        error "镜像构建失败"
    fi
}

# 登录 Docker Hub
login_dockerhub() {
    echo ""
    info "登录 Docker Hub..."
    echo ""
    
    # 检查是否已登录
    if docker info | grep -q "Username"; then
        info "已登录 Docker Hub"
        return
    fi
    
    docker login
    
    if [ $? -ne 0 ]; then
        error "Docker Hub 登录失败"
    fi
    
    success "Docker Hub 登录成功"
}

# 推送镜像
push_image() {
    echo ""
    info "推送镜像到 Docker Hub..."
    echo ""
    info "镜像: ${FULL_IMAGE_NAME}"
    echo ""
    
    docker push ${FULL_IMAGE_NAME}
    
    if [ $? -eq 0 ]; then
        success "镜像推送成功！"
        echo ""
        info "现在你可以在宝塔面板中搜索此镜像："
        echo ""
        echo -e "${BLUE}搜索关键词: ${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}${NC}"
        echo ""
        echo "或者在宝塔 Docker 管理中直接拉取："
        echo -e "${BLUE}${FULL_IMAGE_NAME}${NC}"
    else
        error "镜像推送失败"
    fi
}

# 显示镜像信息
show_image_info() {
    echo ""
    info "本地镜像："
    echo ""
    docker images | grep ${DOCKER_IMAGE_NAME} || {
        warn "未找到镜像"
    }
}

# 清理旧镜像
cleanup_old_images() {
    echo ""
    info "清理旧的 Docker 镜像..."
    echo ""
    
    # 删除悬空镜像
    docker image prune -f
    
    # 删除未使用的镜像
    docker image prune -a -f
    
    success "清理完成"
}

# 主菜单
show_menu() {
    echo ""
    echo "=========================================="
    echo "  Docker 镜像推送工具"
    echo "=========================================="
    echo ""
    echo "当前配置："
    echo "  Docker Hub 用户: ${DOCKER_USERNAME}"
    echo "  镜像名称: ${DOCKER_IMAGE_NAME}"
    echo "  镜像标签: ${DOCKER_TAG}"
    echo "  完整镜像: ${FULL_IMAGE_NAME}"
    echo ""
    echo "请选择操作："
    echo "  1) 配置参数"
    echo "  2) 构建镜像"
    echo "  3) 登录 Docker Hub"
    echo "  4) 推送镜像"
    echo "  5) 完整流程（构建+登录+推送）"
    echo "  6) 查看镜像信息"
    echo "  7) 清理旧镜像"
    echo "  0) 退出"
    echo ""
    echo -n "请输入选项 [0-7]: "
}

# 主循环
main() {
    # 初始化检查
    check_docker
    check_dockerfile
    
    while true; do
        show_menu
        read choice
        
        case $choice in
            1)
                configure_params
                ;;
            2)
                build_image
                ;;
            3)
                login_dockerhub
                ;;
            4)
                push_image
                ;;
            5)
                build_image
                login_dockerhub
                push_image
                ;;
            6)
                show_image_info
                ;;
            7)
                cleanup_old_images
                ;;
            0)
                info "退出..."
                exit 0
                ;;
            *)
                error "无效的选项"
                ;;
        esac
        
        echo ""
        read -p "按 Enter 继续..."
    done
}

# 运行
main
