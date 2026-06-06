<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <el-card shadow="hover" class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-inner" :style="{ background: s.color }">
            <div>
              <div class="stat-label">{{ s.label }}</div>
              <div class="stat-value">{{ s.value }}</div>
              <div class="stat-sub">{{ s.sub }}</div>
            </div>
            <el-icon :size="40" color="white" :opacity="0.8"><component :is="s.icon" /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>📊 项目状态分布</span>
              <el-tag type="info" effect="plain" size="small">实时数据</el-tag>
            </div>
          </template>
          <div ref="chartStatus" style="height: 320px"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>💰 各部门预算使用情况</span>
            </div>
          </template>
          <div ref="chartBudget" style="height: 320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>⏰ 最近操作日志</span>
              <el-button type="primary" link size="small" @click="$router.push('/logs')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="logs" size="small" stripe>
            <el-table-column prop="created_at" label="时间" width="160" />
            <el-table-column prop="module" label="模块" width="100">
              <template #default="{ row }">
                <el-tag size="small" type="primary" effect="plain">{{ row.module }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="operation_type" label="操作" width="80" />
            <el-table-column prop="operator" label="操作人" width="100" />
            <el-table-column prop="detail" label="详情" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>📋 待办事项</span>
            </div>
          </template>
          <el-steps direction="vertical" :active="5" finish-status="success">
            <el-step title="采购申请提交" description="自动提取需求信息，支持NLP识别" status="success" />
            <el-step title="预算审批" description="自动校验部门额度，不足自动预警" status="success" />
            <el-step title="招标项目发布" description="按类别金额匹配模板，双平台发布" status="success" />
            <el-step title="供应商投标" description="加密存储，截止自动解密" status="success" />
            <el-step title="专家评审" description="回避规则自动分配，独立打分汇总" status="process" />
            <el-step title="定标+合同" description="中标通知+感谢信+电子合同草稿" status="wait" />
            <el-step title="履约监控" description="交付/验收/付款节点超期预警" status="wait" />
          </el-steps>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/utils/api'

const chartStatus = ref()
const chartBudget = ref()
const logs = ref([])
const stats = ref([
  { label: '本周项目数', value: 0, sub: '较上周 +0%', color: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', icon: 'Files' },
  { label: '进行中项目', value: 0, sub: '投标/评审阶段', color: 'linear-gradient(135deg, #f59e0b, #d97706)', icon: 'Loading' },
  { label: '节约采购资金', value: '¥0', sub: '预算-中标金额', color: 'linear-gradient(135deg, #10b981, #059669)', icon: 'Money' },
  { label: '履约预警', value: 0, sub: '超期未完成节点', color: 'linear-gradient(135deg, #ef4444, #dc2626)', icon: 'Warning' }
])

async function loadData() {
  try {
    const [tendersRes, logsRes, budgetRes] = await Promise.all([
      api.get('/tenders'),
      api.get('/logs', { params: { limit: 10 } }),
      api.get('/budget/overview')
    ])
    const tenders = tendersRes.data
    stats.value[0].value = tenders.length
    stats.value[1].value = tenders.filter(t => ['published', 'decrypted', 'evaluated', 'reviewed'].includes(t.status)).length
    const saved = tenders.filter(t => t.saved_amount).reduce((s, t) => s + (t.saved_amount || 0), 0)
    stats.value[2].value = '¥' + (saved || 0).toLocaleString()
    logs.value = logsRes.data

    await nextTick()
    renderStatusChart(tenders)
    renderBudgetChart(budgetRes.data)
  } catch (e) { console.error(e) }
}

function renderStatusChart(tenders) {
  const statusMap = {}
  const labelMap = { draft: '草稿', published: '已发布', decrypted: '已开标', evaluated: '初评分', reviewed: '已评审', awarded: '已中标', failed: '已流标' }
  tenders.forEach(t => { statusMap[t.status] = (statusMap[t.status] || 0) + 1 })
  const data = Object.entries(statusMap).map(([k, v]) => ({ name: labelMap[k] || k, value: v }))
  const chart = echarts.init(chartStatus.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      avoidLabelOverlap: true,
      label: { show: true, formatter: '{b}: {c}' },
      data,
      color: ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4', '#64748b']
    }]
  })
}

function renderBudgetChart(depts) {
  const chart = echarts.init(chartBudget.value)
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 100, right: 20 },
    xAxis: { type: 'value', max: 100 },
    yAxis: { type: 'category', data: depts.map(d => d.name || d.name), inverse: true },
    series: [
      {
        name: '已使用(%)',
        type: 'bar',
        stack: 'total',
        data: depts.map(d => d.usage_percent || 0),
        itemStyle: { color: '#3b82f6' },
        label: { show: true, position: 'right', formatter: '{c}%' }
      },
      {
        name: '剩余(%)',
        type: 'bar',
        stack: 'total',
        data: depts.map(d => 100 - (d.usage_percent || 0)),
        itemStyle: { color: '#e2e8f0' }
      }
    ]
  })
}

onMounted(loadData)
</script>

<style scoped>
.stat-card { border: none; border-radius: 12px; }
.stat-inner { padding: 16px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; color: white; }
.stat-label { font-size: 13px; opacity: 0.9; }
.stat-value { font-size: 28px; font-weight: 700; margin: 6px 0 4px; }
.stat-sub { font-size: 12px; opacity: 0.8; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
</style>
