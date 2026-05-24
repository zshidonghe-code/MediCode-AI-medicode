import { Result, Button } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <Result
      status="404"
      title="页面不存在"
      subTitle="请检查 URL 是否正确"
      extra={<Button type="primary" onClick={() => navigate('/pipeline')}>返回首页</Button>}
    />
  )
}
