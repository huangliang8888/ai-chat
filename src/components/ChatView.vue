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
      <div class="header-user">
        <template v-if="user">
          <img v-if="user.user_metadata?.avatar_url" :src="user.user_metadata.avatar_url" class="user-avatar" />
          <span class="user-name">{{ user.user_metadata?.full_name || user.email }}</span>
          <button class="logout-btn" @click="$emit('logout')">退出</button>
        </template>
        <button v-else class="login-btn" @click="$emit('login')">
          <svg width="16" height="16" viewBox="0 0 48 48">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          </svg>
          登录
        </button>
      </div>
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
  sidebarOpen: { type: Boolean, default: true },
  user: { type: Object, default: null }
})

defineEmits(['toggle-sidebar', 'login', 'logout'])

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
