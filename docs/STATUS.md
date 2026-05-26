# SentinelTrade 项目状态

> 更新日期：2026-05-26

## 总览

| 模块 | 状态 | 说明 |
|------|------|------|
| config | 已完成 | 配置加载与解析 |
| common | 已完成 | 共享类型、枚举、EventBus |
| database | 已完成 | SQLite 引擎与数据访问 |
| market | 已完成 | 行情服务（xtquant） |
| strategy | 已完成 | ETF 轮动策略与因子计算 |
| risk | 已完成 | 风控引擎与规则链 |
| broker | 已完成 | 券商对接与模拟盘 |
| scheduler | 已完成 | APScheduler 任务调度 |
| backtest | 已完成 | 回测引擎、分析器、报告 |
| dashboard | 已完成 | Streamlit 可视化面板 |
| ai | 仅占位 | 抽象接口，无具体实现 |
| utils | 已完成 | 日志、通知、交易日历 |
| main.py | 已完成 | 主入口，模块集成 |

---

## 已完成

### 1. config - 配置管理
- `settings.py`：所有配置 dataclass（AppConfig、StrategyConfig、RiskConfig 等）
- `loader.py`：YAML + .env 加载，环境变量覆盖

### 2. common - 共享基础设施
- `enums.py`：Direction、OrderStatus、SignalType、TrendDirection
- `types.py`：Bar、Tick、Signal、Order、Trade、Position、Account
- `events.py`：线程安全的 EventBus（subscribe/unsubscribe/publish）

### 3. database - 数据持久化
- `engine.py`：SQLite 连接管理，4 张表（trades、signals、daily_pnl、risk_events）
- `repository.py`：TradeRepository、SignalRepository、RiskEventRepository 完整 CRUD

### 4. market - 行情服务
- `market_base.py`：MarketProvider 抽象基类
- `xt_provider.py`：xtquant 实现（实时行情、历史 K 线、DataFrame 导出）
- `data_cache.py`：TTL 缓存

### 5. strategy - 策略引擎
- `strategy_base.py`：Strategy 抽象基类
- `etf_rotation.py`：ETF 轮动策略（MA 趋势判断 + 排名 + 信号生成）
- `factor.py`：7 个技术指标（MA、EMA、动量、波动率、趋势强度、ATR、RSI）
- `strategy_manager.py`：策略管理器（事件分发 + 信号收集）
- `signal.py`：StrategySignal 数据结构

### 6. risk - 风控系统
- `risk_engine.py`：规则链引擎（按优先级执行）
- `blacklist.py`：黑名单 + 网络/行情异常检测
- `breaker.py`：熔断机制（最大回撤 + 连续亏损 + 冷却）
- `stop_loss.py`：止损 + 止盈 + 日亏损限额
- `position_limit.py`：持仓数量限制 + 仓位比例 + 余额检查

### 7. broker - 交易执行
- `broker_base.py`：Broker 抽象基类
- `paper_broker.py`：模拟盘（内存撮合、佣金、滑点）
- `xt_broker.py`：实盘券商（382 行，回调适配、订单映射、断线重连）
- `qmt_client.py`：QMT 连接管理 + 指数退避重连
- `order_manager.py`：订单生命周期 + 防重复下单
- `trade_callback.py`：xtquant 成交回调桥接
- `account_manager.py`：持仓/资金查询（带缓存）

### 8. scheduler - 任务调度
- `task_scheduler.py`：APScheduler 封装（每日任务 + 间隔任务）

### 9. backtest - 回测引擎
- `backtest_engine.py`：Backtrader 封装（A 股佣金、滑点、仓位管理、参数优化）
- `analyzer.py`：4 个自定义分析器（交易统计、夏普、回撤、收益率）
- `performance.py`：绩效报告（收益率、回撤、夏普、胜率、盈亏比等）
- `plot.py`：5 个 Plotly 图表 + HTML 报告生成
- `backtest_run.py`：回测运行脚本（支持 --sample 和真实数据）
- `examples/backtest_etf_rotation.py`：ETF 轮动策略回测示例

### 10. dashboard - Web 面板
- `app.py`：Streamlit 主入口（4 页面导航）
- `pages/portfolio.py`：持仓总览
- `pages/signals.py`：信号记录
- `pages/trades.py`：交易流水
- `pages/risk.py`：风控状态
- `components/charts.py`：资金曲线、K 线、回撤图
- `components/metrics.py`：指标卡片

### 11. utils - 工具模块
- `logger.py`：loguru 配置（控制台 + 文件 + 错误 + 风控日志）
- `notify.py`：通知接口（LogNotifier、NoopNotifier）
- `trading_calendar.py`：A 股交易日历

### 12. main.py - 主入口
- 完整的模块集成与事件注册
- APScheduler 定时任务（09:35 扫描、14:30 调仓、14:50 收盘检查、15:05 结算）

### 13. 测试
- `tests/test_backtest.py`：8 个 pytest 用例（佣金、印花税、引擎运行、绩效报告、多 ETF、回撤）
- 全部通过（2026-05-26 验证）

### 14. 环境配置
- xtquant：v250516，路径 `D:\software\xtquant`，虚拟环境 `D:\software\xtquant\.venv`
- Python：3.11.15
- 已安装依赖：backtrader、akshare、baostock、loguru、plotly、streamlit、pyyaml、python-dotenv、apscheduler、pytest
- 代理配置：Git 已配置 `http://127.0.0.1:7890`（影响 Python requests 库访问东方财富 API）

---

## 进行中

### 1. 回测验证（进行中）
- [x] 安装 xtquant（v250516，路径：D:\software\xtquant）
- [x] 配置 `.env` 中的 QMT_PATH
- [x] 安装回测依赖（backtrader、akshare、baostock、loguru、plotly 等）
- [x] 用模拟数据运行回测验证策略逻辑（`python backtest_run.py --sample`）
  - 结果：65 笔交易完成，信号生成→风控→下单→成交→统计全流程跑通
  - 8 个 pytest 测试全部通过
- [ ] 用真实历史数据运行回测（需解决代理问题或启动 QMT 客户端）
- [ ] 检查回测报告指标是否合理（收益率、回撤、夏普、交易明细）

---

## 待完成

### 2. AI 模块（低优先级，预留）
- [ ] 实现具体的 AI 模型（如 LSTM、XGBoost 等）
- [ ] 将 AI 信号接入 StrategyManager
- [ ] 特征工程与模型训练流程

### 3. 通知功能（低优先级）
- [ ] 微信 webhook 通知实现
- [ ] 钉钉 webhook 通知实现
- [ ] 邮件通知实现

### 4. 实盘联调（需 QMT 环境）
- [ ] QMT 连接测试
- [ ] 实盘下单流程验证
- [ ] 成交回调正确性验证
- [ ] 断线重连机制验证

---

## 已知问题

| 编号 | 文件 | 问题 | 严重程度 |
|------|------|------|----------|
| 1 | `backtest_engine.py:260-264` | 死代码：第一个 return 之后的代码不可达 | 低 |
| 2 | `xt_provider.py` subscribe() | 订阅行情但从不触发回调 | 中 |
| 3 | `breaker.py` _calc_drawdown() | 仅计算日损益回撤，非峰值回撤 | 中 |
| 4 | `src/ai/` | 整个模块为占位符，无具体实现 | 低 |
| 5 | Python requests 库 | Git 代理配置（127.0.0.1:7890）导致 requests/urllib 无法直连东方财富 API | 中 |
