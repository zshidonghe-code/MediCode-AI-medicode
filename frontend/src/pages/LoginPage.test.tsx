import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import LoginPage from './LoginPage'

describe('LoginPage demo accounts', () => {
  it('shows all three verified demo credentials', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('演示验证账号')).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
    expect(screen.getByText('coder')).toBeInTheDocument()
    expect(screen.getByText('doctor')).toBeInTheDocument()
    expect(screen.getAllByText('123456')).toHaveLength(3)
  })
})
