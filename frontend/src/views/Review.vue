<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px;">
      <el-form :inline="true">
        <el-form-item label="选择项目">
          <el-select v-model="projectId" style="width: 320px;" @change="loadData">
            <el-option v-for="t in tenders" :key="t.id" :label="`${t.project_code} - ${t.project_name}`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="warning" @click="aggregateScores">🔢 汇总打分（去高低分取平均）</el-button>
          <el-button type="primary" @click="genReport">📄 生成评审报告</el-button>
          <el-button type="danger" plain @click="exportPDF">⬇️ 导出PDF</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 600;">
              <span>📊 评审结果汇总</span>
              <el-tag type="info" v-if="tender">
                权重: 技术{{ (tender.weight_technical*100).toFixed(0) }}% /
                商务{{ (tender.weight_commercial*100).toFixed(0) }}% /
                资质{{ (tender.weight_qualification*100).toFixed(0) }}%
              </el-tag>
            </div>
          </template>
          <el-table :data="bids" stripe>
            <el-table-column label="排名" width="70" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.ranking === 1" type="success" effect="dark" size="large">🏆 {{ row.ranking }}</el-tag>
                <el-tag v-else-if="row.ranking === 2" type="warning" size="large">🥈 {{ row.ranking }}</el-tag>
                <el-tag v-else-if="row.ranking === 3" type="" size="large">🥉 {{ row.ranking }}</el-tag>
                <span v-else-if="row.ranking">{{ row.ranking }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="company_name" label="投标供应商" min-width="180" />
            <el-table-column prop="bid_amount" label="投标金额" width="130">
              <template #default="{ row }">¥{{ Number(row.bid_amount).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="technical_score" label="技术分" width="90">
              <template #default="{ row }"><el-progress :percentage="row.technical_score || 0" :stroke-width="10" :show-text="true" /></template>
            </el-table-column>
            <el-table-column prop="commercial_score" label="商务分" width="90">
              <template #default="{ row }"><el-progress :percentage="row.commercial_score || 0" :stroke-width="10" color="#f59e0b" /></template>
            </el-table-column>
            <el-table-column prop="qualification_score" label="资质分" width="90">
              <template #default="{ row }"><el-progress :percentage="row.qualification_score || 0" :stroke-width="10" color="#8b5cf6" /></template>
            </el-table-column>
            <el-table-column prop="final_score" label="综合分" width="100">
              <template #default="{ row }">
                <b :style="{ fontSize: '16px', color: row.ranking === 1 ? '#10b981' : '#1e293b' }">{{ row.final_score?.toFixed(2) }}</b>
              </template>
            </el-table-column>
          </el-table>

          <div ref="scoreChart" style="height: 300px; margin-top: 20px;"></div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" style="margin-bottom: 16px;">
          <template #header><span style="font-weight: 600;">✍️ 专家独立打分</span></template>
          <template v-if="userStore.hasRole('expert')">
            <el-form label-width="90px" size="default">
              <el-form-item label="选择投标">
                <el-select v-model="scoreForm.bid_id" style="width: 100%;">
                  <el-option v-for="b in bids" :key="b.id" :label="b.company_name" :value="b.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="技术分">
                <el-slider v-model="scoreForm.technical_score" :min="0" :max="100" :step="0.5" show-input />
              </el-form-item>
              <el-form-item label="商务分">
                <el-slider v-model="scoreForm.commercial_score" :min="0" :max="100" :step="0.5" show-input />
              </el-form-item>
              <el-form-item label="资质分">
                <el-slider v-model="scoreForm.qualification_score" :min="0" :max="100" :step="0.5" show-input />
              </el-form-item>
              <el-form-item label="评审意见">
                <el-input v-model="scoreForm.comment" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="submitScore">提交打分</el-button>
              </el-form-item>
            </el-form>
          </template>
          <el-empty v-else description="仅评审专家可打分，其他角色可查看汇总结果" />
        </el-card>

        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">🧑‍⚖️ 评审委员会</span></template>
          <el-table :data="experts" size="small">
            <el-table-column prop="name" label="姓名" width="80" />
            <el-table-column prop="title" label="职称" width="100" />
            <el-table-column prop="specialty" label="专业" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showReport" title="📄 评审报告" width="800px" top="5vh">
      <pre style="font-family: monospace; white-space: pre-wrap; max-height: 65vh; overflow: auto;">{{ reportContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const tenders = ref([])
const projectId = ref()
const tender = ref()
const bids = ref([])
const experts = ref([])
const scoreChart = ref()
const showReport = ref(false)
const reportContent = ref('')
const scoreForm = reactive({ bid_id: null, technical_score: 85, commercial_score: 85, qualification_score: 85, comment: '' })

async function loadTenders() {
  tenders.value = (await api.get('/tenders')).data
  if (tenders.value.length) {
    projectId.value = tenders.value[0].id
    loadData()
  }
}

async function loadData() {
  if (!projectId.value) return
  const [tRes, bRes, eRes] = await Promise.all([
    api.get(`/tenders/${projectId.value}`),
    api.get(`/tenders/${projectId.value}/bids`),
    api.get(`/tenders/${projectId.value}/experts`),
  ])
  tender.value = tRes.data
  bids.value = bRes.data
  experts.value = eRes.data
  await nextTick()
  renderChart()
}

async function submitScore() {
  if (!scoreForm.bid_id) return ElMessage.warning('请选择投标供应商')
  await api.post(`/tenders/${projectId.value}/expert-score`, scoreForm)
  ElMessage.success('打分已提交')
}

async function aggregateScores() {
  const res = await api.post(`/tenders/${projectId.value}/aggregate-scores`)
  ElMessage.success(res.msg || '汇总完成')
  loadData()
}

async function genReport() {
  const res = await api.post(`/tenders/${projectId.value}/review-report`)
  reportContent.value = res.data.content
  showReport.value = true
}

async function exportPDF() {
  const res = await api.get(`/export/review-report-pdf/${projectId.value}`)
  ElMessage.success('PDF已生成: ' + res.data.pdf_path)
}

function renderChart() {
  if (!scoreChart.value || !bids.value.length) return
  const chart = echarts.init(scoreChart.value)
  const sorted = [...bids.value].sort((a, b) => (b.final_score || 0) - (a.final_score || 0))
  chart.setOption({
    title: { text: '投标供应商综合评分对比（柱状图）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['技术分', '商务分', '资质分', '综合分'], bottom: 0 },
    grid: { left: 150, right: 30, top: 50, bottom: 60 },
    xAxis: { type: 'value', max: 100 },
    yAxis: { type: 'category', data: sorted.map(b => b.company_name.substring(0, 10)), inverse: true },
    series: [
      { name: '技术分', type: 'bar', data: sorted.map(b => b.technical_score || 0), itemStyle: { color: '#3b82f6' } },
      { name: '商务分', type: 'bar', data: sorted.map(b => b.commercial_score || 0), itemStyle: { color: '#f59e0b' } },
      { name: '资质分', type: 'bar', data: sorted.map(b => b.qualification_score || 0), itemStyle: { color: '#8b5cf6' } },
      { name: '综合分', type: 'bar', data: sorted.map(b => b.final_score || 0), itemStyle: { color: '#10b981' } }
    ]
  })
}

watch(projectId, loadData)
onMounted(loadTenders)
</script>
