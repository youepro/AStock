# A股指数实时获取和分析系统

一个功能完整的A股指数实时监控和技术分析系统，提供实时行情、历史数据查询、技术指标计算和数据可视化功能。

## 功能特性

### 核心功能
- ✅ **实时行情获取**：支持7大主要指数的实时数据
- ✅ **历史数据查询**：支持日线、周线、月线多周期数据
- ✅ **技术指标计算**：MA、EMA、BOLL、RSI、KDJ、MACD、OBV等
- ✅ **数据分析**：统计分析、波动率分析、量价关系分析
- ✅ **数据可视化**：K线图、分时图、技术指标图表
- ✅ **数据存储**：SQLite数据库 + Redis缓存
- ✅ **RESTful API**：完整的API接口
- ✅ **Web界面**：直观的数据展示界面

### 支持的指数
- 上证指数（000001.SH）
- 深证成指（399001.SZ）
- 创业板指（399006.SZ）
- 科创50（000688.SH）
- 沪深300（000300.SH）
- 中证500（000905.SH）
- 中证1000（000852.SH）

## 技术栈

### 后端
- **Python 3.8+**
- **FastAPI** - Web框架
- **AkShare** - 数据获取
- **Pandas** - 数据处理
- **SQLAlchemy** - ORM
- **Redis** - 缓存
- **Loguru** - 日志

### 前端
- **HTML5/CSS3/JavaScript**
- **ECharts** - 图表库

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- Redis（可选，用于缓存）

### 2. 安装依赖

```bash
# 克隆项目
cd stockIndex

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据需要修改配置：

```env
# 应用配置
APP_NAME=A股指数分析系统
DEBUG=True

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./data/stock_index.db

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. 启动应用

```bash
python main.py
```

应用将在 `http://localhost:8000` 启动。

### 5. 访问界面

打开浏览器访问：
- **Web界面**：http://localhost:8000
- **API文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## 项目结构

```
stockIndex/
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py        # 配置文件
├── src/                   # 源代码
│   ├── data_fetcher/      # 数据获取模块
│   │   ├── __init__.py
│   │   ├── base_fetcher.py
│   │   └── akshare_fetcher.py
│   ├── indicators/        # 技术指标模块
│   │   ├── __init__.py
│   │   └── calculator.py
│   ├── storage/           # 数据存储模块
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── cache.py
│   ├── analysis/          # 数据分析模块
│   │   ├── __init__.py
│   │   └── analyzer.py
│   ├── api/               # API模块
│   │   ├── __init__.py
│   │   └── main.py
│   ├── constants.py       # 常量定义
│   └── __init__.py
├── frontend/              # 前端文件
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── templates/
│       └── index.html
├── data/                  # 数据目录
├── logs/                  # 日志目录
├── tests/                 # 测试目录
├── main.py               # 应用入口
├── requirements.txt      # 依赖列表
├── .env.example         # 环境变量示例
├── 需求分析.md           # 需求分析文档
└── README.md            # 本文件
```

## API 接口

### 基础接口

#### 获取支持的指数列表
```
GET /api/indices
```

#### 健康检查
```
GET /health
```

### 行情数据接口

#### 获取实时行情
```
GET /api/realtime/{symbol}
```

参数：
- `symbol`: 指数代码（如：sh000001）

#### 获取所有指数实时行情
```
GET /api/realtime/all
```

#### 获取历史数据
```
GET /api/historical/{symbol}?start_date=2024-01-01&end_date=2024-12-31&period=daily
```

参数：
- `symbol`: 指数代码
- `start_date`: 开始日期（YYYY-MM-DD）
- `end_date`: 结束日期（YYYY-MM-DD）
- `period`: 时间周期（daily/weekly/monthly）

### 技术指标接口

#### 获取技术指标
```
GET /api/indicators/{symbol}?start_date=2024-01-01&end_date=2024-12-31
```

返回包含所有技术指标的数据和最新信号。

#### 获取综合分析
```
GET /api/analysis/{symbol}?start_date=2024-01-01&end_date=2024-12-31
```

返回统计分析、波动率分析、连涨连跌等综合数据。

### 对比分析接口

#### 对比多个指数
```
GET /api/compare?symbols=sh000001,sz399001&start_date=2024-01-01&end_date=2024-12-31
```

