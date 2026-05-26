# SentinelTrade ETF 自动交易系统 - 设计规格书

## 1. 项目概述

SentinelTrade 是一个面向中国 A 股 ETF 的自动交易系统，基于 miniQMT (xtquant) 实盘接口，采用事件驱动架构，支持趋势轮动策略、完整风控体系、回测引擎和 Web Dashboard。

**目标用户**：个人开发者，小资金量（3 万元）

**技术栈**：Python 3.11, xtquant, SQLite, APScheduler, Streamlit, loguru, pandas, numpy

## 2. 设计原则

1. **配置驱动**：所有参数从 config.yaml + .env 加载，零硬编码
2. **接口抽象**：每个模块定义抽象基类，实现可替换
3. **事件解耦**：模块间通过 EventBus 通信，无直接依赖
4. **独立可测**：每个模块可独立单元测试
5. **风控独立**：风控模块不依赖任何业务模块
6. **AI 预留**：ai 模块提供抽象接口，后续可无缝接入

## 3. 项目目录结构

```
SentinelTrade/
├── main.py
├── config.yaml
├── .env
├── requirements.txt
├── README.md
├── data/
│   ├── sentinel.db
│   └── logs/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── loader.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── events.py
│   │   ├── types.py
│   │   └── enums.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── market/
│   │   ├── __init__.py
│   │   ├── market_base.py
│   │   ├── xt_provider.py
│   │   └── data_cache.py
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── strategy_base.py
│   │   ├── signal.py
│   │   ├── factor.py
│   │   ├── etf_rotation.py
│   │   └── strategy_manager.py
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── risk_engine.py
│   │   ├── risk_base.py
│   │   ├── stop_loss.py
│   │   ├── position_limit.py
│   │   ├── breaker.py
│   │   └── blacklist.py
│   ├── broker/
│   │   ├── __init__.py
│   │   ├── broker_base.py
│   │   ├── qmt_client.py
│   │   ├── order_manager.py
│   │   ├── trade_callback.py
│   │   ├── account_manager.py
│   │   └── paper_broker.py
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── task_scheduler.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── pages/
│   │   │   ├── portfolio.py
│   │   │   ├── signals.py
│   │   │   ├── trades.py
│   │   │   └── risk.py
│   │   └── components/
│   │       ├── charts.py
│   │       └── metrics.py
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── data_loader.py
│   │   └── report.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── ai_base.py
│   │   └── feature_engine.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── notify.py
│       └── trading_calendar.py
```

## 4. 模块职责与接口

### 4.1 config/ - 配置管理

**settings.py** - 配置 dataclass 定义：
- `AppConfig`：顶层配置，包含所有子配置
- `StrategyConfig`：策略参数（MA 周期、轮动频率、最大持仓数）
- `RiskConfig`：风控参数（止损、止盈、最大仓位、熔断阈值）
- `BrokerConfig`：券商配置（账户 ID、QMT 路径）
- `SchedulerConfig`：调度时间配置
- `DatabaseConfig`：数据库路径配置

**loader.py** - 加载器：
- `load_config(path: str) -> AppConfig`：加载 config.yaml
- `load_env(path: str) -> dict`：加载 .env
- 环境变量覆盖 YAML 配置

### 4.2 common/ - 共享基础设施

**events.py** - EventBus：
- `EventBus` 类：发布/订阅模式
- `subscribe(event_type: str, callback: Callable)`
- `publish(event: Event)`
- 线程安全，支持同步/异步

**types.py** - 共享数据结构：
- `Bar`：K 线数据（open, high, low, close, volume, timestamp）
- `Tick`：实时行情（last_price, bid, ask, volume, timestamp）
- `Signal`：交易信号（code, direction, strength, source, timestamp）
- `Order`：订单（code, direction, price, volume, status）
- `Position`：持仓（code, volume, cost, market_value, pnl）
- `Account`：账户（balance, available, frozen, total_assets）

**enums.py** - 枚举：
- `Direction`：BUY, SELL
- `OrderStatus`：PENDING, FILLED, PARTIAL, CANCELLED, REJECTED
- `SignalType`：ENTRY, EXIT, STOP_LOSS, STOP_PROFIT

### 4.3 database/ - 数据持久化

**engine.py** - SQLite 连接管理：
- 单例模式，连接池
- `get_connection() -> sqlite3.Connection`

**models.py** - 表定义：
- `trades`：交易记录（id, code, direction, price, volume, timestamp, pnl）
- `signals`：信号记录（id, code, signal_type, strength, timestamp）
- `daily_pnl`：每日损益（date, total_assets, pnl, drawdown）
- `risk_events`：风控事件（id, event_type, detail, timestamp）

**repository.py** - 数据访问：
- `TradeRepository`：交易 CRUD
- `SignalRepository`：信号 CRUD
- `PnlRepository`：损益查询
- `RiskEventRepository`：风控事件记录

