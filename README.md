# 定风量化

## 本地git+云端git工作流
开工:git checkout -b (功能名)
阶段存盘:git add .
git commit -m "规范描述"
检查:git status{随时随地输入，看当前改了哪些文件，有没有脏文件收工合流}
git checkout main   切换到main主线
git merge (功能名)   {新功能彻底测通了，把它合进主干线备份}
git push            {同步到 GitHub 存盘}

## git commit 规范  

<type>(<scope>): <subject>

type：本次提交的类型,用来告诉别人，你这次动代码的核心目的是什么。
最常用的 5 个核心类型：
1. feat：引入了新功能（Feature）。 量化场景：feat: 引入布林带交易策略
2. fix：修复了 Bug。          量化场景：fix: 修复回测引擎未计算手续费的Bug
3. refactor：代码重构。    它既不是新增功能，也不是修 Bug，而是为了让代码更好看、结构更合理。
4. docs：只修改了文档、README.md。
5. chore：日常杂务、构建工具、配置变更。不影响代码逻辑本身。
scope（选填）：影响的范围
说明这次修改主要波及到了项目的哪个模块，用括号包起来。
场景：feat(strategy):、fix(data):、refactor(engine):
subject（必填）：一句简短的描述
用一句大白话总结这次提交具体做了什么。

Such as:
1. 初始化项目环境
git commit -m "chore: 配置项目初始.gitignore并完成云端首推"
2. 实现了第一个MVP大闭环
git commit -m "feat: 实现双均线策略与回测引擎的最小可行性闭环"
3. 修复了之前遇到的时区或索引 Bug
git commit -m "fix(data): 修复akshare获取数据时日期索引未对齐的Bug"
4. 进行面向对象重构
git commit -m "refactor: 将过程式回测代码解耦拆分为Data/Strategy/Engine模块"
5. 加入现实摩擦成本
git commit -m "feat(engine): 在模拟账本中引入0.15%的交易手续费计算"
6. 完善项目门面
git commit -m "docs: 完善README中的架构设计图与策略收益率对比表格"