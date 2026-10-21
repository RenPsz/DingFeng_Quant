# 架构优化建议

## 总体判断

当前项目不需要立刻做大规模重构，更适合小步收敛架构边界。

现有结构已经有比较清晰的雏形：

```text
data        数据获取 / 缓存
signals     因子计算
evaluate    因子验证
backtest    回测
strategy    策略信号
plot        本地可视化
main        临时运行入口
```

这个方向是对的。当前主要问题不是目录不够复杂，而是部分模块职责还可以继续拆清楚。架构优化的核心目标应该是服务因子研究闭环，而不是过早进入完整产品工程形态。

## 推荐演进方向

短期不要急着上 FastAPI、React、SQLAlchemy 或完整的 `backend/frontend` 拆分。更推荐先稳定研究内核：

```text
src/
├── data/             # 数据层
├── signals/          # 因子计算层
├── research/         # 因子验证、实验评估
├── warning/          # 预警规则，等因子足够多后再加
├── backtest.py       # 回测引擎
├── strategy.py       # 策略信号
├── plot.py           # 临时可视化
└── main.py           # 临时入口
```

其中最建议优先考虑的是新增 `research/`。当前 `signals/evaluate.py` 更像研究验证工具，而不是信号因子本身。把它从 `signals` 中拆出来，可以让边界更清楚：

```text
signals  负责生产因子
research 负责证明因子有没有用
warning  负责把已验证因子转成预警等级
```

## 优先级 1：拆清 data 层职责

当前 `data/data.py` 承担了多种职责：

- 调用 akshare
- 判断缓存是否最新
- 清洗字段
- 维护股票池 fallback
- 处理指数和个股差异
- 管理交易日历

MVP 阶段这样写没有问题，但后续接入更多数据源后会逐渐变重。建议未来拆成：

```text
src/data/
├── storage.py          # 只管 SQLite 读写
├── providers.py        # 只管 akshare 原始接口调用
├── cleaning.py         # 只管字段清洗和格式统一
├── repository.py       # 对外提供 get_stock_data / get_index_data
└── universe.py         # 股票池、指数池、fallback 样本池
```

核心约束：

- `storage.py` 不知道 akshare。
- `providers.py` 不知道 SQLite。
- `cleaning.py` 不负责缓存判断。
- `repository.py` 作为数据层对外入口，组合 provider、cleaning 和 storage。

这样后续如果从 akshare 切换到其他数据源，主要影响 `providers.py`，不会牵动存储层和因子层。

## 优先级 2：保持 signals 纯计算

`signals` 里的因子函数最好保持以下风格：

```text
输入：DataFrame / Series
输出：Series / DataFrame
不读数据库
不调网络
不 print
不写文件
```

当前大部分因子已经接近这个标准，应该继续保持。以后新增估值因子、资金流因子、宽度因子，也建议遵守这个边界。

好处：

- 因子函数容易测试。
- 因子函数容易复用于 CLI、回测、API 和前端接口。
- 数据源变化不会影响因子计算逻辑。

## 优先级 3：拆分因子验证与因子计算

当前 `signals/evaluate.py` 中包含：

- `future_drawdown`
- `zscore_alert`
- `sign_flip_alert`
- `lower_tail_alert`
- `evaluate`
- `evaluate_traditional_factors`
- RSI / 布林带基准

这些更像研究层逻辑，而不是因子层逻辑。建议后续移动为：

```text
src/research/
├── targets.py       # future_drawdown 等目标定义
├── alerts.py        # 因子转预警事件
├── evaluate.py      # 命中率、lift 等评估指标
└── benchmarks.py    # RSI、布林带等传统基准
```

这样会形成更清楚的链路：

```text
data -> signals -> research -> warning
```

也就是：

1. `data` 提供干净行情。
2. `signals` 计算候选因子。
3. `research` 验证因子是否有效。
4. `warning` 只接纳已验证的因子，输出预警等级。

## 优先级 4：warning 层不要过早复杂化

四级预警方向是合理的：

```text
无 / 关注 / 警惕 / 危险
```

但现在不建议立刻实现复杂规则引擎。原因是当前有效因子的信息源还不够独立。自相关、能量比、高频占比都来自价格收益率序列，信息同源性较强。贸然融合容易形成“看起来丰富，实际信息没有增加”的预警层。

更合适的启动条件是至少具备三类独立信息源：

```text
1. 价格结构：自相关、动量
2. 市场宽度：上涨家数、新高新低、均线以上占比变化
3. 估值 / 资金 / 情绪：PE/PB、股债性价比、资金流向等
```

到那时再新增：

```text
src/warning/
├── rules.py       # 单因子转信号
├── scoring.py     # 多因子打分
├── levels.py      # 四级预警定义
└── schema.py      # 输出结构
```

`warning` 层应该只消费研究层已经验证过的信号，不应该直接承担探索性实验。

## 优先级 5：main.py 保持轻量

`main.py` 最好只是临时实验入口，不要成为所有功能的控制中心。

理想状态：

```python
def main():
    # 选择实验
    # 调用研究函数
    # 打印结果
```

不要把数据同步、因子计算、评估、绘图、参数组合全部堆在 `main.py` 里。后续如果接 FastAPI 或定时任务，薄入口会更容易迁移。

## 优先级 6：规范包结构

当前 `data`、`signals` 作为顶层包名过于通用，易与第三方包冲突，且必须 `cd src` 才能运行。建议：

```text
src/
└── dfquant/
    ├── __main__.py     # python -m dfquant
    ├── data/
    ├── signals/
    ├── research/
    └── ...
tests/                  # pytest，与 src 平级
experiments/            # 可复跑的研究脚本
results/                # 实验输出（参数 + 指标 json）
```

`pyproject.toml` 补 `[project]` 段，`pip install -e .` 后测试和脚本都能直接 `import dfquant`。

## 优先级 7：实验可复现

文档中的每条结论都应能一键复跑：

- 每个实验一个脚本（如 `experiments/autocorr_hs300.py`），只组合 `data` / `signals` / `research` 的函数。
- 参数集中在配置 `dataclass`，不依赖各函数默认值。
- 结果连同参数、数据区间、标的写入 `results/*.json`，changelog 引用结果文件而不是手抄数字。

## 优先级 8：处理闲置模块

`strategy.py`、`backtest.py`、`plot.py` 当前无任何入口调用。要么作为 CLI 子命令接回，要么在模块 docstring 标注暂停维护，避免与主线代码一起腐化。

## 暂时不建议立即做的事

当前阶段不建议立刻做：

- 立刻上 FastAPI。
- 立刻建 React 前端。
- 立刻引入 SQLAlchemy。
- 立刻把整个项目搬成 `backend/frontend`。
- 立刻做复杂多因子规则引擎。

这些方向本身没有错，但时机稍早。当前最有价值的是继续打磨因子研究闭环，让数据、因子、验证三条线清清楚楚。

## 推荐路线

建议按以下顺序演进：

0. 修复已知 bug 并补 pytest 与 CI，具体清单见 `roadmap.md` 第零阶段。
1. 把 `signals/evaluate.py` 迁出为 `research/evaluate.py`，明确研究层边界。
2. 慢慢拆 `data/data.py`，优先拆出 `providers.py` 和 `universe.py`。
3. 新因子全部先进入 `signals`，并通过 `research` 验证。
4. 等独立因子足够后，再建立 `warning` 层。
5. 最后再接 FastAPI。API 只包一层，不改核心研究代码。

一句话总结：

> 当前项目应该优先做研究内核稳定化，而不是产品工程大搬家。先让因子、数据、验证三条线清楚，后续做后端和前端会轻很多。

