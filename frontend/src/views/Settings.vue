<script setup>
// 设置：考试日期是调度算法的关键输入（创新点 1），每日上限用于考前模式。
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi } from '../api'

const form = reactive({ exam_date: null, daily_review_limit: 20 })
const daysToExam = ref(null)
const loading = ref(false)
const saving = ref(false)

const load = async () => {
  loading.value = true
  try {
    const { data } = await settingsApi.get()
    form.exam_date = data.exam_date
    form.daily_review_limit = data.daily_review_limit
    daysToExam.value = data.days_to_exam
  } finally {
    loading.value = false
  }
}

onMounted(load)

const save = async () => {
  saving.value = true
  try {
    const { data } = await settingsApi.update({
      exam_date: form.exam_date || null,
      daily_review_limit: form.daily_review_limit,
    })
    daysToExam.value = data.days_to_exam
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <el-card v-loading="loading">
    <template #header>设置</template>

    <el-form label-width="110px" style="max-width: 560px">
      <el-form-item label="考试日期">
        <el-date-picker
          v-model="form.exam_date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择初试日期"
          style="width: 220px"
        />
        <span v-if="daysToExam !== null" class="hint">
          {{ daysToExam > 0 ? `距考试 ${daysToExam} 天` : '考试日期已过' }}
        </span>
      </el-form-item>

      <el-form-item label="每日复习上限">
        <el-input-number v-model="form.daily_review_limit" :min="1" :max="200" />
        <span class="hint">考前 7 天按优先级排序，只显示前 N 条</span>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </el-form-item>
    </el-form>

    <el-alert type="info" :closable="false" show-icon>
      <template #title>为什么需要考试日期？</template>
      普通记忆软件假设你无限期地学下去，而考研有截止日期。设置了考试日期后，
      系统会保证每道错题在考前都能排上，剩余 7 天时自动切换为按优先级排队的考前模式。
    </el-alert>
  </el-card>
</template>

<style scoped>
.hint { color: #909399; font-size: 13px; margin-left: 12px; }
</style>
