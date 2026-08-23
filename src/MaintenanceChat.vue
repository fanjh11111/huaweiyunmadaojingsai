<template>
  <div class="chat-viewport">
    <header class="chat-header">
      <button class="header-btn ghost" @click="goHome">返回监控中心</button>
      <div class="header-title">
        <span class="title-main">航枢 · 维修知识问答智能体</span>
      </div>
      <button class="header-btn ghost" @click="clearSession">清空会话</button>
    </header>

    <main class="chat-body">
      <section class="chat-main-panel">
        <div class="chat-messages" ref="messagesRef">
        <div v-if="!messages.length" class="chat-welcome">
          <div class="welcome-icon">🛩️</div>
          <h2>维修知识问答智能体</h2>
          <p>我是航空发动机维修知识问答助手，可以回答发动机振动、排气温度、液压泄漏等故障的检查与处置问题。</p>
          <p v-if="hasFaultContext" class="context-tip">
            已自动带入最近一次故障预测上下文：{{ faultContextSummary }}
          </p>
        </div>

        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-row"
          :class="message.role"
        >
          <div class="message-avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>
          <div class="message-content">
            <div class="message-bubble" :class="{ 'markdown-bubble': message.role === 'assistant' }">
              <pre v-if="message.role === 'user'" class="message-text">{{ message.content }}</pre>
              <div v-else class="message-text markdown-body" v-html="renderMarkdown(message.content)"></div>
            </div>
            <div v-if="message.sources && message.sources.length" class="message-sources">
              <span class="sources-label">参考依据：</span>
              <a
                v-for="(source, sIndex) in message.sources"
                :key="sIndex"
                class="source-tag"
                :title="source.source"
              >{{ sourceTitle(source) }}</a>
            </div>
            <div v-if="message.status && message.status !== 'success'" class="message-status" :class="message.status">
              {{ statusText(message.status) }}
            </div>
          </div>
        </div>

        <div v-if="loading" class="message-row assistant">
          <div class="message-avatar">AI</div>
          <div class="message-content">
            <div class="message-bubble loading-bubble">
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
            </div>
          </div>
        </div>
        </div>

        <div class="chat-input-area">
          <input
            v-model="inputText"
            class="chat-input"
            placeholder="输入维修相关问题，例如：发动机振动升高需要检查哪些部件？"
            @keydown.enter="sendMessage"
            :disabled="loading"
          />
          <button class="send-btn" @click="sendMessage" :disabled="loading || !inputText.trim()">
            {{ loading ? '思考中...' : '发送' }}
          </button>
        </div>
      </section>

      <aside class="chat-sidebar" aria-label="维修问答辅助面板">
        <section class="sidebar-card agent-card">
          <span class="sidebar-kicker">MAINTENANCE COPILOT</span>
          <h2>维修知识问答工作台</h2>
          <p>围绕发动机维护、风险排查和故障检测，提供证据驱动的辅助分析。</p>
          <div class="capability-tags">
            <span>维修检查</span>
            <span>风险排查</span>
            <span>故障检测</span>
          </div>
        </section>

        <section class="sidebar-card quick-card">
          <div class="sidebar-card-title">
            <span class="sidebar-icon">✦</span>
            <span>快捷问题</span>
          </div>
          <button
            v-for="question in quickQuestions"
            :key="question"
            class="quick-btn"
            @click="sendQuickQuestion(question)"
          >{{ question }}</button>
        </section>

        <section class="sidebar-note">
          <span>△</span>
          回答用于辅助维修分析；最终检查与放行须依据现行批准数据并由授权人员确认。
        </section>
      </aside>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

const router = useRouter()
const backendUrl = 'http://localhost:8000/api/rag-chat'

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  // 先转义 HTML 再解析 Markdown：模型输出中的原始 HTML/脚本变纯文本，杜绝注入
  return marked.parse(escapeHtml(text)) as string
}

interface Source {
  source: string
  title: string
  score: number
  content_hash?: string
}
interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  status?: string
}

const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(false)
const sessionId = ref<string | null>(null)
const faultContext = ref<any | null>(null)
const messagesRef = ref<HTMLElement | null>(null)