### 4.4 market/ - 行情服务

**market_base.py** - 抽象基类：
```python
class MarketProvider(ABC):
    @abstractmethod
    def get_realtime_quotes(self, codes: list[str]) -> dict[str, Tick]: ...
    @abstractmethod
    def get_history_bars(self, code: str, period: str, count: int) -> list[Bar]: ...
    @abstractmethod
    def subscribe(self, codes: list[str], callback: Callable): ...
```

**xt_provider.py** - xtquant 实现：
- 封装 xtquant xtdata 模块
- 处理连接异常和重连

**data_cache.py** - 行情缓存：
- LRU 缓存，避免重复请求
- 缓存过期策略

### 4.5 strategy/ - 策略引擎

**strategy_base.py** - 抽象基类：
```python
class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bars: dict[str, Bar]) -> list[Signal]: ...
    @abstractmethod
    def get_params(self) -> dict: ...
    @abstractmethod
    def update_params(self, params: dict): ...
```

**signal.py** - 信号定义：
- `Signal` dataclass（继承自 common.types.Signal，扩展策略特有字段）
- `SignalStrength`：信号强度枚举（STRONG, MEDIUM, WEAK）

**factor.py** - 因子计算：
- `ma(series: pd.Series, period: int) -> pd.Series`：移动平均
- `momentum(series: pd.Series, period: int) -> pd.Series`：动量因子
- `volatility(series: pd.Series, period: int) -> pd.Series`：波动率因子
- `trend_strength(series: pd.Series, short: int, long: int) -> pd.Series`：趋势强度

**etf_rotation.py** - ETF 轮动策略：
- 继承 Strategy
- 核心逻辑：
  1. 计算每个 ETF 的 MA5, MA10, MA20
  2. 判断趋势方向（价格 > MA20 为上升趋势）
  3. 计算趋势强度（(MA5 - MA20) / MA20）
  4. 按趋势强度排名
  5. 选择 top N（默认 3）个 ETF
  6. 与当前持仓对比，生成买入/卖出信号
- 参数：ma_periods, trend_threshold, max_holdings, rebalance_days

**strategy_manager.py** - 策略管理：
- 注册多个策略实例
- 收到 MarketDataEvent 后分发给各策略
- 收集信号并发布 SignalEvent

### 4.6 risk/ - 风控系统

**risk_base.py** - 风控规则抽象：
```python
class RiskRule(ABC):
    @abstractmethod
    def check(self, signal: Signal, context: RiskContext) -> RiskResult: ...
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def priority(self) -> int: ...  # 优先级，数字越小越先执行
```

**risk_engine.py** - 风控引擎：
- 规则链模式：按优先级依次执行所有规则
- 任一规则拒绝则整体拒绝
- `add_rule(rule: RiskRule)`
- `check_signal(signal: Signal, context: RiskContext) -> RiskResult`
- `RiskContext`：包含当前持仓、账户余额、当日交易记录等上下文
- `RiskResult`：passed(bool), reason(str), rule_name(str)

**stop_loss.py** - 止损规则：
- 单笔止损：持仓亏损超过 stop_loss 比例时触发卖出信号
- 止盈：持仓盈利超过 stop_profit 比例时触发卖出信号
- 日亏损限额：当日累计亏损超过 daily_loss_limit 时拒绝新买入

**position_limit.py** - 仓位限制：
- 最大持仓数量：不超过 max_holdings
- 单品种仓位占比：不超过 max_position_ratio
- 总仓位限制：可用资金检查

**breaker.py** - 熔断机制：
- 最大回撤熔断：账户回撤超过 max_drawdown 时停止交易
- 连续亏损保护：连续 N 笔亏损后暂停交易
- 熔断持续时间可配置
- 熔断解除条件可配置

**blacklist.py** - 黑名单：
- ETF 黑名单（长期停牌、流动性差等）
- 网络异常保护：xtquant 连接断开时暂停交易
- 行情异常保护：行情数据异常（价格为 0、成交量为 0）时拒绝交易

### 4.7 broker/ - 交易执行

**broker_base.py** - 抽象基类：
```python
class Broker(ABC):
    @abstractmethod
    def buy(self, code: str, price: float, volume: int) -> str: ...
    @abstractmethod
    def sell(self, code: str, price: float, volume: int) -> str: ...
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool: ...
    @abstractmethod
    def get_positions(self) -> list[Position]: ...
    @abstractmethod
    def get_balance(self) -> Account: ...
    @abstractmethod
    def get_orders(self, status: OrderStatus | None = None) -> list[Order]: ...
    @abstractmethod
    def get_trades(self, start: datetime | None = None) -> list[Trade]: ...
```

