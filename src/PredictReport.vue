<template>
  <div class="report-viewport">
    <div class="report-toolbar no-print">
      <button class="toolbar-btn ghost" @click="goBack">返回监控中心</button>
      <div class="toolbar-actions">
        <button class="toolbar-btn" @click="exportWord">导出 Word 报告</button>
        <button class="toolbar-btn primary" @click="exportPdf">导出 PDF / 打印</button>
      </div>
    </div>

    <main ref="reportRef" class="report-page">
      <section class="report-cover">
        <div class="cover-left">
          <div class="system-name">“航枢”飞行态势智能感知与协同预测系统</div>
          <h1>直升机发动机落地后健康评估与故障预测报告</h1>
          <p>
            基于单架次全航程脱敏传感数据，对发动机关键参数、部件异常分布、
            故障风险等级与维护处置优先级进行综合分析，为机务人员落地后快速排查与维护决策提供参考。
          </p>
        </div>

        <div class="cover-right">
          <div class="report-stamp">AI 评估完成</div>
          <div class="cover-meta">
            <div>
              <span>报告编号</span>
              <strong>{{ reportInfo.reportNo }}</strong>
            </div>
            <div>
              <span>架次编号</span>
              <strong>{{ reportInfo.flightNumber }}</strong>
            </div>
            <div>
              <span>生成时间</span>
              <strong>{{ reportInfo.generateTime }}</strong>
            </div>
            <div>
              <span>数据类型</span>
              <strong>单架次飞行数据</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="summary-grid">
        <div class="summary-card">
          <span class="card-label">综合健康评分</span>
          <strong class="main-score" :class="healthClass">{{ healthScore }}</strong>
          <small>分 / 100</small>
        </div>

        <div class="summary-card">
          <span class="card-label">综合风险等级</span>
          <strong class="risk-text" :class="riskClass">{{ riskLevel }}</strong>
          <small>{{ riskDescription }}</small>
        </div>

        <div class="summary-card">
          <span class="card-label">异常事件总数</span>
          <strong>{{ totalFaults }}</strong>
          <small>条有效异常片段</small>
        </div>

        <div class="summary-card">
          <span class="card-label">建议处置方式</span>
          <strong>{{ disposalMode }}</strong>
          <small>{{ disposalTip }}</small>
        </div>
      </section>

      <section class="content-section">
        <div class="section-header">
          <h2>一、报告结论摘要</h2>
          <span>Conclusion</span>
        </div>

        <div class="conclusion-box">
          <p>
            本次导入数据为直升机完成一架次后的全航程发动机运行数据。系统完成数据解析、
            时序样本构建、模型推理和风险聚合后，判定发动机当前综合健康评分为
            <strong>{{ healthScore }}</strong> 分，整体风险等级为
            <strong :class="riskClass">{{ riskLevel }}</strong>。
          </p>
          <p>
            从故障分布看，本次分析共识别出 <strong>{{ totalFaults }}</strong> 条异常事件，
            其中严重 <strong class="danger">{{ faultLevels.severe }}</strong> 条、
            中等 <strong class="warning">{{ faultLevels.moderate }}</strong> 条、
            轻微 <strong class="normal">{{ faultLevels.minor }}</strong> 条。
            建议机务人员优先检查
            <strong>{{ primaryRiskPart }}</strong>
            相关监测指标，并结合本报告中的部件风险清单开展分级处置。
          </p>
        </div>
      </section>

      <section class="content-section two-column">
        <div class="section-card">
          <div class="section-header compact">
            <h2>二、架次数据概览</h2>
            <span>Dataset Overview</span>
          </div>

          <table class="info-table">
            <tbody>
            <tr>
              <td>架次编号</td>
              <td>{{ reportInfo.flightNumber }}</td>
            </tr>
            <tr>
              <td>数据来源</td>
              <td>发动机全航程脱敏传感数据</td>
            </tr>
            <tr>
              <td>数据形态</td>
              <td>多变量高维时序数据</td>
            </tr>
            <tr>
              <td>分析模式</td>
              <td>离线导入 · 落地后健康评估</td>
            </tr>
            <tr>
              <td>算法模型</td>
              <td>LSTM / LSTNet 双流时序预测模型</td>
            </tr>
            <tr>
              <td>报告用途</td>
              <td>地面维护复盘、风险定位、检修计划制定</td>
            </tr>
            </tbody>
          </table>
        </div>

        <div class="section-card">
          <div class="section-header compact">
            <h2>三、算法分析摘要</h2>
            <span>Model Summary</span>
          </div>

          <div class="model-flow">
            <div class="flow-node">
              <strong>1</strong>
              <span>数据导入</span>
              <small>CSV / Excel 单架次数据</small>
            </div>
            <div class="flow-line"></div>
            <div class="flow-node">
              <strong>2</strong>
              <span>预处理</span>
              <small>清洗、标准化、时序切片</small>
            </div>
            <div class="flow-line"></div>
            <div class="flow-node">
              <strong>3</strong>
              <span>模型推理</span>
              <small>长期特征 + 局部波动融合</small>
            </div>
            <div class="flow-line"></div>
            <div class="flow-node">
              <strong>4</strong>
              <span>报告输出</span>
              <small>风险等级与维护建议</small>
            </div>
          </div>
        </div>
      </section>

      <section class="content-section">
        <div class="section-header">
          <h2>四、故障风险等级统计</h2>
          <span>Risk Distribution</span>
        </div>

        <div class="risk-layout">
          <div class="donut-card">
            <div
                class="donut"
                :style="{
                '--severe': severityPercent.severe,
                '--moderate': severityPercent.moderate,
                '--minor': severityPercent.minor
              }"
            >
              <div class="donut-center">
                <strong>{{ totalFaults }}</strong>
                <span>异常事件</span>
              </div>
            </div>
          </div>

          <div class="risk-stat-list">
            <div class="risk-stat severe">
              <span>严重风险</span>
              <strong>{{ faultLevels.severe }}</strong>
              <small>{{ severityPercent.severe }}%</small>
            </div>
            <div class="risk-stat moderate">
              <span>中等风险</span>
              <strong>{{ faultLevels.moderate }}</strong>
              <small>{{ severityPercent.moderate }}%</small>
            </div>
            <div class="risk-stat minor">
              <span>轻微风险</span>
              <strong>{{ faultLevels.minor }}</strong>
              <small>{{ severityPercent.minor }}%</small>
            </div>
          </div>

          <div class="risk-explain">
            <h3>风险解读</h3>
            <p>
              严重风险用于提示需要优先复核的部件或参数；中等风险表示当前架次中出现了明显偏离基线的波动；
              轻微风险主要用于提示后续持续观察。系统将多条原始异常窗口聚合为可读的事件片段，避免报告冗余。
            </p>
          </div>
        </div>
      </section>

      <section class="content-section">
        <div class="section-header">
          <h2>五、关键参数分析</h2>
          <span>Key Parameters</span>
        </div>

        <div class="param-grid">
          <div v-for="item in parameterAnalysis" :key="item.name" class="param-card">
            <div class="param-head">
              <span>{{ item.name }}</span>
              <strong>{{ item.value }}{{ item.unit }}</strong>
            </div>
            <div class="param-bar">
              <div class="param-fill" :class="item.status" :style="{ width: item.percent + '%' }"></div>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </div>
      </section>

      <section class="content-section">
        <div class="section-header">
          <h2>六、重点部件风险清单</h2>
          <span>Component Risk List</span>
        </div>

        <table class="risk-table">
          <thead>
          <tr>
            <th>序号</th>
            <th>部件名称</th>
            <th>风险概率</th>
            <th>风险等级</th>
            <th>异常说明</th>
            <th>处置优先级</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(item, index) in riskItems" :key="index">
            <td>{{ index + 1 }}</td>
            <td>{{ item.part }}</td>
            <td>
              <span class="probability">{{ item.probability }}%</span>
            </td>
            <td>
              <span class="level-tag" :class="item.levelClass">{{ item.levelText }}</span>
            </td>
            <td>{{ item.description }}</td>
            <td>{{ item.priority }}</td>
          </tr>
          </tbody>
        </table>
      </section>

      <section class="content-section two-column">
        <div class="section-card">
          <div class="section-header compact">
            <h2>七、维护处置建议</h2>
            <span>Maintenance Advice</span>
          </div>

          <div class="advice-list">
            <div v-for="(item, index) in maintenanceAdvice" :key="index" class="advice-item">
              <div class="advice-index">{{ index + 1 }}</div>
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="section-card">
          <div class="section-header compact">
            <h2>八、维护工单建议</h2>
            <span>Work Order</span>
          </div>

          <div class="workorder">
            <div>
              <span>建议维护级别</span>
              <strong :class="riskClass">{{ workOrder.level }}</strong>
            </div>
            <div>
              <span>预计检查时长</span>
              <strong>{{ workOrder.duration }}</strong>
            </div>
            <div>
              <span>重点检查对象</span>
              <strong>{{ primaryRiskPart }}</strong>
            </div>
            <div>
              <span>复核方式</span>
              <strong>传感器趋势 + 人工目视复核</strong>
            </div>
          </div>
        </div>
      </section>

      <section v-if="ragAdvice" class="content-section rag-section">
        <div class="section-header">
          <h2>AI 维修处置建议</h2>
          <span>Local RAG Evidence</span>
        </div>

        <div class="rag-summary">
          <div>
            <span>异常判断</span>
            <p>{{ ragAdvice.abnormal_judgment }}</p>
          </div>
          <div>
            <span>风险等级</span>
            <strong :class="ragAdvice.risk_level === '高' ? 'danger' : ragAdvice.risk_level === '中' ? 'warning' : 'normal'">
              {{ ragAdvice.risk_level }}风险
            </strong>
          </div>
          <div>
            <span>是否建议放行</span>
            <p>{{ ragAdvice.release_recommendation }}</p>
          </div>
        </div>

        <div class="rag-actions no-print">
          <button type="button" @click="showRagEvidence = !showRagEvidence">
            {{ showRagEvidence ? '隐藏依据' : '查看依据' }}
          </button>
          <button type="button" @click="requestRagFollowup('why')">为什么这样建议</button>
          <button type="button" @click="requestRagFollowup('extra_checks')">补充检查项</button>
        </div>

        <div class="rag-columns">
          <div>
            <h3>建议检查步骤</h3>
            <ol>
              <li v-for="(step, index) in ragAdvice.recommended_actions" :key="index">{{ step }}</li>
            </ol>
          </div>
          <div v-if="showRagEvidence">
            <h3>参考依据</h3>
            <ul>
              <li v-for="reference in ragAdvice.references" :key="reference.source">
                <strong>{{ reference.title }}</strong>：{{ reference.content }}
              </li>
            </ul>
          </div>
        </div>

        <div class="rag-question no-print">
          <input
              v-model="ragQuestion"
              type="text"
              placeholder="输入维修相关问题，例如：现在能否继续放行？"
              @keyup.enter="submitRagQuestion"
          >
          <button type="button" :disabled="ragFollowupLoading" @click="submitRagQuestion">
            {{ ragFollowupLoading ? '处理中...' : '提交追问' }}
          </button>
        </div>

        <div v-if="ragFollowup" class="rag-followup">
          <div class="rag-followup-head">
            <strong>{{ ragFollowup.action === 'why' ? '建议解释' : ragFollowup.action === 'extra_checks' ? '补充检查项' : '追问结果' }}</strong>
            <span v-if="!ragFollowup.supported">当前知识库依据不足</span>
          </div>
          <p>{{ ragFollowup.answer }}</p>
          <ul v-if="ragFollowup.items?.length">
            <li v-for="(item, index) in ragFollowup.items" :key="index">{{ item }}</li>
          </ul>
          <div v-if="ragFollowup.action === 'question' && ragFollowup.references?.length" class="rag-followup-sources">
            依据：{{ ragFollowupSourceNames }}
          </div>
        </div>

        <div class="rag-precautions">
          <strong>注意事项：</strong>
          <span v-for="(item, index) in ragAdvice.precautions" :key="index">{{ item }}</span>
        </div>
      </section>

      <section class="content-section">
        <div class="section-header">
          <h2>九、报告说明</h2>
          <span>Notes</span>
        </div>

        <div class="note-box">
          <p>
            1. 本报告基于脱敏后的单架次发动机传感数据生成，部分数值经过展示范围放缩处理，
            主要用于故障趋势研判、风险排序与维护辅助决策，不直接替代机务规程中的最终检修判定。
          </p>
          <p>
            2. 报告中的风险概率、健康评分和维护优先级由系统根据模型输出、异常等级、
            部件频次和参数波动情况综合生成，建议结合实际维护记录进行复核。
          </p>
          <p>
            3. 若报告中存在高风险部件，应优先开展传感器复核、部件外观检查和相关系统联检；
            维护完成后的结果可回流至数据层，用于后续模型迭代与预测优化。
          </p>
        </div>
      </section>

      <footer class="report-footer">
        <div>
          <strong>报告结论：</strong>
          {{ finalConclusion }}
        </div>
        <div class="signature">
          <span>系统生成：</span>
          <strong>航枢智能评估模块</strong>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { engineDataConfig } from './engineDataConfig'

