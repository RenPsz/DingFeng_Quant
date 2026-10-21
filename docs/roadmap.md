# 项目规划

## 项目定位
**个人投资决策辅助系统**：用量化数据把投资思路系统化，通过多维度市场结构展示 + 中长期风险预警，辅助主观判断。
金融量化分析系统：策略回测 + (核心)多维度市场结构展示与中长期风险预警 + LLM交互解读 + 前端可视化。

系统不以预测短期涨跌为目标，而是向用户展示市场当下的结构状态，并在结构性风险积累时给出预警。
具体分两层：
- **温度计层（现状描述）**：频域高频占比、时域能量比——回答"市场现在处于什么状态"，供可视化和 LLM 解读
- **预警层（结构判断）**：自相关趋势动能因子、动量低分位弱信号、后续传统多因子（估值/市场宽度/资金流向等）——回答"市场是否有中长期风险"，驱动预警等级

## 短期待办（按开发顺序）

### 第零阶段：工程修复（先于新因子开发）

**已知 bug：**
- [ ] `data.py`：前复权(qfq)数据增量缓存失真——除权除息后 qfq 全序列重算，但缓存只追加新行，新旧数据复权基准不一致。改为缓存不复权价 + 复权因子，或增量时校验重叠日价格，不一致则全量刷新
- [ ] `evaluate.py`：`future_drawdown` 在尾部窗口不足 horizon 时仍返回值，`eligible` 未剔除这约 horizon 行截断样本，与 docstring 不符。改为仅 `i + horizon < n` 时输出
- [ ] `storage.py`：`with sqlite3.connect()` 只提交事务不关闭连接，用 `contextlib.closing` 包装
- [ ] `data.py`：`force_refresh` 只 upsert 不删除旧行，应先 `DELETE WHERE symbol=?`；`_clean` 原地修改入参，开头加 `copy()`

**测试：**
- [ ] 引入 `pytest`，用合成数据覆盖纯函数：`future_drawdown`、各 `*_alert`、`evaluate`、`ma_cross_signal`、`run_backtest`、`calculate_metrics`
- [ ] 数据层 mock akshare，测试增量缓存、交易日跳过、`force_refresh` 逻辑（上面两个 data bug 先写失败用例再修）

**工程化：**
- [ ] 包结构改为 `src/dfquant/`，`pyproject.toml` 补 `[project]`，`pip install -e .` + `python -m dfquant` 运行，去掉 `cd src`
- [ ] `signals/evaluate.py` 迁出到 `research/`（详见 `architecture-suggestions.md`）
- [ ] ruff 规则追加 `B`、`UP`、`NPY`、`PD`、`SIM`
- [ ] GitHub Actions：push 时跑 `ruff check` + `pytest`
- [ ] 数据层 `print` 改 `logging`；网络请求加重试/超时，批量拉取单只失败不中断整批

**可复现性：**
- [ ] 自相关 1.45x 结论补可复跑入口（如 `experiments/autocorr_hs300.py`），参数与结果输出到 `results/*.json`
- [ ] 窗口/horizon/阈值等散落的默认参数收进统一配置 `dataclass`
- [ ] 预警评估加事件去重（冷却期），并用 block bootstrap 给 lift 加置信区间——当前逐日预警高度自相关，`n_alerts` 是天数而非独立事件

**性能（低优先级）：**
- [ ] `autocorr.py` 改 `r.rolling(w-1).corr(r.shift(lag))`；`spectrum.py`、`future_drawdown` 用 `sliding_window_view` 向量化

### 第一阶段：迭代填充因子
- [x] 传统动量因子验证（`momentum_low` 弱预警增益，保留为候选因子）
- [ ] 在数据层接入更多种类的基础数据，增加市场数据宽度
- [ ] 估值因子（PE/PB/股债性价比等）
- [ ] 市场宽度因子（60 日均线以上占比低位信号验证失败，后续改试宽度快速恶化/新高新低/背离类信号）
- [ ] 资金流向与板块轮动因子
- [ ] 输入股票号自动识别市场

### 第二阶段：后端骨架 + 多因子融合预警
- [ ] 重构为 FastAPI 后端架构（backend/ 目录）
- [ ] 规则引擎：多因子融合 → 四级预警（无/关注/警惕/危险）
- [ ] 统一 API 返回格式

