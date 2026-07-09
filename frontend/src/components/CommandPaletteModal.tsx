import { useState, useEffect } from 'react'
import { Modal, Input } from 'antd'

export interface CommandPaletteModalProps {
  open: boolean
  onClose: () => void
  navigate: (path: string) => void
}

interface CmdItem {
  key: string
  label: string
  path: string
  group: string
}

// 最小命令集（覆盖 slice 2/3/4 测试）
const CMD_ITEMS: CmdItem[] = [
  { key: 'pipeline', label: '智能流水线', path: '/pipeline', group: 'navigation' },
  { key: 'coding', label: '编码工作台', path: '/coding', group: 'navigation' },
  { key: 'drg', label: 'DRG 分组', path: '/drg', group: 'navigation' },
]

export function CommandPaletteModal({
  open,
  onClose,
  navigate,
}: CommandPaletteModalProps): JSX.Element | null {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  // 打开时重置选中；query 变化时重置选中到第一项
  useEffect(() => {
    if (open) setSelectedIndex(0)
  }, [open, query])

  if (!open) return null

  // 过滤：query 空时显示全部；否则按 label 包含匹配（大小写不敏感）
  const trimmed = query.trim().toLowerCase()
  const filtered = trimmed
    ? CMD_ITEMS.filter((c) => c.label.toLowerCase().includes(trimmed))
    : CMD_ITEMS

  // 边界保护：selectedIndex 不超出 filtered 范围
  const safeIndex = Math.min(selectedIndex, Math.max(filtered.length - 1, 0))

  // 键盘导航：↑↓ 移动选中；Enter 执行当前选中
  const onInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && filtered[safeIndex]) {
      e.preventDefault()
      navigate(filtered[safeIndex].path)
      onClose()
    }
  }

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={600}
      centered={false}
      closable={false}
      maskClosable
      keyboard
      style={{ top: 100 }}
      destroyOnClose
      data-testid="command-palette-modal"
    >
      <Input
        placeholder="输入命令或搜索..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={onInputKeyDown}
        autoFocus
        data-testid="command-palette-input"
      />
      <div data-testid="command-palette-list" style={{ marginTop: 16 }}>
        {filtered.map((cmd, idx) => (
          <div
            key={cmd.key}
            data-testid={`cmd-${cmd.key}`}
            data-selected={idx === safeIndex ? 'true' : 'false'}
            onClick={() => {
              navigate(cmd.path)
              onClose()
            }}
            style={{
              padding: '8px 12px',
              cursor: 'pointer',
              borderRadius: 4,
              background: idx === safeIndex ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
            }}
          >
            {cmd.label}
          </div>
        ))}
      </div>
    </Modal>
  )
}