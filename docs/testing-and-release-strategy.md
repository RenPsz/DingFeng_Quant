# 测试与 CI/CD 发布策略

本文档定义定风量化当前研究内核，以及后续后端、前端和 LLM 解说层的测试、质量门禁与发布流程。目标不是追求一个脱离业务的覆盖率数字，而是保证四件事：

1. 因子计算和回测结果可重复、可解释、无未来函数。
2. 本地 SQLite 缓存与 AkShare 数据源故障不会污染研究结果。
3. 关键研究结论有可执行的回归测试和固定样本。
4. 每个合并和版本发布都经过自动化检查，并且可以回滚到上一个已验证版本。

## 1. 测试边界与原则

当前仓库是 Python 研究内核，不是自动交易系统。测试默认使用离线合成数据和仓库内固定 fixture；真实行情网络请求不进入普通 PR 门禁。任何测试都不得依赖当前日期、网络可用性、AkShare 返回顺序或本机已有缓存。

量化特有的测试原则：

- **时间因果性**：信号只能使用当前日及之前的数据，重点检查 rolling、shift、未来回撤标签和回测持仓滞后。
- **索引对齐**：输入的日期、Series index 和输出必须保持明确对齐；禁止依靠偶然的整数索引广播。
- **缺失值语义**：窗口未满、常数序列、无有效股票和未来数据不足必须返回约定的 NaN/False，而不是静默填成有效信号。
- **缓存隔离**：测试使用临时 SQLite 文件；不得读取或写入 `src/data/cache/market.db`。
- **结果可复现**：研究样本、参数、Python 版本、依赖版本和结果摘要都应能被再次构造。
- **外部依赖可替换**：AkShare、文件系统和时钟通过 mock 或临时目录隔离；网络集成测试只手动或定时运行。

## 2. 测试金字塔

### 2.1 单元测试：约 70%

单元测试针对无网络、无数据库副作用的函数，运行目标是秒级完成。每个函数至少覆盖正常路径、边界条件、空值/常数值和参数变化。

| 模块 | 核心对象 | 必测行为 |
| --- | --- | --- |
| `signals/autocorr.py` | `_lag_autocorr`, `autocorr_factor` | 正/负相关、常数序列、窗口未满、lag 越界、输出索引和范围 |
| `signals/energy.py` | `energy_ratio` | 短/长窗口、长期能量为 0、窗口未满、名称和索引 |
| `signals/spectrum.py` | `_single_window_ratio`, `high_freq_ratio` | 零能量、频率截止点、输出范围 `[0, 1]`、首日收益缺失 |
| `signals/traditional.py` | `momentum_factor`, `traditional_factors` | pct-change 对齐、窗口边界、汇总列名 |
| `signals/breadth.py` | `ma_above_ratio` | 股票缺列、重复日期、有效股票数不足、比例边界 |
| `signals/evaluate.py` | `future_drawdown`, alert 函数、`evaluate` | 未来窗口、尾部无标签、零预警、eligible 掩码、lift 基准 |
| `strategy.py` | `ma_cross_signal` | 首日空仓、均线交叉、shift 防未来函数、输入索引保持不变 |
| `backtest.py` | `run_backtest`, `calculate_metrics` | 手续费、换仓、起始日归一化、零波动 Sharpe、回撤和年化 |
| `plot.py` | `_drawdown` | 净值新高、回撤为零、输入不变；绘图函数只做 smoke test |

测试数据使用小型确定性价格序列，例如单调上涨、上涨后回撤、交替收益和常数价格。不要用随机数据作为唯一断言依据；如需随机数据，固定 seed 并同时保留性质测试。

### 2.2 集成测试：约 20%

集成测试验证模块边界和持久化协议，仍然默认离线运行。

**SQLite 存储层**

- 建表是幂等的，临时数据库可重复初始化。
- `upsert_daily` 对相同 `(symbol, date)` 幂等覆盖，日期读取升序。
- `read_daily` 能恢复日期类型和 OHLCV 字段。
- 交易日历的写入、按日期查询和空库返回值正确。
- 数据库异常不会让测试污染其他用例。

**数据接入层**

- mock `ak.stock_zh_index_daily` 和 `ak.stock_zh_a_daily`，验证首次全量、已有缓存增量、`sync_latest=False` 和 `force_refresh` 分支。
- mock 交易日历，验证已是最新时跳过请求。
- 验证 `_clean` 的日期排序、重复日期保留最后一条和数值转换。
- 验证交易所股票列表字段兼容、ST 过滤和 fallback 行为。

**跨模块研究流程**

- 固定行情 DataFrame -> 因子 -> 预警 -> 评估表，验证长度、索引、列名和结果类型。
- 固定行情 DataFrame -> 均线持仓 -> 回测 -> 指标，验证回测首日、换仓手续费和净值归一化。

### 2.3 端到端测试：约 10%

端到端测试从用户可调用入口验证离线完整流程。当前入口是 `src/main.py`，因此 E2E 用例应 mock `refresh_indices` 和 `get_stock_data`，使用固定行情运行 `main()`，检查：

- 能够完成数据准备、传统因子计算和评估输出。
- 不触发真实网络请求。
- 输出包含最新因子快照和评估结果。
- 空数据、数据列缺失和因子有效样本不足时失败方式明确。

未来加入 FastAPI/React/LLM 后，E2E 扩展为：

- API 健康检查、行情查询、因子查询、回测查询和错误响应契约。
- 前端 Dashboard 首屏加载、筛选标的、切换时间区间、空态/错误态。
- LLM 只根据后端结构化数据解说，不可自行生成未出现在数据中的价格预测、因子值或预警等级。

