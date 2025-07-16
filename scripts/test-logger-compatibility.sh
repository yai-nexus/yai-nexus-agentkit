#!/bin/bash

# Logger 兼容性测试脚本
# 自动测试新旧 logger 的兼容性

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Logger 兼容性自动测试${NC}"
echo "========================================"

# 检查 Next.js 服务是否运行
check_nextjs_service() {
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Next.js 服务正在运行${NC}"
        return 0
    else
        echo -e "${RED}❌ Next.js 服务未运行${NC}"
        echo "请先运行: ./scripts/start-nextjs.sh"
        return 1
    fi
}

# 测试 API 端点
test_api() {
    local endpoint=$1
    local name=$2
    
    echo -e "\n${YELLOW}🔧 测试 $name...${NC}"
    
    # 发送测试请求
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"test": "compatibility"}' \
        "http://localhost:3000/api/$endpoint" 2>/dev/null)
    
    # 分离响应体和状态码
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "  ✅ $name 测试成功 (HTTP $http_code)"
        
        # 解析 JSON 响应
        success=$(echo "$response_body" | grep -o '"success":[^,}]*' | cut -d':' -f2 | tr -d ' ')
        if [ "$success" = "true" ]; then
            echo -e "  ✅ Logger 功能正常"
            return 0
        else
            echo -e "  ❌ Logger 功能异常"
            echo "  响应: $response_body"
            return 1
        fi
    else
        echo -e "  ❌ $name 测试失败 (HTTP $http_code)"
        echo "  响应: $response_body"
        return 1
    fi
}

# 主测试流程
main() {
    # 检查服务状态
    if ! check_nextjs_service; then
        exit 1
    fi
    
    echo -e "\n${BLUE}开始 API 测试...${NC}"
    
    # 测试结果统计
    total_tests=0
    passed_tests=0
    
    # 测试旧版 logger
    total_tests=$((total_tests + 1))
    if test_api "test-old-logger" "旧版 Logger (pino-support)"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 测试新版 logger
    total_tests=$((total_tests + 1))
    if test_api "test-new-logger" "新版 Logger (loglayer-support)"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 显示测试结果
    echo -e "\n${BLUE}📊 测试结果统计${NC}"
    echo "========================================"
    echo -e "总测试数: $total_tests"
    echo -e "通过测试: $passed_tests"
    echo -e "失败测试: $((total_tests - passed_tests))"
    
    if [ $passed_tests -eq $total_tests ]; then
        echo -e "\n${GREEN}🎉 所有测试通过！${NC}"
        echo -e "${GREEN}✨ Logger 兼容性验证成功${NC}"
        
        echo -e "\n${YELLOW}📋 测试总结:${NC}"
        echo "  • 旧版 Logger (pino-support) 工作状态"
        echo "  • 新版 Logger (loglayer-support) 工作状态"
        echo "  • API 完全兼容，可以无缝迁移"
        
        return 0
    else
        echo -e "\n${RED}❌ 部分测试失败${NC}"
        echo -e "${YELLOW}💡 建议检查:${NC}"
        echo "  • Next.js 应用日志: tail -f logs/current/nextjs-service.log"
        echo "  • 浏览器控制台错误"
        echo "  • 依赖包安装情况"
        
        return 1
    fi
}

# 运行测试
main "$@"
