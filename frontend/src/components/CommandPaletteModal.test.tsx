import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CommandPaletteModal } from './CommandPaletteModal'

describe('CommandPaletteModal', () => {
  // Slice 1: 默认关闭 — open=false 时组件不渲染任何 DOM
  it('renders nothing when open=false', () => {
    const { container } = render(
      <CommandPaletteModal open={false} onClose={vi.fn()} navigate={vi.fn()} />
    )
    expect(container).toBeEmptyDOMElement()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  // Slice 2: 打开后渲染 — open=true 时显示搜索框 + 命令列表（含 ≥1 条命令）
  it('renders search input and command list when open=true', () => {
    render(
      <CommandPaletteModal open={true} onClose={vi.fn()} navigate={vi.fn()} />
    )
    const searchInput = screen.getByRole('textbox')
    expect(searchInput).toBeInTheDocument()
    expect(screen.getByText('智能流水线')).toBeInTheDocument()
  })

  // Slice 3: 搜索关键词过滤命令 — 输入查询字符串后只显示匹配项
  it('filters commands by search query', async () => {
    const user = userEvent.setup()
    render(
      <CommandPaletteModal open={true} onClose={vi.fn()} navigate={vi.fn()} />
    )
    expect(screen.getByText('智能流水线')).toBeInTheDocument()
    expect(screen.getByText('编码工作台')).toBeInTheDocument()
    expect(screen.getByText('DRG 分组')).toBeInTheDocument()

    const input = screen.getByRole('textbox')
    await user.type(input, '编码')

    expect(screen.queryByText('智能流水线')).not.toBeInTheDocument()
    expect(screen.getByText('编码工作台')).toBeInTheDocument()
    expect(screen.queryByText('DRG 分组')).not.toBeInTheDocument()
  })

  // Slice 4: 键盘选中 + Enter 执行 — ArrowDown 移到第二项，Enter 调用 navigate + onClose
  it('ArrowDown selects next command and Enter executes it', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    const navigate = vi.fn()

    render(
      <CommandPaletteModal open={true} onClose={onClose} navigate={navigate} />
    )

    // 初始：第一项（智能流水线）被高亮
    const input = screen.getByTestId('command-palette-input') as HTMLInputElement
    input.focus()
    expect(screen.getByTestId('cmd-pipeline')).toHaveAttribute('data-selected', 'true')
    expect(screen.getByTestId('cmd-coding')).toHaveAttribute('data-selected', 'false')

    // ArrowDown → 第二项高亮
    await user.keyboard('{ArrowDown}')
    expect(screen.getByTestId('cmd-pipeline')).toHaveAttribute('data-selected', 'false')
    expect(screen.getByTestId('cmd-coding')).toHaveAttribute('data-selected', 'true')

    // Enter → 调用 navigate('/coding') + onClose()
    await user.keyboard('{Enter}')
    expect(navigate).toHaveBeenCalledWith('/coding')
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})