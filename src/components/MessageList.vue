<template>
  <div class="message-list" ref="messageListRef">
    <div v-if="messages.length === 0" class="welcome-screen">
      <div class="welcome-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <h2>开始对话</h2>
      <p>输入你的问题，AI 将为你解答</p>
      <div class="suggestions">
        <button class="suggestion-chip" @click="useSuggestion(s)" v-for="s in suggestions" :key="s">
          {{ s }}
        </button>
      </div>
    </div>
    <div v-else class="messages-container">
      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />
      <div v-if="loading && !hasStreamingMsg" class="typing-indicator">
        <div class="typing-avatar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/>
            <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
            <line x1="9" y1="9" x2="9.01" y2="9"/>
            <line x1="15" y1="9" x2="15.01" y2="9"/>
          </svg>
        </div>
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const messageListRef = ref(null)
const emit = defineEmits(['use-suggestion'])

const suggestions = [
  '帮我写一首关于春天的诗',
  '解释一下量子计算的基本原理',
  '用 Python 写一个快速排序算法',
  '推荐几本值得读的经典书籍'
]

const hasStreamingMsg = computed(() =>
  props.messages.some(m => m.id === 'streaming')
)

function useSuggestion(text) {
  // Find the ChatInput and trigger send
  window.__chatUseSuggestion?.(text)
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  }
)

// Also scroll when streaming content updates
watch(
  () => props.messages[props.messages.length - 1]?.content,
  async () => {
    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  }
)
</script>
