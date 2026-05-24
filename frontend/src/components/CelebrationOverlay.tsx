import { TrophyOutlined } from '@ant-design/icons'

interface CelebrationOverlayProps {
  visible: boolean
  onDismiss?: () => void
}

export default function CelebrationOverlay({ visible, onDismiss }: CelebrationOverlayProps) {
  if (!visible) return null

  const colors = ['#0ea5e9', '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#8b5cf6']
  const particles = Array.from({ length: 60 }, (_, i) => ({
    id: i,
    color: colors[i % colors.length],
    left: Math.random() * 100,
    delay: Math.random() * 1.5,
    size: 6 + Math.random() * 8,
    rotation: Math.random() * 360,
  }))

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 9999, cursor: 'pointer',
        overflow: 'hidden',
      }}
      onClick={onDismiss}
    >
      <style>{`
        @keyframes confetti-fall {
          0% { transform: translateY(-20px) rotate(0deg); opacity: 1; }
          100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
        }
        @keyframes celebration-fade-in {
          0% { opacity: 0; transform: scale(0.8); }
          100% { opacity: 1; transform: scale(1); }
        }
        @keyframes celebration-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
      `}</style>

      <div
        style={{
          position: 'absolute', top: '30%', left: '50%',
          transform: 'translate(-50%, -50%)',
          animation: 'celebration-fade-in 0.6s ease-out',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
            borderRadius: 24, padding: '32px 48px',
            boxShadow: '0 20px 60px rgba(14, 165, 233, 0.4)',
            animation: 'celebration-pulse 2s ease-in-out infinite',
          }}
        >
          <TrophyOutlined style={{ fontSize: 56, color: '#fbbf24', marginBottom: 12 }} />
          <div style={{ fontSize: 28, fontWeight: 800, color: '#fff', letterSpacing: 2 }}>
            分析完成！
          </div>
          <div style={{ fontSize: 15, color: 'rgba(255,255,255,0.8)', marginTop: 8 }}>
            AI智能编码流水线演示结束
          </div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginTop: 12 }}>
            点击任意处关闭 · 4秒后自动消失
          </div>
        </div>
      </div>

      {particles.map((p) => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            top: -20,
            left: `${p.left}%`,
            width: p.size,
            height: p.size,
            borderRadius: Math.random() > 0.5 ? '50%' : '2px',
            background: p.color,
            animation: `confetti-fall ${2.5 + Math.random() * 2}s ease-in ${p.delay}s forwards`,
            transform: `rotate(${p.rotation}deg)`,
          }}
        />
      ))}
    </div>
  )
}