### 2.4 外部服务测试：独立于 PR

真实 AkShare 测试使用 `@pytest.mark.network`，只在 `workflow_dispatch` 或每日定时工作流运行。它们检查接口字段、响应可解析性和最近交易日更新，不断言具体行情数值。外部服务失败只标记为数据源告警，不阻塞普通代码合并；若字段契约变化，则由维护者升级 fixture 和适配器。

## 3. 已知缺陷的回归门禁

路线图中列出的四项缺陷必须遵循“先写失败测试，再改实现”的流程：

1. qfq 增量缓存：复权基准变化时不能拼接不一致的旧序列。
2. `future_drawdown`：未来不足完整 horizon 的尾部必须为 NaN，并从 eligible 中剔除。
3. SQLite 连接：事务完成后连接必须关闭，避免长时间进程的文件句柄泄漏。
4. `force_refresh`：刷新前清理旧 symbol 数据；`_clean` 不得原地修改调用方 DataFrame。

这些测试必须单独标记为回归用例，并在 CI 中执行。修复前可在 issue 或专项分支保留红灯，但不得把预期失败测试直接合并到主分支；合并时应同时提交测试和实现修复。

## 4. 测试数据与 fixture 管理

目录约定：

```text
tests/
├── conftest.py              # 公共 fixture、固定日期和合成行情
├── fixtures/                # 小型、脱敏、版本化的 CSV/JSON 样本
├── unit/                    # 纯函数测试
├── integration/             # SQLite、mock AkShare、跨模块测试
└── e2e/                     # 离线用户流程
```

fixture 要求：

- 小于 1 MB，日期固定，字段明确，禁止提交真实用户数据和本地数据库。
- 每个 fixture 写明来源、生成脚本、时间范围和预期用途。
- 关键研究结论使用固定 fixture 做回归；不直接把线上最新行情结果当测试金标准。
- 大型历史数据作为 CI 外部 artifact 或可重建实验输入，不进入 Git。

## 5. CI 质量门禁

`.github/workflows/ci.yml` 在以下事件运行：对 `main` 的 Pull Request、推送到 `main` 和手动触发。当前门禁顺序为：

1. Python 3.13 环境和锁定依赖安装。
2. `ruff check .`。
3. `python -m pytest`，覆盖 unit/integration/e2e 离线测试。

分支保护建议：`main` 禁止直接推送；要求 CI job 通过、至少一名审查者批准、解决 review conversation 后才允许合并。依赖升级使用独立 PR，并要求完整测试通过。

未来测试规模增加后再加入：

- `pytest-cov` 覆盖率报告，先报告后门禁；稳定后为纯计算模块设置 85% 行覆盖率下限。
- `mypy` 或 pyright 类型检查。
- `pip-audit` 依赖漏洞扫描。
- 变异测试只在夜间任务运行，不阻塞普通 PR。

## 6. 发布流水线

`.github/workflows/release.yml` 在推送符合 `vMAJOR.MINOR.PATCH` 的 tag 时运行：

1. 安装生产和开发依赖。
2. 重新执行 lint 和完整离线测试，不能复用 PR 的旧结果。
3. 从该 tag 构建源码归档 `DingFeng_Quant-vX.Y.Z.tar.gz`。
4. 使用 GitHub CLI 创建带自动生成变更说明的 GitHub Release。

版本规则：

- `MAJOR`：研究结果语义、输入输出契约或数据兼容性发生破坏性变化。
- `MINOR`：新增因子、数据源、分析能力或向后兼容的工作流。
- `PATCH`：bug 修复、文档、测试和不改变研究结论的工程修正。

发布前检查清单：

- changelog 已记录变更、影响范围和迁移说明。
- 所有研究参数和结果来源可追溯。
- CI 通过，工作树干净，tag 指向已验证 commit。
- 无本地数据库、缓存、密钥和 Office 大文件进入提交。

## 7. 回滚与故障处理

发布失败时不移动已存在的 tag。代码回滚采用上一个已验证 tag 创建 hotfix 分支，修复后发布递增 PATCH 版本；不要重写公共历史。数据问题与代码问题分开处理：

- 代码回归：定位到 commit，补回归测试，发布 PATCH。
- AkShare 字段或网络故障：保留最近有效缓存，记录数据源告警，不把空数据当成 0 或正常行情。
- 研究结果变化：保留旧结果 artifact，说明数据范围、参数、依赖和算法变化后再更新结论。

## 8. Git 管理流程

推荐顺序：

```bash
git switch -c codex/test-strategy-ci
ruff check .
python -m pytest
git diff --check
git add docs/testing-and-release-strategy.md .github/workflows pyproject.toml requirements-dev.txt tests
git commit -m "chore: 建立测试策略与CI发布流水线"
git push -u origin codex/test-strategy-ci
```

本次任务应先完成并审阅文档，再提交配置和测试代码。提交保持单一目的；若后续修复已知缺陷，应使用独立的 `fix(...)` 提交，并在 PR 中关联对应回归测试。

## 9. 当前落地范围与后续任务

本仓库当前落地：pytest 配置、开发依赖、离线测试目录、CI、tag 发布工作流和本文档。下一步按优先级补齐：

1. 为四个已知缺陷逐一添加失败回归测试并修复实现。
2. 增加固定 fixture 和完整 unit/integration/e2e 测试实现。
3. 将 `src/` 迁移为可安装包 `src/dfquant/`，使 CI 使用 `pip install -e .`。
4. 引入覆盖率、类型检查、依赖安全扫描和定时网络契约测试。

