<template>
  <div class="fault-analysis-viewport">
    <div class="report-header">
      <div class="title">
        <h2>直升机发动机故障段分析报告</h2>
        <p>LSTM模型故障预测 · 基于传感器时序数据分析</p>
      </div>
      <div class="flight-info">
        <div class="tag">分析时间：{{ analysisTime }}</div>
        <div class="tag status success">数据来源：直升机发动机传感器数据</div>
      </div>
    </div>

    <div class="card-grid">
      <div class="card">
        <div class="card-title">总故障段数</div>
        <div class="stat-value danger">{{ faultSegments.length }}</div>
        <div class="stat-desc">识别出的连续故障段</div>
      </div>

      <div class="card">
        <div class="card-title">平均故障长度</div>
        <div class="stat-value">{{ averageFaultLength.toFixed(1) }}</div>
        <div class="stat-desc">样本数/段</div>
      </div>

      <div class="card">
        <div class="card-title">最长故障持续</div>
        <div class="stat-value warning">{{ maxFaultLength }}</div>
        <div class="stat-desc">样本数</div>
      </div>

      <div class="card">
        <div class="card-title">总故障样本</div>
        <div class="stat-value">{{ totalFaultSamples }}</div>
        <div class="stat-desc">占总样本比例 {{ faultRatio }}%</div>
      </div>
    </div>

    <div class="chart-section">
      <div class="chart-card wide">
        <div class="card-title">故障段时长分布</div>
        <div ref="faultLengthChartRef" class="chart"></div>
      </div>
    </div>

    <div class="chart-section">
      <div class="chart-card">
        <div class="card-title">故障类型分布</div>
        <div ref="faultTypeChartRef" class="chart"></div>
      </div>

      <div class="chart-card">
        <div class="card-title">故障严重程度分布</div>
        <div ref="severityChartRef" class="chart"></div>
      </div>
    </div>

    <div class="sensor-section">
      <div class="card-title">关键传感器特征分析</div>
      <div class="sensor-grid">
        <div v-for="(sensor, index) in sensorAnalysis" :key="index" class="sensor-card">
          <div class="sensor-name">{{ sensor.name }}</div>
          <div class="sensor-value" :class="sensor.status">{{ sensor.value }}</div>
          <div class="sensor-desc">{{ sensor.description }}</div>
          <div class="sensor-bar">
            <div class="sensor-bar-fill" :style="{ width: sensor.percentage + '%', background: sensor.color }"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="fault-list-section">
      <div class="card-title">故障段详细信息（前30段）</div>
      <div class="fault-table">
        <table>
          <thead>
            <tr>
              <th>故障段</th>
              <th>起始样本</th>
              <th>结束样本</th>
              <th>持续长度</th>
              <th>Top10关键传感器特征</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in faultSegments" :key="item.故障段">
              <td class="segment-num">{{ item.故障段 }}</td>
              <td>{{ item.起始样本 }}</td>
              <td>{{ item.结束样本 }}</td>
              <td class="length">{{ item.持续长度 }}</td>
              <td class="features">{{ item.Top10关键特征 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="footer-card">
      <div class="conclusion">
        <strong>分析结论：</strong>
        通过LSTM模型对直升机发动机传感器时序数据进行故障预测，
        共识别出 {{ faultSegments.length }} 段连续故障。
        平均故障长度为 {{ averageFaultLength.toFixed(1) }} 个样本，
        最长故障持续 {{ maxFaultLength }} 个样本。
        关键传感器特征分析显示，排气温度(EGT)、发动机转速、滑油压力等为核心监控参数。
      </div>
      <div class="btns">
        <button class="btn primary" @click="exportReport">导出报告</button>
        <button class="btn" @click="refreshData">刷新数据</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as echarts from 'echarts'
import { engineDataConfig } from './engineDataConfig'

interface FaultSegment {
  故障段: number
  起始样本: number
  结束样本: number
  持续长度: number
  Top10关键特征: string
}

interface SensorAnalysis {
  name: string
  value: string
  description: string
  percentage: number
  color: string
  status: string
}

const faultLengthChartRef = ref<HTMLElement>()
const faultTypeChartRef = ref<HTMLElement>()
const severityChartRef = ref<HTMLElement>()

const analysisTime = ref('')

const faultSegments = ref<FaultSegment[]>([])

const sensorAnalysis = ref(engineDataConfig.sensorAnalysis)

const averageFaultLength = computed(() => {
  if (faultSegments.value.length === 0) return 0
  const total = faultSegments.value.reduce((sum, item) => sum + item.持续长度, 0)
  return total / faultSegments.value.length
})

const maxFaultLength = computed(() => {
  if (faultSegments.value.length === 0) return 0
  return Math.max(...faultSegments.value.map(item => item.持续长度))
})

const totalFaultSamples = computed(() => {
  return faultSegments.value.reduce((sum, item) => sum + item.持续长度, 0)
})

const faultRatio = computed(() => {
  const totalSamples = 26304 - 20
  return ((totalFaultSamples.value / totalSamples) * 100).toFixed(2)
})

function loadFaultData() {
  faultSegments.value = engineDataConfig.faultSegments

  analysisTime.value = new Date().toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function initFaultLengthChart() {
  if (!faultLengthChartRef.value) return

  const chart = echarts.init(faultLengthChartRef.value)

  const data = faultSegments.value.slice(0, 10).map(item => ({
    value: item.持续长度,
    name: `段${item.故障段}`
  }))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10,20,40,0.95)',
      borderColor: '#00f0ff',
      borderWidth: 1,
      textStyle: { color: '#00f0ff' },
      formatter: '{b}: {c} 个样本'
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: { lineStyle: { color: '#00f0ff' } },
      axisLabel: { color: '#c1e8ff', rotate: 0 }
    },
    yAxis: {
      type: 'value',
      name: '故障长度',
      axisLine: { lineStyle: { color: '#00f0ff' } },
      axisLabel: { color: '#c1e8ff' },
      splitLine: { lineStyle: { color: 'rgba(0,240,255,0.1)' } }
    },
    series: [{
      type: 'bar',
      data: data,
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#ff4444' },
            { offset: 0.5, color: '#ff6b6b' },
            { offset: 1, color: '#ffa8a8' }
          ]
        },
        borderRadius: [4, 4, 0, 0]
      },
      barWidth: '50%',
      label: {
        show: true,
        position: 'top',
        color: '#00f0ff',
        fontSize: 12,
        formatter: '{c}'
      }
    }],
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: '10%'
    },
    backgroundColor: 'transparent'
  })
}

