<template>
  <div class="dashboard-wrapper">
    <header class="main-header">
      <div class="header-left">
        <span class="time-box">{{ currentTime }}</span>
      </div>

      <div class="header-center">
        <h1>多源数据融合的飞行态势智能感知与协同预测系统</h1>
        <div class="header-line"></div>
      </div>

      <div class="header-right">
        <div v-if="isPredicting" class="mini-progress-wrapper">
          <span class="loading-text">LSTM 算法推理中...</span>
          <div class="mini-progress">
            <div class="mini-progress-bar"></div>
          </div>
        </div>

        <template v-else>
          <input type="file" id="file-upload" @change="handleFileUpload" accept=".csv" hidden />
          <label for="file-upload" class="upload-btn">
            <span class="icon">⏏</span> 导入运行数据集 (.csv)
          </label>
        </template>
      </div>
    </header>

    <main class="main-content">
      <div class="column left-column">
        <div class="panel status-panel">
          <div class="panel-inner">
            <div class="overview">
              <div class="ov-item" @click="toggleInfoItem('flightNumber')">
                <span class="label">架次编号</span>
                <h4 class="value">{{ flightInfo.flightNumber }}</h4>
              </div>

              <div class="ov-item" @click="toggleInfoItem('dataType')">
                <span class="label">数据类型</span>
                <h4 class="value highlight-blue">{{ flightInfo.dataType }}</h4>
              </div>

              <div class="ov-item" @click="toggleInfoItem('sampleCount')">
                <span class="label">样本数量</span>
                <h4 class="value">{{ flightInfo.sampleCount }}</h4>
              </div>

              <div class="ov-item" @click="toggleInfoItem('analysisStatus')">
                <span class="label">分析状态</span>
                <h4 class="value" :class="hasImportedData ? 'highlight-green' : 'highlight-red'">
                  {{ flightInfo.analysisStatus }}
                </h4>
              </div>
            </div>
          </div>
        </div>

        <div class="panel metrics-panel">
          <div class="panel-inner">
            <div class="panel-title">发动机整体关键指标</div>

            <div class="metrics-grid">
              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.maxEgt }}<small>°C</small></h2>
                <span class="m-label">平均排气温度</span>
              </div>

              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.maxRpm }}<small>RPM</small></h2>
                <span class="m-label">平均转速</span>
              </div>

              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.oilConsumption }}<small>L/h</small></h2>
                <span class="m-label">滑油消耗率</span>
              </div>

              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.fuelConsumption }}<small>L/h</small></h2>
                <span class="m-label">燃油消耗率</span>
              </div>

              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.oilTemp }}<small>°C</small></h2>
                <span class="m-label">滑油温度</span>
              </div>

              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.combustionTemp }}<small>°C</small></h2>
                <span class="m-label">燃烧室温度</span>
              </div>

              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.vibrationAvg }}<small>mm/s</small></h2>
                <span class="m-label">平均振动值</span>
              </div>

              <div class="m-item">
                <h2 class="m-value">{{ engineMetrics.thrust }}<small>kN</small></h2>
                <span class="m-label">推力值</span>
              </div>
            </div>

            <div class="sub-chart-section">
              <div class="chart-header">
                <span class="sub-title">指标变化趋势</span>
                <div class="param-tabs">
                  <span
                      v-for="param in trendParams"
                      :key="param"
                      @click="changeTrendParam(param)"
                      :class="{ active: selectedTrendParam === param }"
                  >
                    {{ param }}
                  </span>
                </div>
              </div>

              <div ref="componentTrendChartRef" class="trend-chart"></div>
            </div>
          </div>
        </div>

        <div class="panel fault-pie-panel">
          <div class="panel-inner fault-pie-inner">
            <div class="panel-title">故障等级统计</div>

            <div class="pie-container">
              <div ref="levelPieChartRef" class="pie-chart"></div>

              <div class="pie-legend">
                <div class="leg-item severe" @click="showLevelDetails('severe')">
                  <span>严重</span>
                  <strong>{{ faultLevels.severe }}</strong>
                </div>

                <div class="leg-item moderate" @click="showLevelDetails('moderate')">
                  <span>中等</span>
                  <strong>{{ faultLevels.moderate }}</strong>
                </div>

                <div class="leg-item minor" @click="showLevelDetails('minor')">
                  <span>轻微</span>
                  <strong>{{ faultLevels.minor }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间列 -->
      <div class="column middle-column">
        <div class="panel model-panel">
          <div class="panel-inner">
            <div class="model-header">
              <div class="panel-title">发动机 3D 孪生体</div>

              <div class="model-tools">
                <button @click="toggleModelRotation">旋转</button>
                <button @click="resetView">重置</button>
              </div>
            </div>

            <div ref="modelContainerRef" class="three-container"></div>
          </div>
        </div>

        <div class="panel ranking-panel">
          <div class="panel-inner">
            <div class="panel-title">部件预警频次排行</div>

            <div v-if="faultRanking.length === 0" class="empty-block">
              请先导入运行数据集
            </div>

            <div v-else class="rank-list">
              <div
                  v-for="(item, index) in faultRanking"
                  :key="index"
                  class="rank-row"
                  @click="selectComponent(item.part)"
              >
                <span class="r-num">{{ index + 1 }}</span>
                <span class="r-name">{{ item.part }}</span>
                <div class="r-bar-wrap">
                  <div class="r-bar" :style="{ width: getRankBarWidth(item.count) + '%' }"></div>
                </div>
                <span class="r-count">{{ item.count }} 次</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧列 -->
      <div class="column right-column">
        <div class="panel detail-panel">
          <div class="panel-inner">
            <div class="panel-title">
              部件数据: <span style="color: #fff">{{ selectedComponent.name }}</span>
            </div>

            <div class="detail-header">
              <div class="health-gauge-wrap">
                <div ref="healthGaugeChartRef" class="health-gauge-chart"></div>
                <div class="gauge-label">健康度评分</div>
              </div>

              <div class="comp-sensors">
                <div
                    v-for="(sensor, key) in selectedComponent.sensors"
                    :key="key"
                    class="s-card"
                    @click="toggleSensorDetail(key)"
                >
                  <div class="s-val">
                    {{ sensor.value }}<small>{{ sensor.unit }}</small>
                  </div>
                  <div class="s-lab">{{ sensor.label }}</div>
                </div>
              </div>
            </div>

            <div class="component-status-row">
              <div class="status-chip">
                <span>预警次数</span>
                <strong>{{ selectedComponentEventSummary.count }}</strong>
              </div>

              <div class="status-chip">
                <span>最高风险</span>
                <strong>{{ selectedComponentEventSummary.maxProbability }}%</strong>
              </div>

              <div class="status-chip">
                <span>严重事件</span>
                <strong>{{ selectedComponentEventSummary.severeCount }}</strong>
              </div>

              <div class="status-chip">
                <span>运行状态</span>
                <strong :class="smartMaintenanceSummary.riskClass">
                  {{ smartMaintenanceSummary.riskLevel }}风险
                </strong>
              </div>
            </div>

            <div class="sensor-stat-table">
              <div class="stat-head">
                <span>监测指标</span>
                <span>平均值</span>
                <span>最高值</span>
                <span>最低值</span>
              </div>

              <div
                  v-for="(sensor, index) in selectedComponent.sensors"
                  :key="'stat-' + index"
                  class="stat-row"
              >
                <span class="stat-name">{{ sensor.label }}</span>
                <span>{{ sensor.avg }}{{ sensor.unit }}</span>
                <span>{{ sensor.max }}{{ sensor.unit }}</span>
                <span>{{ sensor.min }}{{ sensor.unit }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel predict-panel">
          <div class="panel-inner">
            <div class="panel-header-row">
              <div class="panel-title">智能维护建议</div>
              <div class="btn-group">
                <button class="ai-btn" @click="goToPredictReport">预测报告</button>
              </div>
            </div>

            <template v-if="hasImportedData">
              <div class="advice-summary">
                <div class="summary-item">
                  <span class="summary-label">综合风险</span>
                  <strong :class="smartMaintenanceSummary.riskClass">
                    {{ smartMaintenanceSummary.riskLevel }}
                  </strong>
                </div>

                <div class="summary-item">
                  <span class="summary-label">当前部件</span>
                  <strong>{{ selectedComponent.name }}</strong>
                </div>

                <div class="summary-item">
                  <span class="summary-label">严重占比</span>
                  <strong>{{ smartMaintenanceSummary.severeRatio }}%</strong>
                </div>
              </div>

              <div class="advice-list">
                <div
                    v-for="(item, index) in maintenanceAdviceList"
                    :key="index"
                    class="advice-card"
                    @click.stop="showPredictionDetails(item)"
                >
                  <div class="advice-top">
                    <span class="advice-part">
                      <i class="icon-warn">!</i> {{ item.area }}
                    </span>
                    <span class="priority-tag" :class="item.priorityClass">
                      {{ item.priority }}
                    </span>
                  </div>

                  <div class="advice-mid">
                    <span>风险概率</span>
                    <div class="p-bar-wrap">
                      <div
                          class="p-bar animated-stripe"
                          :style="{ width: item.probability + '%' }"
                      ></div>
                    </div>
                    <strong>{{ item.probability }}%</strong>
                  </div>

                  <div class="advice-msg" :title="item.suggestion">
                    {{ item.suggestion }}
                  </div>
                </div>
              </div>
            </template>

            <div v-else class="empty-block">
              导入数据集后生成智能维护建议
            </div>
          </div>
        </div>

        <div class="panel log-panel">
          <div class="panel-inner">
            <div class="panel-header-row">
              <div class="panel-title">最近异常事件</div>
              <span class="log-total">共 {{ faultDetails.length }} 条</span>
            </div>

            <div v-if="faultDetails.length === 0" class="empty-block">
              导入数据集后显示异常事件
            </div>

            <div v-else class="compact-log-list">
              <div
                  v-for="(item, index) in faultDetails"
                  :key="index"
                  class="compact-log-row"
                  @click="showFaultDetails(item)"
              >
                <span class="tl-time">{{ item.time }}</span>
                <span class="log-tag" :class="item.level">{{ item.levelText }}</span>
                <span class="log-desc" :title="item.description">
                  {{ item.description }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import * as THREE from 'three'
import { useRouter } from 'vue-router'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import Papa from 'papaparse'

const isPredicting = ref(false)
const currentTime = ref(new Date().toLocaleTimeString())

let timeInterval: any
timeInterval = setInterval(() => {
  currentTime.value = new Date().toLocaleTimeString()
}, 1000)
const router = useRouter()
const levelPieChartRef = ref<HTMLElement>()
const componentTrendChartRef = ref<HTMLElement>()
const modelContainerRef = ref<HTMLElement>()
const healthGaugeChartRef = ref<HTMLElement>()

const dataset = shallowRef<any[]>([])
const componentBackendStats = ref<Record<string, Record<string, any>>>({})

const hasImportedData = computed(() => {
  return dataset.value.length > 0 || faultDetails.value.length > 0
})

const engineMetrics = ref({
  maxEgt: '-' as number | string,
  maxRpm: '-' as number | string,
  oilConsumption: '-' as number | string,
  fuelConsumption: '-' as number | string,
  oilTemp: '-' as number | string,
  combustionTemp: '-' as number | string,
  vibrationAvg: '-' as number | string,
  thrust: '-' as number | string
})

const displayRangeMap: Record<string, [number, number]> = {
  Exhaust_Gas_Temp: [520, 860],
  Overall_Temperature: [680, 1050],
  Engine_Inlet_Temp: [18, 145],
  Transmission_Temp: [70, 180],
  Engine_Oil_Temp: [55, 125],
  Fuel_Tank_Temp: [18, 58],
  Outside_Air_Temperature: [-20, 40],
  Outside_Air_Temperature_2: [-20, 40],

  Engine_RPM: [5200, 14800],
  Turbocharger_RPM: [8500, 24500],
  Transmission_Input_RPM: [2400, 7600],
  Main_Rotor_RPM: [220, 420],

  Engine_Oil_Pressure: [2.2, 7.5],
  Intake_Manifold_Pressure: [0.8, 3.6],
  Fuel_Injection_Pressure: [24, 88],
  Fuel_System_Pressure: [2.4, 6.8],
  Exhaust_System_Pressure: [0.6, 2.8],
  Atmospheric_Pressure: [0.72, 1.05],

  Air_Intake_Flow: [12, 105],
  Exhaust_Gas_Flow: [18, 130],
  Fuel_Flow_Rate: [80, 420],
  Fuel_Consumption_Rate: [120, 520],
  Oil_Flow_Rate: [4, 18],

  Vibration_Level: [0.5, 5.5],
  Transmission_Vibration_X_Axis: [0.3, 4.8],
  Engine_Vibration_X_Axis: [0.4, 5.2],
  Engine_Vibration_Z_Axis: [0.4, 5.6],

  Engine_Thrust: [12, 58],
  Air_Speed_Indicated: [80, 240],
  Rotor_Blade_Wear: [2, 38],
  Engine_Knock_Detection: [0, 8],

  Component_Health_Index: [68, 96],
  Engine_Health_Index: [70, 97],
  Transmission_Health_Index: [70, 96],
  Lubrication_System_Health: [68, 97],
  Fuel_System_Health: [70, 97],
  Engine_Oil_Level: [62, 98],
  Exhaust_Valve_Position_1: [20, 86]
}

const scaleDisplayValue = (value: number | string, key: string): number | string => {
  const num = Number(value)
  if (Number.isNaN(num)) return '-'

  const range = displayRangeMap[key]
  if (!range) return Number(num.toFixed(1))

  const [low, high] = range

  // 普通指标仍然使用压缩映射，避免脱敏数据过大
  const scaled = low + (high - low) * ((Math.tanh(num / 100) + 1) / 2)
  const clipped = Math.min(high, Math.max(low, scaled))

  return Number(clipped.toFixed(1))
}

const scaleTrendSeries = (values: number[], key: string): number[] => {
  if (!values.length) return []

  const range = displayRangeMap[key]
  if (!range) {
    return values.map((v) => Number(v.toFixed(1)))
  }

  const [low, high] = range
  const minRaw = Math.min(...values)
  const maxRaw = Math.max(...values)

  // 如果原始数据确实完全没有波动，就返回同一水平值
  // 这种情况说明该字段本身在数据集中变化很小或没有变化
  if (maxRaw === minRaw) {
    const mid = (low + high) / 2
    return values.map(() => Number(mid.toFixed(1)))
  }

  // 趋势图使用 min-max 放缩，保留波动形态
  // 不直接贴近上下边界，留出 10% 视觉缓冲
  const displayLow = low + (high - low) * 0.1
  const displayHigh = high - (high - low) * 0.1

  return values.map((value) => {
    const normalized = (value - minRaw) / (maxRaw - minRaw)
    const scaled = displayLow + normalized * (displayHigh - displayLow)
    return Number(scaled.toFixed(1))
  })
}

const componentSensorsMap: Record<string, any[]> = {
  '动力涡轮': [
    { key: 'Transmission_Temp', label: '涡轮温度', unit: '°C' },
    { key: 'Transmission_Input_RPM', label: '输入转速', unit: 'RPM' },
    { key: 'Transmission_Vibration_X_Axis', label: 'X轴振动', unit: 'mm/s' },
    { key: 'Transmission_Health_Index', label: '健康指数', unit: '%' }
  ],
  '燃气涡轮': [
    { key: 'Exhaust_Gas_Temp', label: '排气温度', unit: '°C' },
    { key: 'Turbocharger_RPM', label: '涡轮转速', unit: 'RPM' },
    { key: 'Exhaust_Gas_Flow', label: '排气流量', unit: 'kg/s' },
    { key: 'Engine_Health_Index', label: '健康指数', unit: '%' }
  ],
  '压气机': [
    { key: 'Engine_Inlet_Temp', label: '进气温度', unit: '°C' },
    { key: 'Intake_Manifold_Pressure', label: '歧管压力', unit: 'bar' },
    { key: 'Air_Intake_Flow', label: '进气流量', unit: 'kg/s' },
    { key: 'Component_Health_Index', label: '健康指数', unit: '%' }
  ],
  '燃烧室': [
    { key: 'Fuel_Injection_Pressure', label: '喷油压力', unit: 'bar' },
    { key: 'Engine_Knock_Detection', label: '爆震指数', unit: '次' },
    { key: 'Overall_Temperature', label: '整体温度', unit: '°C' },
    { key: 'Fuel_Consumption_Rate', label: '燃油消耗率', unit: 'L/h' }
  ],
  '滑油系统': [
    { key: 'Engine_Oil_Temp', label: '滑油温度', unit: '°C' },
    { key: 'Engine_Oil_Pressure', label: '滑油压力', unit: 'bar' },
    { key: 'Engine_Oil_Level', label: '滑油液位', unit: '%' },
    { key: 'Lubrication_System_Health', label: '系统健康', unit: '%' }
  ],
  '燃油系统': [
    { key: 'Fuel_Tank_Temp', label: '燃油温度', unit: '°C' },
    { key: 'Fuel_System_Pressure', label: '系统压力', unit: 'bar' },
    { key: 'Fuel_Flow_Rate', label: '燃油流量', unit: 'L/h' },
    { key: 'Fuel_System_Health', label: '系统健康', unit: '%' }
  ],
  '进气道': [
    { key: 'Outside_Air_Temperature', label: '外部气温', unit: '°C' },
    { key: 'Atmospheric_Pressure', label: '大气压力', unit: 'bar' },
    { key: 'Air_Intake_Flow', label: '进气流量', unit: 'kg/s' },
    { key: 'Outside_Air_Temperature_2', label: '备用温度', unit: '°C' }
  ],
  '排气系统': [
    { key: 'Exhaust_Gas_Temp', label: '排气温度', unit: '°C' },
    { key: 'Exhaust_System_Pressure', label: '排气压力', unit: 'bar' },
    { key: 'Exhaust_Gas_Flow', label: '排气流量', unit: 'kg/s' },
    { key: 'Exhaust_Valve_Position_1', label: '阀门开度', unit: '%' }
  ],
  '涡轮叶片': [
    { key: 'Rotor_Blade_Wear', label: '叶片磨损', unit: '%' },
    { key: 'Engine_Vibration_Z_Axis', label: 'Z轴振动', unit: 'mm/s' },
    { key: 'Main_Rotor_RPM', label: '主转子转速', unit: 'RPM' },
    { key: 'Component_Health_Index', label: '健康指数', unit: '%' }
  ],
  '压缩机叶片': [
    { key: 'Engine_Vibration_X_Axis', label: 'X轴振动', unit: 'mm/s' },
    { key: 'Air_Speed_Indicated', label: '指示空速', unit: 'kts' },
    { key: 'Component_Health_Index', label: '健康指数', unit: '%' },
    { key: 'Air_Intake_Flow', label: '进气流量', unit: 'kg/s' }
  ]
}

const selectedComponent = ref({
  name: '压气机',
  healthScore: 0,
  sensors: [] as Array<{
    label: string,
    value: number | string,
    unit: string,
    avg: number | string,
    max: number | string,
    min: number | string
  }>
})

const trendParams = ['温度', '转速', '压力', '振动']
const selectedTrendParam = ref('温度')
const trendParamsMap: Record<string, string> = {
  温度: 'Exhaust_Gas_Temp',
  转速: 'Engine_RPM',
  压力: 'Engine_Oil_Pressure',
  振动: 'Vibration_Level'
}

const flightInfo = ref({
  flightNumber: 'CZ-8089',
  dataType: '单架次数据',
  sampleCount: '-',
  analysisStatus: '未导入'
})

const faultLevels = ref({
  severe: 0,
  moderate: 0,
  minor: 0
})

const faultRanking = ref<Array<any>>([])
const faultPredictions = ref<Array<any>>([])
const faultDetails = ref<Array<any>>([])

const getAverage = (key: string): number | string => {
  if (!dataset.value || dataset.value.length === 0) return '-'

  let sum = 0
  let count = 0

  for (let i = 0; i < dataset.value.length; i++) {
    const val = parseFloat(dataset.value[i][key])
    if (!isNaN(val)) {
      sum += val
      count++
    }
  }

  if (count === 0) return '-'
  return scaleDisplayValue(sum / count, key)
}

const getSensorStats = (partName: string, key: string): any => {
  const backendStats = componentBackendStats.value?.[partName]?.[key]

  if (backendStats) {
    return {
      avg: backendStats.avg ?? '-',
      max: backendStats.max ?? '-',
      min: backendStats.min ?? '-'
    }
  }

  if (!dataset.value || dataset.value.length === 0) {
    return {
      avg: '-',
      max: '-',
      min: '-'
    }
  }

  const values = dataset.value
      .map((row: any) => Number(row[key]))
      .filter((value: number) => !Number.isNaN(value))

  if (values.length === 0) {
    return {
      avg: '-',
      max: '-',
      min: '-'
    }
  }

  const sum = values.reduce((acc: number, value: number) => acc + value, 0)

  return {
    avg: scaleDisplayValue(sum / values.length, key),
    max: scaleDisplayValue(Math.max(...values), key),
    min: scaleDisplayValue(Math.min(...values), key)
  }
}

const handleFileUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  isPredicting.value = true

  Papa.parse(file, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
    transformHeader: (h) => h.replace(/[\r\n\s]+/g, ''),
    complete: (res) => {
      if (res.data.length > 0) {
        dataset.value = Object.freeze(res.data) as any[]
        flightInfo.value.sampleCount = `${res.data.length} 条`
        flightInfo.value.analysisStatus = '分析中'
        updateDashboardData()
      }
    }
  })

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('http://localhost:8000/api/predict', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()

    if (result.status === 'success') {
      flightInfo.value.analysisStatus = '已完成'

      const predData = result.data
      const fallbackPart = '燃气涡轮'

      if (predData.globalMetrics) {
        engineMetrics.value = {
          maxEgt: predData.globalMetrics.maxEgt ?? '-',
          maxRpm: predData.globalMetrics.maxRpm ?? '-',
          oilConsumption: predData.globalMetrics.oilConsumption ?? '-',
          fuelConsumption: predData.globalMetrics.fuelConsumption ?? '-',
          oilTemp: predData.globalMetrics.oilTemp ?? '-',
          combustionTemp: predData.globalMetrics.combustionTemp ?? '-',
          vibrationAvg: predData.globalMetrics.vibrationAvg ?? '-',
          thrust: predData.globalMetrics.thrust ?? '-'
        }
      }

      const rankMap = new Map()

      predData.faultRanking.forEach((item: any) => {
        const pName = item.part === '综合系统' ? fallbackPart : item.part

        if (rankMap.has(pName)) {
          rankMap.get(pName).count += item.count
        } else {
          rankMap.set(pName, { ...item, part: pName })
        }
      })

      faultRanking.value = Array.from(rankMap.values()).sort((a: any, b: any) => b.count - a.count)

      predData.faultPredictions.forEach((item: any) => {
        if (item.area === '综合系统') item.area = fallbackPart
      })

      faultPredictions.value = predData.faultPredictions

      predData.faultDetails.forEach((item: any) => {
        if (item.part === '综合系统') {
          item.part = fallbackPart
          item.description = item.description.replace('综合系统', fallbackPart)
        }
      })

      faultDetails.value = predData.faultDetails
      faultLevels.value = predData.faultLevels
      componentBackendStats.value = predData.componentStats || {}

      initLevelPieChart()
      selectComponent(selectedComponent.value.name)
    } else {
      flightInfo.value.analysisStatus = '分析失败'
    }
  } catch (error) {
    flightInfo.value.analysisStatus = '分析失败'
    console.error('模型推理接口调用失败:', error)
  } finally {
    isPredicting.value = false
    target.value = ''
  }
}

const updateDashboardData = () => {
  engineMetrics.value = {
    maxEgt: getAverage('Exhaust_Gas_Temp'),
    maxRpm: getAverage('Engine_RPM'),
    oilConsumption: getAverage('Oil_Flow_Rate'),
    fuelConsumption: getAverage('Fuel_Consumption_Rate'),
    oilTemp: getAverage('Engine_Oil_Temp'),
    combustionTemp: getAverage('Overall_Temperature'),
    vibrationAvg: getAverage('Vibration_Level'),
    thrust: getAverage('Engine_Thrust')
  }

  selectComponent(selectedComponent.value.name)
  updateComponentTrendChart()
}

function calculateHealthScore(partName: string) {
  if (!hasImportedData.value) return 0

  let penalty = 0
  let isFaulty = false

  faultDetails.value.forEach((item: any) => {
    if (item.part === partName || (item.description && item.description.includes(partName))) {
      isFaulty = true

      if (item.level === 'severe') penalty += 7
      else if (item.level === 'moderate') penalty += 4
      else if (item.level === 'minor') penalty += 1.6
    }
  })

  const rankItem = faultRanking.value.find((item: any) => item.part === partName)

  if (rankItem) {
    isFaulty = true
    penalty += rankItem.count * 0.35
  }

  if (penalty > 24) penalty = 24

  const baseScore = isFaulty ? 94 : 98
  let score = baseScore - penalty

  if (score < 66) score = 66
  if (score > 98) score = 98

  return Math.round(score)
}

function selectComponent(part: string) {
  selectedComponent.value.name = part

  const mapConfig = componentSensorsMap[part]
  selectedComponent.value.healthScore = calculateHealthScore(part)

  if (mapConfig) {
    selectedComponent.value.sensors = mapConfig.map((m) => {
      if (m.key.includes('Health')) {
        const healthValue = hasImportedData.value ? selectedComponent.value.healthScore : '-'

        return {
          label: m.label,
          unit: m.unit,
          value: healthValue,
          avg: healthValue,
          max: healthValue,
          min: healthValue
        }
      }

      const stats = getSensorStats(part, m.key)

      return {
        label: m.label,
        unit: m.unit,
        value: stats.avg,
        avg: stats.avg,
        max: stats.max,
        min: stats.min
      }
    })
  } else {
    selectedComponent.value.sensors = []
  }

  updateHealthGaugeChart()
}

function getTrendDataFromDataset(key: string, maxPoints = 60) {
  if (!dataset.value || dataset.value.length === 0) {
    return {
      xAxis: [],
      data: []
    }
  }

  const step = Math.max(1, Math.floor(dataset.value.length / maxPoints))
  const xAxis: any[] = []
  const rawValues: number[] = []

  for (let i = 0; i < dataset.value.length; i += step) {
    const rawValue = Number(dataset.value[i][key])

    if (!Number.isNaN(rawValue)) {
      rawValues.push(rawValue)

      xAxis.push(
          dataset.value[i]['Timestamp']
              ? String(dataset.value[i]['Timestamp']).split(' ')[1]?.substring(0, 5) || i
              : i
      )
    }
  }

  return {
    xAxis,
    data: scaleTrendSeries(rawValues, key)
  }
}

function updateComponentTrendChart() {
  if (!componentTrendChartRef.value) return

  const chart = echarts.getInstanceByDom(componentTrendChartRef.value) || echarts.init(componentTrendChartRef.value)
  const { xAxis, data } = getTrendDataFromDataset(trendParamsMap[selectedTrendParam.value])

  chart.setOption({
    grid: {
      top: 28,
      bottom: 32,
      left: 50,
      right: 16
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      backgroundColor: 'rgba(16,17,41,0.8)',
      borderColor: '#00f0ff',
      textStyle: {
        color: '#00f0ff',
        fontSize: 14
      }
    },
    xAxis: {
      type: 'category',
      data: xAxis,
      axisLabel: {
        color: '#4c9bfd',
        fontSize: 13
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0,240,255,0.2)'
        }
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: {
        lineStyle: {
          color: 'rgba(0,240,255,0.05)'
        }
      },
      axisLabel: {
        color: '#4c9bfd',
        fontSize: 13
      }
    },
    series: [
      {
        name: selectedTrendParam.value,
        data,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#00f0ff',
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(0,240,255,0.3)'
            },
            {
              offset: 1,
              color: 'transparent'
            }
          ])
        }
      }
    ]
  })
}

