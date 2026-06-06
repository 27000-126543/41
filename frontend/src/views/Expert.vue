<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600;">🧑‍⚖️ 专家库</span>
              <el-input v-model="filterSpecialty" placeholder="按专业搜索" clearable style="width: 180px;" prefix-icon="Search" />
            </div>
          </template>
          <el-table :data="filteredExperts" stripe>
            <el-table-column prop="expert_code" label="专家编号" width="100" />
            <el-table-column prop="name" label="姓名" width="90" />
            <el-table-column prop="gender" label="性别" width="60" />
            <el-table-column prop="title" label="职称" width="110" />
            <el-table-column prop="organization" label="所属单位" min-width="160" show-overflow-tooltip />
            <el-table-column prop="specialty" label="主专业" width="110" />
            <el-table-column prop="sub_specialty" label="副专业" width="110" />
            <el-table-column prop="years_of_experience" label="年限" width="70">
              <template #default="{ row }">{{ row.years_of_experience }}年</template>
            </el-table-column>
            <el-table-column label="联系方式" width="180">
              <template #default="{ row }">
                <div style="font-size: 12px;">
                  📞 {{ row.phone || '-' }}<br/>
                  ✉️ {{ row.email || '-' }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="70">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" style="margin-bottom: 16px;">
          <template #header><span style="font-weight: 600;">🎯 项目专家分配</span></template>
          <el-form label-width="90px">
            <el-form-item label="选择项目">
              <el-select v-model="projectId" placeholder="选择招标项目" style="width: 100%;" @change="loadProjectExperts">
                <el-option v-for="t in tenders" :key="t.id" :label="t.project_name" :value="t.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="专家人数">
              <el-radio-group v-model="expertNum">
                <el-radio-button :value="3">3人</el-radio-button>
                <el-radio-button :value="5">5人</el-radio-button>
                <el-radio-button :value="7">7人</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="assignExperts" :icon="MagicStick">按专业+回避自动分配</el-button>
            </el-form-item>
          </el-form>
          <el-alert v-if="projectExperts.length" type="success" :closable="false" style="margin-bottom: 12px;">
            <template #title>已分配 {{ projectExperts.length }} 位评审专家（回避规则已校验）</template>
          </el-alert>
          <el-table :data="projectExperts" size="small" stripe>
            <el-table-column prop="name" label="姓名" width="90" />
            <el-table-column prop="title" label="职称" width="100" />
            <el-table-column prop="specialty" label="专业" />
          </el-table>
        </el-card>

        <el-card shadow="never">
          <template #header><span style="font-weight: 600;">📊 专家专业分布</span></template>
          <div ref="chart" style="height: 260px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/utils/api'

const experts = ref([])
const tenders = ref([])
const projectId = ref()
const expertNum = ref(5)
const projectExperts = ref([])
const filterSpecialty = ref('')
const chart = ref()

const filteredExperts = computed(() => {
  if (!filterSpecialty.value) return experts.value
  const kw = filterSpecialty.value.toLowerCase()
  return experts.value.filter(e =>
    (e.specialty || '').toLowerCase().includes(kw) ||
    (e.sub_specialty || '').toLowerCase().includes(kw) ||
    (e.name || '').includes(kw)
  )
})

async function loadAll() {
  experts.value = (await api.get('/experts')).data
  tenders.value = (await api.get('/tenders')).data
  if (tenders.value.length) projectId.value = tenders.value[0].id
  await nextTick()
  renderChart()
}

async function loadProjectExperts() {
  if (!projectId.value) return
  projectExperts.value = (await api.get(`/tenders/${projectId.value}/experts`)).data
}

async function assignExperts() {
  if (!projectId.value) return ElMessage.warning('请先选择项目')
  const res = await api.post(`/tenders/${projectId.value}/assign-experts`, { num_experts: expertNum.value })
  if (res.data) {
    ElMessage.success(`成功分配${res.data.length}位专家`)
    loadProjectExperts()
  } else {
    ElMessage.error(res.msg)
  }
}

function renderChart() {
  const counts = {}
  experts.value.forEach(e => counts[e.specialty] = (counts[e.specialty] || 0) + 1)
  const c = echarts.init(chart.value)
  c.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '50%'],
      label: { show: true, formatter: '{b}: {c}' },
      data: Object.entries(counts).map(([k, v]) => ({ name: k.substring(0, 6), value: v }))
    }]
  })
}

watch(projectId, loadProjectExperts)
onMounted(loadAll)
</script>
