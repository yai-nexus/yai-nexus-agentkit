#!/bin/bash

# Run Logging Demos Script
# 运行日志演示：SLS Loguru + SLS Pino 示例

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📝 运行日志演示...${NC}"
echo "项目根目录: $PROJECT_ROOT"

# 确保在项目根目录执行
cd "$PROJECT_ROOT"

# 创建日志目录
mkdir -p logs

# 分隔符函数
print_separator() {
    echo -e "${YELLOW}$1${NC}"
    echo "=================================================="
}

# 运行单个演示的函数
run_demo() {
    local demo_name=$1
    local demo_command=$2
    local demo_description=$3
    
    print_separator "🚀 运行 $demo_name"
    echo -e "${GREEN}描述: $demo_description${NC}"
    echo -e "${YELLOW}命令: $demo_command${NC}"
    echo ""
    
    # 执行命令
    if eval "$demo_command"; then
        echo -e "\n${GREEN}✅ $demo_name 运行完成${NC}"
    else
        echo -e "\n${RED}❌ $demo_name 运行失败${NC}"
        return 1
    fi
    
    echo ""
}

# 检查依赖
echo -e "${YELLOW}🔍 检查依赖...${NC}"

# 检查 Python 虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ 未找到 Python 虚拟环境 (.venv)${NC}"
    echo "请运行: uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt"
    exit 1
fi

# 检查 pnpm 命令
if ! command -v pnpm &> /dev/null; then
    echo -e "${RED}❌ 未找到 pnpm 命令${NC}"
    echo "请安装 pnpm: npm install -g pnpm"
    exit 1
fi

echo -e "${GREEN}✅ 依赖检查通过${NC}"
echo ""

# 运行演示
DEMO_STATUS=0

# 1. 运行 SLS Loguru 演示
run_demo "SLS Loguru 演示" "pnpm dev:example:sls-loguru" "Python 日志集成演示 (Loguru + SLS)" || DEMO_STATUS=1

# 2. 运行 SLS Pino 演示  
run_demo "SLS Pino 演示" "pnpm dev:example:sls-pino" "Node.js 日志集成演示 (Pino + SLS)" || DEMO_STATUS=1

# 显示演示结果
print_separator "📊 演示结果汇总"

if [ $DEMO_STATUS -eq 0 ]; then
    echo -e "${GREEN}✨ 所有日志演示运行成功！${NC}"
else
    echo -e "${RED}⚠️  部分演示运行失败${NC}"
fi

# 显示日志位置
echo -e "\n${YELLOW}📁 日志文件位置:${NC}"
echo "  📋 统一日志目录: ./logs/"
echo "  📝 Loguru 演示日志: 查看 logs/ 目录中的小时分目录"
echo "  📋 Pino 演示日志: 查看 logs/ 目录中的小时分目录"

# 显示实用命令
echo -e "\n${YELLOW}📋 实用命令:${NC}"
echo "  查看最新日志: ls -la logs/"
echo "  查看当前小时日志: ls -la logs/current/"
echo "  清理旧日志: node scripts/cleanup-logs.js"
echo "  查看日志统计: node scripts/cleanup-logs.js --stats"

echo -e "\n${BLUE}🎉 日志演示完成！${NC}"

exit $DEMO_STATUS