function changeTrendParam(p: string) {
  selectedTrendParam.value = p
  updateComponentTrendChart()
}

function initLevelPieChart() {
  if (!levelPieChartRef.value) return

  const chart = echarts.getInstanceByDom(levelPieChartRef.value) || echarts.init(levelPieChartRef.value)

  chart.setOption({
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['35%', '42%'],
        roseType: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#05081a',
          borderWidth: 2
        },
        label: {
          show: false
        },
        data: [
          {
            value: faultLevels.value.severe,
            name: '严重',
            itemStyle: {
              color: '#ed3f35',
              shadowBlur: 10,
              shadowColor: 'rgba(237, 63, 53, 0.6)'
            }
          },
          {
            value: faultLevels.value.moderate,
            name: '中等',
            itemStyle: {
              color: '#eacf19',
              shadowBlur: 10,
              shadowColor: 'rgba(234, 207, 25, 0.6)'
            }
          },
          {
            value: faultLevels.value.minor,
            name: '轻微',
            itemStyle: {
              color: '#60cda0',
              shadowBlur: 10,
              shadowColor: 'rgba(96, 205, 160, 0.6)'
            }
          }
        ]
      }
    ]
  })
}

function updateHealthGaugeChart() {
  if (!healthGaugeChartRef.value) return

  const chart = echarts.getInstanceByDom(healthGaugeChartRef.value) || echarts.init(healthGaugeChartRef.value)
  const score = selectedComponent.value.healthScore || 0
  const color = score > 80 ? '#00f0ff' : score > 50 ? '#eacf19' : '#ed3f35'

  chart.setOption({
    series: [
      {
        type: 'gauge',
        radius: '90%',
        center: ['50%', '55%'],
        startAngle: 210,
        endAngle: -30,
        axisLine: {
          lineStyle: {
            width: 8,
            color: [
              [score / 100, hasImportedData.value ? color : 'rgba(255,255,255,0.15)'],
              [1, 'rgba(255,255,255,0.1)']
            ]
          }
        },
        pointer: {
          length: '50%',
          width: 3,
          itemStyle: {
            color: hasImportedData.value ? color : 'rgba(255,255,255,0.25)'
          }
        },
        axisTick: {
          show: false
        },
        splitLine: {
          length: 12,
          lineStyle: {
            color: 'auto',
            width: 2
          }
        },
        axisLabel: {
          show: false
        },
        detail: {
          valueAnimation: true,
          formatter: hasImportedData.value ? '{value}' : '--',
          color: '#fff',
          fontSize: 36,
          offsetCenter: [0, '60%'],
          fontFamily: 'Orbitron'
        },
        data: [
          {
            value: score
          }
        ]
      }
    ]
  })
}

