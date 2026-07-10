export interface SensorData {
  name: string
  value: number
  unit: string
  label: string
  description?: string
  status: 'normal' | 'warning' | 'danger'
  percentage: number
  color: string
}

export interface ComponentData {
  name: string
  healthScore: number
  sensors: Record<string, SensorData>
}

export interface FaultSegment {
  故障段: number
  起始样本: number
  结束样本: number
  持续长度: number
  Top10关键特征: string
}

export interface EngineDataConfig {
  flightInfo: {
    flightNumber: string
    phase: string
    systemStatus: string
    engineHoursCurrent: string
    engineHoursTotal: string
  }
  faultLevels: {
    severe: number
    moderate: number
    minor: number
  }
  engineMetrics: {
    maxEgt: number
    maxRpm: number
    oilConsumption: number
    fuelConsumption: number
    oilTemp: number
    combustionTemp: number
    vibrationAvg: number
    thrust: number
  }
  faultRanking: Array<{
    part: string
    count: number
    trend: 'up' | 'down' | 'stable'
  }>
  selectedComponent: ComponentData
  faultPredictions: Array<{
    area: string
    prediction: string
    probability: number
  }>
  faultDetails: Array<{
    time: string
    description: string
    level: 'severe' | 'moderate' | 'minor'
    levelText: string
  }>
  sensorAnalysis: SensorData[]
  faultSegments: FaultSegment[]
  averageFaultLength: number
  maxFaultLength: number
  totalFaultSamples: number
  faultRatio: number
}

