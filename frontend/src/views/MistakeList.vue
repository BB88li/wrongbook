<script setup>
// 错题列表：科目 / 错因筛选 + 删除
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mistakeApi } from '../api'

const mistakes = ref([])
const subject = ref('')
const errorType = ref('')
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    const { data } = await mistakeApi.list(
      subject.value || undefined,
      errorType.value || undefined,
    )
    mistakes.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)

const errorTypeText = { careless: '粗心', concept: '概念不清', method: '方法不会' }
const errorTagType = { careless: 'info', concept: 'danger', method: 'warning' }

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
    <div class="toolbar">
      <el-select v-model="subject" placeholder="全部科目" clearable class="filter" @change="load">
        <el-option label="高数" value="高数" />
        <el-option label="线代" value="线代" />
      </el-select>

      <el-select v-model="errorType" placeholder="全部错因" clearable class="filter" @change="load">
        <el-option label="粗心" value="careless" />
        <el-option label="概念不清" value="concept" />
        <el-option label="方法不会" value="method" />
      </el-select>

      <span class="count">共 {{ mistakes.length }} 道</span>
      <div class="spacer" />
      <el-button type="primary" @click="$router.push('/mistakes/new')">＋ 录入错题</el-button>
    </div>

    <el-table v-loading="loading" :data="mistakes" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="subject" label="科目" width="80" />
      <el-table-column prop="question_text" label="题目" show-overflow-tooltip />
      <el-table-column label="错误原因" width="110">
        <template #default="{ row }">
          <el-tag :type="errorTagType[row.error_type] || 'info'" size="small" effect="plain">
            {{ errorTypeText[row.error_type] || row.error_type }}
          </el-tag>
        </template>
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

    <el-empty
      v-if="!loading && mistakes.length === 0"
      :description="subject || errorType ? '没有符合筛选条件的错题' : '还没有错题，去录入第一道吧'"
    />
  </div>
</template>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.filter { width: 180px; }
.count { color: #909399; font-size: 13px; }
.spacer { flex: 1; }

@media (max-width: 768px) {
  .filter { width: 100%; }
  .spacer { display: none; }
  .count { order: 2; }
}
</style>
