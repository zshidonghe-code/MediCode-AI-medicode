import '@testing-library/jest-dom/vitest'

// jsdom 不提供 window.matchMedia，AntD Card/Table/Grid 响应式 observer 需要它。
// 测试里 matchMedia 始终返回不匹配（mobile/desktop 都 false），即可禁用响应式分支。
if (typeof window !== 'undefined' && !window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {}, // deprecated API
      removeListener: () => {}, // deprecated API
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  })
}