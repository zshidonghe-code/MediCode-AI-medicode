import { create } from 'zustand'
import { setApiAuth, api } from './api'

interface User {
  username: string
  role: string
  name: string
}

function _isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

function _loadInitialToken(): string | null {
  const token = localStorage.getItem('medicode_token')
  if (token && !_isTokenExpired(token)) {
    setApiAuth(token)
    return token
  }
  localStorage.removeItem('medicode_token')
  return null
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
  token: _loadInitialToken(),
  isAuthenticated: !!localStorage.getItem('medicode_token'),

  login: async (username: string, password: string) => {
    // OAuth2PasswordRequestForm requires application/x-www-form-urlencoded
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)

    const { data } = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    localStorage.setItem('medicode_token', data.access_token)
    setApiAuth(data.access_token)
    set({
      token: data.access_token,
      isAuthenticated: true,
      user: { username: data.username, role: data.role, name: data.name },
    })
  },

  logout: () => {
    localStorage.removeItem('medicode_token')
    setApiAuth(null)
    set({ user: null, token: null, isAuthenticated: false })
  },
}))
