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
      :user="user"
      :login-error="loginError"
      @toggle-sidebar="sidebarOpen = !sidebarOpen"
      @login="loginWithGoogle"
      @logout="logout"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatView from './components/ChatView.vue'
import { supabase } from './services/supabase.js'

const user = ref(null)
const sessions = ref([])
const currentSessionId = ref(null)
const sidebarOpen = ref(true)
const loginError = ref('')

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

async function loginWithGoogle() {
  loginError.value = ''
  if (!supabase) {
    loginError.value = 'Supabase 未配置，请在 .env 中设置 VITE_SUPABASE_URL 和 VITE_SUPABASE_ANON_KEY'
    return
  }
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin
    }
  })
  if (error) {
    loginError.value = error.message
  }
}

async function logout() {
  if (!supabase) return
  await supabase.auth.signOut()
  user.value = null
}

// Expose for ChatView to update messages
window.__chatSessions = sessions
window.__chatSaveSessions = saveSessions

onMounted(async () => {
  loadSessions()

  if (!supabase) return

  const { data: { session } } = await supabase.auth.getSession()
  user.value = session?.user ?? null

  const { data } = supabase.auth.onAuthStateChange((_event, session) => {
    user.value = session?.user ?? null
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
</style>