const quickQuestions = [
  '发动机振动持续升高需要检查哪些部件？',
  '液压系统压力下降疑似泄漏怎么处置？',
  '排气温度超限是否需要停场检查？',
  '发动机振动异常现在能否继续放行？',
]

const hasFaultContext = computed(() => !!faultContext.value)
const faultContextSummary = computed(() => {
  const ctx = faultContext.value
  if (!ctx) return ''
  const parts: string[] = []
  if (ctx.component) parts.push(ctx.component)
  if (ctx.fault_type) parts.push(ctx.fault_type)
  if (ctx.risk_level) parts.push(`${ctx.risk_level}风险`)
  return parts.join(' · ')
})

function goHome() {
  router.push('/')
}

function sourceTitle(source: Source): string {
  const filename = source.source.split('/').pop() || source.source
  return filename.replace('.md', '')
}

function statusText(status: string): string {
  const map: Record<string, string> = {
    no_evidence: '知识库无足够依据，未编造答案',
    out_of_scope: '超出维修知识范围',
    empty_input: '请输入问题',
  }
  return map[status] || status
}

function loadFaultContext() {
  try {
    const stored = localStorage.getItem('ragAdvice')
    if (stored) {
      const advice = JSON.parse(stored)
      faultContext.value = {
        component: advice.component || '',
        fault_type: advice.fault_type || advice.abnormal_judgment || '',
        risk_level: advice.risk_level || '',
        abnormal_features: advice.abnormal_features || [],
        description: advice.description || '',
      }
    }
  } catch {
    faultContext.value = null
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        message: text,
        fault_context: faultContext.value,
      }),
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const data = await response.json()
    sessionId.value = data.session_id
    messages.value.push({
      role: 'assistant',
      content: data.answer,
      sources: data.sources || [],
      status: data.status,
    })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `调用智能体失败：${error instanceof Error ? error.message : '未知错误'}。请确认后端服务已启动并配置 AgentArts 环境变量。`,
      status: 'error',
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function sendQuickQuestion(question: string) {
  inputText.value = question
  sendMessage()
}

async function clearSession() {
  if (sessionId.value) {
    try {
      await fetch(`${backendUrl}/sessions/${sessionId.value}`, { method: 'DELETE' })
    } catch {
      // 忽略清除失败
    }
  }
  messages.value = []
  sessionId.value = null
}

function consumePendingQuestion() {
  const pending = localStorage.getItem('ragPendingQuestion')
  if (!pending) return

  // 立即删除，保证 onMounted + onActivated 首次双触发时只发送一次
  localStorage.removeItem('ragPendingQuestion')
  inputText.value = pending
  sendMessage()
}

onMounted(() => {
  loadFaultContext()
  consumePendingQuestion()
})

// App.vue 使用 keep-alive，二次进入本页时 onMounted 不会再触发，需 onActivated 兜底
onActivated(() => {
  loadFaultContext()
  consumePendingQuestion()
})
</script>

<style scoped>
.chat-viewport {
  height: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(135deg, #07111f, #0f172a 45%, #111827);
  color: #e5f6ff;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px clamp(24px, 3vw, 56px);
  background: rgba(8, 15, 34, 0.94);
  border-bottom: 1px solid rgba(0, 240, 255, 0.18);
}

.header-title {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.title-main {
  font-size: 18px;
  font-weight: 600;
  color: #8eeeff;
  letter-spacing: 1px;
}

.header-btn {
  border: 1px solid rgba(0, 240, 255, 0.35);
  background: rgba(0, 240, 255, 0.08);
  color: #8eeeff;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.header-btn:hover {
  background: rgba(0, 240, 255, 0.18);
}

.chat-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 20px;
  max-width: 1720px;
  width: calc(100% - 56px);
  margin: 0 auto;
  padding: 22px 0 26px;
}

.chat-main-panel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 22px;
  background: rgba(4, 15, 34, 0.6);
  border: 1px solid rgba(0, 240, 255, 0.08);
  border-radius: 8px;
  margin-bottom: 0;
}

