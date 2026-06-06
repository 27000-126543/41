<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card shadow="never" style="margin-bottom: 16px;">
          <el-steps :active="stepStatus" finish-status="success" align-center>
            <el-step title="定标" description="按综合排名自动确定中标方" :status="steps.determine ? 'success' : ''" />
            <el-step title="发送通知" description="中标通知书+未中标感谢信" :status="steps.notify ? 'success' : ''" />
            <el-step title="生成合同" description="含中文大写金额的电子合同" :status="steps.contract ? 'success' : ''" />
            <el-step title="归档" description="历史数据归档" :status="steps.archive ? 'success' : ''" />
          </el-steps>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600;">🏆 中标项目列表</span>
              <el-button type="primary" @click="loadList" :icon="Refresh">刷新</el-button>
            </div>
          </template>
          <el-table :data="awards" stripe>
            <el-table-column prop="project_code" label="项目编号" width="170" />
            <el-table-column prop="project_name" label="项目名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="company_name" label="中标供应商" min-width="180" />
            <el-table-column prop="award_amount" label="中标金额" width="130">
              <template #default="{ row }"><b style="color: #10b981;">¥{{ Number(row.award_amount).toLocaleString() }}</b></template>
            </el-table-column>
            <el-table-column prop="award_date" label="中标日期" width="110" />
            <el-table-column label="通知" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.notification_sent" type="success" size="small">已发送</el-tag>
                <el-tag v-else type="warning" size="small">待发送</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="合同" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.contract_generated" type="success" size="small">已生成</el-tag>
                <el-tag v-else type="info" size="small">未生成</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <el-button type="success" size="small" link @click="notify(row)">发送通知</el-button>
                <el-button type="primary" size="small" link @click="genContract(row)">生成合同</el-button>
                <el-button size="small" link @click="viewDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" style="margin-bottom: 16px;">
          <template #header><span style="font-weight: 600;">⚡ 快捷操作</span></template>
          <el-select v-model="projectId" placeholder="选择招标项目" style="width: 100%; margin-bottom: 12px;">
            <el-option v-for="t in tenders" :key="t.id" :label="t.project_name" :value="t.id" />
          </el-select>
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <el-button type="success" @click="determineWinner">🎯 自动定标（按排名）</el-button>
            <el-button type="info" @click="notifyBidders">📧 推送所有通知</el-button>
            <el-button type="primary" @click="genContract">📋 生成合同草稿</el-button>
            <el-button type="warning" @click="archive">🗃 归档未中标</el-button>
            <el-button type="danger" @click="runAll">🚀 一键完成（定标→通知→合同→归档）</el-button>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">📊 中标金额分布</span></template>
          <div ref="chart" style="height: 280px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showContract" title="📋 合同草稿预览" width="700px" top="5vh">
      <pre style="font-family: 'Courier New', monospace; white-space: pre-wrap; max-height: 70vh; overflow: auto; background: #f8fafc; padding: 16px; border-radius: 8px;">{{ contractText }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/utils/api'

const awards = ref([])
const tenders = ref([])
const projectId = ref()
const chart = ref()
const showContract = ref(false)
const contractText = ref('')
const steps = reactive({ determine: false, notify: false, contract: false, archive: false })
const stepStatus = computedSteps()

function computedSteps() {
  let s = 0
  if (steps.determine) s = 1
  if (steps.notify) s = 2
  if (steps.contract) s = 3
  if (steps.archive) s = 4
  return s
}

async function loadAll() {
  const [tRes, aRes] = await Promise.all([
    api.get('/tenders'),
    api.get('/tenders'),
  ])
  tenders.value = tRes.data.filter(t => ['reviewed', 'awarded', 'evaluated'].includes(t.status))
  awards.value = []
  for (const t of tRes.data) {
    try {
      const res = await api.get(`/tenders/${t.id}/award`)
      if (res.data) awards.value.push(res.data)
    } catch {}
  }
  if (tenders.value.length) projectId.value = tenders.value[0].id
  renderChart()
}

async function loadList() { await loadAll() }

async function determineWinner() {
  if (!projectId.value) return ElMessage.warning('请选择项目')
  const res = await api.post(`/tenders/${projectId.value}/determine-winner`)
  ElMessage.success(`中标: ${res.data.winner.company_name}`)
  steps.determine = true
  loadAll()
}

async function notifyBidders() {
  if (!projectId.value) return
  await api.post(`/tenders/${projectId.value}/notify-bidders`)
  ElMessage.success('已发送中标通知书和感谢信')
  steps.notify = true
  loadAll()
}

async function genContract(row) {
  const pid = row?.project_id || projectId.value
  if (!pid) return
  const res = await api.post(`/tenders/${pid}/generate-contract`)
  contractText.value = res.data.content
  showContract.value = true
  steps.contract = true
  ElMessage.success('合同已生成')
  loadAll()
}

async function archive() {
  if (!projectId.value) return
  await api.post(`/tenders/${projectId.value}/archive`)
  steps.archive = true
  ElMessage.success('归档完成')
}

async function runAll() {
  if (!projectId.value) return ElMessage.warning('请选择项目')
  await determineWinner()
  await notifyBidders()
  await genContract()
  await archive()
  ElMessage.success('✅ 全流程完成')
}

function viewDetail(row) { }
function notify(row) { projectId.value = row.project_id; notifyBidders() }

function renderChart() {
  if (!chart.value || !awards.value.length) return
  const c = echarts.init(chart.value)
  c.setOption({
    tooltip: { trigger: 'item', formatter: '{b}<br/>¥{c}' },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
      label: { show: true, formatter: p => `${p.name.substring(0, 6)}: ¥${(p.value / 10000).toFixed(0)}万` },
      data: awards.value.map(a => ({ name: a.company_name, value: a.award_amount }))
    }]
  })
}

onMounted(loadAll)
</script>
