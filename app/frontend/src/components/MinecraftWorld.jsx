import { useEffect, useRef } from 'react'

const BLOCKS = [
  { color: '#5D9A3C', label: '🌿', size: 40 },
  { color: '#888888', label: '🪨', size: 32 },
  { color: '#39D4E0', label: '💎', size: 28 },
  { color: '#FEC84B', label: '⭐', size: 36 },
  { color: '#866043', label: '🧱', size: 44 },
  { color: '#3EE07A', label: '💚', size: 24 },
  { color: '#FF3333', label: '🔴', size: 20 },
  { color: '#1A4BE6', label: '🔷', size: 32 },
]

function PixelBlock({ x, y, size, color, delay, duration, layer }) {
  return (
    <div
      className="float-block fixed pointer-events-none"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        width: size,
        height: size,
        backgroundColor: color,
        boxShadow: `inset -${size/8}px -${size/6}px 0 rgba(0,0,0,0.5), inset ${size/8}px ${size/8}px 0 rgba(255,255,255,0.15)`,
        imageRendering: 'pixelated',
        zIndex: layer,
        '--dur': `${duration}s`,
        '--delay': `${delay}s`,
        opacity: 0.12,
      }}
    />
  )
}

function StarField() {
  const stars = Array.from({ length: 80 }, (_, i) => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() < 0.3 ? 3 : 2,
    delay: Math.random() * 5,
  }))

  return (
    <>
      {stars.map((s, i) => (
        <div
          key={i}
          className="fixed pointer-events-none"
          style={{
            left: `${s.x}%`,
            top: `${s.y}%`,
            width: s.size,
            height: s.size,
            background: '#E6EDF3',
            imageRendering: 'pixelated',
            zIndex: 0,
            opacity: 0.4,
            animation: `blink ${2 + Math.random() * 3}s step-end ${s.delay}s infinite`,
          }}
        />
      ))}
    </>
  )
}

function GroundLayer() {
  return (
    <div className="fixed bottom-0 left-0 right-0 pointer-events-none" style={{ zIndex: 1 }}>
      {/* Bedrock */}
      <div style={{ height: 8, background: '#111111' }} />
      {/* Stone */}
      <div style={{ height: 16, background: '#555555', boxShadow: 'inset 0 2px 0 rgba(255,255,255,0.05)' }} />
      {/* Dirt */}
      <div style={{ height: 12, background: '#6B4A2A', boxShadow: 'inset 0 2px 0 rgba(255,255,255,0.05)' }} />
      {/* Grass */}
      <div style={{ height: 8, background: '#5D9A3C', boxShadow: 'inset 0 2px 0 rgba(255,255,255,0.2)' }} />
    </div>
  )
}

export default function MinecraftWorld() {
  const blocks = [
    { x: 5,  y: 15, size: 48, color: '#2A5A1A', delay: 0,   duration: 9,  layer: 1 },
    { x: 15, y: 60, size: 32, color: '#555555', delay: 1.5, duration: 11, layer: 1 },
    { x: 25, y: 30, size: 24, color: '#39D4E0', delay: 3,   duration: 8,  layer: 2 },
    { x: 35, y: 75, size: 40, color: '#866043', delay: 0.5, duration: 13, layer: 1 },
    { x: 45, y: 20, size: 28, color: '#FEC84B', delay: 2,   duration: 7,  layer: 2 },
    { x: 55, y: 50, size: 20, color: '#3EE07A', delay: 4,   duration: 10, layer: 1 },
    { x: 65, y: 35, size: 36, color: '#888888', delay: 1,   duration: 12, layer: 1 },
    { x: 75, y: 65, size: 24, color: '#39D4E0', delay: 3.5, duration: 9,  layer: 2 },
    { x: 85, y: 25, size: 32, color: '#5D9A3C', delay: 2.5, duration: 11, layer: 1 },
    { x: 92, y: 55, size: 20, color: '#FEC84B', delay: 0.8, duration: 8,  layer: 2 },
    { x: 10, y: 80, size: 28, color: '#1A4BE6', delay: 1.2, duration: 14, layer: 1 },
    { x: 70, y: 10, size: 16, color: '#FF3333', delay: 4.5, duration: 6,  layer: 2 },
  ]

  return (
    <div className="fixed inset-0 overflow-hidden" style={{ zIndex: 0 }}>
      <StarField />
      {blocks.map((b, i) => (
        <PixelBlock key={i} {...b} />
      ))}
      {/* Moon pixel art */}
      <div
        className="fixed pointer-events-none"
        style={{
          top: '8%', right: '8%',
          width: 32, height: 32,
          background: '#FFFDE7',
          imageRendering: 'pixelated',
          zIndex: 1,
          opacity: 0.7,
          boxShadow: 'inset -6px -6px 0 rgba(0,0,0,0.15), 0 0 20px rgba(255,253,231,0.3)',
        }}
      />
      {/* Moon crater */}
      <div
        className="fixed pointer-events-none"
        style={{
          top: 'calc(8% + 8px)', right: 'calc(8% + 6px)',
          width: 8, height: 8,
          background: '#E8E4C4',
          imageRendering: 'pixelated',
          zIndex: 2, opacity: 0.7,
        }}
      />
      <GroundLayer />
    </div>
  )
}
