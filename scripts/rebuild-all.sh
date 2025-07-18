#!/bin/bash

# 重新构建所有 packages 和 examples 的脚本
# 清除缓存并重新构建所有内容

set -e  # 遇到错误时停止执行

echo "🔧 开始重新构建所有 packages 和 examples..."

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 解析命令行参数
DEV_MODE=false
SKIP_EXAMPLES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --skip-examples)
            SKIP_EXAMPLES=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --dev             开发模式（跳过 examples 构建，只构建 packages）"
            echo "  --skip-examples   跳过 examples 构建"
            echo "  -h, --help        显示帮助信息"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 -h 或 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查必要工具
check_dependencies() {
    log_info "检查必要工具..."
    
    if ! command -v pnpm &> /dev/null; then
        log_error "pnpm 未安装，请先安装 pnpm"
        exit 1
    fi
    
    if ! command -v uv &> /dev/null; then
        log_error "uv 未安装，请先安装 uv（Python 包管理器）"
        exit 1
    fi
    
    log_success "所有必要工具已安装"
}

# 清除 Node.js 缓存
clean_node_cache() {
    log_info "清除 Node.js 缓存..."
    
    # 删除所有 node_modules
    find . -name 'node_modules' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
    
    # 删除所有 dist 目录
    find . -name 'dist' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
    
    # 清除 pnpm 缓存
    pnpm store prune || true
    
    log_success "Node.js 缓存已清除"
}

# 清除 Python 缓存
clean_python_cache() {
    log_info "清除 Python 缓存..."
    
    # 删除虚拟环境
    if [ -d ".venv" ]; then
        rm -rf .venv
        log_info "已删除 .venv 虚拟环境"
    fi
    
    # 删除 Python 缓存文件
    find . -name '__pycache__' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
    find . -name '*.pyc' -delete 2>/dev/null || true
    find . -name '*.pyo' -delete 2>/dev/null || true
    find . -name '.pytest_cache' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
    
    # 删除构建产物
    find . -name 'build' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
    find . -name '*.egg-info' -type d -prune -exec rm -rf '{}' + 2>/dev/null || true
    
    log_success "Python 缓存已清除"
}

# 设置 Python 环境
setup_python_env() {
    log_info "设置 Python 虚拟环境..."
    
    # 创建虚拟环境
    uv venv .venv
    
    # 激活虚拟环境并安装依赖
    source .venv/bin/activate
    uv pip install -r requirements.txt
    
    log_success "Python 环境设置完成"
}

# 安装 Node.js 依赖
install_node_deps() {
    log_info "安装 Node.js 依赖..."
    
    pnpm install
    
    log_success "Node.js 依赖安装完成"
}

# 构建所有 packages
build_packages() {
    log_info "构建所有 packages..."
    
    # 构建 Python packages
    log_info "构建 Python packages..."
    
    local python_packages=("agentkit" "loguru-support")
    for package in "${python_packages[@]}"; do
        if [ -d "packages/$package" ]; then
            log_info "构建 packages/$package..."
            cd "packages/$package"
            
            # 激活虚拟环境
            source ../../.venv/bin/activate
            
            # 如果有构建脚本则执行
            if [ -f "pyproject.toml" ]; then
                # 安装当前包（开发模式）
                uv pip install -e .
                log_success "packages/$package 构建完成"
            fi
            
            cd "$PROJECT_ROOT"
        else
            log_warning "packages/$package 不存在，跳过"
        fi
    done
    
    # 构建 TypeScript packages
    log_info "构建 TypeScript packages..."
    
    local ts_packages=("fekit" "loglayer-support")
    for package in "${ts_packages[@]}"; do
        if [ -d "packages/$package" ]; then
            log_info "构建 packages/$package..."
            
            # 使用 pnpm 构建，确保依赖正确
            if pnpm --filter "$package" build; then
                log_success "packages/$package 构建完成"
            else
                log_error "packages/$package 构建失败"
                exit 1
            fi
        else
            log_warning "packages/$package 不存在，跳过"
        fi
    done
    
    log_success "所有 packages 构建完成"
}

# 构建所有 examples
build_examples() {
    if [ "$SKIP_EXAMPLES" = true ] || [ "$DEV_MODE" = true ]; then
        log_info "跳过 examples 构建（开发模式或明确跳过）"
        return 0
    fi
    
    log_info "构建所有 examples..."
    
    # 构建 Python examples
    log_info "构建 Python examples..."
    
    local python_examples=("python-backend" "loguru-example")
    for example in "${python_examples[@]}"; do
        if [ -d "examples/$example" ]; then
            log_info "设置 examples/$example..."
            cd "examples/$example"
            
            # 激活虚拟环境
            source ../../.venv/bin/activate
            
            # 如果有 pyproject.toml 则安装
            if [ -f "pyproject.toml" ]; then
                uv pip install -e .
                log_success "examples/$example 设置完成"
            fi
            
            cd "$PROJECT_ROOT"
        else
            log_warning "examples/$example 不存在，跳过"
        fi
    done
    
    # 构建 TypeScript examples（跳过 nextjs-app 的生产构建）
    log_info "设置 TypeScript examples..."
    
    local ts_examples=("loglayer-example")
    for example in "${ts_examples[@]}"; do
        if [ -d "examples/$example" ]; then
            log_info "构建 examples/$example..."
            if pnpm --filter "$example" build; then
                log_success "examples/$example 构建完成"
            else
                log_warning "examples/$example 构建失败，但继续执行"
            fi
        else
            log_warning "examples/$example 不存在，跳过"
        fi
    done
    
    # 特殊处理 nextjs-app：只验证依赖，不进行生产构建
    if [ -d "examples/nextjs-app" ]; then
        log_info "验证 examples/nextjs-app 依赖..."
        cd "examples/nextjs-app"
        
        # 检查关键模块是否能正确解析
        if node -e "require.resolve('@yai-nexus/fekit/client'); require.resolve('@yai-nexus/fekit/server')" 2>/dev/null; then
            log_success "examples/nextjs-app 依赖验证通过"
        else
            log_error "examples/nextjs-app 依赖验证失败"
            exit 1
        fi
        
        cd "$PROJECT_ROOT"
    fi
    
    log_success "所有 examples 设置完成"
}

# 主函数
main() {
    if [ "$DEV_MODE" = true ]; then
        echo "🚀 开发模式构建"
        echo "================"
    else
        echo "🚀 完整构建项目"
        echo "================"
    fi
    
    check_dependencies
    
    echo ""
    echo "🧹 清除缓存阶段"
    echo "================"
    clean_node_cache
    clean_python_cache
    
    echo ""
    echo "📦 依赖安装阶段"
    echo "================"
    setup_python_env
    install_node_deps
    
    echo ""
    echo "🔨 构建阶段"
    echo "==========="
    build_packages
    build_examples
    
    echo ""
    log_success "🎉 构建完成！"
    echo ""
    if [ "$DEV_MODE" = true ]; then
        echo "开发模式构建完成，接下来您可以："
        echo "  - 运行 pnpm dev:example:next 启动 Next.js 开发服务器"
        echo "  - 运行 pnpm dev:example:python 启动 Python 后端开发服务器"
    else
        echo "完整构建完成，接下来您可以："
        echo "  - 运行 pnpm dev:example:next 启动 Next.js 示例"
        echo "  - 运行 pnpm dev:example:python 启动 Python 后端示例"
        echo "  - 运行 pnpm test:logging 运行日志测试"
    fi
}

# 处理中断信号
trap 'log_error "构建被中断"; exit 1' INT TERM

# 执行主函数
main "$@"