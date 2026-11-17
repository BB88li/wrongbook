<script setup>
// 录入错题：题干 + 我的作答 + 正确答案/解析。支持按科目过滤知识点。
// 为连续录入做了三处优化：自动聚焦题干、Ctrl+Enter 保存、记住上次的科目/错因/知识点。
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeApi, mistakeApi } from '../api'

const STORAGE_KEY = 'wrongbook:last-mistake-form'

const router = useRouter()
const form = reactive({
  subject: '高数',
  question_text: '',
  knowledge_point_id: null,
  error_type: 'careless',
  my_answer: '',
  correct_answer: '',
  analysis: '',
  source: '',
})
const knowledge = ref([])
const submitting = ref(false)
const questionRef = ref(null)

const chapters = computed(() =>
  knowledge.value.filter((k) => k.parent_id === null && k.subject === form.subject),
)

const remember = () => {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        subject: form.subject,
        error_type: form.error_type,
        knowledge_point_id: form.knowledge_point_id,
      }),
    )
  } catch {
    // 隐私模式下 localStorage 可能不可用，忽略
  }
}

onMounted(async () => {
  const { data } = await knowledgeApi.list()
  // 章节结构：parent_id 为 null 的是章；节后续再启用
  knowledge.value = data

  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    if (saved.subject) form.subject = saved.subject
    if (saved.error_type) form.error_type = saved.error_type
    if (saved.knowledge_point_id) form.knowledge_point_id = saved.knowledge_point_id
  } catch {
    // 本地缓存损坏时用默认值
  }

  await nextTick()
  questionRef.value?.focus()
})

const submit = async () => {
  if (!form.question_text.trim()) {
    ElMessage.warning('题目内容不能为空')
    return
  }
  submitting.value = true
  try {
    await mistakeApi.create({
      ...form,
      my_answer: form.my_answer || null,
      correct_answer: form.correct_answer || null,
      analysis: form.analysis || null,
      source: form.source || null,
    })
    remember()
    ElMessage.success('录入成功，明天开始进入复习队列')
    router.push('/mistakes')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-card>
    <el-form label-width="90px" style="max-width: 760px" @keydown.ctrl.enter.prevent="submit" @submit.prevent>
      <el-form-item label="科目">
        <el-radio-group v-model="form.subject" @change="form.knowledge_point_id = null">
          <el-radio-button value="高数">高数</el-radio-button>
          <el-radio-button value="线代">线代</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="题目内容">
        <el-input
          ref="questionRef"
          v-model="form.question_text"
          type="textarea"
          :rows="5"
          placeholder="输入题目（后续版本：拍照 + AI 自动识别）"
        />
      </el-form-item>

      <el-form-item label="正确答案">
        <el-input
          v-model="form.correct_answer"
          type="textarea"
          :rows="2"
          placeholder="标准答案。复习时先自评再对答案，没有它就无法验证对错"
        />
      </el-form-item>

      <el-form-item label="解析">
        <el-input
          v-model="form.analysis"
          type="textarea"
          :rows="4"
          placeholder="思路 / 考点 / 当时为什么错（可留空，后续 AI 生成后补）"
        />
      </el-form-item>

      <el-form-item label="我的解答">
        <el-input v-model="form.my_answer" type="textarea" :rows="2" placeholder="选填：你当时是怎么写的" />
      </el-form-item>

      <el-form-item label="错误原因">
        <el-select v-model="form.error_type" style="width: 200px">
          <el-option label="粗心" value="careless" />
          <el-option label="概念不清" value="concept" />
          <el-option label="方法不会" value="method" />
        </el-select>
      </el-form-item>

      <el-form-item label="知识点">
        <el-select v-model="form.knowledge_point_id" placeholder="选择章节" clearable filterable style="width: 320px">
          <el-option v-for="k in chapters" :key="k.id" :label="k.name" :value="k.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="来源">
        <el-input v-model="form.source" maxlength="100" placeholder="选填：2023 数一真题 / 660 题 / 模拟卷" style="width: 320px" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="submit">保存错题</el-button>
        <el-button @click="$router.back()">取消</el-button>
        <span class="kbd-hint">Ctrl + Enter 保存 · 科目/错因/知识点会记住上次的选择</span>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<style scoped>
.kbd-hint { color: #909399; font-size: 12px; margin-left: 12px; }

@media (max-width: 768px) {
  .kbd-hint { display: none; }
}
</style>
