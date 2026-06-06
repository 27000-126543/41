<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px;">
      <el-form :inline="true">
        <el-form-item label="模块">
          <el-select v-model="filter.module" style="width: 150px;" clearable>
            <el-option label="采购申请" value="procurement" />
            <el-option label="预算审批" value="budget" />
            <el-option label="招标项目" value="tender" />
            <el-option label="投标" value="bid" />
            <el-option label="专家" value="expert" />
            <el-option label="评审" value="review" />
            <el-option label="中标" value="award" />
            <el-option label="合同履约" value="contract" />
            <el-option label="统计" value="statistics" />
            <el-option label="系统" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="filter.op_type" style="width: 130px;" clearable>
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="发布" value="publish" />
            <el-option label="开标" value="open" />
            <el-option label="评分" value="score" />
            <el-option label="审批" value="approve" />
            <el-option label="通知" value="notify" />
            <el-option label="归档" value="archive" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作者">
          <el-input v-model="filter.operator" style="width: 140px;" clearable />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="filter.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">查询</el-button>
          <el-button @click="filter = { module: '', op_type: '', operator: '', dateRange: [] }; loadLogs()">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 600;">📝 操作日志（{{ logs.length }}条）</span>
          <div>
            <el-tag type="primary" effect="dark">实时同步WebSocket推送</el-tag>
          </div>
        </div>
      </template>
      <el-table :data="filteredLogs" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="op_type" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="opTypeMap[row.op_type]">{{ row.op_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="110">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ moduleMap[row.module] || row.module }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作者" width="110" />
        <el-table-column prop="record_id" label="关联记录" width="100" />
        <el-table-column prop="detail" label="操作详情" min-width="320" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP地址" width="120" />
        <el-table-column prop="created_at" label="操作时间" width="170">
          <template #default="{ row }">
            <span style="font-family: monospace;">{{ row.created_at }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useSocket } from '@/utils/websocket'

const logs = ref([])
const filter = reactive({ module: '', op_type: '', operator: '', dateRange: [] })
const socket = useSocket()

socket.onLog(log => {
  logs.value.unshift(log)
  if (logs.value.length > 500) logs.value.pop()
})

const moduleMap = {
  procurement: '采购申请', budget: '预算审批', tender: '招标项目', bid: '投标',
  expert: '专家', review: '评审', award: '中标', contract: '合同履约',
  statistics: '统计', system: '系统'
}
const opTypeMap = {
  create: 'success', update: '', publish: 'primary', open: 'warning',
  score: '', approve: 'success', notify: 'info', archive: 'info', login: ''
}

const filteredLogs = computed(() => {
  return logs.value.filter(l => {
    if (filter.module && l.module !== filter.module) return false
    if (filter.op_type && l.op_type !== filter.op_type) return false
    if (filter.operator && !(l.operator || '').includes(filter.operator)) return false
    if (filter.dateRange?.length === 2) {
      const t = l.created_at?.substring(0, 10)
      if (t < filter.dateRange[0] || t > filter.dateRange[1]) return false
    }
    return true
  })
})

async function loadLogs() {
  logs.value = (await api.get('/logs')).data.slice(0, 200)
}

onMounted(loadLogs)
</script>