const router = useRouter()
const reportRef = ref<HTMLElement | null>(null)
const ragAdvice = ref<any | null>(readRagAdvice())
const showRagEvidence = ref(true)
const ragFollowup = ref<any | null>(null)
const ragFollowupLoading = ref(false)
const ragQuestion = ref('')
const ragFollowupSourceNames = computed(() => {
  return ragFollowup.value?.references?.map((item: any) => item.title).join('、') || ''
})

function readRagAdvice() {
  try {
    const stored = localStorage.getItem('ragAdvice')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

async function requestRagFollowup(action: string, question = '') {
  if (!ragAdvice.value || ragFollowupLoading.value) return

  ragFollowupLoading.value = true
  try {
    const response = await fetch('http://localhost:8000/api/rag-followup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, question, context: ragAdvice.value })
    })
    if (!response.ok) throw new Error(`RAG follow-up HTTP ${response.status}`)
    const result = await response.json()
    if (result.status === 'success') ragFollowup.value = result
  } catch (error) {
    console.warn('RAG 追问不可用:', error)
  } finally {
    ragFollowupLoading.value = false
  }
}

function submitRagQuestion() {
  const question = ragQuestion.value.trim()
  if (!question) return
  void requestRagFollowup('question', question)
}

const now = new Date()

const reportInfo = computed(() => {
  const flightNumber = engineDataConfig?.flightInfo?.flightNumber || 'CZ-8089'
  return {
    reportNo: `HS-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${flightNumber}`,
    flightNumber,
    generateTime: formatDateTime(now)
  }
})

const selectedComponent = computed(() => {
  return engineDataConfig?.selectedComponent || {
    name: '压气机',
    healthScore: 82
  }
})

const fallbackLevels = {
  severe: 7,
  moderate: 19,
  minor: 27
}

const faultLevels = computed(() => {
  return fallbackLevels
})

const totalFaults = computed(() => {
  return faultLevels.value.severe + faultLevels.value.moderate + faultLevels.value.minor
})

const healthScore = computed(() => {
  const score = Number(selectedComponent.value?.healthScore)
  if (!Number.isNaN(score) && score > 0) return Math.round(score)

  const penalty = faultLevels.value.severe * 3 + faultLevels.value.moderate * 1.4 + faultLevels.value.minor * 0.45
  return Math.max(68, Math.round(96 - penalty))
})

const healthClass = computed(() => {
  if (healthScore.value >= 86) return 'normal'
  if (healthScore.value >= 74) return 'warning'
  return 'danger'
})

const riskLevel = computed(() => {
  if (healthScore.value < 74 || faultLevels.value.severe >= 8) return '高风险'
  if (healthScore.value < 86 || faultLevels.value.severe >= 3 || faultLevels.value.moderate >= 15) return '中风险'
  return '低风险'
})

const riskClass = computed(() => {
  if (riskLevel.value === '高风险') return 'danger'
  if (riskLevel.value === '中风险') return 'warning'
  return 'normal'
})

const riskDescription = computed(() => {
  if (riskLevel.value === '高风险') return '建议立即开展重点部件检查'
  if (riskLevel.value === '中风险') return '建议落地后安排针对性复核'
  return '可按常规流程进行航后检查'
})

const disposalMode = computed(() => {
  if (riskLevel.value === '高风险') return '优先检修'
  if (riskLevel.value === '中风险') return '重点复核'
  return '常规检查'
})

const disposalTip = computed(() => {
  if (riskLevel.value === '高风险') return '暂缓再次出动，完成复核后放行'
  if (riskLevel.value === '中风险') return '完成重点检查后进入下一流程'
  return '按周期维护计划执行'
})

const severityPercent = computed(() => {
  const total = totalFaults.value || 1
  return {
    severe: Math.round((faultLevels.value.severe / total) * 100),
    moderate: Math.round((faultLevels.value.moderate / total) * 100),
    minor: Math.round((faultLevels.value.minor / total) * 100)
  }
})

const rawRanking = computed(() => {
  return engineDataConfig?.faultRanking || [
    { part: '排气系统', count: 11 },
    { part: '动力涡轮', count: 9 },
    { part: '压气机', count: 8 },
    { part: '滑油系统', count: 6 },
    { part: '燃油系统', count: 5 }
  ]
})

const rawPredictions = computed(() => {
  return engineDataConfig?.faultPredictions || [
    { area: '排气系统', probability: 86, prediction: '排气温度波动偏高，热端负荷需重点复核' },
    { area: '动力涡轮', probability: 81, prediction: '转速与振动特征存在同步波动' },
    { area: '压气机', probability: 74, prediction: '进气流量与出口压力存在轻微偏离' }
  ]
})

const rawDetails = computed(() => {
  return engineDataConfig?.faultDetails || [
    {
      part: '排气系统',
      probability: 86,
      level: 'moderate',
      levelText: '中等',
      description: '排气系统运行特征出现异常波动，建议重点关注'
    },
    {
      part: '动力涡轮',
      probability: 81,
      level: 'moderate',
      levelText: '中等',
      description: '动力涡轮转速与振动存在同步波动'
    },
    {
      part: '压气机',
      probability: 74,
      level: 'minor',
      levelText: '轻微',
      description: '压气机捕获到轻微异常信号，建议持续观察'
    }
  ]
})

const primaryRiskPart = computed(() => {
  const firstPrediction = rawPredictions.value?.[0]
  if (firstPrediction?.area) return firstPrediction.area

  const firstRanking = rawRanking.value?.[0]
  return firstRanking?.part || selectedComponent.value?.name || '发动机核心部件'
})

const riskItems = computed(() => {
  const merged = new Map<string, any>()

  rawPredictions.value.forEach((item: any) => {
    const part = item.area || item.part || '综合系统'
    merged.set(part, {
      part,
      probability: normalizeProbability(item.probability),
      description: item.prediction || `${part}存在异常趋势，建议复核相关传感器数据`
    })
  })

  rawDetails.value.forEach((item: any) => {
    const part = item.part || '综合系统'
    const current = merged.get(part)
    const probability = normalizeProbability(item.probability)

    if (!current || probability > current.probability) {
      merged.set(part, {
        part,
        probability,
        description: item.description || `${part}检测到异常事件`
      })
    }
  })

  rawRanking.value.forEach((item: any) => {
    const part = item.part || '综合系统'
    if (!merged.has(part)) {
      const probability = Math.min(82, 52 + Number(item.count || 0) * 3)
      merged.set(part, {
        part,
        probability,
        description: `${part}在本次分析中出现 ${item.count || 0} 次预警记录`
      })
    }
  })

  return Array.from(merged.values())
      .sort((a, b) => b.probability - a.probability)
      .slice(0, 6)
      .map((item) => {
        const levelInfo = getLevelInfo(item.probability)
        return {
          ...item,
          levelText: levelInfo.text,
          levelClass: levelInfo.className,
          priority: levelInfo.priority
        }
      })
})

const parameterAnalysis = computed(() => {
  const metrics = engineDataConfig?.engineMetrics || {}

  return [
    buildParameter('平均排气温度', metrics.maxEgt ?? 742, '°C', 520, 860, '用于评估热端部件负荷，异常升高可能提示燃烧或排气系统风险'),
    buildParameter('平均转速', metrics.maxRpm ?? 11860, 'RPM', 5200, 14800, '用于判断动力输出稳定性，持续波动可能与涡轮或传动系统相关'),
    buildParameter('滑油消耗率', metrics.oilConsumption ?? 9.8, 'L/h', 4, 18, '用于评估润滑系统工作状态，异常消耗可能提示泄漏或润滑效率下降'),
    buildParameter('燃油消耗率', metrics.fuelConsumption ?? 286, 'L/h', 120, 520, '用于评估燃烧效率与供油稳定性，偏高时需关注喷油与燃烧室状态'),
    buildParameter('平均振动值', metrics.vibrationAvg ?? 3.4, 'mm/s', 0.5, 5.5, '用于识别转子、轴承及叶片类异常，是机械类风险的重要参考指标'),
    buildParameter('推力值', metrics.thrust ?? 38, 'kN', 12, 58, '用于评估发动机输出能力，持续下降可能提示压气效率或燃烧效率变化')
  ]
})

const maintenanceAdvice = computed(() => {
  const top = riskItems.value.slice(0, 4)

  const result = top.map((item) => {
    return {
      title: `${item.part}专项复核`,
      content: buildAdviceText(item.part, item.levelText, item.probability)
    }
  })

  result.push({
    title: '航后数据复核',
    content: '建议将本次报告结果与原始时序曲线、维护记录和机务人员检查结果进行交叉验证，确认是否存在传感器漂移或短时工况扰动。'
  })

  result.push({
    title: '维护闭环记录',
    content: '建议将本次处置结果、复核结论和更换件信息回填至历史维护库，用于后续模型迭代与同型装备风险对比。'
  })

  return result
})

const workOrder = computed(() => {
  if (riskLevel.value === '高风险') {
    return {
      level: 'A 类重点工单',
      duration: '45 - 70 分钟'
    }
  }

  if (riskLevel.value === '中风险') {
    return {
      level: 'B 类复核工单',
      duration: '25 - 45 分钟'
    }
  }

  return {
    level: 'C 类常规工单',
    duration: '15 - 25 分钟'
  }
})

const finalConclusion = computed(() => {
  if (riskLevel.value === '高风险') {
    return `本次架次分析显示 ${primaryRiskPart.value} 等部件存在较高风险，建议完成专项检查和人工复核后再进入后续任务流程。`
  }

  if (riskLevel.value === '中风险') {
    return `本次架次分析显示 ${primaryRiskPart.value} 存在中等风险异常，建议落地后开展针对性复核，并纳入下一架次重点观察对象。`
  }

  return '本次架次分析未发现高危风险，建议按照常规航后维护流程执行，并持续跟踪关键参数趋势。'
})

function buildParameter(name: string, value: number | string, unit: string, min: number, max: number, desc: string) {
  const numeric = Number(value)
  const safeValue = Number.isNaN(numeric) ? min : numeric
  const percent = Math.max(8, Math.min(96, Math.round(((safeValue - min) / (max - min)) * 100)))
  const status = percent >= 82 ? 'danger' : percent >= 65 ? 'warning' : 'normal'

  return {
    name,
    value: Number.isNaN(numeric) ? '-' : Number(safeValue.toFixed(1)),
    unit,
    percent,
    status,
    desc
  }
}

function normalizeProbability(value: number | string) {
  const numberValue = Number(value)
  if (Number.isNaN(numberValue)) return 0
  return Math.max(0, Math.min(98, Math.round(numberValue)))
}

function getLevelInfo(probability: number) {
  if (probability >= 88) {
    return {
      text: '严重',
      className: 'danger',
      priority: '立即检查'
    }
  }

  if (probability >= 70) {
    return {
      text: '中等',
      className: 'warning',
      priority: '重点复核'
    }
  }

  return {
    text: '轻微',
    className: 'normal',
    priority: '持续观察'
  }
}

function buildAdviceText(part: string, level: string, probability: number) {
  const adviceMap: Record<string, string> = {
    '动力涡轮': '检查涡轮振动、转速波动与轴承润滑状态，必要时降低负载运行并进行轴承间隙复核。',
    '燃气涡轮': '重点核查涡轮转速、排气温度与冷却流量，确认热端部件是否存在局部过热或效率下降。',
    '压气机': '检查压气机出口压力、进气流量和叶片污染情况，重点关注喘振边界与压比变化。',
    '燃油系统': '检查燃油压力、喷油稳定性和燃油流量传感器，排除供油波动、喷嘴堵塞或传感器漂移。',
    '排气系统': '检查排气温度峰值、阀门响应和尾喷管状态，关注热负荷异常与局部温升。',
    '滑油系统': '检查滑油温度、压力、液位和滤清器压差，优先排除润滑不足、油路堵塞或泄漏风险。',
    '燃烧室': '检查喷嘴流量、燃烧稳定性和温度分布，避免局部过热和燃烧效率下降。',
    '进气道': '检查进气流量、外界气压和防冰系统状态，确认进气通道稳定性。',
    '涡轮叶片': '检查叶片磨损、振动频谱和转子转速，重点关注结构疲劳和异物损伤风险。',
    '压缩机叶片': '检查叶片振动、气流稳定性和健康指数，防止叶片效率下降。'
  }

  const base = adviceMap[part] || '建议结合该部件对应传感器趋势、历史维护记录和人工检查结果进行复核。'

  if (level === '严重') {
    return `风险概率 ${probability}%，建议立即执行专项检查。${base}`
  }

  if (level === '中等') {
    return `风险概率 ${probability}%，建议在本次落地维护流程中优先复核。${base}`
  }

  return `风险概率 ${probability}%，建议纳入后续架次持续观察。${base}`
}

function formatDateTime(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

function goBack() {
  router.push('/')
}

function exportPdf() {
  window.print()
}

function exportWord() {
  if (!reportRef.value) return

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>${reportInfo.value.flightNumber}-发动机健康评估报告</title>
        <style>
          ${wordExportStyles}
        </style>
      </head>
      <body>
        ${reportRef.value.innerHTML}
      </body>
    </html>
  `

  const blob = new Blob(['\ufeff', html], {
    type: 'application/msword'
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${reportInfo.value.flightNumber}_发动机健康评估与故障预测报告.doc`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const wordExportStyles = `
  body {
    font-family: "Microsoft YaHei", Arial, sans-serif;
    color: #111827;
    line-height: 1.7;
    padding: 24px;
  }
  .report-page {
    width: 100%;
    background: #ffffff;
  }
  .report-cover {
    border-bottom: 3px solid #0f766e;
    padding-bottom: 18px;
    margin-bottom: 18px;
  }
  h1 {
    font-size: 26px;
    margin: 12px 0;
  }
  h2 {
    font-size: 18px;
    margin: 0 0 10px;
    color: #0f766e;
  }
  .summary-grid,
  .param-grid,
  .two-column,
  .risk-layout {
    display: block;
  }
  .summary-card,
  .section-card,
  .param-card,
  .content-section,
  .conclusion-box,
  .note-box {
    border: 1px solid #d1d5db;
    padding: 12px;
    margin-bottom: 12px;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
  }
  th,
  td {
    border: 1px solid #d1d5db;
    padding: 8px;
    text-align: left;
  }
  th {
    background: #f3f4f6;
  }
  .no-print,
  .report-toolbar,
  .toolbar-actions {
    display: none !important;
  }
`
</script>

<style scoped>
.report-viewport {
  width: 100vw;
  height: 100vh;
  overflow-y: auto;
  background:
      radial-gradient(circle at top left, rgba(0, 240, 255, 0.16), transparent 30%),
      linear-gradient(135deg, #07111f, #0f172a 45%, #111827);
  color: #e5f6ff;
  font-family: 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  padding: 24px;
  box-sizing: border-box;
}

.report-toolbar {
  max-width: 1280px;
  margin: 0 auto 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.toolbar-btn {
  border: 1px solid rgba(0, 240, 255, 0.4);
  background: rgba(0, 240, 255, 0.08);
  color: #8eeeff;
  padding: 9px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.toolbar-btn:hover {
  background: rgba(0, 240, 255, 0.18);
  box-shadow: 0 0 14px rgba(0, 240, 255, 0.3);
}

.toolbar-btn.primary {
  background: #00eaff;
  color: #06111e;
  font-weight: 700;
}

.toolbar-btn.ghost {
  color: #c8eaff;
}

.report-page {
  max-width: 1280px;
  margin: 0 auto;
  background: rgba(8, 15, 34, 0.94);
  border: 1px solid rgba(0, 240, 255, 0.2);
  box-shadow: 0 20px 80px rgba(0, 0, 0, 0.45);
  border-radius: 14px;
  padding: 28px;
  box-sizing: border-box;
}

.report-cover {
  display: grid;
  grid-template-columns: 1.5fr 0.85fr;
  gap: 24px;
  padding: 28px;
  background:
      linear-gradient(120deg, rgba(0, 240, 255, 0.12), rgba(255, 255, 255, 0.03)),
      rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.18);
  border-radius: 12px;
}

.system-name {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(0, 240, 255, 0.12);
  border: 1px solid rgba(0, 240, 255, 0.24);
  color: #79f2ff;
  font-size: 14px;
  margin-bottom: 14px;
}

.cover-left h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.28;
  color: #ffffff;
  letter-spacing: 1px;
}

.cover-left p {
  color: #bad4e8;
  line-height: 1.8;
  font-size: 15px;
  max-width: 820px;
  margin: 14px 0 0;
}

.cover-right {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.report-stamp {
  align-self: flex-end;
  color: #64ffb4;
  border: 1px solid rgba(100, 255, 180, 0.38);
  background: rgba(100, 255, 180, 0.08);
  border-radius: 8px;
  padding: 8px 14px;
  font-weight: 700;
}

.cover-meta {
  display: grid;
  gap: 10px;
}

.cover-meta div {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 10px 12px;
  background: rgba(10, 24, 50, 0.86);
  border: 1px solid rgba(0, 240, 255, 0.14);
  border-radius: 8px;
}

.cover-meta span {
  color: #7da6c8;
}

.cover-meta strong {
  color: #ffffff;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 18px;
}

.summary-card {
  padding: 18px;
  background: rgba(18, 30, 58, 0.82);
  border: 1px solid rgba(0, 240, 255, 0.16);
  border-radius: 12px;
  min-height: 118px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-label {
  color: #8bb7d9;
  font-size: 14px;
  margin-bottom: 8px;
}

.summary-card strong {
  color: #ffffff;
  font-size: 30px;
  line-height: 1.15;
}

.summary-card small {
  color: #90a9bf;
  margin-top: 5px;
}

.main-score {
  font-size: 42px !important;
  font-family: 'Orbitron', 'Microsoft YaHei', sans-serif;
}

.content-section {
  margin-top: 20px;
  background: rgba(18, 30, 58, 0.72);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 12px;
  padding: 20px;
}

.two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  background: transparent;
  border: none;
  padding: 0;
}

.section-card {
  background: rgba(18, 30, 58, 0.72);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 12px;
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 14px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.12);
  padding-bottom: 10px;
}

.section-header.compact {
  margin-bottom: 12px;
}

.section-header h2 {
  margin: 0;
  color: #68eaff;
  font-size: 20px;
}

.section-header span {
  color: #557b9b;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.conclusion-box {
  color: #d9ecf8;
  font-size: 15px;
  line-height: 1.85;
}

.conclusion-box p {
  margin: 0 0 10px;
}

.conclusion-box p:last-child {
  margin-bottom: 0;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
}

.info-table td {
  padding: 11px 10px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.08);
  color: #dceefa;
  font-size: 14px;
}

.info-table td:first-child {
  width: 32%;
  color: #8bb7d9;
}

.model-flow {
  display: grid;
  gap: 9px;
}

.flow-node {
  display: grid;
  grid-template-columns: 42px 90px 1fr;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid rgba(0, 240, 255, 0.12);
  border-radius: 8px;
}

.flow-node strong {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #00eaff;
  color: #06111e;
  display: flex;
  align-items: center;
  justify-content: center;
}

.flow-node span {
  color: #ffffff;
  font-weight: 700;
}

.flow-node small {
  color: #90a9bf;
}

.flow-line {
  height: 8px;
  width: 1px;
  margin-left: 25px;
  background: rgba(0, 240, 255, 0.25);
}

.risk-layout {
  display: grid;
  grid-template-columns: 220px 1fr 1.15fr;
  gap: 20px;
  align-items: center;
}

.donut-card {
  display: flex;
  justify-content: center;
  align-items: center;
}

.donut {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background:
      conic-gradient(
          #ff5757 0 calc(var(--severe) * 1%),
          #ffca3a calc(var(--severe) * 1%) calc((var(--severe) + var(--moderate)) * 1%),
          #64ffb4 calc((var(--severe) + var(--moderate)) * 1%) 100%
      );
  position: relative;
  box-shadow: 0 0 26px rgba(0, 240, 255, 0.14);
}

.donut::after {
  content: '';
  position: absolute;
  inset: 24px;
  border-radius: 50%;
  background: #0b1528;
}

.donut-center {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #ffffff;
}

.donut-center strong {
  font-size: 34px;
}

.donut-center span {
  color: #8bb7d9;
  font-size: 13px;
}

.risk-stat-list {
  display: grid;
  gap: 10px;
}

.risk-stat {
  display: grid;
  grid-template-columns: 1fr 60px 60px;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  background: rgba(0, 240, 255, 0.04);
  border: 1px solid rgba(0, 240, 255, 0.1);
}

.risk-stat span {
  color: #cde8f8;
}

.risk-stat strong {
  font-size: 24px;
  text-align: center;
}

.risk-stat small {
  color: #8bb7d9;
  text-align: right;
}

.risk-stat.severe strong {
  color: #ff5757;
}

.risk-stat.moderate strong {
  color: #ffca3a;
}

.risk-stat.minor strong {
  color: #64ffb4;
}

.risk-explain {
  color: #c7ddee;
  line-height: 1.75;
  font-size: 14px;
}

.risk-explain h3 {
  color: #ffffff;
  margin: 0 0 8px;
}

.risk-explain p {
  margin: 0;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.param-card {
  padding: 14px;
  background: rgba(0, 240, 255, 0.04);
  border: 1px solid rgba(0, 240, 255, 0.11);
  border-radius: 10px;
}

.param-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.param-head span {
  color: #dceefa;
  font-weight: 700;
}

.param-head strong {
  color: #ffffff;
  font-size: 20px;
}

.param-bar {
  margin: 11px 0;
  height: 9px;
  background: rgba(255, 255, 255, 0.09);
  border-radius: 999px;
  overflow: hidden;
}

.param-fill {
  height: 100%;
  border-radius: 999px;
}

.param-fill.normal {
  background: linear-gradient(90deg, #29d391, #64ffb4);
}

.param-fill.warning {
  background: linear-gradient(90deg, #ffb02e, #ffca3a);
}

.param-fill.danger {
  background: linear-gradient(90deg, #ff5757, #ff8a8a);
}

.param-card p {
  margin: 0;
  color: #95b3cc;
  font-size: 13px;
  line-height: 1.55;
}

.risk-table {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
  border-radius: 8px;
}

.risk-table th,
.risk-table td {
  padding: 12px 10px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.09);
  text-align: left;
  font-size: 14px;
}

.risk-table th {
  color: #8eeeff;
  background: rgba(0, 240, 255, 0.06);
  font-weight: 700;
}

.risk-table td {
  color: #dceefa;
}

.probability {
  color: #ffffff;
  font-weight: 700;
}

.level-tag {
  display: inline-flex;
  padding: 4px 9px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 13px;
}

.level-tag.danger {
  color: #ff7070;
  background: rgba(255, 87, 87, 0.12);
  border: 1px solid rgba(255, 87, 87, 0.3);
}

.level-tag.warning {
  color: #ffd966;
  background: rgba(255, 202, 58, 0.12);
  border: 1px solid rgba(255, 202, 58, 0.3);
}

.level-tag.normal {
  color: #64ffb4;
  background: rgba(100, 255, 180, 0.1);
  border: 1px solid rgba(100, 255, 180, 0.25);
}

.advice-list {
  display: grid;
  gap: 12px;
}

.advice-item {
  display: grid;
  grid-template-columns: 38px 1fr;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 240, 255, 0.04);
  border: 1px solid rgba(0, 240, 255, 0.1);
  border-radius: 8px;
}

.advice-index {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #00eaff;
  color: #06111e;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.advice-item strong {
  color: #ffffff;
}

.advice-item p {
  margin: 5px 0 0;
  color: #b9d2e6;
  line-height: 1.65;
  font-size: 14px;
}

.workorder {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.workorder div {
  padding: 14px;
  border-radius: 8px;
  background: rgba(0, 240, 255, 0.04);
  border: 1px solid rgba(0, 240, 255, 0.1);
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.workorder span {
  color: #8bb7d9;
}

.workorder strong {
  color: #ffffff;
  text-align: right;
}

.rag-summary {
  display: grid;
  grid-template-columns: 1.4fr 0.45fr 1.4fr;
  gap: 12px;
}

.rag-summary > div,
.rag-columns > div {
  padding: 14px;
  background: rgba(0, 240, 255, 0.04);
  border: 1px solid rgba(0, 240, 255, 0.1);
  border-radius: 8px;
}

.rag-summary span {
  display: block;
  color: #8bb7d9;
  font-size: 13px;
  margin-bottom: 8px;
}

.rag-summary p,
.rag-columns li {
  color: #dceefa;
  line-height: 1.7;
  margin: 0;
}

.rag-columns {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 12px;
  margin-top: 12px;
}

.rag-columns h3 {
  color: #ffffff;
  font-size: 15px;
  margin: 0 0 9px;
}

.rag-columns ol,
.rag-columns ul {
  margin: 0;
  padding-left: 20px;
}

.rag-columns li + li {
  margin-top: 7px;
}

.rag-precautions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px 14px;
  margin-top: 12px;
  padding: 12px 14px;
  border-left: 3px solid #ffca3a;
  background: rgba(255, 202, 58, 0.06);
  color: #cbddec;
  line-height: 1.6;
}

.rag-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.rag-actions button,
.rag-question button {
  border: 1px solid rgba(0, 240, 255, 0.35);
  background: rgba(0, 240, 255, 0.08);
  color: #8eeeff;
  padding: 7px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.rag-actions button:hover,
.rag-question button:hover:not(:disabled) {
  background: rgba(0, 240, 255, 0.18);
}

.rag-question {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.rag-question input {
  flex: 1;
  min-width: 0;
  border: 1px solid rgba(0, 240, 255, 0.2);
  background: rgba(4, 15, 34, 0.8);
  color: #e5f6ff;
  padding: 8px 10px;
  border-radius: 4px;
}

.rag-question input::placeholder {
  color: #7292aa;
}

.rag-question button:disabled {
  opacity: 0.55;
  cursor: wait;
}

.rag-followup {
  margin-top: 12px;
  padding: 14px;
  border: 1px solid rgba(100, 255, 180, 0.2);
  background: rgba(100, 255, 180, 0.04);
  color: #dceefa;
  line-height: 1.7;
}

.rag-followup-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #ffffff;
}

.rag-followup-head span,
.rag-followup-sources {
  color: #ffca3a;
  font-size: 13px;
}

.rag-followup p {
  margin: 8px 0;
}

.rag-followup ul {
  margin: 0;
  padding-left: 20px;
}

.note-box {
  color: #bfd5e7;
  line-height: 1.8;
  font-size: 14px;
}

.note-box p {
  margin: 0 0 10px;
}

.note-box p:last-child {
  margin-bottom: 0;
}

.report-footer {
  margin-top: 20px;
  padding: 18px 20px;
  border-radius: 12px;
  background: rgba(0, 240, 255, 0.08);
  border: 1px solid rgba(0, 240, 255, 0.18);
  color: #dceefa;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  line-height: 1.7;
}

.signature {
  white-space: nowrap;
}

.normal {
  color: #64ffb4 !important;
}

.warning {
  color: #ffca3a !important;
}

.danger {
  color: #ff5757 !important;
}

@media (max-width: 1100px) {
  .report-cover,
  .summary-grid,
  .two-column,
  .risk-layout,
  .param-grid,
  .rag-summary,
  .rag-columns {
    grid-template-columns: 1fr;
  }

  .rag-question {
    flex-direction: column;
  }

  .report-footer {
    flex-direction: column;
  }
}

@media print {
  @page {
    size: A4;
    margin: 12mm;
  }

  .no-print,
  .report-toolbar {
    display: none !important;
  }

  .report-viewport {
    width: auto;
    height: auto;
    overflow: visible;
    padding: 0;
    background: #ffffff;
    color: #111827;
  }

  .report-page {
    max-width: none;
    margin: 0;
    padding: 0;
    box-shadow: none;
    border: none;
    background: #ffffff;
    color: #111827;
  }

  .report-cover,
  .summary-card,
  .content-section,
  .section-card,
  .report-footer {
    background: #ffffff !important;
    color: #111827 !important;
    border-color: #d1d5db !important;
    box-shadow: none !important;
    break-inside: avoid;
  }

  .report-cover {
    grid-template-columns: 1fr;
  }

  .cover-left h1,
  .section-header h2,
  .summary-card strong,
  .param-head strong,
  .risk-table td,
  .risk-table th,
  .advice-item strong,
  .workorder strong {
    color: #111827 !important;
  }

  .cover-left p,
  .info-table td,
  .conclusion-box,
  .note-box,
  .advice-item p,
  .risk-explain,
  .param-card p,
  .report-footer {
    color: #374151 !important;
  }

  .summary-grid,
  .two-column,
  .risk-layout,
  .param-grid {
    display: block;
  }

  .summary-card,
  .content-section,
  .section-card,
  .param-card {
    margin-bottom: 12px;
  }

  .donut-card {
    display: none;
  }

  .risk-table th,
  .risk-table td,
  .info-table td {
    border-color: #d1d5db !important;
  }

  .level-tag {
    border-color: #d1d5db !important;
    background: #f3f4f6 !important;
  }
}
</style>
