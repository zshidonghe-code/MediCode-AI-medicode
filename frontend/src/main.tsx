import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#0ea5e9',
          colorSuccess: '#10b981',
          colorWarning: '#f59e0b',
          colorError: '#ef4444',
          colorInfo: '#6366f1',
          borderRadius: 8,
          colorBgContainer: '#ffffff',
          colorBgLayout: '#f0f5f9',
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
          fontSize: 14,
          colorText: '#1e293b',
          colorTextSecondary: '#64748b',
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        },
        components: {
          Layout: {
            siderBg: '#0f172a',
            headerBg: '#ffffff',
            bodyBg: '#f0f5f9',
          },
          Menu: {
            darkItemBg: '#0f172a',
            darkItemSelectedBg: '#1e3a5f',
            darkItemHoverBg: '#1a2744',
          },
          Card: {
            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
          },
          Table: {
            headerBg: '#f8fafc',
            headerColor: '#475569',
            rowHoverBg: '#f0f9ff',
          },
          Statistic: {
            contentFontSize: 28,
          },
        },
      }}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>,
)
