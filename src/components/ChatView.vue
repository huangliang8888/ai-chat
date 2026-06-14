<template>
  <main class="chat-view">
    <header class="chat-header">
      <button class="menu-btn" @click="$emit('toggle-sidebar')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
      <h1 class="chat-title">AI Chat</h1>
      <div class="header-spacer"></div>
    </header>

    <MessageList
      :messages="currentMessages"
      :loading="isLoading"
    />

    <ChatInput
      :disabled="isLoading"
      @send="handleSend"
    />
  </main>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'
import { sendChatMessage, streamChatMessage } from '../services/api.js'

const props = defineProps({
  sessionId: { type: String, default: null },
  sidebarOpen: { type: Boolean, default: true }
})

defineEmits(['toggle-sidebar'])

const isLoading = ref(false)
const streamingContent = ref('')

const currentMessages = computed(() => {
  if (!props.sessionId || !window.__chatSessions) return []
  const session = window.__chatSessions.value.find(s => s.id === props.sessionId)
  if (!session) return []
  const msgs = [...session.messages]
  if (streamingContent.value && isLoading.value) {
    msgs.push({
      id: 'streaming',
      role: 'assistant',
      content: streamingContent.value,
      createdAt: new Date().toISOString()
    })
  }
  return msgs
})

function updateSession(sessionId, updater) {
  if (!window.__chatSessions) return
  const sessions = window.__chatSessions.value
  const idx = sessions.findIndex(s => s.id === sessionId)
  if (idx !== -1) {
    updater(sessions[idx])
    window.__chatSaveSessions?.()
  }
}

async function handleSend(content) {
  if (!props.sessionId || isLoading.value) return

  const userMessage = {
    id: 'msg_' + Date.now(),
    role: 'user',
    content,
    createdAt: new Date().toISOString()
  }

  updateSession(props.sessionId, (session) => {
    session.messages.push(userMessage)
    if (session.messages.length === 1) {
      session.title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
    }
  })

  isLoading.value = true
  streamingContent.value = ''

  try {
    const session = window.__chatSessions.value.find(s => s.id === props.sessionId)
    const history = session ? session.messages.map(m => ({ role: m.role, content: m.content })) : []

    // Try streaming first
    const reader = await streamChatMessage(props.sessionId, history, content)

    if (reader) {
      let fullContent = ''
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                fullContent += parsed.content
                streamingContent.value = fullContent
              }
            } catch (e) {
              // skip invalid JSON
            }
          }
        }
      }

      streamingContent.value = ''
      const assistantMessage = {
        id: 'msg_' + Date.now() + '_ai',
        role: 'assistant',
        content: fullContent || '抱歉，未能获取到回复内容。',
        createdAt: new Date().toISOString()
      }
      updateSession(props.sessionId, (session) => {
        session.messages.push(assistantMessage)
      })
    } else {
      // Fallback to non-streaming
      const response = await sendChatMessage(props.sessionId, history, content)
      const assistantMessage = {
        id: 'msg_' + Date.now() + '_ai',
        role: 'assistant',
        content: response.content || '抱歉，未能获取到回复内容。',
        createdAt: new Date().toISOString()
      }
      updateSession(props.sessionId, (session) => {
        session.messages.push(assistantMessage)
      })
    }
  } catch (error) {
    console.error('Chat error:', error)
    const errorMessage = {
      id: 'msg_' + Date.now() + '_err',
      role: 'assistant',
      content: '抱歉，发生了错误：' + (error.message || '网络请求失败，请稍后重试。'),
      createdAt: new Date().toISOString()
    }
    updateSession(props.sessionId, (session) => {
      session.messages.push(errorMessage)
    })
  } finally {
    isLoading.value = false
    streamingContent.value = ''
  }
}
</script>