const maintenanceSuggestionMap: Record<string, string> = {
  '动力涡轮': '检查涡轮振动、转速波动与轴承润滑状态，必要时降低负载运行。',
  '燃气涡轮': '重点核查涡轮转速、排气温度与冷却流量，确认热端部件工作状态。',
  '压气机': '检查压气机出口压力、进气流量和叶片污染情况，防止压比继续下降。',
  '燃油系统': '检查燃油压力、喷油稳定性和燃油流量传感器，排除供油波动。',
  '排气系统': '检查排气温度峰值、阀门响应和尾喷管状态，关注热负荷异常。',
  '滑油系统': '检查滑油温度、压力、液位和滤清器压差，优先排除润滑不足风险。',
  '燃烧室': '检查喷嘴流量、燃烧稳定性和温度分布，避免局部过热。',
  '进气道': '检查进气流量、外界气压和防冰系统状态，确认进气通道稳定。',
  '涡轮叶片': '检查叶片磨损、振动频谱和转子转速，关注结构疲劳风险。',
  '压缩机叶片': '检查叶片振动、气流稳定性和健康指数，防止叶片效率下降。',
  '综合系统': '建议进行全系统联检，优先复核高波动传感器与高频告警部件。'
}

const getPriority = (probability: number) => {
  if (probability >= 90) {
    return {
      text: '立即检查',
      className: 'priority-severe'
    }
  }

  if (probability >= 70) {
    return {
      text: '重点关注',
      className: 'priority-moderate'
    }
  }

  return {
    text: '持续观察',
    className: 'priority-minor'
  }
}

