<template>
  <div v-if="checking" class="app loading">
    <div class="loading-spinner"></div>
  </div>
  <LoginPage v-else-if="!user" @login="handleLogin" />
  <div v-else class="app">
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
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatView from './components/ChatView.vue'
import LoginPage from './components/LoginPage.vue'
import { supabase } from './services/supabase.js'

const user = ref(null)
const checking = ref(true)
const sessions = ref([])
const currentSessionId = ref(null)
const sidebarOpen = ref(true)

let authSubscription = null

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

function handleLogin() {
  // OAuth redirect handled by Supabase, auth state change listener will update user
}

// Expose for ChatView to update messages
window.__chatSessions = sessions
window.__chatSaveSessions = saveSessions

onMounted(async () => {
  // If Supabase is not configured, skip login and go directly to chat
  if (!supabase) {
    checking.value = false
    user.value = 'no-auth'
    loadSessions()
    return
  }

  // Check current session
  const { data: { session } } = await supabase.auth.getSession()
  user.value = session?.user ?? null
  checking.value = false

  if (user.value) {
    loadSessions()
  }

  // Listen for auth state changes (handles OAuth callback)
  const { data } = supabase.auth.onAuthStateChange((_event, session) => {
    user.value = session?.user ?? null
    if (user.value) {
      loadSessions()
    }
  })
  authSubscription = data.subscription
})

onUnmounted(() => {
  authSubscription?.unsubscribe()
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

.app.loading {
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--text-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