.chat-sidebar {
  min-width: 0;
  overflow-y: auto;
  padding-right: 2px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-card {
  padding: 16px;
  border: 1px solid rgba(0, 240, 255, 0.16);
  border-radius: 8px;
  background: linear-gradient(145deg, rgba(13, 28, 55, 0.88), rgba(6, 17, 35, 0.86));
  box-shadow: inset 0 1px 0 rgba(142, 238, 255, 0.05);
}

.sidebar-kicker {
  display: block;
  margin-bottom: 7px;
  color: #35dcf2;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.2px;
}

.agent-card {
  border-color: rgba(0, 240, 255, 0.3);
  background: linear-gradient(145deg, rgba(0, 112, 160, 0.2), rgba(11, 27, 53, 0.92));
}

.agent-card h2 {
  margin: 0 0 8px;
  color: #e7fbff;
  font-size: 18px;
  line-height: 1.35;
}

.agent-card p {
  margin: 0;
  color: #93b8d1;
  font-size: 13px;
  line-height: 1.7;
}

.capability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 13px;
}

.capability-tags span {
  padding: 4px 8px;
  border: 1px solid rgba(0, 240, 255, 0.25);
  border-radius: 3px;
  background: rgba(0, 240, 255, 0.07);
  color: #a5f6ff;
  font-size: 12px;
}

.sidebar-card-title {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 10px;
  color: #ccefff;
  font-size: 14px;
  font-weight: 600;
}

.sidebar-icon {
  color: #00eaff;
  font-size: 15px;
}

.quick-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-card .sidebar-card-title {
  margin-bottom: 2px;
}

.quick-card .quick-btn {
  width: 100%;
  padding: 9px 10px;
  border-radius: 5px;
  color: #bfe7f5;
  text-align: left;
  line-height: 1.45;
}

.quick-card .quick-btn:hover {
  transform: translateX(3px);
}

.sidebar-note {
  display: flex;
  gap: 7px;
  padding: 11px 12px;
  border-left: 2px solid rgba(255, 202, 58, 0.65);
  color: #91aabd;
  font-size: 12px;
  line-height: 1.65;
}

.sidebar-note span {
  color: #ffca3a;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 240, 255, 0.25);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 240, 255, 0.45);
}

.markdown-bubble {
  border-top: 1px solid rgba(0, 240, 255, 0.25);
  background: linear-gradient(180deg, rgba(14, 26, 52, 0.9), rgba(18, 30, 58, 0.82));
}

.chat-welcome {
  max-width: 760px;
  margin: auto;
  text-align: center;
  padding: 48px 20px;
  color: #b9d2e6;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.chat-welcome h2 {
  color: #8eeeff;
  font-size: 22px;
  margin: 0 0 12px;
}

.chat-welcome p {
  color: #8bb7d9;
  line-height: 1.7;
  margin: 6px 0;
}

.context-tip {
  color: #ffca3a !important;
  font-size: 13px;
  margin-top: 12px !important;
}

.quick-questions {
  margin-top: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.quick-label {
  color: #7292aa;
  font-size: 13px;
}

.quick-btn {
  border: 1px solid rgba(0, 240, 255, 0.3);
  background: rgba(0, 240, 255, 0.06);
  color: #cde8f8;
  padding: 7px 14px;
  border-radius: 16px;
  cursor: pointer;
  font-size: 13px;
}

.quick-btn:hover {
  background: rgba(0, 240, 255, 0.18);
  color: #8eeeff;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
  align-items: flex-start;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.message-row.user .message-avatar {
  background: #00eaff;
  color: #06111e;
}

.message-row.assistant .message-avatar {
  background: rgba(0, 240, 255, 0.18);
  color: #8eeeff;
  border: 1px solid rgba(0, 240, 255, 0.4);
}

.message-content {
  max-width: min(84%, 980px);
  display: flex;
  flex-direction: column;
}

.message-row.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
}

.message-row.user .message-bubble {
  background: rgba(0, 240, 255, 0.14);
  border: 1px solid rgba(0, 240, 255, 0.3);
  color: #e5f6ff;
}

.message-row.assistant .message-bubble {
  background: rgba(18, 30, 58, 0.82);
  border: 1px solid rgba(0, 240, 255, 0.12);
  color: #dceefa;
}

.message-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
}