### 第三阶段：前端仪表盘骨架
- [ ] React + TypeScript 项目初始化
- [ ] TradingView 轻量级图表接入
- [ ] 仪表盘页面：K线 + 因子走势 + 预警指示灯
- [ ] 前后端联调

## 因子验证结论（已完成）
- **自相关转负**：捕捉趋势动能结构的衰竭，对中长期重大回撤有显著领先性（命中率提升 1.45x，优于 RSI/布林带），作为**预警主力**。
- **动量低分位**：`momentum_low` 具备弱预警增益（lift 1.119），保留为候选预警因子，但不能单独驱动高等级预警。
- **能量比 / 高频占比**：幅度类因子，是波动的同期产物、无预警领先性。定位为**温度计**——展示"市场现在处于高噪声/高波动状态"，供可视化和 LLM 对话解读，不驱动预警等级。
- **市场宽度低位（60 日均线以上占比低分位）**：lift 0.758，未跑赢基准，不进入预警层；后续只保留为实验方向。
- **波动率 / 量能放大 / 贝塔**：单因子验证未跑赢基准，已从当前代码中删除。
- 根本原因：能量类因子描述"现在有多乱"，自相关和动量类因子更接近"趋势结构是否正在走弱"。
- 多因子融合探索已回滚，相关复盘见 `changelog.md` [1.0.3]；传统动量因子验证见 `changelog.md` [1.0.4]。

## 等待建设的大架构

### 后端：
1. FastAPI(web框架，写api接口) 
2. APScheduler(定时任务调度器，让数据自动更新，不用手动跑脚本)
3. PostgreSQL or SQLite(数据库，避免重复抓取数据)
4. SQLAlchemy(Python操作数据库的ORM框架)
5. 市场结构因子库（中长期维度）
   - 板块轮动因子
   - 资金流向因子
   - 抱团主线强度因子
   - 期现联动/基差因子

### 前端：
1. React(目前最主流的前端UI框架，组件化开发)
2. shadcn/ui(基于Tailwind CSS的组件库，当前前端圈最流行的UI方案)
3. TradingView Lightweight Charts(专为金融场景设计的图表库)
4. React Query(管理请求状态和缓存,下发送HTTP请求)
5. Axios(HTTP请求库，负责前端调用后端API)

## 架构设计

### 当前项目结构(已实现)
```
src/
├── data/
│   ├── __init__.py    # 包对外接口声明(__all__)
│   ├── data.py        # 数据采集 + 缓存逻辑
│   ├── storage.py     # SQLite 存储层(懒加载建表)
│   └── cache/         # 本地数据库（已 gitignore）
├── signals/           # 信号处理因子包
│   ├── __init__.py    # 包对外接口声明(__all__)
│   ├── spectrum.py    # 频域高频占比因子(FFT)
│   ├── energy.py      # 时域能量比因子
│   ├── autocorr.py    # 自相关因子(预警主力)
│   ├── breadth.py     # 市场宽度实验因子(低位信号已验证失败)
│   ├── traditional.py # 传统动量因子(弱预警候选)
│   └── evaluate.py    # 预警有效性评估 + 基准对比
├── strategy.py        # 策略信号
├── backtest.py        # 回测计算
├── plot.py            # 可视化
└── main.py            # 编排入口(main() + __main__ 保护)
docs/
├── changelog.md            # 开发记录
├── roadmap.md              # 开发计划
├── domain-notes.md         # 量化知识笔记
└── git-workflow.md         # git工作流 && tips
assets/
└── DFquant_logo.png
.gitignore
README.md
requirements.txt          # 运行依赖(精确版本锁定)
requirements-dev.txt      # 开发依赖(当前仅 ruff，lint/format 工具)
pyproject.toml            # ruff 配置
```

### 目标前后端整体架构
```
project/
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── signals/          # 因子计算（从现有 signals/ 搬过来）
│   ├── warning/          # 新增：多因子融合 + 规则引擎 + 预警等级
│   ├── models/
│   └── scheduler.py
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Dashboard.tsx   # 市场总览
    │   │   ├── Signals.tsx     # 信号面板
    │   │   └── Backtest.tsx    # 回测结果
    │   ├── components/         # 复用组件
    │   └── api/                # Axios请求封装
    └── package.json
```