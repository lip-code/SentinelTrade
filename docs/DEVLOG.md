# SentinelTrade 开发日志

## 2026-05-26

### 环境搭建

- 项目初始化：从 GitHub 克隆 `lip-code/SentinelTrade` 仓库到 `D:\project\SentinelTrade`
- 配置 Git 代理：`http://127.0.0.1:7890`（解决 GitHub 连接问题）
- 安装 xtquant：版本 `xtquant_250516`，路径 `D:\software\xtquant`，虚拟环境 `D:\software\xtquant\.venv`
- 更新 `.env` 文件：`QMT_PATH=D:\software\xtquant`
- 安装项目依赖到 xtquant 虚拟环境：
  - backtrader（回测引擎）
  - akshare（A 股数据源，因代理问题暂不可用）
  - baostock（A 股数据源，不支持 ETF）
  - loguru（日志）
  - plotly（图表）
  - streamlit（Web 面板）
  - pyyaml、python-dotenv、apscheduler（配置与调度）
  - pytest（测试）

### 代码审计

对全部源码模块进行了实现状态审计，结果如下：

| 模块 | 状态 |
|------|------|
| config | 已完成 |
| common | 已完成 |
| database | 已完成 |
| market | 已完成 |
| strategy | 已完成 |
| risk | 已完成 |
| broker | 已完成 |
| scheduler | 已完成 |
| backtest | 已完成 |
| dashboard | 已完成 |
| ai | 仅占位 |
| utils | 已完成 |
| main.py | 已完成 |

发现 4 个已知问题：
1. `backtest_engine.py:260-264` 死代码
2. `xt_provider.py` subscribe() 不触发回调
3. `breaker.py` _calc_drawdown() 仅计算日损益回撤
4. `src/ai/` 整个模块为占位符

### 回测验证

- 运行 `python backtest_run.py --sample --days 500`，模拟数据回测成功
- 结果：7 个 ETF、500 个交易日、65 笔交易，全流程（信号生成 → 风控检查 → 下单 → 成交 → 绩效统计）跑通
- 绩效指标：总收益 -7.90%、最大回撤 12.90%、夏普 -1.44、胜率 32.31%（随机数据上属正常）
- 运行 `pytest tests/test_backtest.py`：8 个测试全部通过

### 数据源探索

- akshare：因 Git 代理配置干扰 Python requests 库，无法连接东方财富 API
- baostock：不支持 ETF 数据，仅支持股票和指数
- xtquant：需要 QMT 客户端运行才能连接 xtdata
- 结论：真实数据回测需启动 QMT 客户端，或关闭系统代理后重试 akshare

### 文档更新

- 创建 `docs/STATUS.md`：项目完成状态总览
- 创建 `docs/DEVLOG.md`：本开发日志