**qmt_client.py** - QMT 连接客户端：
- 封装 xtquant xttrader 连接管理
- 自动重连机制（断线检测 + 指数退避重试）
- 连接状态事件发布
- 账户登录/登出

**order_manager.py** - 订单管理：
- 买入/卖出下单封装
- 撤单操作
- 订单状态查询
- 委托回调处理（委托成功/失败/部分成交）
- 防重复下单（本地订单 ID 去重）

**trade_callback.py** - 成交回调：
- xtquant 回调函数注册
- 成交回报解析
- 发布 TradeEvent 到 EventBus
- 异常保护（回调函数内 try-catch）

**account_manager.py** - 账户管理：
- 持仓查询（实时刷新）
- 资金查询（可用余额、冻结资金、总资产）
- 成交记录查询
- 数据缓存（避免频繁请求）

**paper_broker.py** - 模拟盘：
- 内存撮合引擎
- 模拟滑点和手续费
- 用于回测和测试

### 4.8 scheduler/ - 任务调度

**task_scheduler.py** - APScheduler 封装：
- `add_daily_task(time: str, func: Callable, name: str)`
- `add_interval_task(seconds: int, func: Callable, name: str)`
- 内置任务：
  - 09:35 行情扫描 + 策略计算
  - 14:30 调仓执行
  - 14:50 收盘前检查（止损）
  - 15:05 日终结算（写入数据库）

### 4.9 dashboard/ - Web 界面

**app.py** - Streamlit 主入口：
- 侧边栏导航
- 全局刷新按钮

**pages/portfolio.py** - 持仓总览：
- 当前持仓列表
- 账户资产曲线
- 每日损益表

**pages/signals.py** - 信号记录：
- 信号列表（时间、标的、方向、强度）
- 信号来源标注

**pages/trades.py** - 交易记录：
- 交易流水
- 盈亏分析

**pages/risk.py** - 风控状态：
- 当前风控规则状态
- 风控事件日志
- 熔断状态显示

**components/charts.py** - 图表：
- K 线图 + 均线
- 资产曲线
- 回撤曲线

**components/metrics.py** - 指标卡片：
- 总资产、当日盈亏、持仓数量、最大回撤

### 4.10 backtest/ - 回测引擎

**engine.py** - 回测核心：
- 按日回放历史数据
- 调用 Strategy 生成信号
- 调用 PaperBroker 模拟成交
- 调用 RiskManager 风控检查
- 记录每日资产和交易

**data_loader.py** - 数据加载：
- 从 xtquant 或本地 CSV 加载历史数据
- 数据预处理和清洗

**report.py** - 回测报告：
- 总收益率、年化收益、最大回撤、夏普比率
- 交易明细
- 可视化图表

### 4.11 ai/ - AI 模块（预留）

**ai_base.py** - 抽象接口：
```python
class AIModel(ABC):
    @abstractmethod
    def predict(self, features: np.ndarray) -> float: ...
    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray): ...
```

**feature_engine.py** - 特征工程：
- 技术指标特征提取
- 数据标准化

### 4.12 utils/ - 工具模块

**logger.py** - loguru 配置：
- 控制台输出（INFO 级别，带颜色）
- 文件输出（DEBUG 级别，按天轮转）
- 错误文件（ERROR 级别，单独记录）
- 风控事件单独文件

**notify.py** - 消息通知：
- 抽象通知接口
- 可选实现：微信、钉钉、邮件

**trading_calendar.py** - 交易日历：
- A 股交易日判断
- 下一交易日计算

## 5. 核心数据流

```
APScheduler (09:35 触发)
    │
    ▼
MarketProvider.get_realtime_quotes(etf_pool)
    │  → EventBus.publish(MarketDataEvent)
    ▼
StrategyManager.on_market_data(event)
    │  → Factor.ma(bars, 5/10/20)
    │  → ETFRotationStrategy.on_bar(bars)
    │  → 生成 Signal 列表
    │  → EventBus.publish(SignalEvent)
    ▼
RiskEngine.on_signal(event)
    │  → StopLossRule.check()      # 止损止盈检查
    │  → PositionLimitRule.check() # 仓位检查
    │  → BreakerRule.check()       # 熔断检查
    │  → BlacklistRule.check()     # 黑名单检查
    │  → 通过 → EventBus.publish(OrderEvent)
    │  → 拒绝 → 记录风控事件，发送通知
    ▼
Broker.execute_order(event)
    │  → xt_broker.submit_order()
    │  → EventBus.publish(TradeEvent)
    ▼
Repository.save_trade(event)
    → 写入 SQLite
```

## 6. 风控流程图

