核心分析规则（你提到的逻辑）
风格匹配度检验：
高风险指数（中证2000、创业板）涨跌幅 > 低风险指数（沪深300）→ 正常
高风险指数涨跌幅 < 低风险指数 → 异常（市场风险偏好下降）
基差分析：
正基差（期货升水）：市场情绪偏乐观
负基差（期货贴水）：市场情绪偏谨慎
可设置阈值：基差<-20点或>20点为异常区间
市场广度：
涨跌停家数：跌停家数显著增多（如>50家）是市场弱势信号
20日新高家数：沪深300和中证2000的新高家数对比，判断大小盘强弱

-----------  

第一周：搭建基础框架

完成指数行情采集（最简单的部分）

存入CSV，跑通每日追加

第二周：增加市场情绪指标

实现涨跌停统计

实现基差计算（需获取期货数据）

第三周：实现成分股新高统计

获取成分股列表（可每月更新一次）

计算20日新高数量（这一步最耗时，可考虑只计算抽样或分批）

第四周：完善风险评估规则+可视化

用Matplotlib或Plotly生成每日仪表盘

设置邮件或微信提醒（可选）

-----------  
📋 项目规划
项目定位：金融量化分析系统，包含策略回测 + (核心)市场信号收集 + 前端可视化展示
等待建设技术栈
后端：
1. FastAPI(web框架，写api接口) 
2. APScheduler(定时任务调度器，让数据自动更新，不用手动跑脚本)
3. PostgreSQL or SQLite(数据库，避免重复抓取数据)
4. SQLAlchemy(Python操作数据库的ORM框架)
前端：
1. React(目前最主流的前端UI框架，组件化开发)
2. shadcn/ui(基于Tailwind CSS的组件库，当前前端圈最流行的UI方案)
3. TradingView Lightweight Charts(专为金融场景设计的图表库)
4. React Query(管理请求状态和缓存,下发送HTTP请求)
5. Axios(HTTP请求库，负责前端调用后端API)

----------- 

market_monitor/
│
├── data/                    # 数据存储
│   ├── raw/                 # 原始数据
│   │   ├── index_daily.csv
│   │   ├── futures.csv
│   │   └── limit_up_down.csv
│   ├── processed/           # 处理后数据
│   │   └── market_daily.csv
│   └── static/              # 静态数据（成分股列表等）
│       ├── hs300_cons.csv
│       └── zz2000_cons.csv
│
├── src/                     # 源代码
│   ├── collectors/          # 数据采集器
│   │   ├── index_collector.py
│   │   ├── futures_collector.py
│   │   └── stock_collector.py
│   ├── analyzers/           # 分析器
│   │   ├── risk_analyzer.py
│   │   ├── breadth_analyzer.py
│   │   └── basis_analyzer.py
│   ├── reporters/           # 报告生成
│   │   ├── daily_report.py
│   │   └── weekly_report.py
│   └── utils/               # 工具函数
│       ├── data_fetcher.py  # 统一数据获取接口
│       ├── cache.py         # 缓存管理
│       └── notifier.py      # 通知推送
│
├── config/                   # 配置文件
│   ├── settings.yaml        # 数据源、阈值配置
│   └── indices.yaml         # 指数列表及代码
│
├── scripts/                  # 可执行脚本
│   ├── daily_update.py      # 每日更新
│   ├── backtest.py          # 回测阈值
│   └── init_static_data.py  # 初始化静态数据
│
├── reports/                  # 生成的报告
│   └── 2026/
│       └── 03/
│           └── daily_20260305.html
│
├── logs/                     # 日志
│   └── market_monitor.log
│
├── requirements.txt          # 依赖包
├── README.md                 # 项目说明
└── .gitignore                # Git忽略文件

前期整体架构
├── data/           # 数据处理层
├── strategy/       # 策略层  
├── backtest/       # 回测分析层
├── signals/        # 信号分析层（新增）
├── frontend/       # 前端展示层（新增）
└── main.py

后期前后端整体架构
project/
├── backend/
│   ├── main.py          # FastAPI 入口
│   ├── routers/
│   │   ├── market.py    # 行情接口
│   │   ├── signals.py   # 信号接口
│   │   └── backtest.py  # 回测接口
│   ├── services/        # 你现有的计算逻辑迁移到这里
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