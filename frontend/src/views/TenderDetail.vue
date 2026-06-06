<template>
  <div v-if="tender">
    <el-page-header :content="tender.project_name" @back="$router.back()">
      <template #extra>
        <el-tag v-for="tag in statusTags" :key="tag" :type="tag.type" style="margin-left: 8px;">{{ tag.label }}</el-tag>
      </template>
    </el-page-header>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="16">
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane label="📋 项目信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="项目编号">{{ tender.project_code }}</el-descriptions-item>
              <el-descriptions-item label="项目类别">{{ catMap[tender.category] }}</el-descriptions-item>
              <el-descriptions-item label="预算金额">¥{{ Number(tender.budget_amount).toLocaleString() }}</el-descriptions-item>
              <el-descriptions-item label="采购部门">{{ tender.department_name }}</el-descriptions-item>
              <el-descriptions-item label="发布日期">{{ tender.publish_date }}</el-descriptions-item>
              <el-descriptions-item label="投标截止">{{ tender.bid_deadline }}</el-descriptions-item>
              <el-descriptions-item label="开标日期">{{ tender.open_bid_date }}</el-descriptions-item>
              <el-descriptions-item label="项目状态">
                <el-tag :type="statusMap[tender.status]?.type">{{ statusMap[tender.status]?.label }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="评分权重" :span="2">
                技术 {{ (tender.weight_technical*100).toFixed(0) }}% / 
                商务 {{ (tender.weight_commercial*100).toFixed(0) }}% / 
                资质 {{ (tender.weight_qualification*100).toFixed(0) }}%
              </el-descriptions-item>
              <el-descriptions-item label="项目简介" :span="2">{{ tender.request_description || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="📝 投标列表" name="bids">
            <template v-if="userStore.hasRole('supplier')">
              <el-card shadow="never" style="margin-bottom: 12px;">
                <template #header>📝 提交投标</template>
                <el-form :inline="true" :model="bidForm">
                  <el-form-item label="投标金额"><el-input-number v-model="bidForm.bid_amount" :min="0" :precision="2" /></el-form-item>
                  <el-form-item label="交付日期"><el-date-picker v-model="bidForm.delivery_date" type="date" /></el-form-item>
                  <el-form-item label="方案说明"><el-input v-model="bidForm.bid_content" style="width: 240px" /></el-form-item>
                  <el-form-item><el-button type="primary" @click="submitBid">提交投标</el-button></el-form-item>
                </el-form>
              </el-card>
            </template>
            <el-table :data="bids" stripe>
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="company_name" label="供应商" min-width="180" />
              <el-table-column prop="qualification_level" label="资质" width="80" />
              <el-table-column prop="credit_score" label="信用分" width="80" />
              <el-table-column prop="bid_amount" label="投标金额" width="130">
                <template #default="{ row }">¥{{ Number(row.bid_amount).toLocaleString() }}</template>
              </el-table-column>
              <el-table-column prop="technical_score" label="技术分" width="80" />
              <el-table-column prop="commercial_score" label="商务分" width="80" />
              <el-table-column prop="qualification_score" label="资质分" width="80" />
              <el-table-column prop="final_score" label="综合分" width="90">
                <template #default="{ row }"><b :style="{ color: row.ranking === 1 ? '#10b981' : '' }">{{ row.final_score?.toFixed(2) }}</b></template>
              </el-table-column>
              <el-table-column prop="ranking" label="排名" width="70">
                <template #default="{ row }">
                  <el-tag v-if="row.ranking === 1" type="success" effect="dark">🏆 {{ row.ranking }}</el-tag>
                  <el-tag v-else-if="row.ranking" size="small">{{ row.ranking }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90" />
            </el-table>
            <div style="margin-top: 12px;">
              <el-button v-if="tender.status === 'published'" type="warning" @click="decrypt">🔓 开标解密</el-button>
              <el-button v-if="tender.status === 'decrypted' || tender.status === 'published'" type="info" @click="autoScore">📊 自动评分排名</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="🧑‍⚖️ 评审专家" name="experts">
            <div style="margin-bottom: 12px;">
              <el-select v-model="expertNum" style="width: 120px; margin-right: 8px;">
                <el-option :label="n + '人'" :value="n" v-for="n in [3,5,7]" :key="n" />
              </el-select>
              <el-button type="primary" @click="assignExperts" :disabled="!userStore.hasRole('admin','procurement')">🎲 自动分配专家（按专业+回避）</el-button>
            </div>
            <el-table :data="experts" stripe>
              <el-table-column prop="expert_code" label="专家编号" width="120" />
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="title" label="职称" width="120" />
              <el-table-column prop="specialty" label="专业" width="150" />
              <el-table-column prop="organization" label="所属单位" min-width="180" />
              <el-table-column prop="phone" label="联系电话" width="130" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="⚖️ 评审打分" name="review">
            <template v-if="userStore.hasRole('expert')">
              <el-card shadow="never" style="margin-bottom: 12px;">
                <template #header>✍️ 专家独立打分</template>
                <el-form :inline="true" :model="scoreForm">
                  <el-form-item label="投标"><el-select v-model="scoreForm.bid_id" style="width: 240px;">
                    <el-option v-for="b in bids" :key="b.id" :label="b.company_name" :value="b.id" /></el-select>
                  </el-form-item>
                  <el-form-item label="技术分"><el-input-number v-model="scoreForm.technical_score" :min="0" :max="100" :precision="2" /></el-form-item>
                  <el-form-item label="商务分"><el-input-number v-model="scoreForm.commercial_score" :min="0" :max="100" :precision="2" /></el-form-item>
                  <el-form-item label="资质分"><el-input-number v-model="scoreForm.qualification_score" :min="0" :max="100" :precision="2" /></el-form-item>
                  <el-form-item><el-button type="primary" @click="submitScore">提交打分</el-button></el-form-item>
                </el-form>
              </el-card>
            </template>
            <el-button type="warning" style="margin-bottom: 12px;" @click="aggregateScores">🔢 汇总专家打分（去高低分取平均）</el-button>
            <el-button type="primary" @click="genReport">📄 生成评审报告</el-button>
            <el-card v-if="report" shadow="never" style="margin-top: 12px;">
              <pre style="font-family: monospace; white-space: pre-wrap;">{{ report.report_content }}</pre>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="🏆 中标与合同" name="award">
            <div style="margin-bottom: 12px;">
              <el-button type="success" @click="determineWinner" :disabled="!userStore.hasRole('admin','procurement','manager')">🎯 自动定标</el-button>
              <el-button type="info" @click="notifyBidders">📧 推送通知（中标/感谢信）</el-button>
              <el-button type="primary" @click="genContract">📋 生成合同草稿</el-button>
              <el-button type="warning" @click="archive">🗃 归档未中标</el-button>
            </div>
            <el-descriptions v-if="award" :column="2" border>
              <el-descriptions-item label="中标供应商">{{ award.company_name }}</el-descriptions-item>
              <el-descriptions-item label="中标金额">¥{{ Number(award.award_amount).toLocaleString() }}</el-descriptions-item>
              <el-descriptions-item label="中标日期">{{ award.award_date }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag v-if="award.notification_sent" type="success" size="small">已通知</el-tag>
                <el-tag v-else type="warning" size="small">待通知</el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <el-empty v-else description="尚未定标" />
          </el-tab-pane>
        </el-tabs>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" style="margin-bottom: 16px;">
          <template #header><span style="font-weight: 600;">🎯 快捷操作</span></template>
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <el-button v-if="tender.status === 'draft'" type="primary" @click="publish">📢 发布招标公告</el-button>
            <el-button v-if="tender.status === 'published'" type="warning" @click="decrypt">🔓 开标解密</el-button>
            <el-button v-if="tender.status === 'decrypted' || tender.status === 'evaluated'" type="info" @click="assignAndScore">🧑‍⚖️ 分配专家并评分</el-button>
            <el-button v-if="tender.status === 'reviewed'" type="success" @click="fullAward">🏆 定标+通知+合同（一键）</el-button>
            <el-button type="danger" plain @click="exportPDF">📄 导出评审报告PDF</el-button>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">📊 投标金额分布</span></template>
          <div ref="bidChart" style="height: 260px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const projectId = route.params.id
const catMap = { goods: '货物', engineering: '工程', service: '服务' }
const statusMap = { draft: {label:'草稿',type:'info'}, published: {label:'已发布',type:'primary'}, decrypted: {label:'已开标',type:''}, reviewed: {label:'已评审',type:'warning'}, awarded: {label:'已中标',type:'success'} }

const tender = ref()
const bids = ref([])
const experts = ref([])
const award = ref()
const report = ref()
const activeTab = ref('info')
const expertNum = ref(5)
const bidChart = ref()
const bidForm = reactive({ bid_amount: 0, delivery_date: '', bid_content: '' })
const scoreForm = reactive({ bid_id: null, technical_score: 85, commercial_score: 85, qualification_score: 85 })

const statusTags = computed(() => {
  const tags = [{ label: catMap[tender.value.category], type: '' }]
  const s = statusMap[tender.value.status]
  if (s) tags.push({ label: s.label, type: s.type })
  return tags
})

async function loadAll() {
  const [tRes, bRes, eRes, aRes] = await Promise.all([
    api.get(`/tenders/${projectId}`),
    api.get(`/tenders/${projectId}/bids`),
    api.get(`/tenders/${projectId}/experts`),
    api.get(`/tenders/${projectId}/award`).catch(() => ({ data: null }))
  ])
  tender.value = tRes.data
  bids.value = bRes.data
  experts.value = eRes.data
  award.value = aRes.data
  renderBidChart()
}

async function publish() {
  await api.post(`/tenders/${projectId}/publish`)
  ElMessage.success('已发布到企业官网和供应商门户')
  loadAll()
}

async function decrypt() {
  await api.post(`/tenders/${projectId}/decrypt`)
  ElMessage.success('所有标书已解密')
  loadAll()
}

async function autoScore() {
  const res = await api.post(`/tenders/${projectId}/auto-score`)
  ElMessage.success(`完成${res.data.length}家评分排名`)
  loadAll()
}

async function submitBid() {
  if (!bidForm.bid_amount) return ElMessage.warning('请输入金额')
  await api.post(`/tenders/${projectId}/bids`, bidForm)
  ElMessage.success('投标已加密提交')
  loadAll()
}

async function assignExperts() {
  const res = await api.post(`/tenders/${projectId}/assign-experts`, { num_experts: expertNum.value })
  ElMessage.success(`已分配${res.data.length}位专家`)
  loadAll()
}

async function assignAndScore() {
  await assignExperts()
  await decrypt().catch(()=>{})
  await autoScore()
  activeTab.value = 'review'
}

async function submitScore() {
  if (!scoreForm.bid_id) return ElMessage.warning('请选择投标供应商')
  await api.post(`/tenders/${projectId}/expert-score`, scoreForm)
  ElMessage.success('打分已提交')
}

async function aggregateScores() {
  const res = await api.post(`/tenders/${projectId}/aggregate-scores`)
  ElMessage.success(res.msg || '汇总完成')
  loadAll()
}

async function genReport() {
  const res = await api.get(`/tenders/${projectId}/review-report`)
  report.value = res.data
  ElMessage.success('评审报告已生成')
}

async function determineWinner() {
  const res = await api.post(`/tenders/${projectId}/determine-winner`)
  ElMessage.success(`中标: ${res.data.winner.company_name}`)
  loadAll()
}

async function notifyBidders() {
  await api.post(`/tenders/${projectId}/notify-bidders`)
  ElMessage.success('已向所有投标方发送通知')
  loadAll()
}

async function genContract() {
  await api.post(`/tenders/${projectId}/generate-contract`)
  ElMessage.success('合同草稿已生成')
  loadAll()
}

async function archive() {
  await api.post(`/tenders/${projectId}/archive`)
  ElMessage.success('已归档')
  loadAll()
}

async function fullAward() {
  await determineWinner()
  await notifyBidders()
  await genContract()
  await archive()
  ElMessage.success('全流程完成')
  loadAll()
}

async function exportPDF() {
  const res = await api.get(`/export/review-report-pdf/${projectId}`)
  ElMessage.success('PDF已生成: ' + res.data.pdf_path)
}

function renderBidChart() {
  if (!bidChart.value || !bids.value.length) return
  const chart = echarts.init(bidChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 100, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: bids.value.map(b => b.company_name.substring(0,6)), inverse: true },
    series: [{
      type: 'bar',
      data: bids.value.map(b => b.bid_amount),
      itemStyle: { color: params => params.dataIndex === 0 ? '#10b981' : '#3b82f6' },
      label: { show: true, position: 'right', formatter: p => '¥' + (p.value/10000).toFixed(1) + '万' }
    }]
  })
}

onMounted(loadAll)
</script>
