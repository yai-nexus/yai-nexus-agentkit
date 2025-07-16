#!/bin/bash

# Start Next.js Service Script
# 单独启动 Next.js 应用

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🚀 启动 Next.js 应用...${NC}"
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

# 停止可能已经运行的 Next.js 服务
echo -e "${YELLOW}📋 停止现有 Next.js 服务...${NC}"
pkill -f "dev:example:next" 2>/dev/null && echo "  ✅ 停止现有 Next.js 应用" || echo "  ℹ️  Next.js 应用未运行"
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✅ 释放端口 3000" || echo "  ℹ️  端口 3000 未占用"

# 等待进程完全停止
sleep 2

# 启动 Next.js 服务
echo -e "${GREEN}🔥 启动 Next.js 应用...${NC}"

# 获取按小时分目录的日志路径
NEXTJS_LOG_PATH=$(get_hourly_log_path "nextjs-service")

echo "  📱 启动 Next.js 应用..."
echo "    日志路径: $NEXTJS_LOG_PATH"
nohup pnpm dev:example:next > "$NEXTJS_LOG_PATH" 2>&1 &
NEXTJS_PID=$!

# 等待进程启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 检查进程状态
echo -e "${GREEN}📊 检查服务状态:${NC}"

if kill -0 "$NEXTJS_PID" 2>/dev/null; then
    echo -e "  ✅ Next.js 应用 (PID: $NEXTJS_PID)"
    
    # 显示访问信息
    echo -e "\n${GREEN}🌐 服务访问地址:${NC}"
    echo "  📱 Next.js 应用: http://localhost:3000"
    echo "  🧪 Logger 测试页面: http://localhost:3000/test-logger"
    
    # 显示日志监控命令
    echo -e "\n${YELLOW}📋 实用命令:${NC}"
    echo "  查看 Next.js 日志: tail -f $NEXTJS_LOG_PATH"
    echo "  查看当前小时日志: tail -f logs/current/*.log"
    echo "  停止 Next.js 服务: ./scripts/stop-nextjs.sh"
    
    echo -e "\n${GREEN}✨ Next.js 应用已成功启动！${NC}"
else
    echo -e "  ❌ Next.js 应用启动失败"
    echo -e "\n${RED}⚠️  启动失败，请检查日志: $NEXTJS_LOG_PATH${NC}"
    exit 1
fi