const getPartFaultStats = (partName: string) => {
  const relatedDetails = faultDetails.value.filter((item: any) => {
    return item.part === partName || (item.description && item.description.includes(partName))
  })

  const rankItem = faultRanking.value.find((item: any) => item.part === partName)
  const matchedPrediction = faultPredictions.value.find((item: any) => item.area === partName)

  const severeCount = relatedDetails.filter((item: any) => item.level === 'severe').length
  const moderateCount = relatedDetails.filter((item: any) => item.level === 'moderate').length
  const minorCount = relatedDetails.filter((item: any) => item.level === 'minor').length
  const count = rankItem?.count || relatedDetails.length || 0

  const maxDetailProb = relatedDetails.reduce((max: number, item: any) => {
    return Math.max(max, Number(item.probability) || 0)
  }, 0)

  const predictedProb = Number(matchedPrediction?.probability) || 0

  // 注意：这里必须按 partName 单独计算健康度，不能直接使用当前 selectedComponent 的健康度
  const partHealthScore = hasImportedData.value ? calculateHealthScore(partName) : 0
  const healthDerivedProb = hasImportedData.value
      ? Math.max(0, Math.min(100, 100 - Number(partHealthScore || 100)))
      : 0

  const probability = Math.max(predictedProb, maxDetailProb, healthDerivedProb)

  return {
    relatedDetails,
    rankItem,
    matchedPrediction,
    severeCount,
    moderateCount,
    minorCount,
    count,
    probability,
    healthScore: partHealthScore
  }
}

