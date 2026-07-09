import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// Mock authStore BEFORE importing component
const mockUseAuthStore = vi.fn()
vi.mock('../services/authStore', () => ({
  useAuthStore: () => mockUseAuthStore(),
}))

import { RolePermissionMatrix } from './RolePermissionMatrix'

describe('RolePermissionMatrix', () => {
  beforeEach(() => {
    mockUseAuthStore.mockReset()
  })

  // Slice 1: admin 角色 — 渲染 admin 权限矩阵
  it('renders admin role permission matrix with all permissions', () => {
    mockUseAuthStore.mockReturnValue({
      user: { username: 'admin', role: 'admin', name: '管理员' },
      token: 'fake-token',
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(<RolePermissionMatrix />)

    expect(screen.getByText('角色权限矩阵')).toBeInTheDocument()
    expect(screen.getByText(/管理员/)).toBeInTheDocument()
    expect(screen.getByText('数据驾驶舱')).toBeInTheDocument()
    expect(screen.getByText('系统管理')).toBeInTheDocument()
  })

  // Slice 2: coder 角色 — 渲染编码员权限
  it('renders coder role permission matrix', () => {
    mockUseAuthStore.mockReturnValue({
      user: { username: 'coder', role: 'coder', name: '编码员' },
      token: 'fake-token',
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(<RolePermissionMatrix />)

    expect(screen.getByText(/编码员/)).toBeInTheDocument()
    expect(screen.getByText('智能流水线')).toBeInTheDocument()
    expect(screen.getByText('编码工作台')).toBeInTheDocument()
    expect(screen.getByText('DRG 分组')).toBeInTheDocument()
    expect(screen.getByText('质控中心')).toBeInTheDocument()
  })

  // Slice 3: doctor 角色 — 渲染医生权限
  it('renders doctor role permission matrix', () => {
    mockUseAuthStore.mockReturnValue({
      user: { username: 'doctor', role: 'doctor', name: '医生' },
      token: 'fake-token',
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(<RolePermissionMatrix />)

    expect(screen.getByText(/医生/)).toBeInTheDocument()
    expect(screen.getByText('智能流水线')).toBeInTheDocument()
    expect(screen.getByText('编码工作台')).toBeInTheDocument()
    expect(screen.getByText('DRG 分组')).toBeInTheDocument()
    expect(screen.getByText('质控中心')).toBeInTheDocument()
  })
})