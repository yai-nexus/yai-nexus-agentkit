# Monorepo 合并迁移计划

本文档详细说明了将 `yai-nexus-fekit` (前端) 仓库合并到 `yai-nexus-agentkit` (后端) 仓库，形成一个统一 Monorepo 的完整操作步骤。

## 1. 背景与目标

为了提升开发效率、简化依赖管理并实现原子化提交，我们决定将前后端两个独立的仓库合并为一个 Monorepo。

**核心目标:**
- **保留双方完整的 Git 提交历史**。
- **保留 `yai-nexus-agentkit` 的 GitHub 项目身份** (包括 Issues, PRs, Stars 等)。
- **建立清晰、可扩展的 Monorepo 目录结构**。
- **简化本地开发和 CI/CD 流程**。

## 2. 准备工作

**⚠️ 重要：在开始任何操作之前，请务必备份！**

为防止任何意外发生，请先克隆一份全新的 `yai-nexus-agentkit` 仓库作为备份。

```bash
# 在一个安全的目录下执行
git clone https://github.com/yai-nexus/yai-nexus-agentkit.git yai-nexus-agentkit-backup
```

所有操作都将在你本地的 `yai-nexus-agentkit` 工作副本中进行。

## 3. 目标目录结构

合并完成后，我们期望的目录结构如下：

```
/ (monorepo 根目录)
├── packages/
│   ├── agentkit/          # ⬅️ 所有 Python 后端代码
│   └── fekit/             # ⬅️ 所有前端 SDK 代码
│
├── examples/
│   └── nextjs-app/        # ⬅️ 前端示例应用
│
├── .gitignore
├── LICENSE
├── package.json           # ⬅️ 顶层 pnpm/node 配置
├── pnpm-workspace.yaml
├── README.md              # ⬅️ 全新的、统一的 README
└── ...
```

## 4. 详细操作步骤

请在 `yai-nexus-agentkit` 项目的根目录中，严格按顺序执行以下指令。

### 第 1 步：重构当前后端代码结构

首先，我们将所有现存的 Python 代码和相关文件移动到一个专门的 `packages/agentkit` 目录中，为前端代码腾出根目录空间。

```bash
# 1.1 创建目标目录
mkdir -p packages/agentkit

# 1.2 使用 git mv 移动文件以保留 Git 历史
# 注意：此处的列表应根据你仓库的实际文件进行调整
git mv src tests pyproject.toml configs debug_openrouter.py persistence_architecture.md examples packages/agentkit/

# 1.3 提交这次重构
git commit -m "refactor(core): Restructure agentkit into packages/agentkit"
```

### 第 2 步：添加并拉取前端仓库的历史

我们将 `yai-nexus-fekit` 仓库添加为一个临时的 "git remote"，然后拉取它的所有历史数据。

```bash
# 2.1 添加 fekit 仓库作为 remote，并命名为 "fekit"
git remote add fekit https://github.com/yai-nexus/yai-nexus-fekit.git

# 2.2 从 fekit remote 拉取所有分支和历史记录，但暂不合并
git fetch fekit
```

### 第 3 步：合并前端仓库历史

这是最关键的一步。我们将 `fekit` 的 `main` 分支历史合并到当前分支，但暂时不自动提交，以便我们手动整理文件。

```bash
# 3.1 执行合并
# --allow-unrelated-histories 是必需的，因为这两个项目最初没有共同的历史
# --no-commit 阻止 Git 自动创建一个混乱的合并提交，让我们有机会先整理文件
git merge fekit/main --allow-unrelated-histories --no-commit
```

### 第 4 步：手动整理合并后的文件结构

上一步执行后，`fekit` 的所有文件都被放到了根目录。现在我们需要手动将它们移动到正确的位置并解决文件冲突。

