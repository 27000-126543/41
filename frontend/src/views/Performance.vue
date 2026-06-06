<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <el-card shadow="hover" class="stat-card">
          <div :style="{ background: s.color }" class="stat-inner">
            <div>
              <div class="stat-label">{{ s.label }}</div>
              <div class="stat-value">{{ s.value }}</div>
            </div>
            <el-icon :size="36" color="white"><component :is="s.icon" /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600;">📋 合同履约里程碑看板</span>
              <el-button type="warning" size="small" @click="checkOverdue" :icon="Warning">检查超期节点</el-button>
            </div>
          </template>
          <el-table :data="milestones" stripe>
            <el-table-column prop="contract_code" label="合同编号" width="180" />
            <el-table-column prop="milestone_name" label="里程碑" width="140" />
            <el-table-column prop="milestone_type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="typeMap[row.milestone_type]?.type">{{ typeMap[row.milestone_type]?.label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="planned_date" label="计划日期" width="110" />
            <el-table-column prop="actual_date" label="实际日期" width="110">
              <template #default="{ row }">{{ row.actual_date || '-' }}</template>
            </el-table-column>
            <el-table-column label="延期" width="80">
              <template #default="{ row }">
                <span v-if="row.overdue && row.overdue > 0" style="color: #ef4444; font-weight: bold;">
                  {{ row.overdue }}天
                </span>
                <span v-else style="color: #10b981;">正常</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="statusMap[row.status]?.type">{{ statusMap[row.status]?.label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="updateMs(row)">更新状态</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" style="margin-bottom: 16px;">
          <template #header><span style="font-weight: 600;">📊 履约状态分布</span></template>
          <div ref="chartStatus" style="height: 260px"></div>
        </el-card>

        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">📝 合同列表</span></template>
          <el-table :data="contracts" size="small" stripe>
            <el-table-column prop="contract_code" label="合同编号" width="170" />
            <el-table-column prop="total_amount" label="金额" width="110">
              <template #default="{ row }">¥{{ Number(row.total_amount).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'signed' ? 'success' : 'warning'">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showUpdate" title="更新里程碑" width="400px">
      <el-form label-width="90px">
        <el-form-item label="里程碑">{{ currentMs?.milestone_name }}</el-form-item>
        <el-form-item label="状态">
          <el-select v-model="updateForm.status" style="width: 100%;">
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已延期" value="delayed" />
          </el-select>
        </el-form-item>
        <el-form-item label="实际日期">
          <el-date-picker v-model="updateForm.actual_date" type="date" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="updateForm.comment" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpdate = false">取消</el-button>
        <el-button type="primary" @click="submitUpdate">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/utils/api'
import dayjs from 'dayjs'

const contracts = ref([])
const milestones = ref([])
const chartStatus = ref()
const showUpdate = ref(false)
const currentMs = ref()
const updateForm = reactive({ status: '', actual_date: '', comment: '' })

const typeMap = { delivery: { label: '交付', type: 'primary' }, acceptance: { label: '验收', type: 'success' }, payment: { label: '付款', type: 'warning' } }
const statusMap = { pending: { label: '待处理', type: 'warning' }, in_progress: { label: '进行中', type: 'primary' }, completed: { label: '已完成', type: 'success' }, delayed: { label: '已延期', type: 'danger' } }

const stats = computed(() => {
  const total = milestones.value.length
  const pending = milestones.value.filter(m => m.status === 'pending').length
  const completed = milestones.value.filter(m => m.status === 'completed').length
  const overdue = milestones.value.filter(m => m.overdue && m.overdue > 2).length
  return [
    { label: '合同总数', value: contracts.value.length, icon: 'Tickets', color: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' },
    { label: '待处理节点', value: pending, icon: 'Clock', color: 'linear-gradient(135deg, #f59e0b, #d97706)' },
    { label: '已完成节点', value: completed, icon: 'CircleCheck', color: 'linear-gradient(135deg, #10b981, #059669)' },
    { label: '超期预警', value: overdue, icon: 'Warning', color: 'linear-gradient(135deg, #ef4444, #dc2626)' }
  ]
})

async function loadData() {
  contracts.value = (await api.get('/contracts')).data
  const allMs = []
  for (const c of contracts.value) {
    try {
      const ms = (await api.get(`/contracts/${c.id}/milestones`)).data
      ms.forEach(m => {
        m.contract_code = c.contract_code
        if (m.status !== 'completed' && m.planned_date) {
          m.overdue = dayjs().diff(dayjs(m.planned_date), 'day')
        } else {
          m.overdue = 0
        }
        allMs.push(m)
      })
    } catch {}
  }
  milestones.value = allMs
  await nextTick()
  renderChart()
}

async function checkOverdue() {
  const res = await api.post('/performance/check-overdue')
  ElMessage.success(`检查完成，发现 ${res.data.count} 个超期节点`)
  loadData()
}

function updateMs(row) {
  currentMs.value = row
  updateForm.status = row.status
  updateForm.actual_date = row.actual_date
  updateForm.comment = row.comment || ''
  showUpdate.value = true
}

async function submitUpdate() {
  await api.post(`/milestones/${currentMs.value.id}`, updateForm)
  ElMessage.success('更新成功')
  showUpdate.value = false
  loadData()
}

function renderChart() {
  if (!chartStatus.value) return
  const counts = { pending: 0, in_progress: 0, completed: 0, delayed: 0 }
  milestones.value.forEach(m => counts[m.status] = (counts[m.status] || 0) + 1)
  const c = echarts.init(chartStatus.value)
  c.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '65%'],
      label: { show: true, formatter: '{b}: {c}' },
      data: [
        { name: '待处理', value: counts.pending, itemStyle: { color: '#f59e0b' } },
        { name: '进行中', value: counts.in_progress, itemStyle: { color: '#3b82f6' } },
        { name: '已完成', value: counts.completed, itemStyle: { color: '#10b981' } },
        { name: '已延期', value: counts.delayed, itemStyle: { color: '#ef4444' } }
      ]
    }]
  })
}

onMounted(loadData)
</script>

<style scoped>
.stat-card { border: none; border-radius: 12px; }
.stat-inner { padding: 16px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; color: white; }
.stat-label { font-size: 13px; opacity: 0.9; }
.stat-value { font-size: 24px; font-weight: 700; margin-top: 4px; }
</style>
