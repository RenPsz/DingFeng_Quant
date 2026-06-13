# 架构设计和展望

## 当前项目结构(已实现)
```
src/
├── data.py        # 数据采集
├── strategy.py    # 策略信号
├── backtest.py    # 回测计算
├── plot.py        # 可视化
└── main.py        # 编排入口
doc/
├── architecture.md         # 架构设计
├── roadmap.md              # 开发计划
├── domain-notes.md         # 量化知识笔记
└── git-workflow.md         # git工作流 && tips
.gitignore
README.md
requirements.txt
```

## 目标结构(前后端分离)

#### 前期整体架构规划
```
├── data/           # 数据处理层
├── strategy/       # 策略层  
├── backtest/       # 回测分析层
├── plot/           # 可视化展示层
├── signals/        # 信号分析层（未完成）
└── main.py

#### 后期前后端整体架构
project/
├── backend/
│   ├── main.py          # FastAPI 入口
│   ├── routers/
│   │   ├── market.py    # 行情接口
│   │   ├── signals.py   # 信号接口
│   │   └── backtest.py  # 回测接口
│   ├── services/        # 计算逻辑
│   ├── models/          # 数据库模型
│   └── scheduler.py     # 定时任务
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