```
Signal 输入
    │
    ▼
[黑名单检查] ──拒绝──→ 记录事件 + 通知
    │通过
    ▼
[网络/行情异常检查] ──拒绝──→ 记录事件 + 通知
    │通过
    ▼
[熔断检查] ──触发──→ 记录事件 + 通知
    │通过
    ▼
[止损止盈检查] ──触发──→ 生成反向信号
    │通过
    ▼
[仓位限制检查] ──超限──→ 记录事件
    │通过
    ▼
[日亏损限额检查] ──超限──→ 记录事件
    │通过
    ▼
[防重复下单检查] ──重复──→ 拒绝
    │通过
    ▼
OrderEvent 输出 → Broker 执行
```

## 7. 策略执行流程

```
MarketDataEvent（实时行情）
    │
    ▼
获取 ETF Pool 所有标的的 K 线数据
    │
    ▼
Factor 计算:
    ├── MA5, MA10, MA20
    ├── 趋势强度 = (MA5 - MA20) / MA20
    └── 动量 = (close - close_n) / close_n
    │
    ▼
趋势判断:
    ├── 上升趋势: close > MA20 且 MA5 > MA10
    ├── 下降趋势: close < MA20 且 MA5 < MA10
    └── 震荡: 其他
    │
    ▼
ETF 排名:
    ├── 仅保留上升趋势的 ETF
    ├── 按趋势强度降序排列
    └── 取 Top N（max_holdings=3）
    │
    ▼
信号生成:
    ├── 新 ETF 进入 Top N 且不在持仓 → BUY 信号
    ├── 持仓 ETF 跌出 Top N → SELL 信号
    └── 持仓 ETF 转为下降趋势 → SELL 信号
    │
    ▼
SignalEvent 输出 → RiskEngine
```

## 8. 配置文件设计

### config.yaml

```yaml
# ETF 标的池
etf_pool:
  - { code: "510300", name: "沪深300ETF" }
  - { code: "510500", name: "中证500ETF" }
  - { code: "159915", name: "创业板ETF" }
  - { code: "512100", name: "中证1000ETF" }
  - { code: "159941", name: "纳指ETF" }
  - { code: "518880", name: "黄金ETF" }
  - { code: "511010", name: "国债ETF" }

# 策略参数
strategy:
  ma_periods: [5, 10, 20]
  trend_threshold: 0.02
  max_holdings: 3
  rebalance_days: [0, 4]  # 0=周一, 4=周五

# 风控参数
risk:
  max_position_ratio: 0.30
  max_drawdown: 0.05
  daily_loss_limit: 0.02
  stop_profit: 0.08
  stop_loss: 0.03
  max_consecutive_losses: 3
  cooldown_minutes: 30

# 调度时间
scheduler:
  scan_time: "09:35"
  rebalance_time: "14:30"
  close_check_time: "14:50"
  settle_time: "15:05"

# 数据库
database:
  path: "data/sentinel.db"

# 日志
logging:
  level: "DEBUG"
  rotation: "1 day"
  retention: "30 days"
```

### .env

```
# QMT 配置
QMT_PATH=C:\国金证券QMT交易端\userdata_mini
QMT_ACCOUNT=你的账户ID
QMT_ACCOUNT_TYPE=STOCK

# 数据库
DB_PATH=data/sentinel.db

# 通知（可选）
NOTIFY_TYPE=none
WECHAT_WEBHOOK=
DINGTALK_WEBHOOK=
```

## 9. requirements.txt

```
# 核心依赖
xtquant>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
python-dotenv>=1.0.0

# 调度
apscheduler>=3.10.0

# 数据库
# SQLite 为 Python 内置，无需额外安装

# Web Dashboard
streamlit>=1.28.0
plotly>=5.18.0

# 日志
loguru>=0.7.0

# 类型支持
typing-extensions>=4.8.0
```

## 10. 启动流程 (main.py)

```python
"""
SentinelTrade 启动流程:
1. 加载配置 (.env + config.yaml)
2. 初始化日志 (loguru)
3. 初始化数据库 (SQLite)
4. 初始化 EventBus
5. 初始化各模块 (Market, Strategy, Risk, Broker)
6. 注册事件处理器
7. 启动调度器 (APScheduler)
8. 保持运行
"""
```

## 11. 扩展点

| 扩展方向 | 扩展方式 |
|---------|---------|
| 新策略 | 继承 Strategy 基类，在 StrategyManager 注册 |
| 新风控规则 | 继承 RiskRule 基类，在 RiskEngine 注册 |
| 新行情源 | 继承 MarketProvider 基类 |
| AI 模型 | 继承 AIModel 基类，接入 Strategy 或独立信号源 |
| 通知方式 | 继承通知基类 |
| Dashboard 页面 | 在 pages/ 下新增页面文件 |

## 12. 测试策略

- 每个模块独立单元测试
- 使用 PaperBroker 进行集成测试
- 使用历史数据进行回测验证
- 风控模块使用边界值测试
