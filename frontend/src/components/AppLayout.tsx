import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Dropdown, Space, Typography } from 'antd'
import {
  FileTextOutlined,
  MedicineBoxOutlined,
  SafetyCertificateOutlined,
  DashboardOutlined,
  LogoutOutlined,
  UserOutlined,
  NodeIndexOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../services/authStore'
import { useEffect, useState } from 'react'
import { CommandPaletteModal } from './CommandPaletteModal'

const { Header, Sider, Content } = Layout
const { Text } = Typography

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [cmdOpen, setCmdOpen] = useState(false)

  // === Issue #3: ⌘⇧P / Ctrl+Shift+P 全局命令面板快捷键 ===
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey
      if (isMod && e.shiftKey && (e.key === 'P' || e.key === 'p')) {
        e.preventDefault()
        setCmdOpen((v) => !v)
      }
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handler)
      return () => window.removeEventListener('keydown', handler)
    }
  }, [])

  const isAdmin = user?.role === 'admin'

  const menuItems = isAdmin
    ? [
        { key: '/dashboard', icon: <DashboardOutlined />, label: '数据驾驶舱' },
        { key: '/admin', icon: <SettingOutlined />, label: '系统管理' },
      ]
    : [
        { key: '/pipeline', icon: <NodeIndexOutlined />, label: '智能流水线' },
        { key: '/coding', icon: <FileTextOutlined />, label: '编码工作台' },
        { key: '/drg', icon: <MedicineBoxOutlined />, label: 'DRG分组' },
        { key: '/qc', icon: <SafetyCertificateOutlined />, label: '质控中心' },
      ]

  const roleMap: Record<string, string> = {
    admin: '管理员', coder: '编码员', doctor: '医生',
  }

  const userMenu = {
    items: [
      {
        key: 'role',
        label: `角色: ${roleMap[user?.role || ''] || '用户'}`,
        disabled: true,
      },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'logout') {
        logout()
        navigate('/login')
      }
    },
  }

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <Sider
        breakpoint="lg"
        collapsedWidth={64}
        style={{
          background: 'linear-gradient(180deg, #0f172a 0%, #162d50 100%)',
          borderRight: '1px solid rgba(255,255,255,0.04)',
          overflow: 'hidden',
        }}
      >
        {/* Brand */}
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          gap: 10,
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <MedicineBoxOutlined style={{ fontSize: 18, color: '#fff' }} />
          </div>
          <Text strong style={{ color: '#fff', fontSize: 17, letterSpacing: 1 }}>
            码医 MediCode
          </Text>
        </div>

        {/* Menu */}
        <Menu
          style={{ background: 'transparent', borderRight: 'none', marginTop: 8 }}
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />

        {/* Bottom version badge */}
        <div style={{
          position: 'absolute', bottom: 16, left: 16, right: 16,
          padding: '10px 16px',
          borderRadius: 10,
        }}>
          <Text style={{ color: 'rgba(255,255,255,0.25)', fontSize: 10 }}>
            CHS-DRG 1.2 · ICD-10
          </Text>
        </div>
      </Sider>

      <Layout style={{ height: '100%', overflow: 'hidden' }}>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          borderBottom: '1px solid #f0f0f0',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          zIndex: 10,
          flexShrink: 0,
        }}>
          <Space size="middle">
            <Dropdown menu={userMenu}>
              <Button type="text" style={{ borderRadius: 8, height: 40 }}>
                <Space>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontSize: 13, fontWeight: 600,
                  }}>
                    {(user?.name || 'U')[0]}
                  </div>
                  <span style={{ fontWeight: 500 }}>{user?.name || '用户'}</span>
                </Space>
              </Button>
            </Dropdown>
          </Space>
        </Header>

        <Content id="main-content" style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 12, overflowY: 'auto', flex: 1, minHeight: 0 }}>
          <Outlet />
        </Content>
      </Layout>

      {/* Issue #3: 命令面板 — ⌘⇧P 触发 */}
      <CommandPaletteModal
        open={cmdOpen}
        onClose={() => setCmdOpen(false)}
        navigate={navigate}
      />
    </Layout>
  )
}