```bash
# 4.1. 将 fekit 的核心 SDK 包移动到 packages/ 目录下
# (原名是 packages/yai-nexus-fekit，我们重命名为 fekit 以保持简洁)
git mv packages/yai-nexus-fekit packages/fekit

# 4.2. 清理合并来的 examples 目录
# fekit 仓库带来了顶层的 examples/ 目录，其中包含 nextjs-app 和 python-backend。
# 我们保留 nextjs-app，并以此为准，删除与 agentkit 重复的 python-backend 示例。
git rm -r examples/python-backend

# 4.3. 移动 pnpm/Node.js 相关的配置文件到项目根目录
git mv package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json .

# 4.4. 处理其他根目录文件
# 检查根目录下是否有其他项目相关文件，如 CLAUDE.md。
# 将这些文件移动到它们所属的包中，以保持根目录清洁。
# 例如，如果 CLAUDE.md 是 agentkit 项目的，则执行：
git mv CLAUDE.md packages/agentkit/

# 4.5. 详细处理根目录的文件冲突与合并
# 你需要手动编辑以下文件，将 fekit 中的相关内容合理地合并到当前文件中。

# 4.5.1. .gitignore
# - 打开 fekit 的 .gitignore (在 fekit/main 分支的历史中查看)。
# - 将其内容追加到当前根目录的 .gitignore 文件末尾。
# - 检查并删除重复的条目。

# 4.5.2. LICENSE
# - 检查两个项目的 LICENSE 是否一致 (大概率都是 MIT)。
# - 如果一致，保留 agentkit 的 LICENSE 文件即可。

# 4.5.3. package.json
# - 这个文件从 fekit 移动而来，将成为整个 monorepo 的根 package.json。
# - 打开它并进行修改：
#   - 确保 "name": "yai-nexus-monorepo" (或一个合适的新名字)。
#   - 确保 "private": true，因为 monorepo 的根通常不发布。
#   - 检查 "scripts"，保留对整个工作区有用的命令 (如 lint, format)。
#   - 确保 "workspaces" 或 pnpm 的 "packages" 字段已在 pnpm-workspace.yaml 中正确定义。

# 4.5.4. README.md
# - 不要尝试逐行合并。
# - 以 agentkit 的 README 为基础，进行彻底重写，以反映这是一个包含前后端的 monorepo 项目。
# - 完成编辑后，将这些文件暂存：
git add .gitignore LICENSE package.json README.md
```

### 第 5 步：配置工作区并完成最终提交

文件结构已经正确，我们进行最后的配置和提交。

```bash
# 5.1 验证 pnpm-workspace.yaml 配置
# 打开 pnpm-workspace.yaml 文件，确保其内容如下，以识别所有包。
# 使用引号是更规范的 YAML 做法。
packages:
  - "packages/*"
  - "examples/*"

# 5.2 创建最终的合并提交
# 所有文件都整理好并暂存后，我们创建一个干净、有意义的提交
git commit -m "feat(core): Merge yai-nexus-fekit repository into a unified monorepo"
```

## 5. 后续操作

### 第 6 步：推送变更并清理

```bash
# 6.1 推送到远程主仓库 (yai-nexus-agentkit)
git push origin main

# 6.2 删除不再需要的 fekit remote
git remote remove fekit
```

### 第 7 步：归档旧的前端仓库

为了避免社区混淆和重复提 issue，必须将旧的 `yai-nexus/yai-nexus-fekit` 仓库归档。

1.  前往 `https://github.com/yai-nexus/yai-nexus-fekit`
2.  进入 `Settings` 标签页
3.  在 `General` 部分，拉到最下方找到 "Danger Zone"
4.  点击 `Archive this repository` 并按提示操作。

### 第 8 步：验证合并结果

迁移是否成功，需要通过实际的构建和测试来验证。

```bash
# 8.1 验证前端
# 首先，安装所有 JS/TS 依赖并链接工作区
pnpm install

# 构建 fekit SDK
pnpm --filter @yai-nexus/fekit build

# 构建前端示例应用
pnpm --filter nextjs-app build

# 如果以上命令全部成功，说明前端部分迁移成功。

# 8.2 验证后端
# 进入 agentkit 包目录
cd packages/agentkit

# 创建虚拟环境并安装依赖
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\activate # Windows

pip install -e ".[test]" # 安装可编辑模式和测试依赖

# 运行测试
pytest

# 如果测试全部通过，说明后端部分迁移成功。
cd ../.. # 返回根目录
```

### 第 9 步：更新 CI/CD 工作流程

这是一个关键的后续步骤，以确保自动化流程能够继续工作。

1.  **检查 CI/CD 配置文件**: 在 `.github/workflows/` 目录下查找现有的 GitHub Actions 工作流文件。
2.  **更新路径**: 修改工作流文件，以适应新的 monorepo 结构。
    -   如果你的测试或构建步骤有 `working-directory` 参数，请将其更新为 `packages/agentkit` 或 `packages/fekit`。
    -   修改所有指向旧路径的文件引用。
3.  **优化触发器 (可选)**:
    -   为了提高效率，你可以设置路径过滤器，使得 CI 作业仅在相关包的代码发生变更时才运行。例如，仅当 `packages/agentkit/**` 目录下的文件被修改时，才运行 Python 的测试。

---
至此，迁移工作全部完成。 