#!/bin/bash

# 统一测试脚本
# 替代：test-end-to-end.sh, test-logger-compatibility.sh

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
    echo -e "${BLUE}🧪 统一测试脚本${NC}"
    echo "用法: $0 <test-type> [options]"
    echo ""
    echo "测试类型:"
    echo "  unit              - 单元测试"
    echo "  build             - 构建测试"
    echo "  integration       - 集成测试"
    echo "  compatibility     - 兼容性测试"
    echo "  all               - 所有测试 (默认)"
    echo ""
    echo "选项:"
    echo "  --verbose         - 详细输出"
    echo "  --project <name>  - 只测试特定项目"
    echo ""
    echo "示例:"
    echo "  $0 all            - 运行所有测试"
    echo "  $0 build          - 只运行构建测试"
    echo "  $0 unit --project loglayer-support"
}

# 测试统计
total_tests=0
passed_tests=0
verbose=false
target_project=""

# 记录测试结果
record_test() {
    local test_name=$1
    local result=$2
    
    total_tests=$((total_tests + 1))
    if [ "$result" = "0" ]; then
        passed_tests=$((passed_tests + 1))
        echo -e "  ✅ $test_name"
    else
        echo -e "  ❌ $test_name"
    fi
}

# 运行 Nx 命令
run_nx_command() {
    local target=$1
    local project=$2
    local description=$3
    
    if [ -n "$project" ]; then
        if $verbose; then
            nx $target $project
        else
            nx $target $project > /dev/null 2>&1
        fi
    else
        if $verbose; then
            nx run-many --target=$target --all
        else
            nx run-many --target=$target --all > /dev/null 2>&1
        fi
    fi
}

# 单元测试
run_unit_tests() {
    echo -e "${YELLOW}🧪 单元测试${NC}"
    echo "----------------------------------------"
    
    if [ -n "$target_project" ]; then
        echo "测试项目: $target_project"
        if run_nx_command "test" "$target_project" "单元测试"; then
            record_test "$target_project 单元测试" 0
        else
            record_test "$target_project 单元测试" 1
        fi
    else
        # 测试所有有测试目标的项目
        for project in loglayer-support loguru-support agentkit; do
            echo "测试项目: $project"
            if run_nx_command "test" "$project" "单元测试"; then
                record_test "$project 单元测试" 0
            else
                record_test "$project 单元测试" 1
            fi
        done
    fi
}

# 构建测试
run_build_tests() {
    echo -e "${YELLOW}🔧 构建测试${NC}"
    echo "----------------------------------------"
    
    if [ -n "$target_project" ]; then
        echo "构建项目: $target_project"
        if run_nx_command "build" "$target_project" "构建测试"; then
            record_test "$target_project 构建" 0
        else
            record_test "$target_project 构建" 1
        fi
    else
        # 构建所有项目
        echo "构建所有项目..."
        if run_nx_command "build" "" "构建测试"; then
            record_test "所有项目构建" 0
        else
            record_test "所有项目构建" 1
        fi
    fi
}

# 集成测试
run_integration_tests() {
    echo -e "${YELLOW}🔗 集成测试${NC}"
    echo "----------------------------------------"
    
    # 测试 loglayer-example 的集成功能
    echo "测试 loglayer-example 集成..."
    cd examples/loglayer-example
    if npm run test:all > /dev/null 2>&1; then
        record_test "loglayer-example 集成测试" 0
    else
        record_test "loglayer-example 集成测试" 1
    fi
    cd "$PROJECT_ROOT"
}

# 兼容性测试
run_compatibility_tests() {
    echo -e "${YELLOW}🔄 兼容性测试${NC}"
    echo "----------------------------------------"
    
    # 检查服务是否运行
    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "启动 Next.js 服务进行兼容性测试..."
        ./scripts/services.sh start nextjs
        sleep 5
    fi
    
    # 测试 API 兼容性
    echo "测试 API 兼容性..."
    
    # 测试新版 Logger
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"test": "compatibility"}' \
        "http://localhost:3000/api/logging-demo" 2>/dev/null)
    
    http_code=$(echo "$response" | tail -n1)
    if [ "$http_code" = "200" ]; then
        record_test "Logger API 兼容性" 0
    else
        record_test "Logger API 兼容性" 1
    fi
}

# 显示测试结果
show_results() {
    echo -e "\n${BLUE}📊 测试结果统计${NC}"
    echo "========================================"
    echo -e "总测试数: $total_tests"
    echo -e "通过测试: $passed_tests"
    echo -e "失败测试: $((total_tests - passed_tests))"
    
    if [ $total_tests -gt 0 ]; then
        pass_rate=$((passed_tests * 100 / total_tests))
        echo -e "通过率: ${pass_rate}%"
    fi
    
    echo
    
    if [ $passed_tests -eq $total_tests ]; then
        echo -e "${GREEN}🎉 所有测试通过！${NC}"
        return 0
    else
        echo -e "${RED}❌ 部分测试失败${NC}"
        return 1
    fi
}

# 主逻辑
main() {
    local test_type=${1:-"all"}
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose)
                verbose=true
                shift
                ;;
            --project)
                target_project="$2"
                shift 2
                ;;
            unit|build|integration|compatibility|all)
                test_type="$1"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    echo -e "${BLUE}🧪 开始测试...${NC}"
    echo "测试类型: $test_type"
    if [ -n "$target_project" ]; then
        echo "目标项目: $target_project"
    fi
    echo
    
    case $test_type in
        unit)
            run_unit_tests
            ;;
        build)
            run_build_tests
            ;;
        integration)
            run_integration_tests
            ;;
        compatibility)
            run_compatibility_tests
            ;;
        all)
            run_build_tests
            echo
            run_unit_tests
            echo
            run_integration_tests
            echo
            run_compatibility_tests
            ;;
        *)
            usage
            exit 1
            ;;
    esac
    
    show_results
}

main "$@" 