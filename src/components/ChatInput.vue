<template>
  <div class="chat-input-container">
    <div class="chat-input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="chat-input"
        placeholder="输入消息..."
        rows="1"
        :disabled="disabled"
        @keydown="handleKeydown"
        @input="autoResize"
      ></textarea>
      <button
        class="send-btn"
        :disabled="!inputText.trim() || disabled"
        @click="handleSend"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
    <div class="input-footer">按 Enter 发送，Shift + Enter 换行</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['send'])

const inputText = ref('')
const textareaRef = ref(null)

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || props.disabled) return
  emit('send', text)
  inputText.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}

// Listen for suggestion clicks
function onSuggestion(text) {
  inputText.value = text
  handleSend()
}

onMounted(() => {
  window.__chatUseSuggestion = onSuggestion
  textareaRef.value?.focus()
})

onUnmounted(() => {
  window.__chatUseSuggestion = null
})
</script>