const getSensorBrief = (partName: string) => {
  const sensors = selectedComponent.value.name === partName ? selectedComponent.value.sensors : []

  if (!sensors || sensors.length === 0) return ''

  const usefulSensors = sensors
      .filter((sensor: any) => !String(sensor.label).includes('健康'))
      .slice(0, 2)
      .map((sensor: any) => `${sensor.label}均值${sensor.avg}${sensor.unit}`)

  return usefulSensors.length > 0 ? `当前${usefulSensors.join('、')}，` : ''
}

const buildAdviceItem = (partName: string, baseProbability?: number) => {
  const stats = getPartFaultStats(partName)
  const probability = Math.max(Number(baseProbability) || 0, stats.probability)
  const priority = getPriority(probability)
  const sensorBrief = getSensorBrief(partName)

  const riskText = stats.severeCount > 0
      ? `已出现 ${stats.severeCount} 条严重异常，`
      : stats.count > 0
          ? `累计 ${stats.count} 次预警，`
          : '暂无高频告警，'

  return {
    area: partName,
    probability: Math.round(probability),
    priority: priority.text,
    priorityClass: priority.className,
    suggestion: `${sensorBrief}${riskText}${maintenanceSuggestionMap[partName] || '建议结合传感器趋势进行人工复核。'}`
  }
}

const maintenanceAdviceList = computed(() => {
  if (!hasImportedData.value) return []

  const currentPart = selectedComponent.value.name
  const currentAdvice = buildAdviceItem(currentPart)

  const otherAdvices = faultPredictions.value
      .filter((item: any) => item.area !== currentPart)
      .slice(0, 2)
      .map((item: any) => {
        const partName = item.area || '综合系统'
        return {
          ...buildAdviceItem(partName, Number(item.probability) || 0),
          prediction: item.prediction
        }
      })

  if (otherAdvices.length < 2) {
    faultRanking.value
        .filter((item: any) => {
          return item.part !== currentPart && !otherAdvices.some((advice: any) => advice.area === item.part)
        })
        .slice(0, 2 - otherAdvices.length)
        .forEach((item: any) => {
          otherAdvices.push(buildAdviceItem(item.part))
        })
  }

  return [currentAdvice, ...otherAdvices].slice(0, 3)
})

const smartMaintenanceSummary = computed(() => {
  if (!hasImportedData.value) {
    return {
      riskLevel: '--',
      riskClass: '',
      mainPart: selectedComponent.value.name,
      severeRatio: 0
    }
  }

  const total = faultLevels.value.severe + faultLevels.value.moderate + faultLevels.value.minor
  const severeRatio = total > 0 ? Math.round((faultLevels.value.severe / total) * 100) : 0

  const currentPart = selectedComponent.value.name
  const currentStats = getPartFaultStats(currentPart)
  const currentHealth = Number(selectedComponent.value.healthScore) || 100
  const maxProbability = Number(currentStats.probability) || 0

  // 运行状态只根据当前部件判断，不再用全局严重占比决定当前部件风险
  if (
      currentStats.severeCount >= 2 ||
      maxProbability >= 92 ||
      currentHealth < 72
  ) {
    return {
      riskLevel: '高',
      riskClass: 'risk-high',
      mainPart: currentPart,
      severeRatio
    }
  }

  if (
      currentStats.severeCount >= 1 ||
      currentStats.moderateCount >= 2 ||
      maxProbability >= 75 ||
      currentHealth < 86
  ) {
    return {
      riskLevel: '中',
      riskClass: 'risk-mid',
      mainPart: currentPart,
      severeRatio
    }
  }

  return {
    riskLevel: '低',
    riskClass: 'risk-low',
    mainPart: currentPart,
    severeRatio
  }
})

const selectedComponentEventSummary = computed(() => {
  if (!hasImportedData.value) {
    return {
      count: 0,
      severeCount: 0,
      maxProbability: 0
    }
  }

  const partName = selectedComponent.value.name
  const stats = getPartFaultStats(partName)

  return {
    count: stats.count,
    severeCount: stats.severeCount,
    maxProbability: Math.round(Number(stats.probability) || 0)
  }
})