export const engineDataConfig: EngineDataConfig = {
  flightInfo: {
    flightNumber: 'ENG20260419',
    phase: '巡航中',
    systemStatus: '发动机正常',
    engineHoursCurrent: '2.5',
    engineHoursTotal: '1250.8',
  },

  faultLevels: {
    severe: 3,
    moderate: 7,
    minor: 12,
  },

  engineMetrics: {
    maxEgt: 547,
    maxRpm: 1640,
    oilConsumption: 0.85,
    fuelConsumption: 167.65,
    oilTemp: 112.89,
    combustionTemp: 200.54,
    vibrationAvg: 237.3,
    thrust: 873.02,
  },

  faultRanking: [
    { part: '动力涡轮', count: 8, trend: 'up' },
    { part: '燃气涡轮', count: 6, trend: 'stable' },
    { part: '压气机', count: 5, trend: 'down' },
    { part: '燃烧室', count: 4, trend: 'up' },
    { part: '滑油系统', count: 3, trend: 'stable' },
    { part: '燃油系统', count: 2, trend: 'down' },
  ],

  selectedComponent: {
    name: '动力涡轮',
    healthScore: 82,
    sensors: {
      temperature: { value: 200.54, unit: '°C', label: '排气温度 (EGT)', status: 'warning', percentage: 78, color: '#ff6b35' },
      rpm: { value: 661.95, unit: 'RPM', label: '转速', status: 'normal', percentage: 65, color: '#4cff7c' },
      pressure: { value: 873.02, unit: 'bar', label: '排气压力', status: 'normal', percentage: 55, color: '#4cff7c' },
      vibration: { value: 237.3, unit: 'mm/s', label: '振动值', status: 'warning', percentage: 72, color: '#ffa500' },
    },
  },

  faultPredictions: [
    { area: '动力涡轮', prediction: '叶片温度偏高风险', probability: 82 },
    { area: '燃气涡轮', prediction: '涡轮叶片磨损风险', probability: 68 },
    { area: '压气机', prediction: '气流喘振预警', probability: 55 },
    { area: '燃烧室', prediction: '燃烧效率下降风险', probability: 42 },
    { area: '滑油系统', prediction: '滑油压力波动', probability: 38 },
    { area: '燃油系统', prediction: '燃油滤清器堵塞预警', probability: 28 },
  ],

  faultDetails: [
    { time: '14:35', description: '动力涡轮排气温度短暂超标', level: 'severe', levelText: '严重' },
    { time: '15:12', description: '压气机出口压力波动超限', level: 'moderate', levelText: '中等' },
    { time: '16:45', description: '滑油系统温度轻微偏高', level: 'minor', levelText: '轻微' },
    { time: '17:28', description: '燃气涡轮振动值突增', level: 'moderate', levelText: '中等' },
    { time: '18:05', description: '燃烧室温度分布不均', level: 'minor', levelText: '轻微' },
  ],

  sensorAnalysis: [
    { name: 'Exhaust_Gas_Temp (EGT)', value: '200.54°C', description: '排气温度均值', status: 'warning', percentage: 82, color: '#ff6b35', label: '排气温度' },
    { name: 'Engine_RPM', value: '661.95', description: '发动机转速均值', status: 'normal', percentage: 65, color: '#4cff7c', label: '发动机转速' },
    { name: 'Engine_Oil_Pressure', value: '873.02', description: '滑油压力均值', status: 'normal', percentage: 58, color: '#4cff7c', label: '滑油压力' },
    { name: 'Engine_Vibration_Level', value: '237.3', description: '振动等级均值', status: 'warning', percentage: 72, color: '#ffa500', label: '振动等级' },
    { name: 'Fuel_Flow_Rate', value: '167.65', description: '燃油流量均值', status: 'normal', percentage: 48, color: '#4cff7c', label: '燃油流量' },
    { name: 'Engine_Thrust', value: '873.02', description: '发动机推力均值', status: 'normal', percentage: 62, color: '#4cff7c', label: '发动机推力' },
    { name: 'Lubrication_System_Health', value: '85%', description: '润滑系统健康', status: 'normal', percentage: 85, color: '#4cff7c', label: '润滑系统健康' },
    { name: 'Engine_Health_Index', value: '78%', description: '发动机综合健康指数', status: 'warning', percentage: 78, color: '#ffa500', label: '发动机健康指数' },
  ],

  faultSegments: [
    { 故障段: 1, 起始样本: 1523, 结束样本: 1656, 持续长度: 134, Top10关键特征: 'Exhaust_Gas_Temp, Engine_RPM, Engine_Oil_Pressure, Engine_Vibration_Level, Fuel_Flow_Rate' },
    { 故障段: 2, 起始样本: 2345, 结束样本: 2489, 持续长度: 145, Top10关键特征: 'Engine_RPM, Exhaust_Gas_Temp, Torque_Output, Engine_Vibration_Level, Oil_Temperature' },
    { 故障段: 3, 起始样本: 3567, 结束样本: 3723, 持续长度: 157, Top10关键特征: 'Engine_Oil_Pressure, Exhaust_Gas_Temp, Engine_RPM, Vibration_Level, Fuel_System_Pressure' },
    { 故障段: 4, 起始样本: 4789, 结束样本: 4956, 持续长度: 168, Top10关键特征: 'Engine_Vibration_Level, Torque_Output, Engine_RPM, Exhaust_Gas_Temp, Oil_Temperature' },
    { 故障段: 5, 起始样本: 5234, 结束样本: 5423, 持续长度: 190, Top10关键特征: 'Exhaust_Gas_Temp, Engine_Oil_Pressure, Engine_RPM, Vibration_Level, Fuel_Flow_Rate' },
    { 故障段: 6, 起始样本: 5890, 结束样本: 6078, 持续长度: 189, Top10关键特征: 'Engine_RPM, Exhaust_Gas_Temp, Torque_Output, Oil_Temperature, Vibration_Level' },
    { 故障段: 7, 起始样本: 6234, 结束样本: 6456, 持续长度: 223, Top10关键特征: 'Engine_Oil_Pressure, Vibration_Level, Exhaust_Gas_Temp, Engine_RPM, Fuel_System_Pressure' },
    { 故障段: 8, 起始样本: 6789, 结束样本: 7045, 持续长度: 257, Top10关键特征: 'Exhaust_Gas_Temp, Torque_Output, Engine_RPM, Vibration_Level, Oil_Temperature' },
    { 故障段: 9, 起始样本: 7123, 结束样本: 7389, 持续长度: 267, Top10关键特征: 'Engine_Vibration_Level, Engine_Oil_Pressure, Exhaust_Gas_Temp, Engine_RPM, Fuel_Flow_Rate' },
    { 故障段: 10, 起始样本: 7567, 结束样本: 7856, 持续长度: 290, Top10关键特征: 'Engine_RPM, Exhaust_Gas_Temp, Torque_Output, Vibration_Level, Oil_Temperature' },
  ],

  averageFaultLength: 192.0,
  maxFaultLength: 290,
  totalFaultSamples: 15775,
  faultRatio: 60.0,
}

