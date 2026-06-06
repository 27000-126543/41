<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px;">
      <el-form :inline="true" :model="filter">
        <el-form-item label="状态">
          <el-select v-model="filter.status" clearable placeholder="全部" style="width: 140px" @change="loadList">
            <el-option label="待审批" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="showCreate = true" :icon="Plus">新建申请</el-button>
          <el-button type="success" @click="showAuto = true" :icon="MagicStick">智能提取创建</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="申请标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="department_name" label="申请部门" width="120" />
        <el-table-column prop="category" label="类别" width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ catMap[row.category] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_amount" label="预估金额" width="130">
          <template #default="{ row }">¥{{ Number(row.estimated_amount).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type" size="small">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="success" link @click="approve(row)">通过</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="danger" link @click="reject(row)">驳回</el-button>
            <el-button v-if="row.status === 'approved'" size="small" type="warning" link @click="createTender(row)">生成招标</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAuto" title="🤖 智能提取采购需求" width="560px">
      <el-input v-model="rawText" type="textarea" :rows="6" placeholder="粘贴采购需求原文，系统自动提取金额、类别、日期..." />
      <el-select v-model="autoDeptId" style="width: 100%; margin-top: 12px;">
        <el-option v-for="d in depts" :key="d.id" :label="d.name" :value="d.id" />
      </el-select>
      <template #footer>
        <el-button @click="showAuto = false">取消</el-button>
        <el-button type="primary" @click="autoCreate" :loading="submitting">智能提取并创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreate" title="新建采购申请" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="标题" prop="title"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="申请部门" prop="department_id">
          <el-select v-model="form.department_id" style="width: 100%">
            <el-option v-for="d in depts" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="货物类" value="goods" /><el-option label="工程类" value="engineering" /><el-option label="服务类" value="service" />
          </el-select>
        </el-form-item>
        <el-form-item label="预估金额" prop="estimated_amount"><el-input-number v-model="form.estimated_amount" :min="0" :precision="2" style="width: 100%" /></el-form-item>
        <el-form-item label="需求描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="需求日期"><el-date-picker v-model="form.required_date" type="date" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createSubmit">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MagicStick } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const catMap = { goods: '货物', engineering: '工程', service: '服务' }
const statusMap = { pending: { label: '待审批', type: 'warning' }, approved: { label: '已通过', type: 'success' }, rejected: { label: '已驳回', type: 'danger' } }

const list = ref([])
const depts = ref([])
const loading = ref(false)
const filter = reactive({ status: '' })
const showCreate = ref(false)
const showAuto = ref(false)
const formRef = ref()
const submitting = ref(false)
const rawText = ref('')
const autoDeptId = ref(1)
const form = reactive({ title: '', description: '', category: 'goods', estimated_amount: 0, required_date: '', department_id: 1 })
const rules = { title: [{ required: true }], estimated_amount: [{ required: true }], department_id: [{ required: true }] }

async function loadList() {
  loading.value = true
  try {
    const res = await api.get('/procurements', { params: filter })
    list.value = res.data
  } finally { loading.value = false }
}

async function loadDepts() {
  const res = await api.get('/departments')
  depts.value = res.data
  if (depts.value.length && !form.department_id) {
    form.department_id = depts.value[0].id
    autoDeptId.value = depts.value[0].id
  }
}

async function createSubmit() {
  await formRef.value.validate()
  await api.post('/procurements', form)
  ElMessage.success('申请已提交')
  showCreate.value = false
  loadList()
}

async function autoCreate() {
  if (!rawText.value.trim()) return ElMessage.warning('请输入采购需求原文')
  submitting.value = true
  try {
    const res = await api.post('/procurements', { raw_text: rawText.value, department_id: autoDeptId.value, auto_extract: true })
    ElMessage.success(res.data.msg || '创建成功')
    showAuto.value = false
    rawText.value = ''
    loadList()
  } finally { submitting.value = false }
}

function viewDetail(row) {
  ElMessageBox.alert(`标题: ${row.title}\n部门: ${row.department_name}\n金额: ¥${Number(row.estimated_amount).toLocaleString()}\n描述: ${row.description || ''}`, '申请详情', { dangerouslyUseHTMLString: false })
}

async function approve(row) {
  await ElMessageBox.confirm(`确认通过申请「${row.title}」？`)
  await api.post(`/procurements/${row.id}/approve`)
  ElMessage.success('已通过')
  loadList()
}

async function reject(row) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '驳回申请', { inputPattern: /.+/, inputErrorMessage: '必填' })
  await api.post(`/procurements/${row.id}/reject`, { reason: value })
  ElMessage.success('已驳回')
  loadList()
}

async function createTender(row) {
  const res = await api.post(`/tenders/from-request/${row.id}`)
  ElMessage.success(`已生成招标项目: ${res.data.project_code}`)
  router.push(`/tender/${res.data.id}`)
}

onMounted(() => { loadDepts(); loadList() })
</script>