const maxRankCount = computed(() => {
  if (faultRanking.value.length === 0) return 1
  return Math.max(...faultRanking.value.map((item: any) => Number(item.count) || 0), 1)
})

function getRankBarWidth(count: number) {
  return Math.max(6, Math.round((count / maxRankCount.value) * 100))
}

function goToPredictReport() {
  router.push('/predict-report')
}
function toggleInfoItem(item: any) {}
function showLevelDetails(level: any) {}
function toggleSensorDetail(key: any) {}
function showPredictionDetails(item: any) {}
function showFaultDetails(item: any) {}

let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let model: THREE.Object3D | null = null
let controls: OrbitControls | null = null
let raycaster: THREE.Raycaster | null = null
let mouse: THREE.Vector2 = new THREE.Vector2()
let interactiveMeshes: THREE.Mesh[] = []
let isRotating = false
let animationId: number

function initModel() {
  if (!modelContainerRef.value) return

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x05081a)

  camera = new THREE.PerspectiveCamera(
      50,
      modelContainerRef.value.clientWidth / modelContainerRef.value.clientHeight,
      0.1,
      1000
  )
  camera.position.set(5, 3, 8)

  renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true
  })
  renderer.setSize(modelContainerRef.value.clientWidth, modelContainerRef.value.clientHeight)
  modelContainerRef.value.appendChild(renderer.domElement)

  const ambientLight = new THREE.AmbientLight(0xffffff, 1.2)
  scene.add(ambientLight)

  const mainLight = new THREE.DirectionalLight(0xffffff, 1.5)
  mainLight.position.set(5, 10, 7)
  scene.add(mainLight)

  const fillLight = new THREE.DirectionalLight(0xe0eaff, 1.0)
  fillLight.position.set(-5, 3, -5)
  scene.add(fillLight)

  const backLight = new THREE.DirectionalLight(0xffffff, 0.8)
  backLight.position.set(0, -5, 5)
  scene.add(backLight)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.enablePan = false
  controls.minDistance = 2
  controls.maxDistance = 20

  raycaster = new THREE.Raycaster()

  modelContainerRef.value.addEventListener('click', onModelClick)
  modelContainerRef.value.addEventListener('mousemove', onMouseMove)

  loadEngineModel()
  animate()
}

function loadEngineModel() {
  const loader = new GLTFLoader()

  loader.load(
      '/models/turbine__turbofan_engine__jet_engine.glb',
      (gltf) => {
        model = gltf.scene

        if (model) {
          model.scale.set(1.5, 1.5, 1.5)
          scene?.add(model)
          setupModelParts()
        }
      },
      undefined,
      () => {
        createDefaultEngineModel()
      }
  )
}

function setupModelParts() {
  if (!model) return

  const partNames = [
    '压气机',
    '燃烧室',
    '燃气涡轮',
    '动力涡轮',
    '滑油系统',
    '燃油系统',
    '进气道',
    '排气系统',
    '涡轮叶片',
    '压缩机叶片'
  ]

  let partIndex = 0
  interactiveMeshes = []

  model.traverse((child) => {
    if (child instanceof THREE.Mesh && child.geometry) {
      const partName = partNames[partIndex % partNames.length]
      child.userData.mappedPartName = partName
      interactiveMeshes.push(child)
      partIndex++
    }
  })

  applyColorToEngineParts()
}

function applyColorToEngineParts() {
  if (!model) return

  model.traverse((child) => {
    if (child instanceof THREE.Mesh && child.userData.mappedPartName) {
      const partName = child.userData.mappedPartName

      let color = 0xdcdcdc
      let specular = 0xffffff
      let shininess = 100

      switch (partName) {
        case '压气机':
          color = 0x8892b0
          shininess = 80
          break
        case '燃烧室':
          color = 0x64748b
          shininess = 50
          break
        case '燃气涡轮':
          color = 0x94a3b8
          shininess = 90
          break
        case '动力涡轮':
          color = 0xa1a1aa
          shininess = 90
          break
        case '滑油系统':
          color = 0x71717a
          shininess = 40
          break
        case '燃油系统':
          color = 0x52525b
          shininess = 40
          break
        case '进气道':
          color = 0xe2e8f0
          shininess = 120
          break
        case '排气系统':
          color = 0xa3a3a3
          shininess = 60
          break
        case '涡轮叶片':
          color = 0xffffff
          shininess = 150
          break
        case '压缩机叶片':
          color = 0xf8fafc
          shininess = 120
          break
      }

      child.material = new THREE.MeshPhongMaterial({
        color,
        specular,
        shininess,
        side: THREE.DoubleSide
      })

      child.userData.originalMaterial = child.material
    }
  })
}

function createDefaultEngineModel() {
  const geom = new THREE.CylinderGeometry(0.5, 0.5, 3, 32)
  const mat = new THREE.MeshPhongMaterial({
    color: 0xe2e8f0,
    specular: 0xffffff,
    shininess: 100
  })

  model = new THREE.Mesh(geom, mat)
  model.userData.mappedPartName = '压气机'
  model.userData.originalMaterial = mat
  interactiveMeshes.push(model as THREE.Mesh)
  scene?.add(model)
}

function onMouseMove(event: MouseEvent) {
  if (!modelContainerRef.value || !camera || !raycaster || !model) return

  const rect = modelContainerRef.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)

  const intersects = raycaster.intersectObjects(interactiveMeshes, false)

  model.traverse((child) => {
    if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
      child.material = child.userData.originalMaterial
    }
  })

  if (intersects.length > 0) {
    modelContainerRef.value.style.cursor = 'pointer'
    const hoveredPart = intersects[0].object

    if (hoveredPart instanceof THREE.Mesh) {
      hoveredPart.material = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.5
      })
    }
  } else {
    modelContainerRef.value.style.cursor = 'default'
  }
}

