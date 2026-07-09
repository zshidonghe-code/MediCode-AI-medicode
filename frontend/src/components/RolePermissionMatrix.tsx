import { Table, Tag, Typography, Card, Space } from 'antd'
import { useAuthStore } from '../services/authStore'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

/**
 * 角色权限矩阵 — 展示当前角色的菜单权限。
 * 从 useAuthStore 读 role，无 props。
 *
 * 来源：Issue #4 — AppLayout 模块下沉。
 */

interface PermissionRow {
  key: string
  label: string
  path: string
  group: string
}

// === ICON_MAP：标签 → emoji 文本图标（与 AppLayout 菜单图标呼应） ===
const ICON_MAP: Record<string, string> = {
  '数据驾驶舱': '📊',
  '系统管理': '⚙️',
  '智能流水线': '🔄',
  '编码工作台': '📝',
  'DRG 分组': '🏥',
  '质控中心': '✅',
}

// === DEMO_USERS：3 个角色的菜单权限 ===
const DEMO_USERS: Record<string, PermissionRow[]> = {
  admin: [
    { key: 'dashboard', label: '数据驾驶舱', path: '/dashboard', group: 'admin' },
    { key: 'admin', label: '系统管理', path: '/admin', group: 'admin' },
  ],
  coder: [
    { key: 'pipeline', label: '智能流水线', path: '/pipeline', group: 'coder' },
    { key: 'coding', label: '编码工作台', path: '/coding', group: 'coder' },
    { key: 'drg', label: 'DRG 分组', path: '/drg', group: 'coder' },
    { key: 'qc', label: '质控中心', path: '/qc', group: 'coder' },
  ],
  doctor: [
    { key: 'pipeline', label: '智能流水线', path: '/pipeline', group: 'doctor' },
    { key: 'coding', label: '编码工作台', path: '/coding', group: 'doctor' },
    { key: 'drg', label: 'DRG 分组', path: '/drg', group: 'doctor' },
    { key: 'qc', label: '质控中心', path: '/qc', group: 'doctor' },
  ],
}

// === VERSION_INFO：版本元信息（与 AppLayout 底部徽章呼应） ===
const VERSION_INFO = {
  drgStandard: 'CHS-DRG 1.2',
  icdStandard: 'ICD-10',
  version: 'v1.0.0',
}

const ROLE_LABEL: Record<string, string> = {
  admin: '管理员',
  coder: '编码员',
  doctor: '医生',
}

export function RolePermissionMatrix() {
  const { user } = useAuthStore()
  const role = user?.role ?? ''
  const rows = DEMO_USERS[role] ?? []
  const roleLabel = ROLE_LABEL[role] || role || '未登录'

  const columns: ColumnsType<PermissionRow> = [
    {
      title: '图标',
      dataIndex: 'label',
      key: 'icon',
      width: 80,
      render: (label: string) => (
        <span style={{ fontSize: 18 }}>{ICON_MAP[label] ?? '·'}</span>
      ),
    },
    {
      title: '权限名称',
      dataIndex: 'label',
      key: 'label',
      render: (label: string) => <Text strong>{label}</Text>,
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      render: (path: string) => <Text code>{path}</Text>,
    },
    {
      title: '分组',
      dataIndex: 'group',
      key: 'group',
      render: (group: string) => (
        <Tag color={group === 'admin' ? 'purple' : 'blue'}>{group}</Tag>
      ),
    },
  ]

  return (
    <Card data-testid="role-permission-matrix" style={{ maxWidth: 800 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <Title level={4} style={{ margin: 0 }}>角色权限矩阵</Title>
          <Text type="secondary">
            当前角色:{' '}
            <Tag color="geekblue" data-testid="current-role">{roleLabel}</Tag>
          </Text>
        </div>

        <Table<PermissionRow>
          columns={columns}
          dataSource={rows}
          rowKey="key"
          pagination={false}
          size="middle"
          data-testid="permission-table"
        />

        <Text type="secondary" style={{ fontSize: 12 }}>
          {VERSION_INFO.drgStandard} · {VERSION_INFO.icdStandard} · {VERSION_INFO.version}
        </Text>
      </Space>
    </Card>
  )
}