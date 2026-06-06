<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card shadow="never" style="margin-bottom: 16px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 600;">
              <span>📊 部门预算看板</span>
              <el-tag type="primary" effect="plain">实时数据</el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="8" v-for="d in depts" :key="d.id" style="margin-bottom: 16px;">
              <div class="budget-card">
                <div class="dept-name">
                  <el-icon><OfficeBuilding /></el-icon>
                  {{ d.name || d.name }}
                </div>
                <div class="budget-main">
                  <span class="used">¥{{ Number(d.budget_used).toLocaleString() }}</span>
                  <span class="sep">/</span>
                  <span class="total">¥{{ Number(d.budget_limit).toLocaleString() }}</span>
                </div>
                <el-progress 
                  :percentage="Math.min(d.usage_percent || 0, 100)" 
                  :color="progressColor(d.usage_percent)"
                  :stroke-width="14"
                />
                <div class="budget-footer">
                  <span>剩余: ¥{{ Number(d.available_budget || (d.budget_limit - d.budget_used)).toLocaleString() }}</span>
                  <el-tag v-if="(d.usage_percent || 0) >= 80" type="danger" size="small" effect="dark">超预算风险</el-tag>
                  <el-tag v-else-if="(d.usage_percent || 0) >= 60" type="warning" size="small">关注</el-tag>
                  <el-tag v-else type="success" size="small">健康</el-tag>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">⏳ 待审批申请</span></template>
          <el-table :data="pendingList" size="small" stripe>
            <el-table-column prop="title" label="申请标题" show-overflow-tooltip />
            <el-table-column prop="department_name" label="部门" width="100" />
            <el-table-column prop="estimated_amount" label="金额" width="120">
              <template #default="{ row }">¥{{ Number(row.estimated_amount).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button size="small" type="success" link @click="approve(row)">通过</el-button>
                <el-button size="small" type="danger" link @click="reject(row)">驳回</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">💰 部门预算使用趋势</span></template>
          <div ref="chartTrend" style="height: 320px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const depts = ref([])
const pendingList = ref([])
const chartTrend = ref()

function progressColor(p) {
  if (p >= 80) return '#ef4444'
  if (p >= 60) return '#f59e0b'
  return '#10b981'
}

async function loadDepts() {
  const res = await api.get('/budget/overview')
  depts.value = res.data
}

async function loadPending() {
  const res = await api.get('/procurements', { params: { status: 'pending' } })
  pendingList.value = res.data
}

async function approve(row) {
  await ElMessageBox.confirm(`通过 ${row.title}？`)
  await api.post(`/procurements/${row.id}/approve`)
  ElMessage.success('已通过')
  loadPending(); loadDepts()
}

async function reject(row) {
  const { value } = await ElMessageBox.prompt('驳回原因', '驳回', { inputPattern: /.+/ })
  await api.post(`/procurements/${row.id}/reject`, { reason: value })
  ElMessage.success('已驳回')
  loadPending()
}

async function renderChart() {
  await nextTick()
  const chart = echarts.init(chartTrend.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['预算限额', '已使用'] },
    xAxis: { type: 'category', data: depts.value.map(d => d.name || d.name).map(n => n.substring(0, 4)) },
    yAxis: { type: 'value' },
    series: [
      { name: '预算限额', type: 'bar', data: depts.value.map(d => d.budget_limit), itemStyle: { color: '#94a3b8' } },
      { name: '已使用', type: 'bar', data: depts.value.map(d => d.budget_used), itemStyle: { color: '#3b82f6' } }
    ]
  })
}

onMounted(async () => {
  await loadDepts()
  await loadPending()
  renderChart()
})
</script>

<style scoped>
.budget-card { padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%); border: 1px solid #e2e8f0; }
.dept-name { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 12px; }
.budget-main { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
.used { font-size: 24px; font-weight: 700; color: #3b82f6; }
.sep { color: #94a3b8; font-size: 18px; }
.total { font-size: 16px; color: #64748b; }
.budget-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 13px; color: #64748b; }
</style>