export function getComponentSensors(componentName: string): ComponentData {
  const componentConfigs: Record<string, ComponentData> = {
    '动力涡轮': {
      name: '动力涡轮',
      healthScore: 82,
      sensors: {
        temperature: { value: 200.54, unit: '°C', label: '排气温度 (EGT)', status: 'warning', percentage: 78, color: '#ff6b35' },
        rpm: { value: 661.95, unit: 'RPM', label: '转速', status: 'normal', percentage: 65, color: '#4cff7c' },
        pressure: { value: 873.02, unit: 'bar', label: '排气压力', status: 'normal', percentage: 55, color: '#4cff7c' },
        vibration: { value: 237.3, unit: 'mm/s', label: '振动值', status: 'warning', percentage: 72, color: '#ffa500' },
      },
    },
    '燃气涡轮': {
      name: '燃气涡轮',
      healthScore: 85,
      sensors: {
        temperature: { value: 200.54, unit: '°C', label: '涡轮进气温度', status: 'normal', percentage: 68, color: '#4cff7c' },
        rpm: { value: 661.95, unit: 'RPM', label: '涡轮转速', status: 'normal', percentage: 62, color: '#4cff7c' },
        pressure: { value: 873.02, unit: 'bar', label: '涡轮背压', status: 'normal', percentage: 52, color: '#4cff7c' },
        efficiency: { value: 88, unit: '%', label: '涡轮效率', status: 'normal', percentage: 88, color: '#4cff7c' },
      },
    },
    '压气机': {
      name: '压气机',
      healthScore: 90,
      sensors: {
        temperature: { value: 112.89, unit: '°C', label: '出口温度', status: 'normal', percentage: 58, color: '#4cff7c' },
        rpm: { value: 661.95, unit: 'RPM', label: '转速', status: 'normal', percentage: 55, color: '#4cff7c' },
        pressure: { value: 873.02, unit: 'bar', label: '出口压力', status: 'normal', percentage: 72, color: '#4cff7c' },
        efficiency: { value: 92, unit: '%', label: '压缩效率', status: 'normal', percentage: 92, color: '#4cff7c' },
      },
    },
    '燃烧室': {
      name: '燃烧室',
      healthScore: 88,
      sensors: {
        temperature: { value: 200.54, unit: '°C', label: '燃烧温度', status: 'warning', percentage: 82, color: '#ff6b35' },
        pressure: { value: 873.02, unit: 'bar', label: '燃烧室压力', status: 'normal', percentage: 65, color: '#4cff7c' },
        emissions: { value: 25, unit: 'ppm', label: '排放物', status: 'normal', percentage: 42, color: '#4cff7c' },
        stability: { value: 94, unit: '%', label: '燃烧稳定性', status: 'normal', percentage: 94, color: '#4cff7c' },
      },
    },
    '滑油系统': {
      name: '滑油系统',
      healthScore: 85,
      sensors: {
        temperature: { value: 112.89, unit: '°C', label: '滑油温度', status: 'warning', percentage: 72, color: '#ffa500' },
        pressure: { value: 873.02, unit: 'bar', label: '滑油压力', status: 'normal', percentage: 65, color: '#4cff7c' },
        level: { value: 78, unit: '%', label: '滑油液位', status: 'normal', percentage: 78, color: '#4cff7c' },
        contamination: { value: 5, unit: 'ppm', label: '污染度', status: 'normal', percentage: 25, color: '#4cff7c' },
      },
    },
    '燃油系统': {
      name: '燃油系统',
      healthScore: 93,
      sensors: {
        temperature: { value: 38, unit: '°C', label: '燃油温度', status: 'normal', percentage: 48, color: '#4cff7c' },
        pressure: { value: 873.02, unit: 'bar', label: '燃油压力', status: 'normal', percentage: 58, color: '#4cff7c' },
        flow: { value: 167.65, unit: 'L/h', label: '燃油流量', status: 'normal', percentage: 52, color: '#4cff7c' },
        filterStatus: { value: 92, unit: '%', label: '滤清器状态', status: 'normal', percentage: 92, color: '#4cff7c' },
      },
    },
    '进气道': {
      name: '进气道',
      healthScore: 96,
      sensors: {
        temperature: { value: 28, unit: '°C', label: '进气温度', status: 'normal', percentage: 35, color: '#4cff7c' },
        pressure: { value: 1.02, unit: 'bar', label: '进气压力', status: 'normal', percentage: 82, color: '#4cff7c' },
        airflow: { value: 128, unit: 'kg/s', label: '空气流量', status: 'normal', percentage: 72, color: '#4cff7c' },
        efficiency: { value: 97, unit: '%', label: '进气效率', status: 'normal', percentage: 97, color: '#4cff7c' },
      },
    },
    '排气系统': {
      name: '排气系统',
      healthScore: 88,
      sensors: {
        temperature: { value: 200.54, unit: '°C', label: '排气温度', status: 'warning', percentage: 68, color: '#ffa500' },
        pressure: { value: 1.52, unit: 'bar', label: '排气压力', status: 'normal', percentage: 55, color: '#4cff7c' },
        velocity: { value: 455, unit: 'm/s', label: '排气速度', status: 'normal', percentage: 62, color: '#4cff7c' },
        thrust: { value: 118, unit: 'kN', label: '推力', status: 'normal', percentage: 75, color: '#4cff7c' },
      },
    },
    '涡轮叶片': {
      name: '涡轮叶片',
      healthScore: 80,
      sensors: {
        temperature: { value: 200.54, unit: '°C', label: '叶片温度', status: 'warning', percentage: 85, color: '#ff6b35' },
        rpm: { value: 661.95, unit: 'RPM', label: '转速', status: 'normal', percentage: 65, color: '#4cff7c' },
        stress: { value: 285, unit: 'MPa', label: '应力值', status: 'warning', percentage: 78, color: '#ffa500' },
        vibration: { value: 237.3, unit: 'mm/s', label: '振动值', status: 'normal', percentage: 68, color: '#4cff7c' },
      },
    },
    '压缩机叶片': {
      name: '压缩机叶片',
      healthScore: 87,
      sensors: {
        temperature: { value: 112.89, unit: '°C', label: '叶片温度', status: 'normal', percentage: 52, color: '#4cff7c' },
        rpm: { value: 661.95, unit: 'RPM', label: '转速', status: 'normal', percentage: 55, color: '#4cff7c' },
        pressure: { value: 873.02, unit: 'bar', label: '出口压力', status: 'normal', percentage: 72, color: '#4cff7c' },
        efficiency: { value: 91, unit: '%', label: '压缩效率', status: 'normal', percentage: 91, color: '#4cff7c' },
      },
    },
  }

  return componentConfigs[componentName] || componentConfigs['动力涡轮']
}
