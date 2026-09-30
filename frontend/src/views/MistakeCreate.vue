<script setup>
// 录入错题：骨架版（AI 识别/讲解后置），手动填文本
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { knowledgeApi, mistakeApi } from '../api'

const router = useRouter()
const form = reactive({
  subject: '高数',
  question_text: '',
  knowledge_point_id: null,
  error_type: 'careless',
  my_answer: '',
})
const knowledge = ref([])
const submitting = ref(false)

onMounted(async () => {
  const { data } = await knowledgeApi.list()
  // 骨架先按科目过滤章；节结构后置
  knowledge.value = data.filter((k) => k.parent_id === null)
})

const submit = async () => {
  if (!form.question_text.trim()) {
    ElMessage.warning('题目内容不能为空')
    return
  }
  submitting.value = true
  try {
    await mistakeApi.create({ ...form, my_answer: form.my_answer || null })
    ElMessage.success('录入成功')
    router.push('/mistakes')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-card>
    <el-form label-width="90px" style="max-width: 720px">
      <el-form-item label="科目">
        <el-radio-group v-model="form.subject">
          <el-radio-button value="高数">高数</el-radio-button>
          <el-radio-button value="线代">线代</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="题目内容">
        <el-input
          v-model="form.question_text"
          type="textarea"
          :rows="5"
          placeholder="输入题目（后续版本：拍照 + AI 自动识别）"
        />
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
          <el-option v-for="k in knowledge" :key="k.id" :label="`${k.subject} · ${k.name}`" :value="k.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="我的解答">
        <el-input v-model="form.my_answer" type="textarea" :rows="3" placeholder="选填：你当时是怎么错的" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="submit">保存错题</el-button>
        <el-button @click="$router.back()">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>
