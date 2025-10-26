// API基础URL
const API_BASE_URL = 'http://localhost:8000/api';

// 全局变量
let currentSymbol = 'sh000001';
let currentPeriod = 'daily';
let currentDays = 365;
let klineChart = null;
let realtimeInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    setupEventListeners();
    loadData();
});

// 初始化图表
function initializeChart() {
    const chartDom = document.getElementById('klineChart');
    klineChart = echarts.init(chartDom);
}

// 设置事件监听
function setupEventListeners() {
    document.getElementById('indexSelect').addEventListener('change', function(e) {
        currentSymbol = e.target.value;
        loadData();
    });

    document.getElementById('periodSelect').addEventListener('change', function(e) {
        currentPeriod = e.target.value;
        loadData();
    });

    document.getElementById('daysSelect').addEventListener('change', function(e) {
        currentDays = parseInt(e.target.value);
        loadData();
    });

    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadData();
    });

    document.getElementById('realtimeBtn').addEventListener('click', function() {
        toggleRealtimePanel();
    });
}

// 加载数据
async function loadData() {
    try {
        updateLoadingState(true);

        // 计算日期范围
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - currentDays);

        const startDateStr = formatDate(startDate);
        const endDateStr = formatDate(endDate);

        // 获取历史数据和指标
        const [historicalData, indicatorsData, analysisData] = await Promise.all([
            fetchHistoricalData(currentSymbol, startDateStr, endDateStr, currentPeriod),
            fetchIndicators(currentSymbol, startDateStr, endDateStr, currentPeriod),
            fetchAnalysis(currentSymbol, startDateStr, endDateStr, currentPeriod)
        ]);

        // 更新界面
        if (historicalData) {
            updateInfoCards(historicalData);
            updateChart(historicalData);
        }

        if (indicatorsData) {
            updateIndicators(indicatorsData.signals);
        }

        if (analysisData) {
            updateAnalysis(analysisData);
        }

        updateTime();
        updateLoadingState(false);

    } catch (error) {
        console.error('Error loading data:', error);
        alert('加载数据失败: ' + error.message);
        updateLoadingState(false);
    }
}

// 获取历史数据
async function fetchHistoricalData(symbol, startDate, endDate, period) {
    const response = await fetch(
        `${API_BASE_URL}/historical/${symbol}?start_date=${startDate}&end_date=${endDate}&period=${period}`
    );
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const result = await response.json();
    return result.success ? result.data : null;
}

// 获取技术指标
async function fetchIndicators(symbol, startDate, endDate, period) {
    const response = await fetch(
        `${API_BASE_URL}/indicators/${symbol}?start_date=${startDate}&end_date=${endDate}&period=${period}`
    );
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const result = await response.json();
    return result.success ? result : null;
}

// 获取分析数据
async function fetchAnalysis(symbol, startDate, endDate, period) {
    const response = await fetch(
        `${API_BASE_URL}/analysis/${symbol}?start_date=${startDate}&end_date=${endDate}&period=${period}`
    );
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const result = await response.json();
    return result.success ? result.data : null;
}

