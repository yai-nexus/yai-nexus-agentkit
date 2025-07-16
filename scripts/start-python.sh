#!/bin/bash

# Start Python Backend Service Script
# 单独启动 Python 后端

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🚀 启动 Python 后端...${NC}"
echo "项目根目录: $PROJECT_ROOT"

# 确保在项目根目录执行
cd "$PROJECT_ROOT"

# 获取按小时分目录的日志路径
get_hourly_log_path() {
    local service_name=$1
    local hour_dir=$(date '+%Y%m%d-%H')
    local log_dir="logs/$hour_dir"

    # 确保目录存在
    mkdir -p "$log_dir"

    # 创建或更新 current 软链接
    if [ -L "logs/current" ] || [ -e "logs/current" ]; then
        rm -f "logs/current"
    fi
    ln -sf "$hour_dir" "logs/current"

    echo "$log_dir/$service_name.log"
}

# 创建日志目录
mkdir -p logs

# 停止可能已经运行的 Python 服务
echo -e "${YELLOW}📋 停止现有 Python 服务...${NC}"
pkill -f "dev:example:python" 2>/dev/null && echo "  ✅ 停止现有 Python 后端" || echo "  ℹ️  Python 后端未运行"
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 8000" || echo "  ℹ️  端口 8000 未占用"

# 等待进程完全停止
sleep 2

# 启动 Python 服务
echo -e "${GREEN}🔥 启动 Python 后端...${NC}"

# 获取按小时分目录的日志路径
PYTHON_LOG_PATH=$(get_hourly_log_path "python-service")

echo "  🐍 启动 Python 后端..."
echo "    日志路径: $PYTHON_LOG_PATH"
nohup pnpm dev:example:python > "$PYTHON_LOG_PATH" 2>&1 &
PYTHON_PID=$!

# 等待进程启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 检查进程状态
echo -e "${GREEN}📊 检查服务状态:${NC}"

if kill -0 "$PYTHON_PID" 2>/dev/null; then
    echo -e "  ✅ Python 后端 (PID: $PYTHON_PID)"
    
    # 显示访问信息
    echo -e "\n${GREEN}🌐 服务访问地址:${NC}"
    echo "  🐍 Python 后端: http://localhost:8000"
    echo "  📚 FastAPI 文档: http://localhost:8000/docs"
    echo "  🔧 健康检查: http://localhost:8000/health"
    
    # 显示日志监控命令
    echo -e "\n${YELLOW}📋 实用命令:${NC}"
    echo "  查看 Python 日志: tail -f $PYTHON_LOG_PATH"
    echo "  查看当前小时日志: tail -f logs/current/*.log"
    echo "  停止 Python 服务: ./scripts/stop-python.sh"
    
    echo -e "\n${GREEN}✨ Python 后端已成功启动！${NC}"
else
    echo -e "  ❌ Python 后端启动失败"
    echo -e "\n${RED}⚠️  启动失败，请检查日志: $PYTHON_LOG_PATH${NC}"
    exit 1
fi
