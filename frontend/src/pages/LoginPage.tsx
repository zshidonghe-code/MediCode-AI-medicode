import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Form, Input, Button, Typography, message, Space, Tag } from 'antd'
import { MedicineBoxOutlined, ThunderboltOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { useAuthStore } from '../services/authStore'

const { Title, Text } = Typography

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      await login(values.username, values.password)
      message.success('登录成功')
      navigate('/pipeline')
    } catch {
      message.error('用户名或密码错误')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-bg" style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #0c1929 0%, #0f2744 40%, #162d50 100%)',
    }}>
      {/* Animated floating elements */}
      <div style={{ position: 'absolute', top: '10%', left: '15%', opacity: 0.06 }}>
        <MedicineBoxOutlined style={{ fontSize: 120, color: '#fff' }} />
      </div>
      <div style={{ position: 'absolute', bottom: '15%', right: '12%', opacity: 0.04 }}>
        <SafetyCertificateOutlined style={{ fontSize: 100, color: '#fff' }} />
      </div>

      <Card
        style={{
          width: 420,
          borderRadius: 16,
          boxShadow: '0 25px 60px rgba(0,0,0,0.3), 0 0 80px rgba(14,165,233,0.1)',
          border: '1px solid rgba(255,255,255,0.08)',
          background: 'rgba(255,255,255,0.97)',
        }}
        styles={{ body: { padding: 40 } }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          {/* Logo area */}
          <div>
            <div style={{
              width: 72, height: 72, borderRadius: 18, margin: '0 auto 16px',
              background: 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(14,165,233,0.3)',
            }}>
              <MedicineBoxOutlined style={{ fontSize: 36, color: '#fff' }} />
            </div>
            <Title level={2} style={{ marginBottom: 4, fontWeight: 700, letterSpacing: 2 }}>
              码医 <span style={{ fontWeight: 300, color: '#0ea5e9' }}>MediCode</span>
            </Title>
            <Text type="secondary" style={{ fontSize: 14 }}>
              AI驱动 · DRG编码 · 病历质控 · 医保支付
            </Text>
          </div>

          {/* Feature tags */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8 }}>
            <Tag color="blue" style={{ borderRadius: 20, padding: '2px 12px' }}>
              <ThunderboltOutlined /> NLP智能编码
            </Tag>
            <Tag color="green" style={{ borderRadius: 20, padding: '2px 12px' }}>
              <SafetyCertificateOutlined /> 内涵质控
            </Tag>
          </div>

          {/* Form */}
          <Form layout="vertical" onFinish={onFinish} autoComplete="off" size="large">
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
              style={{ marginBottom: 16 }}
            >
              <Input
                placeholder="用户名"
                style={{ borderRadius: 8, height: 44 }}
                prefix={<span style={{ color: '#94a3b8', marginRight: 8 }}>👤</span>}
              />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
              style={{ marginBottom: 24 }}
            >
              <Input.Password
                placeholder="密码"
                style={{ borderRadius: 8, height: 44 }}
                prefix={<span style={{ color: '#94a3b8', marginRight: 8 }}>🔒</span>}
              />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                style={{
                  height: 48,
                  borderRadius: 8,
                  fontSize: 16,
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)',
                  border: 'none',
                }}
              >
                进入系统
              </Button>
            </Form.Item>
          </Form>

          <div style={{
            padding: '12px 16px',
            background: '#f8fafc',
            borderRadius: 8,
            border: '1px solid #e8edf2',
          }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              演示账号 <Text code style={{ fontSize: 12 }}>admin</Text> / <Text code style={{ fontSize: 12 }}>medicode2024</Text>
            </Text>
          </div>
        </Space>
      </Card>

      {/* Footer */}
      <div style={{ position: 'absolute', bottom: 24, color: 'rgba(255,255,255,0.3)', fontSize: 12 }}>
        全国大学生创业大赛 · 码医团队
      </div>
    </div>
  )
}
