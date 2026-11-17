<script setup>
// 今日复习：先自己回忆，再看答案，最后三档自评 -> SM-2 + 倒计时约束调度。
// 队列接口已把题干、答案、解析、掌握度一起返回，前端不再拉全量错题列表。
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { reviewApi } from '../api'

const queue = ref([])
const loading = ref(false)
const showAnswer = ref(false)
const submitting = ref(false)

const current = computed(() => queue.value[0] || null)

const load = async () => {
  loading.value = true
  showAnswer.value = false
  try {
    const { data } = await reviewApi.due()
    queue.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)

const feedback = async (quality) => {
  if (!current.value || submitting.value) return
  submitting.value = true
  try {
    const { data } = await reviewApi.submit({
      mistake_id: current.value.mistake_id,
      quality,
    })
    const label = { 0: '忘了', 3: '模糊', 5: '还记得' }[quality] || '已提交'
    const plan =
      data.mode === 'exam'
        ? '考前模式，明天再复习'
        : `下次复习 ${data.due_date}（${data.interval_days} 天后）`
    ElMessage.success(`${label} · ${plan}`)
    await load()
    if (queue.value.length === 0) {
      ElMessage.success('🎉 今日复习完成')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-card v-loading="loading">
    <template #header>今日复习（{{ queue.length }} 题待复习）</template>

    <el-empty v-if="!loading && !current" description="今天没有到期的复习，去录几道新错题吧" />

    <div v-else-if="current" class="review-card">
      <div class="q-meta">
        <el-tag size="small">{{ current.subject }}</el-tag>
        <el-tag size="small" type="warning" effect="plain">{{ current.error_type_label }}</el-tag>
        <el-tag v-if="current.knowledge_point" size="small" type="info" effect="plain">
          {{ current.knowledge_point }}
        </el-tag>
        <span class="q-stat">
          已复习 {{ current.review_count }} 次 · 掌握度 {{ Math.round(current.mastery * 100) }}%
        </span>
      </div>

      <div class="q-text">{{ current.question_text }}</div>
      <el-image
        v-if="current.question_image"
        :src="current.question_image"
        fit="contain"
        style="max-height: 320px; margin-top: 12px"
      />

      <el-button v-if="!showAnswer" class="peek" @click="showAnswer = true">查看答案 / 解析</el-button>

      <div v-else class="answer">
        <el-divider content-position="left">正确答案</el-divider>
        <div class="answer-text">{{ current.correct_answer || '（未填写答案）' }}</div>
        <template v-if="current.analysis">
          <el-divider content-position="left">解析</el-divider>
          <div class="answer-text">{{ current.analysis }}</div>
        </template>
        <div v-if="current.source" class="source">来源：{{ current.source }}</div>
      </div>

      <el-divider>这道题现在能独立做出来吗？</el-divider>
      <div class="feedback">
        <el-button type="danger" size="large" :loading="submitting" @click="feedback(0)">😵 忘了</el-button>
        <el-button type="warning" size="large" :loading="submitting" @click="feedback(3)">🤔 模糊</el-button>
        <el-button type="success" size="large" :loading="submitting" @click="feedback(5)">💪 还记得</el-button>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.q-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.q-stat { color: #909399; font-size: 13px; margin-left: auto; }
.q-text { font-size: 16px; line-height: 1.8; white-space: pre-wrap; }
.peek { margin-top: 16px; }
.answer { margin-top: 16px; background: #fafafa; padding: 4px 16px 16px; border-radius: 6px; }
.answer-text { font-size: 15px; line-height: 1.8; white-space: pre-wrap; }
.source { color: #909399; font-size: 12px; margin-top: 12px; }
.feedback { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }

@media (max-width: 768px) {
  .q-stat { margin-left: 0; }
  .feedback { gap: 8px; }
  .feedback .el-button { margin-left: 0; flex: 1; }
}
</style>