function initFaultTypeChart() {
  if (!faultTypeChartRef.value) return

  const chart = echarts.init(faultTypeChartRef.value)

  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10,20,40,0.95)',
      borderColor: '#00f0ff',
      borderWidth: 1,
      textStyle: { color: '#00f0ff' }
    },
    series: [{
      type: 'pie',
      radius: ['30%', '70%'],
      roseType: 'radius',
      itemStyle: {
        borderColor: 'rgba(0,240,255,0.3)',
        borderWidth: 2,
        borderRadius: 4
      },
      label: {
        show: true,
        color: '#00f0ff',
        fontSize: 11,
        formatter: '{b}\n{c}次',
        lineHeight: 14
      },
      labelLine: {
        length: 8,
        length2: 12,
        lineStyle: { color: '#00f0ff', width: 1 }
      },
      data: [
        { value: 35, name: '温度异常', itemStyle: { color: '#ff4444' } },
        { value: 25, name: '压力异常', itemStyle: { color: '#ff6b35' } },
        { value: 20, name: '振动异常', itemStyle: { color: '#ffa500' } },
        { value: 15, name: '转速异常', itemStyle: { color: '#ffd700' } },
        { value: 5, name: '其他', itemStyle: { color: '#9acd32' } }
      ]
    }],
    backgroundColor: 'transparent'
  })
}

function initSeverityChart() {
  if (!severityChartRef.value) return

  const chart = echarts.init(severityChartRef.value)

  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10,20,40,0.95)',
      borderColor: '#00f0ff',
      borderWidth: 1,
      textStyle: { color: '#00f0ff' }
    },
    series: [{
      type: 'pie',
      radius: ['25%', '65%'],
      roseType: 'radius',
      itemStyle: {
        borderColor: 'rgba(0,240,255,0.3)',
        borderWidth: 2,
        borderRadius: 4
      },
      label: {
        show: true,
        color: '#00f0ff',
        fontSize: 11,
        formatter: '{b}\n{d}%',
        lineHeight: 14
      },
      labelLine: {
        length: 8,
        length2: 12,
        lineStyle: { color: '#00f0ff', width: 1 }
      },
      data: [
        { value: 15, name: '严重', itemStyle: { color: '#ff4444' } },
        { value: 35, name: '中等', itemStyle: { color: '#ffa500' } },
        { value: 50, name: '轻微', itemStyle: { color: '#4cff7c' } }
      ]
    }],
    backgroundColor: 'transparent'
  })
}