参数：
- `symbols`: 指数代码列表（逗号分隔）

### 预警接口

#### 获取预警规则
```
GET /api/alerts?symbol=sh000001
```

#### 创建预警规则
```
POST /api/alerts
```

#### 删除预警规则
```
DELETE /api/alerts/{rule_id}
```

## 使用示例

### Python 调用示例

```python
import requests

# 获取实时行情
response = requests.get('http://localhost:8000/api/realtime/sh000001')
data = response.json()
print(data)

# 获取历史数据
response = requests.get(
    'http://localhost:8000/api/historical/sh000001',
    params={
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'period': 'daily'
    }
)
data = response.json()
print(f"获取到 {data['count']} 条数据")

# 获取技术指标
response = requests.get('http://localhost:8000/api/indicators/sh000001')
data = response.json()
signals = data['signals']
print(f"MACD信号: {signals['macd']}")
```

### JavaScript 调用示例

```javascript
// 获取实时行情
fetch('http://localhost:8000/api/realtime/sh000001')
    .then(response => response.json())
    .then(data => {
        console.log('当前价格:', data.data.current);
        console.log('涨跌幅:', data.data.pct_change);
    });

// 获取历史数据
fetch('http://localhost:8000/api/historical/sh000001?start_date=2024-01-01&end_date=2024-12-31')
    .then(response => response.json())
    .then(data => {
        console.log('数据条数:', data.count);
        console.log('历史数据:', data.data);
    });
```

## 技术指标说明

### 趋势指标
- **MA（移动平均线）**：5日、10日、20日、30日、60日、120日、250日
- **EMA（指数移动平均线）**：12日、26日
- **BOLL（布林带）**：中轨、上轨、下轨

### 动量指标
- **RSI（相对强弱指标）**：6日、12日、24日
- **KDJ（随机指标）**：K值、D值、J值
- **MACD**：DIF、DEA、HIST

### 成交量指标
- **VOL（成交量）**
- **VOL_MA（成交量均线）**：5日、10日、20日
- **OBV（能量潮）**

## 数据分析功能

### 统计分析
- 价格统计（最高、最低、平均、标准差）
- 涨跌统计（涨跌天数、涨跌幅）
- 成交量统计

### 波动率分析
- 历史波动率
- 当前波动率
- 波动率区间

### 连涨连跌分析
- 当前连续状态
- 最大连涨天数
- 最大连跌天数

### 量价关系分析
- 价涨量增/价涨量缩
- 价跌量增/价跌量缩
- 成交量异常检测

## 性能优化

### 缓存策略
- 实时数据缓存：5秒
- 历史数据缓存：1小时
- 技术指标缓存：5分钟

### 数据库优化
- 日期和指数代码建立索引
- 批量插入优化
- 连接池管理

## 注意事项

1. **数据来源**：本系统使用AkShare获取数据，数据仅供学习和研究使用
2. **免责声明**：本系统提供的数据和分析仅供参考，不构成投资建议
3. **使用限制**：请遵守数据源的使用条款，避免频繁请求
4. **Redis可选**：如果不使用Redis，系统会自动禁用缓存功能

## 常见问题

### 1. 如何添加新的指数？

编辑 `src/constants.py` 文件，在 `SUPPORTED_INDICES` 字典中添加新的指数信息。

### 2. 如何修改数据更新频率？

编辑 `.env` 文件，修改 `DATA_UPDATE_INTERVAL` 参数。

### 3. 数据存储在哪里？

- SQLite数据库：`data/stock_index.db`
- 日志文件：`logs/app.log`

### 4. 如何清除缓存？

```python
from src.storage import Cache
cache = Cache()
cache.clear_all()
```

### 5. Redis连接失败怎么办？

系统会自动检测Redis连接状态，如果连接失败会禁用缓存功能，不影响主要功能使用。

## 开发计划

- [ ] 添加更多技术指标（CCI、DMI、SAR等）
- [ ] 实现预警通知功能（邮件、微信）
- [ ] 支持个股数据分析
- [ ] 添加回测功能
- [ ] 移动端适配
- [ ] 数据导出功能增强

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue。

---

**免责声明**：本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