function onModelClick(event: MouseEvent) {
  if (!modelContainerRef.value || !camera || !raycaster || !model) return

  const rect = modelContainerRef.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)

  const intersects = raycaster.intersectObjects(interactiveMeshes, false)

  if (intersects.length > 0) {
    const clickedMesh = intersects[0].object
    const mappedName = clickedMesh.userData.mappedPartName

    if (mappedName) {
      selectComponent(mappedName)
    }
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)

  if (isRotating && model) {
    model.rotation.y += 0.01
  }

  if (controls) {
    controls.update()
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

const toggleModelRotation = () => {
  isRotating = !isRotating
}

const resetView = () => {
  if (camera && controls) {
    camera.position.set(5, 3, 8)
    controls.target.set(0, 0, 0)
    controls.update()
  }
}

const onWindowResize = () => {
  if (renderer && camera && modelContainerRef.value) {
    camera.aspect = modelContainerRef.value.clientWidth / modelContainerRef.value.clientHeight
    camera.updateProjectionMatrix()
    renderer.setSize(modelContainerRef.value.clientWidth, modelContainerRef.value.clientHeight)

    echarts.getInstanceByDom(componentTrendChartRef.value as any)?.resize()
    echarts.getInstanceByDom(levelPieChartRef.value as any)?.resize()
    echarts.getInstanceByDom(healthGaugeChartRef.value as any)?.resize()
  }
}

onMounted(() => {
  initModel()
  initLevelPieChart()

  nextTick(() => {
    selectComponent(selectedComponent.value.name)
    updateComponentTrendChart()
  })

  window.addEventListener('resize', onWindowResize)
})

onUnmounted(() => {
  clearInterval(timeInterval)
  window.removeEventListener('resize', onWindowResize)

  if (animationId) {
    cancelAnimationFrame(animationId)
  }

  renderer?.dispose()
})
</script>

<style scoped>
.dashboard-wrapper {
  width: 100vw;
  height: 100vh;
  background-color: #05081a;
  background-image: radial-gradient(circle at center, #0a1435 0%, #05081a 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #fff;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 16px;
}

.main-header {
  height: 70px;
  flex-shrink: 0;
  background: url('../images/header-bg.png') no-repeat center bottom;
  background-size: 100% 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  position: relative;
}

.header-center h1 {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 4px;
  margin: 0;
  background: linear-gradient(to bottom, #fff, #4db7ff);
  -webkit-background-clip: text;
  color: transparent;
  text-shadow: 0 0 15px rgba(77, 183, 255, 0.6);
}

.header-line {
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00f0ff, transparent);
  margin-top: 4px;
}

.time-box {
  color: #00f0ff;
  font-family: 'Orbitron', sans-serif;
  font-weight: bold;
  font-size: 21px;
}

.upload-btn {
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid #00f0ff;
  padding: 8px 18px;
  border-radius: 4px;
  cursor: pointer;
  color: #00f0ff;
  font-size: 16px;
  transition: 0.3s;
  display: inline-block;
}

.upload-btn:hover {
  background: rgba(0, 240, 255, 0.3);
  box-shadow: 0 0 10px #00f0ff;
}

.mini-progress-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.loading-text {
  color: #00f0ff;
  font-size: 14px;
  font-family: 'Orbitron', sans-serif;
  animation: blink 1.2s infinite ease-in-out;
}

.mini-progress {
  width: 180px;
  height: 5px;
  background: rgba(0, 240, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.mini-progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 30%;
  background: #00f0ff;
  border-radius: 2px;
  box-shadow: 0 0 8px #00f0ff;
  animation: indeterminateBar 1.2s infinite linear;
}

@keyframes indeterminateBar {
  0% {
    transform: translateX(-100%);
  }

  100% {
    transform: translateX(350%);
  }
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

.main-content {
  flex: 1;
  display: flex;
  padding: 10px;
  gap: 10px;
  min-height: 0;
}

.column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.left-column {
  width: 28%;
}

.middle-column {
  width: 42%;
}

.right-column {
  width: 30%;
  min-height: 0;
}

.panel {
  background: rgba(16, 25, 58, 0.4);
  border: 1px solid rgba(0, 240, 255, 0.2);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 10px;
  height: 10px;
  border-top: 2px solid #00f0ff;
  border-left: 2px solid #00f0ff;
}

.panel-inner {
  padding: 14px;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.panel-title {
  font-size: 18px;
  font-weight: bold;
  color: #68d8fe;
  padding-left: 10px;
  border-left: 3px solid #00f0ff;
  margin-bottom: 14px;
  flex-shrink: 0;
  line-height: 1.2;
}

.status-panel {
  height: 90px;
  flex-shrink: 0;
}

.overview {
  display: flex;
  justify-content: space-between;
  text-align: center;
  height: 100%;
  align-items: center;
}

.ov-item {
  cursor: pointer;
}

.ov-item .label {
  font-size: 14px;
  color: #4c9bfd;
  display: block;
  margin-bottom: 5px;
}

.ov-item .value {
  font-size: 21px;
  font-weight: bold;
  margin: 0;
}

.metrics-panel {
  flex: 1;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 11px;
  margin-bottom: 15px;
}

.m-item {
  background: rgba(0, 240, 255, 0.05);
  padding: 11px;
  border-radius: 4px;
}

.m-value {
  font-size: 28px;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
  margin: 0;
}

.m-value small {
  font-size: 14px;
  margin-left: 4px;
  color: #00f0ff;
  font-weight: normal;
}

.m-label {
  font-size: 14px;
  color: #4c9bfd;
  margin-top: 5px;
  display: block;
}

.sub-chart-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.sub-title {
  font-size: 14px;
  color: #4c9bfd;
}

.param-tabs {
  display: flex;
  gap: 6px;
}

.param-tabs span {
  font-size: 13px;
  padding: 3px 8px;
  border: 1px solid rgba(0, 240, 255, 0.3);
  cursor: pointer;
  border-radius: 2px;
}

.param-tabs span.active {
  background: #00f0ff;
  color: #000;
  font-weight: bold;
}

.trend-chart {
  flex: 1;
}

.fault-pie-panel {
  height: 182px;
  flex-shrink: 0;
}

.fault-pie-inner {
  padding-top: 12px;
  padding-bottom: 6px;
}

.pie-container {
  display: flex;
  height: calc(100% - 28px);
  align-items: flex-start;
  margin-top: -2px;
}

.pie-chart {
  flex: 1.15;
  height: 118px;
  transform: translateY(-4px);
}

.pie-legend {
  width: 140px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 10px;
  transform: translateY(-2px);
}

.leg-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  cursor: pointer;
  border-radius: 4px;
  border: 1px solid transparent;
  transition: all 0.3s;
  min-height: 28px;
}

.leg-item:hover {
  background: rgba(0, 240, 255, 0.08);
  border-color: rgba(0, 240, 255, 0.3);
  transform: translateX(5px);
}

.leg-item span {
  font-size: 15px;
}

.leg-item strong {
  font-size: 20px;
  font-family: 'Orbitron';
  text-shadow: 0 0 8px currentColor;
}

.leg-item.severe strong {
  color: #ed3f35;
}

.leg-item.moderate strong {
  color: #eacf19;
}

.leg-item.minor strong {
  color: #60cda0;
}

.model-panel {
  flex: 1;
  min-height: 0;
}

.model-header {
  display: flex;
  justify-content: space-between;
}

.model-tools button {
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.5);
  color: #00f0ff;
  font-size: 14px;
  padding: 4px 10px;
  margin-left: 5px;
  cursor: pointer;
}

.three-container {
  flex: 1;
}

.ranking-panel {
  height: 280px;
  flex-shrink: 0;
}

.rank-list {
  overflow-y: auto;
  height: 100%;
  padding-right: 5px;
}

.rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 0;
  border-bottom: 1px solid rgba(0, 240, 255, 0.05);
  cursor: pointer;
  transition: 0.3s;
}

.rank-row:hover {
  background: rgba(0, 240, 255, 0.1);
  padding-left: 5px;
}

.r-num {
  width: 26px;
  font-weight: bold;
  color: #00f0ff;
  font-size: 18px;
}

.r-name {
  width: 100px;
  font-size: 16px;
  font-weight: bold;
}

.r-bar-wrap {
  flex: 1;
  height: 9px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.r-bar {
  height: 100%;
  background: linear-gradient(90deg, #00f0ff, #006cff);
  border-radius: 4px;
}

.r-count {
  font-size: 15px;
  color: #4c9bfd;
  font-weight: bold;
}

.detail-panel {
  height: 430px;
  flex-shrink: 0;
}

.detail-header {
  display: flex;
  gap: 12px;
  height: 132px;
  flex-shrink: 0;
}

.health-gauge-wrap {
  width: 140px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.health-gauge-chart {
  width: 100%;
  height: 135px;
}

.health-gauge-wrap .gauge-label {
  font-size: 15px;
  color: #4c9bfd;
  margin-top: -15px;
}

.comp-sensors {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  align-content: center;
}

.s-card {
  background: rgba(0, 240, 255, 0.03);
  padding: 9px 5px;
  text-align: center;
  cursor: pointer;
  position: relative;
  border: 1px solid transparent;
  min-height: 48px;
}

.s-card::before,
.s-card::after {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  border: 1px solid #00f0ff;
  transition: 0.3s;
}

.s-card::before {
  top: -1px;
  left: -1px;
  border-right: none;
  border-bottom: none;
}

.s-card::after {
  bottom: -1px;
  right: -1px;
  border-left: none;
  border-top: none;
}

.s-card:hover {
  background: rgba(0, 240, 255, 0.1);
}

.s-card:hover::before,
.s-card:hover::after {
  width: 12px;
  height: 12px;
}

.s-val {
  font-size: 26px;
  font-weight: bold;
  color: #fff;
  font-family: 'Orbitron';
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.6);
}

.s-val small {
  font-size: 13px;
  margin-left: 2px;
}

.s-lab {
  font-size: 15px;
  color: #4c9bfd;
  margin-top: 6px;
}

.component-status-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 10px;
  flex-shrink: 0;
}

.status-chip {
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.15);
  padding: 8px 6px;
  border-radius: 4px;
  text-align: center;
}

.status-chip span {
  display: block;
  color: #4c9bfd;
  font-size: 13px;
  margin-bottom: 4px;
}

.status-chip strong {
  color: #fff;
  font-size: 18px;
  font-family: 'Orbitron', 'PingFang SC';
}

.sensor-stat-table {
  margin-top: 10px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  border: 1px solid rgba(0, 240, 255, 0.12);
}

.stat-head,
.stat-row {
  display: grid;
  grid-template-columns: 1.4fr repeat(3, 1fr);
  align-items: center;
  column-gap: 8px;
}

.stat-head {
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgba(10, 18, 45, 0.96);
  color: #68d8fe;
  font-size: 14px;
  padding: 9px 10px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.14);
}

.stat-row {
  color: #dbeafe;
  font-size: 14px;
  padding: 9px 10px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.06);
}

