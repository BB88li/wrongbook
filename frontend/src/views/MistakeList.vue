<script setup>
// 错题列表：科目筛选 + 删除
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mistakeApi } from '../api'

const mistakes = ref([])
const subject = ref('')
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    const { data } = await mistakeApi.list(subject.value || undefined)
    mistakes.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)

const errorTypeText = { careless: '粗心', concept: '概念不清', method: '方法不会' }

// 后端返回 ISO 时间串（2026-11-17T10:44:48），表格里只显示到分钟
const formatTime = (value) => (value ? value.replace('T', ' ').slice(0, 16) : '')

const remove = async (id) => {
  await ElMessageBox.confirm('确定删除这条错题？', '提示', { type: 'warning' })
  await mistakeApi.remove(id)
  ElMessage.success('已删除')
  load()
}
</script>

<template>
  <div>
    <el-row :gutter="16" class="toolbar">
      <el-col :span="6">
        <el-select v-model="subject" placeholder="全部科目" clearable @change="load">
          <el-option label="高数" value="高数" />
          <el-option label="线代" value="线代" />
        </el-select>
      </el-col>
      <el-col :span="18" style="text-align: right">
        <el-button type="primary" @click="$router.push('/mistakes/new')">＋ 录入错题</el-button>
      </el-col>
    </el-row>

    <el-table v-loading="loading" :data="mistakes" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="subject" label="科目" width="80" />
      <el-table-column prop="question_text" label="题目" show-overflow-tooltip />
      <el-table-column label="错误原因" width="110">
        <template #default="{ row }">{{ errorTypeText[row.error_type] || row.error_type }}</template>
      </el-table-column>
      <el-table-column label="录入时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button type="danger" link @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && mistakes.length === 0" description="还没有错题，去录入第一道吧" />
  </div>
</template>

<style scoped>
.toolbar { margin-bottom: 16px; }
</style>
