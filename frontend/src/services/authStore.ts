import { create } from 'zustand'
import axios from 'axios'
import { setApiAuth } from './api'

interface User {
  username: string
  role: string
  name: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('medicode_token'),
  isAuthenticated: !!localStorage.getItem('medicode_token'),

  login: async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const { data } = await axios.post('/api/v1/auth/login', formData)
    localStorage.setItem('medicode_token', data.access_token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
    setApiAuth(data.access_token)
    set({
      token: data.access_token,
      isAuthenticated: true,
      user: { username: data.username, role: data.role, name: data.name },
    })
  },

  logout: () => {
    localStorage.removeItem('medicode_token')
    delete axios.defaults.headers.common['Authorization']
    setApiAuth(null)
    set({ user: null, token: null, isAuthenticated: false })
  },
}))

// Defer to setApiAuth — it handles both global axios + api instance
const token = localStorage.getItem('medicode_token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  setApiAuth(token)
}
