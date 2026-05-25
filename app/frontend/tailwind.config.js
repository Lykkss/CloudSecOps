/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        pixel: ['"Press Start 2P"', 'monospace'],
        mono: ['"VT323"', 'monospace'],
        ui: ['"Share Tech Mono"', 'monospace'],
      },
      colors: {
        mc: {
          dirt:    '#866043',
          grass:   '#5D9A3C',
          stone:   '#888888',
          cobble:  '#777777',
          coal:    '#2C2C2C',
          iron:    '#AFAFAF',
          gold:    '#FEC84B',
          diamond: '#39D4E0',
          emerald: '#3EE07A',
          redstone:'#FF3333',
          lapis:   '#1A4BE6',
          sky:     '#7EC8FF',
          night:   '#0A0E1A',
          cave:    '#111827',
          block:   '#1C2233',
          border:  '#2D3A4A',
          light:   '#E6EDF3',
          muted:   '#6B7A8D',
        }
      },
      boxShadow: {
        'mc':      'inset -2px -4px 0 rgba(0,0,0,0.4), inset 2px 2px 0 rgba(255,255,255,0.15)',
        'mc-btn':  'inset -3px -6px 0 rgba(0,0,0,0.5), inset 3px 3px 0 rgba(255,255,255,0.2)',
        'mc-hover':'inset -3px -6px 0 rgba(0,0,0,0.3), inset 3px 3px 0 rgba(255,255,255,0.3)',
        'mc-press':'inset 3px 6px 0 rgba(0,0,0,0.5)',
        'mc-glow-diamond': '0 0 20px rgba(57,212,224,0.4), inset -2px -4px 0 rgba(0,0,0,0.4)',
        'mc-glow-emerald': '0 0 20px rgba(62,224,122,0.4), inset -2px -4px 0 rgba(0,0,0,0.4)',
        'mc-glow-red':     '0 0 20px rgba(255,51,51,0.4), inset -2px -4px 0 rgba(0,0,0,0.4)',
        'mc-glow-gold':    '0 0 20px rgba(254,200,75,0.4), inset -2px -4px 0 rgba(0,0,0,0.4)',
      },
      animation: {
        'float':    'float 6s ease-in-out infinite',
        'float-2':  'float 8s ease-in-out infinite 2s',
        'float-3':  'float 10s ease-in-out infinite 4s',
        'pixel-in': 'pixelIn .3s steps(4) forwards',
        'blink':    'blink 1s step-end infinite',
        'dig':      'dig .4s steps(4) forwards',
        'torch':    'torch .1s steps(2) infinite',
        'spin-slow':'spin 8s linear infinite',
      },
      keyframes: {
        float:   { '0%,100%': { transform: 'translateY(0px) rotate(0deg)' }, '50%': { transform: 'translateY(-20px) rotate(5deg)' } },
        pixelIn: { '0%': { opacity: 0, transform: 'scale(0.8)' }, '100%': { opacity: 1, transform: 'scale(1)' } },
        blink:   { '0%,100%': { opacity: 1 }, '50%': { opacity: 0 } },
        dig:     { '0%': { transform: 'rotate(-30deg)' }, '50%': { transform: 'rotate(30deg)' }, '100%': { transform: 'rotate(-30deg)' } },
        torch:   { '0%': { boxShadow: '0 0 8px 4px rgba(254,200,75,0.8)' }, '100%': { boxShadow: '0 0 12px 8px rgba(254,200,75,0.6)' } },
      },
      backgroundImage: {
        'mc-pattern': "url(\"data:image/svg+xml,%3Csvg width='64' height='64' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='64' height='64' fill='%230A0E1A'/%3E%3Crect x='0' y='0' width='32' height='32' fill='%230D1220' opacity='0.5'/%3E%3Crect x='32' y='32' width='32' height='32' fill='%230D1220' opacity='0.5'/%3E%3C/svg%3E\")",
        'stone-pattern': "url(\"data:image/svg+xml,%3Csvg width='32' height='32' viewBox='0 0 32 32' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='32' height='32' fill='%231C2233'/%3E%3Crect x='0' y='0' width='16' height='16' fill='%23202840' opacity='0.3'/%3E%3Crect x='16' y='16' width='16' height='16' fill='%23202840' opacity='0.3'/%3E%3C/svg%3E\")",
      }
    },
  },
  plugins: [],
}