// 获取实时数据
async function fetchRealtimeData() {
    const response = await fetch(`${API_BASE_URL}/realtime/all`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const result = await response.json();
    return result.success ? result.data : null;
}

// 更新信息卡片
function updateInfoCards(data) {
    if (!data || data.length === 0) return;

    const latest = data[data.length - 1];

    document.getElementById('currentPrice').textContent = latest.close.toFixed(2);

    const change = latest.change || 0;
    const pctChange = latest.pct_change || 0;

    const changeElement = document.getElementById('priceChange');
    changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}`;
    changeElement.className = change >= 0 ? 'card-change up' : 'card-change down';

    const pctElement = document.getElementById('pctChange');
    pctElement.textContent = `${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(2)}%`;
    pctElement.className = pctChange >= 0 ? 'card-value up' : 'card-value down';

    document.getElementById('volume').textContent = formatNumber(latest.volume);
    document.getElementById('amount').textContent = formatNumber(latest.amount / 100000000, 2);
}

// 更新图表
function updateChart(data) {
    if (!data || data.length === 0) return;

    const dates = data.map(item => item.date);
    const ohlc = data.map(item => [item.open, item.close, item.low, item.high]);
    const volumes = data.map(item => item.volume);

    // 提取MA数据
    const ma5 = data.map(item => item.MA5 || null);
    const ma10 = data.map(item => item.MA10 || null);
    const ma20 = data.map(item => item.MA20 || null);
    const ma60 = data.map(item => item.MA60 || null);

    const option = {
        title: {
            text: '价格走势',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['K线', 'MA5', 'MA10', 'MA20', 'MA60'],
            top: 30
        },
        grid: [
            {
                left: '10%',
                right: '10%',
                top: '15%',
                height: '50%'
            },
            {
                left: '10%',
                right: '10%',
                top: '70%',
                height: '15%'
            }
        ],
        xAxis: [
            {
                type: 'category',
                data: dates,
                scale: true,
                boundaryGap: false,
                axisLine: { onZero: false },
                splitLine: { show: false },
                min: 'dataMin',
                max: 'dataMax'
            },
            {
                type: 'category',
                gridIndex: 1,
                data: dates,
                scale: true,
                boundaryGap: false,
                axisLine: { onZero: false },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false },
                min: 'dataMin',
                max: 'dataMax'
            }
        ],
        yAxis: [
            {
                scale: true,
                splitArea: {
                    show: true
                }
            },
            {
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: { show: false },
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { show: false }
            }
        ],
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0, 1],
                start: 0,
                end: 100
            },
            {
                show: true,
                xAxisIndex: [0, 1],
                type: 'slider',
                top: '90%',
                start: 0,
                end: 100
            }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: ohlc,
                itemStyle: {
                    color: '#ef5350',
                    color0: '#26a69a',
                    borderColor: '#ef5350',
                    borderColor0: '#26a69a'
                }
            },
            {
                name: 'MA5',
                type: 'line',
                data: ma5,
                smooth: true,
                lineStyle: {
                    opacity: 0.5
                }
            },
            {
                name: 'MA10',
                type: 'line',
                data: ma10,
                smooth: true,
                lineStyle: {
                    opacity: 0.5
                }
            },
            {
                name: 'MA20',
                type: 'line',
                data: ma20,
                smooth: true,
                lineStyle: {
                    opacity: 0.5
                }
            },
            {
                name: 'MA60',
                type: 'line',
                data: ma60,
                smooth: true,
                lineStyle: {
                    opacity: 0.5
                }
            },
            {
                name: '成交量',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes
            }
        ]
    };

    klineChart.setOption(option);
}

// 更新技术指标
function updateIndicators(signals) {
    if (!signals) return;

    const grid = document.getElementById('indicatorsGrid');
    grid.innerHTML = '';

    // MA指标
    if (signals.ma && Object.keys(signals.ma).length > 0) {
        const maItem = createIndicatorItem('移动平均线 (MA)', signals.ma);
        grid.appendChild(maItem);
    }

    // MACD指标
    if (signals.macd && Object.keys(signals.macd).length > 0) {
        const macdItem = document.createElement('div');
        macdItem.className = 'indicator-item';
        macdItem.innerHTML = `
            <h3>MACD</h3>
            <div class="indicator-value">
                <span class="label">DIF:</span>
                <span class="value">${signals.macd.dif?.toFixed(2) || '--'}</span>
            </div>
            <div class="indicator-value">
                <span class="label">DEA:</span>
                <span class="value">${signals.macd.dea?.toFixed(2) || '--'}</span>
            </div>
            <div class="indicator-value">
                <span class="label">HIST:</span>
                <span class="value">${signals.macd.hist?.toFixed(2) || '--'}</span>
            </div>
            ${signals.macd.golden_cross ? '<span class="signal-badge bullish">金叉</span>' : ''}
            ${signals.macd.death_cross ? '<span class="signal-badge bearish">死叉</span>' : ''}
        `;
        grid.appendChild(macdItem);
    }

    // KDJ指标
    if (signals.kdj && Object.keys(signals.kdj).length > 0) {
        const kdjItem = document.createElement('div');
        kdjItem.className = 'indicator-item';
        kdjItem.innerHTML = `
            <h3>KDJ</h3>
            <div class="indicator-value">
                <span class="label">K:</span>
                <span class="value">${signals.kdj.k?.toFixed(2) || '--'}</span>
            </div>
            <div class="indicator-value">
                <span class="label">D:</span>
                <span class="value">${signals.kdj.d?.toFixed(2) || '--'}</span>
            </div>
            <div class="indicator-value">
                <span class="label">J:</span>
                <span class="value">${signals.kdj.j?.toFixed(2) || '--'}</span>
            </div>
            ${signals.kdj.overbought ? '<span class="signal-badge bearish">超买</span>' : ''}
            ${signals.kdj.oversold ? '<span class="signal-badge bullish">超卖</span>' : ''}
        `;
        grid.appendChild(kdjItem);
    }

    // RSI指标
    if (signals.rsi && Object.keys(signals.rsi).length > 0) {
        const rsiItem = createIndicatorItem('RSI', signals.rsi);
        grid.appendChild(rsiItem);
    }
}

// 创建指标项
function createIndicatorItem(title, data) {
    const item = document.createElement('div');
    item.className = 'indicator-item';

    let html = `<h3>${title}</h3>`;

    for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'object' && value.value !== undefined) {
            html += `
                <div class="indicator-value">
                    <span class="label">${key}:</span>
                    <span class="value">${value.value.toFixed(2)}</span>
                </div>
            `;
        }
    }

    item.innerHTML = html;
    return item;
}

// 更新分析数据
function updateAnalysis(data) {
    if (!data) return;

    const grid = document.getElementById('analysisGrid');
    grid.innerHTML = '';

    // 统计数据
    if (data.statistics) {
        const stats = data.statistics;
        const statsItem = document.createElement('div');
        statsItem.className = 'analysis-item';
        statsItem.innerHTML = `
            <h3>统计数据</h3>
            <div class="indicator-value">
                <span class="label">最高价:</span>
                <span class="value">${stats.price?.max?.toFixed(2) || '--'}</span>
            </div>
            <div class="indicator-value">
                <span class="label">最低价:</span>
                <span class="value">${stats.price?.min?.toFixed(2) || '--'}</span>
            </div>
            <div class="indicator-value">
                <span class="label">平均价:</span>
                <span class="value">${stats.price?.avg?.toFixed(2) || '--'}</span>
            </div>
            <div class="indicator-value">
                <span class="label">总涨跌幅:</span>
                <span class="value ${stats.change?.total_pct >= 0 ? 'up' : 'down'}">
                    ${stats.change?.total_pct?.toFixed(2) || '--'}%
                </span>
            </div>
        `;
        grid.appendChild(statsItem);
    }

    // 波动率
    if (data.volatility) {
        const vol = data.volatility;
        const volItem = document.createElement('div');
        volItem.className = 'analysis-item';
        volItem.innerHTML = `
            <h3>波动率分析</h3>
            <div class="indicator-value">
                <span class="label">历史波动率:</span>
                <span class="value">${vol.historical?.toFixed(2) || '--'}%</span>
            </div>
            <div class="indicator-value">
                <span class="label">当前波动率:</span>
                <span class="value">${vol.current?.toFixed(2) || '--'}%</span>
            </div>
            <div class="indicator-value">
                <span class="label">平均波动率:</span>
                <span class="value">${vol.avg?.toFixed(2) || '--'}%</span>
            </div>
        `;
        grid.appendChild(volItem);
    }

    // 连涨连跌
    if (data.consecutive_days) {
        const consec = data.consecutive_days;
        const consecItem = document.createElement('div');
        consecItem.className = 'analysis-item';
        consecItem.innerHTML = `
            <h3>连涨连跌</h3>
            <div class="indicator-value">
                <span class="label">当前状态:</span>
                <span class="value ${consec.current?.type === 'up' ? 'up' : 'down'}">
                    ${consec.current?.type === 'up' ? '连涨' : '连跌'} ${consec.current?.days || 0}天
                </span>
            </div>
            <div class="indicator-value">
                <span class="label">最大连涨:</span>
                <span class="value">${consec.max_up?.days || 0}天</span>
            </div>
            <div class="indicator-value">
                <span class="label">最大连跌:</span>
                <span class="value">${consec.max_down?.days || 0}天</span>
            </div>
        `;
        grid.appendChild(consecItem);
    }
}

// 切换实时行情面板
async function toggleRealtimePanel() {
    const panel = document.getElementById('realtimePanel');

    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        await updateRealtimePanel();
        // 每5秒更新一次
        realtimeInterval = setInterval(updateRealtimePanel, 5000);
    } else {
        panel.style.display = 'none';
        if (realtimeInterval) {
            clearInterval(realtimeInterval);
            realtimeInterval = null;
        }
    }
}

// 更新实时行情面板
async function updateRealtimePanel() {
    try {
        const data = await fetchRealtimeData();
        if (!data) return;

        const grid = document.getElementById('realtimeGrid');
        grid.innerHTML = '';

        data.forEach(item => {
            const div = document.createElement('div');
            div.className = `realtime-item ${item.pct_change >= 0 ? 'up' : 'down'}`;
            div.innerHTML = `
                <div class="name">${item.name}</div>
                <div class="price">${item.current.toFixed(2)}</div>
                <div class="change">
                    ${item.pct_change >= 0 ? '+' : ''}${item.pct_change.toFixed(2)}%
                    (${item.change >= 0 ? '+' : ''}${item.change.toFixed(2)})
                </div>
            `;
            grid.appendChild(div);
        });

    } catch (error) {
        console.error('Error updating realtime panel:', error);
    }
}

// 工具函数
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatNumber(num, decimals = 0) {
    if (num >= 100000000) {
        return (num / 100000000).toFixed(decimals) + '亿';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(decimals) + '万';
    }
    return num.toFixed(decimals);
}

function updateTime() {
    const now = new Date();
    document.getElementById('updateTime').textContent = now.toLocaleString('zh-CN');
}

function updateLoadingState(isLoading) {
    const btn = document.getElementById('refreshBtn');
    btn.disabled = isLoading;
    btn.textContent = isLoading ? '加载中...' : '刷新数据';
}
