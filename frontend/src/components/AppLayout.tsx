import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Dropdown, Space, Typography, Tooltip, Badge } from 'antd'
import {
  FileTextOutlined,
  MedicineBoxOutlined,
  SafetyCertificateOutlined,
  DashboardOutlined,
  LogoutOutlined,
  UserOutlined,
  NodeIndexOutlined,
  ThunderboltOutlined,
  ReadOutlined,
  SettingOutlined,
  ApiOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../services/authStore'

const { Header, Sider, Content } = Layout
const { Text } = Typography

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [llmOnline, setLlmOnline] = useState<boolean | null>(null)

  useEffect(() => {
    fetch('/health/llm')
      .then(r => r.json())
      .then(d => setLlmOnline(d.llm_available))
      .catch(() => setLlmOnline(false))
  }, [])

  const menuItems = [
    { key: '/pipeline', icon: <NodeIndexOutlined />, label: '智能流水线' },
    { key: '/coding', icon: <FileTextOutlined />, label: '编码工作台' },
    { key: '/drg', icon: <MedicineBoxOutlined />, label: 'DRG分组' },
    { key: '/qc', icon: <SafetyCertificateOutlined />, label: '质控中心' },
    { key: '/dashboard', icon: <DashboardOutlined />, label: '数据驾驶舱' },
    { key: '/guide', icon: <ReadOutlined />, label: '使用指南' },
    ...(user?.role === 'admin'
      ? [{ key: '/admin', icon: <SettingOutlined />, label: '系统管理' } as const]
      : []),
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
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        breakpoint="lg"
        collapsedWidth={64}
        style={{
          background: 'linear-gradient(180deg, #0f172a 0%, #162d50 100%)',
          borderRight: '1px solid rgba(255,255,255,0.04)',
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

        {/* Bottom badge */}
        <div style={{
          position: 'absolute', bottom: 16, left: 16, right: 16,
          padding: '12px 16px',
          background: 'rgba(14,165,233,0.08)',
          borderRadius: 10,
          border: '1px solid rgba(14,165,233,0.12)',
        }}>
          <Space direction="vertical" size={4}>
            <Space size={6}>
              <Tooltip title={llmOnline ? 'Ollama 在线' : llmOnline === null ? '检测中...' : 'Ollama 离线，使用规则引擎'}>
                <Badge
                  status={llmOnline ? 'success' : 'error'}
                  style={llmOnline === null ? { opacity: 0.5 } : undefined}
                />
              </Tooltip>
              <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11 }}>
                AI {llmOnline ? '在线' : llmOnline === null ? '检测中' : '离线'}
              </Text>
            </Space>
            <Text style={{ color: 'rgba(255,255,255,0.3)', fontSize: 10 }}>
              CHS-DRG 1.2 · ICD-10
            </Text>
            <Button
              type="link"
              size="small"
              icon={<ApiOutlined />}
              onClick={() => window.open('/docs', '_blank')}
              style={{ color: 'rgba(255,255,255,0.4)', padding: 0, fontSize: 10, height: 20 }}
            >
              API 文档
            </Button>
          </Space>
        </div>
      </Sider>

      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          borderBottom: '1px solid #f0f0f0',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          zIndex: 10,
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

        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 12, overflow: 'auto', minHeight: 360 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
