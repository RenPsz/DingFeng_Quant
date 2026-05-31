# 定风量化

![DFquant_logo](assets/DFquant_logo.png)

## 简要介绍

*定风量化*，是一个专注**A股市场**的个人量化研究项目，完整覆盖数据采集、策略生成、回测验证全流程，搭建起从研究到检验的闭环体系。

**命名由来：**  
> 回首向来萧瑟处，归去，也无风雨也无晴。—— 苏轼《定风波》
  
框架之名，取自苏轼词作《定风波》。金融市场行情起落无常，涨跌之间极易牵动人心：涨则心生贪念，跌则陷入恐慌，纷繁热点与短期波动，常使人的判断随情绪摇摆。而量化的意义，正是以数据为基石、以逻辑为锚点，剥离情绪干扰，在变幻莫测的市场中守住清醒与笃定。

**核心目标：**  
依托客观数据与可复现逻辑，摒弃主观臆断，理性、系统地洞察市场规律。

## 当前进度
- [x] 双均线策略 + 回测引擎 MVP
- [x] 项目重构 + 文档完善
- [ ] 市场情绪信号采集
- [ ] 前端可视化

## 快速开始

1. 克隆项目并安装依赖
```bash
git clone https://github.com/RenPsz/DingFeng_Quant.git
cd DingFeng_Quant
pip install -r requirements.txt
```
2. 运行回测
```bash
cd src
python main.py
```

## 文档
- [架构设计](docs/architecture.md)
- [开发计划](docs/roadmap.md)
- [量化知识笔记](docs/domain-notes.md)
- [Git 工作流](docs/git-workflow.md)

## 当前项目结构(已实现)
src/
├── data.py        # 数据采集
├── strategy.py    # 策略信号
├── backtest.py    # 回测计算
├── plot.py        # 可视化
└── main.py        # 编排入口
docs/
├── architecture.md         # 架构设计
├── roadmap.md              # 开发计划
├── domain-notes.md         # 量化知识笔记
└── git-workflow.md         # git工作流 && tips
assets/
└── DFquant_logo.png            # 项目logo
.gitignore
README.md
requirements.txt