.stat-row:hover {
  background: rgba(0, 240, 255, 0.06);
}

.stat-name {
  color: #fff;
  font-weight: 600;
}

.predict-panel {
  height: 300px;
  flex-shrink: 0;
}

.panel-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.panel-header-row .panel-title {
  margin-bottom: 0;
}

.ai-btn {
  background: rgba(0, 240, 255, 0.2);
  border: 1px solid #00f0ff;
  color: #00f0ff;
  font-size: 14px;
  padding: 4px 12px;
  border-radius: 2px;
  cursor: pointer;
}

.ai-btn:hover {
  background: #00f0ff;
  color: #000;
}

.advice-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  flex-shrink: 0;
  margin-bottom: 10px;
}

.summary-item {
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.12);
  padding: 8px 6px;
  border-radius: 4px;
  text-align: center;
}

.summary-label {
  display: block;
  color: #4c9bfd;
  font-size: 13px;
  margin-bottom: 4px;
}

.summary-item strong {
  font-size: 18px;
  font-family: 'Orbitron', 'PingFang SC';
  color: #fff;
}

.risk-high {
  color: #ed3f35 !important;
  text-shadow: 0 0 8px rgba(237, 63, 53, 0.65);
}

.risk-mid {
  color: #eacf19 !important;
  text-shadow: 0 0 8px rgba(234, 207, 25, 0.55);
}

.risk-low {
  color: #60cda0 !important;
  text-shadow: 0 0 8px rgba(96, 205, 160, 0.55);
}

.advice-list {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.advice-card {
  background: linear-gradient(90deg, rgba(237, 63, 53, 0.1), rgba(0, 240, 255, 0.03));
  border: 1px solid rgba(0, 240, 255, 0.12);
  border-left: 3px solid #ed3f35;
  padding: 8px 10px;
  cursor: pointer;
  transition: 0.3s;
}

.advice-card:hover {
  transform: translateX(4px);
  background: rgba(0, 240, 255, 0.08);
  border-color: rgba(0, 240, 255, 0.35);
}

.advice-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.icon-warn {
  color: #ed3f35;
  font-style: normal;
  font-weight: bold;
  margin-right: 4px;
}

.advice-part {
  font-weight: bold;
  font-size: 16px;
  color: #fff;
}

.priority-tag {
  padding: 3px 8px;
  border-radius: 2px;
  font-size: 13px;
  font-weight: bold;
}

.priority-severe {
  background: rgba(237, 63, 53, 0.2);
  color: #ed3f35;
  border: 1px solid #ed3f35;
}

.priority-moderate {
  background: rgba(234, 207, 25, 0.2);
  color: #eacf19;
  border: 1px solid #eacf19;
}

.priority-minor {
  background: rgba(96, 205, 160, 0.2);
  color: #60cda0;
  border: 1px solid #60cda0;
}

.advice-mid {
  display: grid;
  grid-template-columns: 68px 1fr 54px;
  gap: 8px;
  align-items: center;
  color: #4c9bfd;
  font-size: 14px;
}

.advice-mid strong {
  color: #ed3f35;
  font-family: 'Orbitron';
  font-size: 15px;
  text-align: right;
}

.advice-msg {
  margin-top: 6px;
  color: #cbd5e1;
  font-size: 14px;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.p-bar-wrap {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(237, 63, 53, 0.3);
}

.animated-stripe {
  height: 100%;
  border-radius: 4px;
  background: repeating-linear-gradient(
      -45deg,
      #ed3f35,
      #ed3f35 10px,
      #b81e15 10px,
      #b81e15 20px
  );
  background-size: 28px 28px;
  animation: moveStripes 1s linear infinite;
  box-shadow: 0 0 10px rgba(237, 63, 53, 0.8);
}

@keyframes moveStripes {
  0% {
    background-position: 0 0;
  }

  100% {
    background-position: 28px 0;
  }
}

.log-panel {
  flex: 1;
  min-height: 0;
  flex-shrink: 1;
  display: flex;
  flex-direction: column;
}

.log-total {
  color: #4c9bfd;
  font-size: 14px;
}

.compact-log-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 4px;
  padding-right: 4px;
}

.compact-log-row {
  display: grid;
  grid-template-columns: 84px 60px 1fr;
  align-items: center;
  gap: 9px;
  padding: 8px 9px;
  background: rgba(0, 240, 255, 0.035);
  border-left: 2px solid rgba(0, 240, 255, 0.35);
  cursor: pointer;
  transition: 0.3s;
}

.compact-log-row:hover {
  background: rgba(0, 240, 255, 0.09);
  transform: translateX(3px);
}

.tl-time {
  color: #00f0ff;
  font-family: 'Orbitron';
  font-size: 14px;
  letter-spacing: 0.5px;
}

.log-desc {
  flex: 1;
  font-size: 15px;
  color: #ddd;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-tag {
  padding: 3px 7px;
  border-radius: 3px;
  font-size: 13px;
  flex-shrink: 0;
  font-weight: bold;
  text-align: center;
}

.log-tag.severe {
  background: rgba(237, 63, 53, 0.2);
  color: #ed3f35;
  border: 1px solid #ed3f35;
}

.log-tag.moderate {
  background: rgba(234, 207, 25, 0.2);
  color: #eacf19;
  border: 1px solid #eacf19;
}

.log-tag.minor {
  background: rgba(96, 205, 160, 0.2);
  color: #60cda0;
  border: 1px solid #60cda0;
}

.empty-block {
  flex: 1;
  min-height: 80px;
  border: 1px dashed rgba(0, 240, 255, 0.2);
  background: rgba(0, 240, 255, 0.03);
  color: rgba(104, 216, 254, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  letter-spacing: 1px;
}

.highlight-green {
  color: #60cda0;
}

.highlight-red {
  color: #ed3f35;
}

.highlight-blue {
  color: #00f0ff;
}

::-webkit-scrollbar {
  width: 5px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 240, 255, 0.3);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 240, 255, 0.6);
}
</style>