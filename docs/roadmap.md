# 项目规划

## 项目定位
金融量化分析系统，包含策略回测 + (核心)市场信号收集 + 前端可视化展示

## 短期待办
- [ ] 输入股票号，自动抓取数据，不需要分辨那个市场
- [ ] 无
- [ ] 无

## 等待建设的大架构

### 后端：
1. FastAPI(web框架，写api接口) 
2. APScheduler(定时任务调度器，让数据自动更新，不用手动跑脚本)
3. PostgreSQL or SQLite(数据库，避免重复抓取数据)
4. SQLAlchemy(Python操作数据库的ORM框架)

### 前端：
1. React(目前最主流的前端UI框架，组件化开发)
2. shadcn/ui(基于Tailwind CSS的组件库，当前前端圈最流行的UI方案)
3. TradingView Lightweight Charts(专为金融场景设计的图表库)
4. React Query(管理请求状态和缓存,下发送HTTP请求)
5. Axios(HTTP请求库，负责前端调用后端API)