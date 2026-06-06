<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px;">
      <template #header>
        <span style="font-weight: 600;">🔍 全网检索 - 按条件组合查询</span>
      </template>
      <el-form :inline="true" :model="form" @submit.prevent="doSearch">
        <el-form-item label="关键字">
          <el-input v-model="form.keyword" placeholder="项目名称/供应商/专家" style="width: 240px;" clearable />
        </el-form-item>
        <el-form-item label="项目类型">
          <el-select v-model="form.type" style="width: 140px;" clearable>
            <el-option label="货物类" value="goods" />
            <el-option label="工程类" value="engineering" />
            <el-option label="服务类" value="service" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 140px;" clearable>
            <el-option label="待审批" value="pending_approval" />
            <el-option label="审批通过" value="approved" />
            <el-option label="招标中" value="bidding" />
            <el-option label="已开标" value="opened" />
            <el-option label="评审中" value="reviewed" />
            <el-option label="已定标" value="awarded" />
            <el-option label="履约中" value="execution" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额区间">
          <el-input-number v-model="form.min_amount" :min="0" placeholder="最低" style="width: 120px;" />
          <span style="margin: 0 6px;">至</span>
          <el-input-number v-model="form.max_amount" :min="0" placeholder="最高" style="width: 120px;" />
        </el-form-item>
        <el-form-item label="时间段">
          <el-date-picker v-model="form.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doSearch" :icon="Search">检索</el-button>
          <el-button @click="resetForm" :icon="RefreshRight">重置</el-button>
          <el-button type="success" @click="exportResults" :icon="Download" :disabled="!results.length">导出Excel</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 600;">📋 检索结果（共 {{ results.length }} 条）</span>
        </div>
      </template>
      <el-alert v-if="results.length === 0 && searched" type="info" :closable="false" style="margin-bottom: 16px;">未找到匹配的项目</el-alert>
      <el-table :data="results" stripe>
        <el-table-column prop="project_code" label="项目编号" width="170" />
        <el-table-column prop="project_name" label="项目名称" min-width="240" show-overflow-tooltip />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">{{ typeLabel[row.category] }}</template>
        </el-table-column>
        <el-table-column prop="budget_amount" label="预算金额" width="130">
          <template #default="{ row }">¥{{ Number(row.budget_amount || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="中标金额" width="130">
          <template #default="{ row }">{{ row.final_amount ? '¥' + Number(row.final_amount).toLocaleString() : '-' }}</template>
        </el-table-column>
        <el-table-column label="节约金额" width="130">
          <template #default="{ row }">{{ row.saved_amount ? '¥' + Number(row.saved_amount).toLocaleString() : '-' }}</template>
        </el-table-column>
        <el-table-column label="中标方" width="150">
          <template #default="{ row }">{{ row.winner_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="department_name" label="需求部门" width="110" />
        <el-table-column prop="publish_date" label="发布日期" width="110" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType[row.status]">{{ statusLabel[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="goDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, RefreshRight, Download } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useRouter } from 'vue-router'

const router = useRouter()
const results = ref([])
const searched = ref(false)
const form = reactive({
  keyword: '', type: '', status: '',
  min_amount: null, max_amount: null,
  dateRange: []
})

const typeLabel = { goods: '货物类', engineering: '工程类', service: '服务类' }
const statusLabel = {
  pending_approval: '待审批', approved: '已审批', bidding: '招标中', opened: '已开标',
  reviewed: '评审中', awarded: '已定标', execution: '履约中', completed: '已完成', archived: '已归档'
}
const statusType = {
  pending_approval: 'warning', approved: 'info', bidding: 'primary', opened: 'warning',
  reviewed: '', awarded: 'success', execution: 'primary', completed: 'success', archived: 'info'
}

async function doSearch() {
  const params = {}
  if (form.keyword) params.keyword = form.keyword
  if (form.type) params.category = form.type
  if (form.status) params.status = form.status
  if (form.min_amount) params.min_amount = form.min_amount
  if (form.max_amount) params.max_amount = form.max_amount
  if (form.dateRange?.length === 2) {
    params.start_date = form.dateRange[0]
    params.end_date = form.dateRange[1]
  }
  results.value = (await api.get('/search/projects', { params })).data
  searched.value = true
  ElMessage.success(`找到 ${results.value.length} 条记录`)
}

function resetForm() {
  Object.assign(form, { keyword: '', type: '', status: '', min_amount: null, max_amount: null, dateRange: [] })
  doSearch()
}

async function exportResults() {
  const res = await api.post('/export/projects')
  ElMessage.success('已导出: ' + res.data.path)
}

function goDetail(row) {
  router.push(`/tender/${row.id}`)
}

onMounted(doSearch)
</script>
