<script setup>
// 今日复习：队列 + 还记得/模糊/忘了 反馈 -> SM-2 动态调度
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mistakeApi, reviewApi } from '../api'

const queue = ref([])
const current = ref(null)
const currentDetail = ref(null)
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    const { data } = await reviewApi.due()
    queue.value = data
    current.value = data.length ? data[0] : null
    if (current.value) {
      const { data: detail } = await mistakeApi.list()
      currentDetail.value = detail.find((m) => m.id === current.value.mistake_id) || null
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)

const feedback = async (quality) => {
  await reviewApi.submit({ mistake_id: current.value.mistake_id, quality })
  const text = { 0: '忘了', 3: '模糊', 5: '还记得' }
  ElMessage.success(`已反馈：${text[quality]}，下一次复习安排在 ${current.value.interval_days} 天后`)
  // 重新拉队列，继续下一题
  await load()
  if (queue.value.length === 0) {
    ElMessage.success('🎉 今日复习完成！')
  }
}
</script>

<template>
  <el-card>
    <template #header>今日复习队列（{{ queue.length }} 题待复习）</template>

    <el-empty v-if="!loading && !current" description="今天没有到期的复习，去学点新东西吧" />

    <div v-else-if="current" class="review-card">
      <div class="q-subject">
        {{ currentDetail?.subject }} · {{ currentDetail?.error_type }}
      </div>
      <div class="q-text">{{ currentDetail?.question_text }}</div>

      <el-divider>你觉得这道题现在怎么样？</el-divider>
      <div class="feedback">
        <el-button type="danger" size="large" @click="feedback(0)">😵 忘了</el-button>
        <el-button type="warning" size="large" @click="feedback(3)">🤔 模糊</el-button>
        <el-button type="success" size="large" @click="feedback(5)">💪 还记得</el-button>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.q-subject { color: #909399; font-size: 13px; margin-bottom: 8px; }
.q-text { font-size: 16px; line-height: 1.7; white-space: pre-wrap; }
.feedback { display: flex; gap: 16px; justify-content: center; }
</style>
