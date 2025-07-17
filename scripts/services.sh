#!/bin/bash

# 统一服务管理脚本
# 替代：start-nextjs.sh, start-python.sh, start-services.sh, stop-nextjs.sh, stop-python.sh, stop-services.sh

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 使用方法
usage() {
    echo -e "${BLUE}🚀 统一服务管理脚本${NC}"
    echo "用法: $0 <action> [service]"
    echo ""
    echo "Actions:"
    echo "  start [service]    - 启动服务"
    echo "  stop [service]     - 停止服务"
    echo "  restart [service]  - 重启服务"
    echo "  status            - 查看服务状态"
    echo ""
    echo "Services:"
    echo "  nextjs            - Next.js 应用"
    echo "  python            - Python 后端"
    echo "  all               - 所有服务 (默认)"
    echo ""
    echo "示例:"
    echo "  $0 start          - 启动所有服务"
    echo "  $0 start nextjs   - 只启动 Next.js"
    echo "  $0 stop python    - 只停止 Python 后端"
    echo "  $0 restart all    - 重启所有服务"
}

# 日志路径管理
get_log_path() {
    local service=$1
    local hour_dir=$(date '+%Y%m%d-%H')
    local log_dir="logs/$hour_dir"
    
    mkdir -p "$log_dir"
    
    # 更新 current 软链接
    if [ -L "logs/current" ] || [ -e "logs/current" ]; then
        rm -f "logs/current"
    fi
    ln -sf "$hour_dir" "logs/current"
    
    echo "$log_dir/$service.log"
}

# 启动服务
start_service() {
    local service=$1
    
    case $service in
        nextjs)
            echo -e "${GREEN}🚀 启动 Next.js 应用...${NC}"
            pkill -f "dev.*nextjs-app" 2>/dev/null || true
            lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true
            sleep 2
            
            log_path=$(get_log_path "nextjs")
            nohup nx dev nextjs-app > "$log_path" 2>&1 &
            echo "  📱 Next.js 应用已启动 (日志: $log_path)"
            echo "  🌐 访问地址: http://localhost:3000"
            ;;
        python)
            echo -e "${GREEN}🚀 启动 Python 后端...${NC}"
            pkill -f "serve.*python-backend" 2>/dev/null || true
            lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
            sleep 2
            
            log_path=$(get_log_path "python")
            nohup nx serve python-backend > "$log_path" 2>&1 &
            echo "  🐍 Python 后端已启动 (日志: $log_path)"
            echo "  🌐 访问地址: http://localhost:8000"
            ;;
        all)
            start_service nextjs
            start_service python
            ;;
        *)
            echo -e "${RED}❌ 未知服务: $service${NC}"
            usage
            exit 1
            ;;
    esac
}

# 停止服务
stop_service() {
    local service=$1
    
    case $service in
        nextjs)
            echo -e "${RED}🛑 停止 Next.js 应用...${NC}"
            pkill -f "dev.*nextjs-app" 2>/dev/null && echo "  ✅ Next.js 应用已停止" || echo "  ℹ️  Next.js 应用未运行"
            lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 端口 3000 已释放" || echo "  ℹ️  端口 3000 未占用"
            ;;
        python)
            echo -e "${RED}🛑 停止 Python 后端...${NC}"
            pkill -f "serve.*python-backend" 2>/dev/null && echo "  ✅ Python 后端已停止" || echo "  ℹ️  Python 后端未运行"
            lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 端口 8000 已释放" || echo "  ℹ️  端口 8000 未占用"
            ;;
        all)
            stop_service nextjs
            stop_service python
            ;;
        *)
            echo -e "${RED}❌ 未知服务: $service${NC}"
            usage
            exit 1
            ;;
    esac
}

# 查看服务状态
show_status() {
    echo -e "${BLUE}📊 服务状态:${NC}"
    
    # 检查 Next.js
    if pgrep -f "dev.*nextjs-app" > /dev/null; then
        echo -e "  ✅ Next.js 应用 - 运行中"
        echo -e "     🌐 http://localhost:3000"
    else
        echo -e "  ❌ Next.js 应用 - 未运行"
    fi
    
    # 检查 Python
    if pgrep -f "serve.*python-backend" > /dev/null; then
        echo -e "  ✅ Python 后端 - 运行中"
        echo -e "     🌐 http://localhost:8000"
    else
        echo -e "  ❌ Python 后端 - 未运行"
    fi
    
    # 显示日志路径
    if [ -L "logs/current" ]; then
        echo -e "\n  📁 当前日志目录: logs/current/"
        echo -e "  📋 实用命令:"
        echo -e "    tail -f logs/current/*.log  # 查看所有日志"
        echo -e "    $0 stop all                 # 停止所有服务"
    fi
}

# 主逻辑
main() {
    local action=${1:-""}
    local service=${2:-"all"}
    
    case $action in
        start)
            start_service $service
            sleep 3
            show_status
            ;;
        stop)
            stop_service $service
            ;;
        restart)
            stop_service $service
            sleep 2
            start_service $service
            sleep 3
            show_status
            ;;
        status)
            show_status
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@" 