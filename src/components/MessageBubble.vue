<template>
  <div class="message-bubble" :class="message.role">
    <div class="bubble-avatar">
      <svg v-if="message.role === 'user'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/>
        <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
        <line x1="9" y1="9" x2="9.01" y2="9"/>
        <line x1="15" y1="9" x2="15.01" y2="9"/>
      </svg>
    </div>
    <div class="bubble-content">
      <div class="bubble-header">{{ message.role === 'user' ? '你' : 'AI 助手' }}</div>
      <div class="bubble-text" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../services/api.js'

const props = defineProps({
  message: { type: Object, required: true }
})

const renderedContent = computed(() => {
  return renderMarkdown(props.message.content || '')
})
</script>
