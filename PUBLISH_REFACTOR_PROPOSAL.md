# CI/CD 发布流程重构方案

本文档旨在分析当前 GitHub Actions 发布流程的现状，并提出三种可行的重构方案，以提高工作流的可维护性、可读性和可扩展性。

## 1. 当前现状分析

目前，我们有三个与发布相关的 GitHub Actions 工作流：
- `publish-all.yml`：当 `git tag` 以 `v` 开头时，发布所有 NPM 和 PyPI 包。
- `npm-publish.yml`：当 `git tag` 以特定包名（如 `fekit-v`）开头时，独立发布该 NPM 包。
- `pypi-publish.yml`：当 `git tag` 以特定包名（如 `agentkit-v`）开头时，独立发布该 PyPI 包。

这种结构存在以下主要问题：
- **代码冗余**：NPM 和 PyPI 的发布逻辑在 `publish-all.yml` 和各自独立的发布文件中被大量复制。
- **维护困难**：当需要更新依赖（如 Node.js 版本、pnpm 版本）或修改发布步骤时，需要在多个文件中进行同步修改，容易出错。
- **逻辑分散**：发布逻辑分散在三个文件中，需要通过 `git tag` 的命名约定来路由，新成员理解成本较高。

## 2. 重构方案

为了解决上述问题，我们提出以下三个重构方案。

---

### 方案一：使用可重用工作流 (Reusable Workflows)

这是 GitHub Actions 官方推荐的、用于在工作流之间共享代码的最佳实践。

#### 核心思想

创建两个独立的、可重用的工作流，一个用于发布 NPM 包，另一个用于发布 PyPI 包。然后创建一个主工作流，根据 `git tag` 的不同，调用这两个可重用的工作流来执行发布。

#### 实现步骤

1.  **创建可重用的 NPM 发布工作流 (`.github/workflows/reusable-npm-publish.yml`)**:
    - 此文件定义了发布一个 NPM 包所需的所有步骤。
    - 它通过 `workflow_call` 触发，并接收 `package-name` 和 `package-path` 作为输入参数。

2.  **创建可重用的 PyPI 发布工作流 (`.github/workflows/reusable-pypi-publish.yml`)**:
    - 类似地，此文件定义了发布 PyPI 包的完整逻辑。
    - 也通过 `workflow_call` 触发，并接收 `package-name` 和 `package-path` 作为输入。

3.  **创建主发布工作流 (`.github/workflows/publish-packages.yml`)**:
    - 这是唯一的发布入口文件，取代现有的三个文件。
    - 它包含多个 `job`，每个 `job` 负责一种发布场景（如发布 fekit、发布 agentkit、发布所有包）。
    - 每个 `job` 通过 `uses:` 语法调用相应的可重用工作流，并传递所需的参数和 `secrets`。

#### 优点

- **高度模块化和 DRY**：发布逻辑被完美封装，任何修改只需在可重用工作流中进行一次。
- **逻辑清晰集中**：所有发布场景都在一个主文件中定义，一目了然。
- **极佳的可扩展性**：添加新包时，只需在主文件中增加一个调用相应可重用工作流的 `job` 即可。
- **安全性好**：通过 `secrets: inherit` 明确地传递密钥，符合最小权限原则。

#### 缺点

- **语法稍复杂**：需要理解 `workflow_call`、`inputs` 和 `secrets` 的传递机制。

---

### 方案二：使用复合操作 (Composite Actions)

复合操作允许你将多个 `run` 步骤打包成一个可在同一仓库内复用的操作。

#### 核心思想

将 NPM 和 PyPI 的发布步骤分别封装成两个本地的复合操作。主工作流则像使用 `actions/checkout@v4` 一样使用这些本地操作。

#### 实现步骤

1.  **创建 NPM 复合操作 (`.github/actions/npm-publish/action.yml`)**:
    - 在 `.github/actions/npm-publish` 目录下创建 `action.yml`。
    - 文件中定义 `inputs`（如 `package-name`, `package-path`, `node-version`）和 `runs`（使用 `composite` 类型），其中包含所有 `run` 步骤。

