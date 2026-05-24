import { useState, useEffect, useRef } from 'react'

export default function AnimatedCounter({ value, duration = 1500 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(0)
  const raf = useRef<number>(0)
  const startTime = useRef<number>(0)

  useEffect(() => {
    startTime.current = performance.now()
    const animate = (now: number) => {
      const elapsed = now - startTime.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(value * eased))
      if (progress < 1) raf.current = requestAnimationFrame(animate)
    }
    raf.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf.current)
  }, [value, duration])

  return <span>¥{display.toLocaleString()}</span>
}
