<template>
  <div class="app">
    <Sidebar
      :sessions="sessions"
      :current-session-id="currentSessionId"
      @select-session="selectSession"
      @new-session="createNewSession"
      @delete-session="deleteSession"
      :sidebar-open="sidebarOpen"
      @toggle-sidebar="sidebarOpen = !sidebarOpen"
    />
    <ChatView
      :session-id="currentSessionId"
      :sidebar-open="sidebarOpen"
      @toggle-sidebar="sidebarOpen = !sidebarOpen"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatView from './components/ChatView.vue'

const sessions = ref([])
const currentSessionId = ref(null)
const sidebarOpen = ref(true)

function generateId() {
  return 'sess_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function loadSessions() {
  try {
    const stored = localStorage.getItem('ai_chat_sessions')
    if (stored) {
      sessions.value = JSON.parse(stored)
    }
  } catch (e) {
    sessions.value = []
  }
  if (sessions.value.length > 0) {
    currentSessionId.value = sessions.value[0].id
  } else {
    createNewSession()
  }
}

function saveSessions() {
  try {
    localStorage.setItem('ai_chat_sessions', JSON.stringify(sessions.value))
  } catch (e) {
    // Storage quota exceeded - trim old sessions
    console.warn('localStorage quota exceeded, trimming old sessions')
    while (sessions.value.length > 5) {
      sessions.value.pop()
    }
    try {
      localStorage.setItem('ai_chat_sessions', JSON.stringify(sessions.value))
    } catch (e2) {
      console.error('Failed to save sessions:', e2)
    }
  }
}

function createNewSession() {
  const session = {
    id: generateId(),
    title: '新对话',
    messages: [],
    createdAt: new Date().toISOString()
  }
  sessions.value.unshift(session)
  currentSessionId.value = session.id
  saveSessions()
}

function selectSession(id) {
  currentSessionId.value = id
}

function deleteSession(id) {
  sessions.value = sessions.value.filter(s => s.id !== id)
  saveSessions()
  if (sessions.value.length === 0) {
    createNewSession()
  } else if (currentSessionId.value === id) {
    currentSessionId.value = sessions.value[0].id
  }
}

// Expose for ChatView to update messages
window.__chatSessions = sessions
window.__chatSaveSessions = saveSessions

onMounted(() => {
  loadSessions()
})
</script>

<style>
@import './assets/style.css';

.app {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>