2.  **创建 PyPI 复合操作 (`.github/actions/pypi-publish/action.yml`)**:
    - 类似地，在 `.github/actions/pypi-publish` 目录下创建 `action.yml` 来封装 PyPI 的发布步骤。

3.  **创建主发布工作流 (`.github/workflows/publish-packages.yml`)**:
    - 主工作流定义多个 `job`。
    - 在每个 `job` 的 `steps` 中，通过 `uses: ./.github/actions/npm-publish` 或 `uses: ./.github/actions/pypi-publish` 来调用复合操作，并通过 `with` 传递参数。

#### 优点

- **封装性好**：将一系列命令封装成一个步骤，简化了主工作流的 `steps` 部分。
- **本地复用**：非常适合在单个仓库内共享重复的脚本序列。

#### 缺点

- **能力受限**：复合操作不能直接调用其他操作（`uses`），所有逻辑必须是 `run` 命令。这使得它不如可重用工作流灵活。
- **日志可读性**：整个复合操作在日志中显示为一个大的步骤，不如可重用工作流中分离的 `job` 清晰。

---

### 方案三：使用矩阵策略 (Matrix Strategy)

矩阵策略允许你使用变量来自动创建多个 `job`，非常适合对一系列相似目标执行相同操作的场景。

#### 核心思想

创建两个 `job`，一个用于 NPM，一个用于 PyPI。每个 `job` 内部使用 `strategy: matrix` 来定义所有待发布的包列表。通过 `if` 条件来控制是运行矩阵中的所有项，还是只运行特定的一项。

#### 实现步骤

1. **创建统一的发布工作流 (`.github/workflows/publish-packages.yml`)**
   - **NPM 发布 Job**:
     - 定义一个 `matrix`，包含每个 NPM 包的信息（如 `name`, `path`, `tag_prefix`）。
     - `if` 条件会检查触发的 `git tag`：
       - 如果是 `v*`，则所有矩阵组合都会执行。
       - 如果是 `fekit-v*` 或 `loglayer-support-v*`，则只有 `matrix.tag_prefix` 匹配的组合会执行。
     - `steps` 中使用 `matrix.name` 和 `matrix.path` 来执行构建和发布。
   - **PyPI 发布 Job**:
     - 采用与 NPM Job 完全相同的矩阵逻辑，只是矩阵内容和发布步骤不同。

#### 优点

- **非常 DRY**：发布步骤只定义一次，矩阵负责生成所有 `job`。
- **易于扩展**：添加新包只需在 `matrix` 定义中增加一行。
- **高度并行**：矩阵中的所有 `job` 默认并行执行，可以加快“发布所有”场景的速度。

#### 缺点

- **条件逻辑复杂**：`if` 条件需要精心设计，以正确处理“全部发布”和“独立发布”的场景，这可能会变得难以阅读和维护。
- **灵活性较低**：如果不同包的发布步骤有细微差异，就需要在 `steps` 中添加额外的 `if` 条件，进一步增加复杂性。

## 3. 总结与建议

| 特性 | 方案一 (Reusable Workflows) | 方案二 (Composite Actions) | 方案三 (Matrix Strategy) |
| :--- | :--- | :--- | :--- |
| **代码复用** | 非常高 (逻辑级) | 高 (脚本级) | 非常高 (Job 级) |
| **可维护性** | 高 | 中 | 中（`if` 逻辑可能变复杂） |
| **灵活性** | 非常高 | 低 | 中 |
| **推荐指数** | ★★★★★ | ★★★☆☆ | ★★★★☆ |

**综合来看，我们强烈推荐采用【方案一：使用可重用工作流 (Reusable Workflows)】。**

它是目前 GitHub Actions 中最强大、最灵活的模块化方案，完美地平衡了代码复用、可读性和可扩展性。虽然初次接触时有一点学习成本，但它能为项目的长期健康发展提供最坚实的基础。 