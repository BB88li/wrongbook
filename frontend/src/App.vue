<script setup>
// 布局骨架：左侧菜单 + 顶部标题 + 内容区。窄屏时菜单转成顶部横排。
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <el-container class="layout">
    <el-aside width="200px" class="aside">
      <div class="logo">📚 智能错题本</div>
      <el-menu router :default-active="route.path" class="menu">
        <el-menu-item index="/mistakes">错题列表</el-menu-item>
        <el-menu-item index="/mistakes/new">录入错题</el-menu-item>
        <el-menu-item index="/review">今日复习</el-menu-item>
        <el-menu-item index="/report">学习报告</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">{{ route.meta.title || '考研智能错题本' }}</el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style>
body { margin: 0; font-family: 'Microsoft YaHei', sans-serif; background: #f5f7fa; }
.layout { min-height: 100vh; }
.aside { background: #fff; border-right: 1px solid #e4e7ed; }
.logo { font-size: 18px; font-weight: bold; padding: 20px 16px; color: #409eff; }
.menu { border-right: none; }
.header { background: #fff; border-bottom: 1px solid #e4e7ed; display: flex; align-items: center; font-size: 16px; font-weight: 600; }
.main { padding: 20px; }

/* 手机端：侧边栏变顶部导航，表单不再挤成一列 */
@media (max-width: 768px) {
  .layout { flex-direction: column; }
  .el-container { min-width: 0; }
  .aside { width: 100% !important; min-width: 0; border-right: none; border-bottom: 1px solid #e4e7ed; }
  .logo { padding: 12px 16px; font-size: 16px; }
  .menu { display: flex; overflow-x: auto; min-width: 0; }
  .menu .el-menu-item { flex: 0 0 auto; padding: 0 14px; height: 44px; line-height: 44px; }
  .header { display: none; }
  .main { padding: 12px; min-width: 0; }
  .el-form-item__label { width: auto !important; }
  .el-form-item { flex-wrap: wrap; }
}
</style>