function exportReport() {
  const csvContent = [
    ['故障段', '起始样本', '结束样本', '持续长度', 'Top10关键传感器特征'],
    ...faultSegments.value.map(item => [
      item.故障段.toString(),
      item.起始样本.toString(),
      item.结束样本.toString(),
      item.持续长度.toString(),
      `"${item.Top10关键特征}"`
    ])
  ].map(row => row.join(',')).join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `故障段分析报告_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
}

function refreshData() {
  loadFaultData()
  setTimeout(() => {
    initFaultLengthChart()
    initFaultTypeChart()
    initSeverityChart()
  }, 100)
}

onMounted(() => {
  loadFaultData()
  setTimeout(() => {
    initFaultLengthChart()
    initFaultTypeChart()
    initSeverityChart()
  }, 100)
})
</script>

<style scoped>
.fault-analysis-viewport {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0f172a, #1e293b);
  padding: 24px;
  box-sizing: border-box;
  overflow-y: auto;
  color: #fff;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title h2 {
  margin: 0;
  font-size: 22px;
  color: #00f0ff;
}

.title p {
  margin: 4px 0 0;
  color: #a0b4c8;
  font-size: 14px;
}

.flight-info {
  display: flex;
  gap: 12px;
}

.tag {
  padding: 6px 12px;
  background: rgba(0,240,255,0.1);
  border: 1px solid rgba(0,240,255,0.3);
  border-radius: 6px;
  font-size: 13px;
  color: #c1e8ff;
}

.tag.success {
  background: rgba(76,255,124,0.1);
  border-color: rgba(76,255,124,0.4);
  color: #4cff7c;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.card {
  background: rgba(25,32,56,0.8);
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 10px;
  padding: 20px;
  text-align: center;
}

.card-title {
  font-size: 14px;
  color: #a0b4c8;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #00f0ff;
}

.stat-value.danger { color: #ff4444; }
.stat-value.warning { color: #ffa500; }

.stat-desc {
  font-size: 12px;
  color: #99a6b7;
  margin-top: 4px;
}

.chart-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card {
  background: rgba(25,32,56,0.8);
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 10px;
  padding: 20px;
}

.chart-card.wide {
  grid-column: span 2;
}

.chart {
  height: 280px;
  margin-top: 12px;
}

.sensor-section {
  background: rgba(25,32,56,0.8);
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.sensor-card {
  background: rgba(16,17,41,0.8);
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 8px;
  padding: 16px;
}

.sensor-name {
  font-size: 14px;
  color: #00f0ff;
  font-weight: bold;
  margin-bottom: 8px;
}

.sensor-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.sensor-value.danger { color: #ff4444; }
.sensor-value.warning { color: #ffa500; }
.sensor-value.normal { color: #4cff7c; }

.sensor-desc {
  font-size: 12px;
  color: #99a6b7;
  margin-bottom: 8px;
}

.sensor-bar {
  height: 6px;
  background: rgba(255,255,255,0.1);
  border-radius: 3px;
  overflow: hidden;
}

.sensor-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.fault-list-section {
  background: rgba(25,32,56,0.8);
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
}

.fault-table {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  position: sticky;
  top: 0;
  background: rgba(25,32,56,0.95);
  z-index: 1;
}

th {
  padding: 12px 8px;
  text-align: left;
  color: #00f0ff;
  font-size: 13px;
  border-bottom: 2px solid rgba(0,240,255,0.3);
  font-weight: 600;
}

td {
  padding: 10px 8px;
  font-size: 13px;
  color: #c1e8ff;
  border-bottom: 1px solid rgba(0,240,255,0.1);
}

tr:hover {
  background: rgba(0,240,255,0.05);
}

.segment-num {
  color: #00f0ff;
  font-weight: bold;
}

.length {
  color: #ffa500;
  font-weight: bold;
}

.features {
  font-size: 11px;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.footer-card {
  background: rgba(25,32,56,0.8);
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conclusion {
  flex: 1;
  font-size: 14px;
  color: #c1e8ff;
  line-height: 1.6;
}

.btns {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  background: rgba(0,240,255,0.1);
  color: #00f0ff;
  cursor: pointer;
  font-size: 13px;
}

.btn.primary {
  background: #00f0ff;
  color: #0f172a;
  font-weight: bold;
}

.btn:hover {
  background: rgba(0,240,255,0.2);
}
</style>
