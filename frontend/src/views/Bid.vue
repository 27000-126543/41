<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px;">
      <el-form :inline="true">
        <el-form-item>
          <el-select v-model="projectId" placeholder="选择招标项目" style="width: 280px;" @change="loadBids">
            <el-option v-for="t in tenders" :key="t.id" :label="`${t.project_code} - ${t.project_name}`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadBids" :icon="Refresh">刷新</el-button>
          <el-button type="success" @click="exportDetails" :icon="Download">导出投标明细</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="bids" stripe>
        <el-table-column prop="project_code" label="项目编号" width="170" />
        <el-table-column prop="company_name" label="供应商" min-width="180" />
        <el-table-column prop="qualification_level" label="资质等级" width="90" />
        <el-table-column prop="credit_score" label="信用分" width="80" />
        <el-table-column prop="bid_amount" label="投标金额" width="130">
          <template #default="{ row }"><b style="color: #1d4ed8;">¥{{ Number(row.bid_amount).toLocaleString() }}</b></template>
        </el-table-column>
        <el-table-column prop="delivery_date" label="交付日期" width="110" />
        <el-table-column prop="technical_score" label="技术分" width="80" />
        <el-table-column prop="commercial_score" label="商务分" width="80" />
        <el-table-column prop="qualification_score" label="资质分" width="80" />
        <el-table-column prop="final_score" label="综合分" width="90">
          <template #default="{ row }">
            <b :style="{ color: row.ranking === 1 ? '#10b981' : '#1e293b' }">{{ row.final_score?.toFixed(2) }}</b>
          </template>
        </el-table-column>
        <el-table-column prop="ranking" label="排名" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.ranking === 1" type="success" effect="dark">🏆 1</el-tag>
            <span v-else-if="row.ranking">{{ row.ranking }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType[row.status]">{{ statusLabel[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="submitted_at" label="提交时间" width="170" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const tenders = ref([])
const bids = ref([])
const projectId = ref()
const statusLabel = { submitted: '已提交', decrypted: '已解密', evaluated: '初评分', reviewed: '已评审', notified: '已通知', winning: '中标', archived: '已归档' }
const statusType = { submitted: '', decrypted: 'warning', evaluated: 'info', reviewed: '', notified: 'success', winning: 'success', archived: 'info' }

async function loadTenders() {
  tenders.value = (await api.get('/tenders')).data
  if (tenders.value.length) {
    projectId.value = tenders.value[0].id
    loadBids()
  }
}

async function loadBids() {
  if (!projectId.value) return
  bids.value = (await api.get(`/tenders/${projectId.value}/bids`)).data
}

async function exportDetails() {
  const res = await api.post('/export/bid-details', projectId.value ? { project_ids: [projectId.value] } : {})
  ElMessage.success(`已导出${res.data.count}条明细: ${res.data.path}`)
}

onMounted(loadTenders)
</script>
