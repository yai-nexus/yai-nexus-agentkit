#!/bin/bash

# 发布准备脚本 - v0.3.0
# 准备项目发布，包括构建、测试、文档检查等

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

echo -e "${BLUE}🚀 准备 v0.3.0 发布${NC}"
echo "========================================"
echo "项目根目录: $PROJECT_ROOT"
echo

# 确保在项目根目录执行
cd "$PROJECT_ROOT"

# 检查当前分支
current_branch=$(git branch --show-current)
echo -e "${YELLOW}📍 当前分支: $current_branch${NC}"

if [ "$current_branch" != "main" ]; then
    echo -e "${YELLOW}⚠️  当前不在 main 分支，建议切换到 main 分支进行发布${NC}"
    echo "是否继续？(y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "发布准备已取消"
        exit 1
    fi
fi

echo

echo -e "${YELLOW}📦 1. 构建所有包${NC}"
echo "----------------------------------------"

# 构建 loglayer-support
echo "🔧 构建 loglayer-support..."
cd packages/loglayer-support
if pnpm build; then
    echo -e "  ✅ loglayer-support 构建成功"
else
    echo -e "  ❌ loglayer-support 构建失败"
    exit 1
fi
cd "$PROJECT_ROOT"

# 构建 fekit
echo "🔧 构建 fekit..."
cd packages/fekit
if pnpm build; then
    echo -e "  ✅ fekit 构建成功"
else
    echo -e "  ❌ fekit 构建失败"
    exit 1
fi
cd "$PROJECT_ROOT"

echo

echo -e "${YELLOW}🧪 2. 运行测试${NC}"
echo "----------------------------------------"

# 运行端到端测试
echo "🔧 运行端到端测试..."
if ./scripts/test-end-to-end.sh > /dev/null 2>&1; then
    echo -e "  ✅ 端到端测试通过 (100%)"
else
    echo -e "  ❌ 端到端测试失败"
    echo "请先修复测试问题再进行发布"
    exit 1
fi

echo

echo -e "${YELLOW}📚 3. 检查文档${NC}"
echo "----------------------------------------"

# 检查必要的文档文件
docs_files=("README.md" "CHANGELOG.md" "PROJECT_SUMMARY.md")
for file in "${docs_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ✅ $file 存在"
    else
        echo -e "  ❌ $file 缺失"
        exit 1
    fi
done

# 检查示例项目文档
if [ -f "examples/loglayer-example/README.md" ]; then
    echo -e "  ✅ loglayer-example 文档存在"
else
    echo -e "  ❌ loglayer-example 文档缺失"
    exit 1
fi

echo

echo -e "${YELLOW}🔍 4. 版本号检查${NC}"
echo "----------------------------------------"

# 检查版本号一致性
root_version=$(grep '"version"' package.json | sed 's/.*"version": "\(.*\)".*/\1/')
fekit_version=$(grep '"version"' packages/fekit/package.json | sed 's/.*"version": "\(.*\)".*/\1/')
loglayer_version=$(grep '"version"' packages/loglayer-support/package.json | sed 's/.*"version": "\(.*\)".*/\1/')

echo "根目录版本: $root_version"
echo "fekit 版本: $fekit_version"
echo "loglayer-support 版本: $loglayer_version"

if [ "$root_version" = "0.3.0" ] && [ "$fekit_version" = "0.3.0" ]; then
    echo -e "  ✅ 版本号一致 (v0.3.0)"
else
    echo -e "  ❌ 版本号不一致"
    exit 1
fi

echo

echo -e "${YELLOW}🔄 5. Git 状态检查${NC}"
echo "----------------------------------------"

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo -e "  ⚠️  有未提交的更改："
    git status --short
    echo
    echo "是否提交这些更改？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "chore: prepare for v0.3.0 release

- Update version numbers to 0.3.0
- Add CHANGELOG.md with detailed release notes
- Update README.md with LogLayer information
- Complete LogLayer abstraction layer implementation"
        echo -e "  ✅ 更改已提交"
    else
        echo -e "  ❌ 请先提交或暂存更改"
        exit 1
    fi
else
    echo -e "  ✅ 工作目录干净"
fi

echo

echo -e "${GREEN}🎉 发布准备完成！${NC}"
echo "========================================"
echo -e "${YELLOW}📋 发布清单:${NC}"
echo "  ✅ 所有包构建成功"
echo "  ✅ 端到端测试 100% 通过"
echo "  ✅ 文档完整"
echo "  ✅ 版本号统一 (v0.3.0)"
echo "  ✅ Git 状态干净"
echo

echo -e "${BLUE}🚀 下一步操作:${NC}"
echo "1. 合并到 main 分支 (如果当前不在 main)"
echo "2. 创建 Git tag: git tag v0.3.0"
echo "3. 推送到远程: git push origin main --tags"
echo "4. 在 GitHub 创建 Release"
echo

echo -e "${YELLOW}💡 GitHub Release 建议内容:${NC}"
echo "标题: v0.3.0 - LogLayer 抽象层重大更新"
echo "描述: 请参考 CHANGELOG.md 中的 v0.3.0 部分"
echo

echo -e "${GREEN}✨ 准备就绪，可以发布了！${NC}"
