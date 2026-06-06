<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px;">
      <el-form :inline="true" :model="filter">
        <el-form-item label="状态">
          <el-select v-model="filter.status" clearable style="width: 140px" @change="loadList">
            <el-option v-for="(v,k) in statusMap" :key="k" :label="v.label" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="filter.category" clearable style="width: 120px" @change="loadList">
            <el-option label="货物类" value="goods" /><el-option label="工程类" value="engineering" /><el-option label="服务类" value="service" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="project_code" label="项目编号" width="180" />
        <el-table-column prop="project_name" label="项目名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="类别" width="80">
          <template #default="{ row }"><el-tag size="small" :type="catType[row.category]">{{ catMap[row.category] }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="budget_amount" label="预算金额" width="130">
          <template #default="{ row }">¥{{ Number(row.budget_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="bid_deadline" label="投标截止" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type" size="small">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="$router.push(`/tender/${row.id}`)">详情</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="success" link @click="publish(row)">发布</el-button>
            <el-button v-if="row.status === 'published'" size="small" type="warning" link @click="decrypt(row)">开标解密</el-button>
            <el-button v-if="row.status === 'decrypted' || row.status === 'published'" size="small" type="info" link @click="autoScore(row)">自动评分</el-button>
            <el-button v-if="row.status === 'reviewed'" size="small" type="warning" link @click="award(row)">定标</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const filter = reactive({ status: '', category: '' })
const catMap = { goods: '货物', engineering: '工程', service: '服务' }
const catType = { goods: '', engineering: 'warning', service: 'success' }
const statusMap = {
  draft: { label: '草稿', type: 'info' },
  published: { label: '已发布', type: 'primary' },
  decrypted: { label: '已开标', type: '' },
  evaluated: { label: '初评分', type: 'warning' },
  reviewed: { label: '已评审', type: 'warning' },
  awarded: { label: '已中标', type: 'success' },
  archived: { label: '已归档', type: 'info' },
  failed: { label: '流标', type: 'danger' }
}

async function loadList() {
  loading.value = true
  try { list.value = (await api.get('/tenders', { params: filter })).data }
  finally { loading.value = false }
}

async function publish(row) {
  await ElMessageBox.confirm(`发布项目「${row.project_name}」到企业官网和供应商门户？`)
  await api.post(`/tenders/${row.id}/publish`)
  ElMessage.success('发布成功')
  loadList()
}

async function decrypt(row) {
  await ElMessageBox.confirm('确定解密所有投标文件？此操作不可撤销。')
  await api.post(`/tenders/${row.id}/decrypt`)
  ElMessage.success('解密完成')
  loadList()
}

async function autoScore(row) {
  const res = await api.post(`/tenders/${row.id}/auto-score`)
  ElMessage.success(`评分完成，共${res.data.length}家`)
  loadList()
}

async function award(row) {
  router.push(`/tender/${row.id}`)
}

onMounted(loadList)
</script>