/* ===== 助手 Markdown 回答排版 ===== */
.markdown-body {
  white-space: normal;
  line-height: 1.75;
}

.markdown-body :deep(p) {
  margin: 0 0 10px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(strong) {
  color: #8eeeff;
  font-weight: 600;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 6px 0 10px;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin: 5px 0;
}

.markdown-body :deep(li::marker) {
  color: #00eaff;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-size: 15px;
  font-weight: 600;
  color: #8eeeff;
  margin: 14px 0 8px;
}

.markdown-body :deep(h1:first-child),
.markdown-body :deep(h2:first-child),
.markdown-body :deep(h3:first-child) {
  margin-top: 2px;
}

.markdown-body :deep(code) {
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.18);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #b9f4ff;
}

.markdown-body :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 12px;
  border-left: 3px solid rgba(0, 240, 255, 0.45);
  background: rgba(0, 240, 255, 0.05);
  border-radius: 0 6px 6px 0;
  color: #a8c6dd;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(0, 240, 255, 0.15);
  margin: 12px 0;
}

.markdown-body :deep(a) {
  color: #64ffb4;
  text-decoration: none;
  border-bottom: 1px dashed rgba(100, 255, 180, 0.4);
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 13px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid rgba(0, 240, 255, 0.2);
  padding: 5px 10px;
}

.markdown-body :deep(th) {
  background: rgba(0, 240, 255, 0.08);
  color: #8eeeff;
}

.message-sources {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.sources-label {
  color: #7292aa;
  font-size: 12px;
}

.source-tag {
  display: inline-block;
  padding: 2px 10px;
  background: rgba(100, 255, 180, 0.1);
  border: 1px solid rgba(100, 255, 180, 0.3);
  color: #64ffb4;
  border-radius: 10px;
  font-size: 12px;
  cursor: default;
}

.message-status {
  margin-top: 6px;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
  display: inline-block;
  align-self: flex-start;
}

.message-status.no_evidence {
  background: rgba(255, 202, 58, 0.12);
  color: #ffca3a;
}

.message-status.out_of_scope {
  background: rgba(255, 87, 87, 0.12);
  color: #ff7070;
}

.message-status.error {
  background: rgba(255, 87, 87, 0.12);
  color: #ff7070;
}

.loading-bubble {
  display: flex;
  gap: 6px;
  align-items: center;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8eeeff;
  animation: dot-pulse 1.4s infinite ease-in-out;
}

.loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 12px;
  flex-shrink: 0;
  background: rgba(8, 15, 34, 0.94);
  border: 1px solid rgba(0, 240, 255, 0.18);
  border-radius: 8px;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  background: rgba(4, 15, 34, 0.8);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 6px;
  color: #e5f6ff;
  font-size: 14px;
  outline: none;
}

.chat-input:focus {
  border-color: rgba(0, 240, 255, 0.5);
}

.chat-input::placeholder {
  color: #557b9b;
}

.send-btn {
  padding: 12px 28px;
  background: #00eaff;
  color: #06111e;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.send-btn:hover:not(:disabled) {
  background: #8eeeff;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 1180px) {
  .chat-body {
    grid-template-columns: minmax(0, 1fr);
    width: calc(100% - 40px);
  }

  .chat-sidebar {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
    overflow: visible;
  }

  .agent-card {
    grid-row: span 2;
  }
}

@media (max-width: 720px) {
  .chat-header {
    padding: 10px 12px;
  }

  .header-title {
    min-width: 0;
  }

  .title-main {
    font-size: 14px;
  }

  .header-btn {
    padding: 7px 9px;
    font-size: 12px;
  }

  .chat-body {
    width: calc(100% - 24px);
    padding: 12px 0 18px;
  }

  .chat-messages {
    padding: 14px;
  }

  .chat-sidebar {
    grid-template-columns: 1fr;
  }

  .agent-card {
    grid-row: auto;
  }

  .message-content {
    max-width: 88%;
  }

  .chat-input-area {
    gap: 8px;
    padding: 8px;
  }

  .send-btn {
    padding: 10px 15px;
  }
}
</style>
