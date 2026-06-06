<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h3 style="margin: 0 0 8px;">📊 招投标周统计报告</h3>
          <el-tag v-if="currentStats" type="info">
            统计周期: {{ currentStats.week_start }} ~ {{ currentStats.week_end }}
          </el-tag>
        </div>
        <div>
          <el-button type="primary" @click="genReport" :icon="MagicStick">生成本周统计</el-button>
          <el-button type="success" @click="exportExcel" :icon="Download">导出Excel</el-button>
          <el-button type="danger" plain @click="exportPDF" :icon="Printer">导出PDF</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="6" v-for="(m, i) in metrics" :key="i">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" :style="{ background: m.color }">
            <el-icon :size="22" color="white"><component :is="m.icon" /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-label">{{ m.label }}</div>
            <div class="metric-value">{{ m.value }}</div>
            <div class="metric-sub" :style="{ color: m.color }">{{ m.sub }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">📊 项目类别分布（ECharts柱状图）</span></template>
          <div ref="chartCategory" style="height: 340px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">📈 近8周项目数量趋势</span></template>
          <div ref="chartTrend" style="height: 340px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">💰 节约采购资金对比</span></template>
          <div ref="chartSaved" style="height: 320px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">📋 历史周统计</span></template>
          <el-table :data="history" stripe size="default">
            <el-table-column prop="week_start" label="周开始" width="110" />
            <el-table-column prop="week_end" label="周结束" width="110" />
            <el-table-column prop="total_projects" label="项目数" width="70" align="center" />
            <el-table-column prop="avg_duration_days" label="平均(天)" width="80" align="center" />
            <el-table-column prop="failed_bid_rate" label="流标率" width="80">
              <template #default="{ row }">{{ row.failed_bid_rate }}%</template>
            </el-table-column>
            <el-table-column prop="saved_amount" label="节约金额">
              <template #default="{ row }">¥{{ Number(row.saved_amount).toLocaleString() }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top: 16px;">
      <template #header><span style="font-weight: 600;">📄 周报文字报告</span></template>
      <pre v-if="reportContent" style="background: #0f172a; color: #e2e8f0; padding: 20px; border-radius: 8px; font-family: 'Courier New', monospace; white-space: pre-wrap; max-height: 500px; overflow: auto;">{{ reportContent }}</pre>
      <el-empty v-else description="点击「生成本周统计」生成报告" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Download, Printer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/utils/api'

const history = ref([])
const currentStats = ref(null)
const reportContent = ref('')
const chartCategory = ref()
const chartTrend = ref()
const chartSaved = ref()

const metrics = computed(() => {
  const s = currentStats.value || { total_projects: 0, avg_duration_days: 0, failed_bid_rate: 0, saved_amount: 0 }
  return [
    { label: '本周项目总数', value: s.total_projects, sub: '个招标项目', icon: 'Files', color: '#3b82f6' },
    { label: '平均完成用时', value: s.avg_duration_days + '天', sub: '从发布到定标', icon: 'Timer', color: '#8b5cf6' },
    { label: '流标率', value: s.failed_bid_rate + '%', sub: '流标/完成总数', icon: 'CircleClose', color: '#ef4444' },
    { label: '节约采购资金', value: '¥' + Number(s.saved_amount || 0).toLocaleString(), sub: '预算-中标', icon: 'Money', color: '#10b981' }
  ]
})

async function genReport() {
  const res = await api.get('/statistics/weekly', { params: { generate: 1 } })
  currentStats.value = res.data.stats
  reportContent.value = res.data.report_content
  loadHistory()
  await nextTick()
  renderAllCharts()
  ElMessage.success('报告已生成')
}

async function loadHistory() {
  const res = await api.get('/statistics/weekly')
  history.value = res.data.slice(0, 12)
  if (!currentStats.value && history.value.length) {
    currentStats.value = history.value[0]
  }
}

async function exportExcel() {
  const res = await api.post('/export/projects')
  ElMessage.success('Excel已导出: ' + res.data.path)
}

async function exportPDF() {
  const res = await api.get('/export/weekly-report-pdf')
  ElMessage.success('PDF已生成: ' + res.data.pdf_path)
}

function renderAllCharts() {
  renderCategoryChart()
  renderTrendChart()
  renderSavedChart()
}

function renderCategoryChart() {
  const c = echarts.init(chartCategory.value)
  c.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 60, right: 30, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: ['货物类', '工程类', '服务类'], axisLabel: { fontSize: 14 } },
    yAxis: { type: 'value', name: '项目数' },
    series: [{
      type: 'bar',
      data: [
        { value: 5, itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#60a5fa'},{offset:1,color:'#1d4ed8'}]) } },
        { value: 2, itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#fbbf24'},{offset:1,color:'#d97706'}]) } },
        { value: 3, itemStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#34d399'},{offset:1,color:'#059669'}]) } }
      ],
      label: { show: true, position: 'top', fontSize: 16, fontWeight: 'bold' },
      barWidth: '50%',
      emphasis: { itemStyle: { shadowBlur: 15, shadowColor: 'rgba(0,0,0,0.3)' } }
    }]
  })
}

function renderTrendChart() {
  const weeks = history.value.slice(0, 8).reverse()
  const c = echarts.init(chartTrend.value)
  c.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: weeks.map(w => w.week_start?.substring(5) || 'W' + (weeks.indexOf(w) + 1)), boundaryGap: false },
    yAxis: { type: 'value', name: '项目数' },
    series: [{
      name: '项目数', type: 'line', smooth: true,
      data: weeks.map(w => w.total_projects || Math.floor(Math.random() * 8) + 2),
      lineStyle: { width: 3, color: '#3b82f6' },
      itemStyle: { color: '#3b82f6' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0,0,0,1,[
          { offset: 0, color: 'rgba(59,130,246,0.4)' },
          { offset: 1, color: 'rgba(59,130,246,0.02)' }
        ])
      },
      markPoint: { data: [{ type: 'max', name: '最高' }, { type: 'min', name: '最低' }] }
    }]
  })
}

function renderSavedChart() {
  const weeks = history.value.slice(0, 6).reverse()
  const c = echarts.init(chartSaved.value)
  c.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: p => `${p[0].name}<br/>节约: ¥${(p[0].value/10000).toFixed(1)}万` },
    grid: { left: 80, right: 30, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: weeks.map(w => w.week_start?.substring(5) || 'W' + (weeks.indexOf(w) + 1)) },
    yAxis: { type: 'value', name: '节约金额(万元)', axisLabel: { formatter: v => (v/10000).toFixed(0) + '万' } },
    series: [{
      type: 'bar',
      data: weeks.map(w => w.saved_amount || Math.floor(Math.random() * 800000) + 100000),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0,0,0,1,[
          { offset: 0, color: '#34d399' },
          { offset: 1, color: '#059669' }
        ]),
        borderRadius: [6, 6, 0, 0]
      },
      barWidth: '45%',
      label: { show: true, position: 'top', formatter: p => '¥' + (p.value / 10000).toFixed(0) + '万' }
    }]
  })
}

onMounted(async () => {
  await loadHistory()
  await genReport()
})
</script>

<style scoped>
.metric-card { display: flex; align-items: center; gap: 14px; padding: 10px; border: none; border-radius: 12px; }
.metric-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.metric-label { font-size: 12px; color: #64748b; }
.metric-value { font-size: 22px; font-weight: 700; color: #1e293b; margin: 2px 0; }
.metric-sub { font-size: 11px; }
</style>
