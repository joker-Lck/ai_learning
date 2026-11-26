import type { Config } from 'tailwindcss';

/**
 * 主题色全部映射到 CSS 变量（globals.css 中按 data-theme 切换）。
 * - white / black 使用 <alpha-value> 通道，text-white/xx、bg-white/[0.04] 等
 *   透明度写法在夜间/白天自动换算为「白墨」或「黑墨」。
 * - purple / cyan 保留类名兼容旧代码，实际输出强调色（荧光绿 / 深绿）。
 */
const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // 画布与面板
        canvas: 'var(--bg)',
        panel: 'var(--panel)',
        'panel-2': 'var(--panel-2)',
        'panel-3': 'var(--panel-3)',

        // 墨色
        ink: {
          DEFAULT: 'var(--ink)',
          2: 'var(--ink-2)',
          3: 'var(--ink-3)',
          4: 'var(--ink-4)',
        },

        // 强调色（荧光绿 / 白天深绿）
        accent: {
          DEFAULT: 'rgb(var(--accent-rgb) / <alpha-value>)',
          2: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
          soft: 'var(--accent-soft)',
        },

        // 白 / 黑 通道（透明度写法主题感知）
        white: 'rgb(var(--white-rgb) / <alpha-value>)',
        black: 'rgb(var(--black-rgb) / <alpha-value>)',

        // 兼容旧类名 → 强调色（琥珀）
        purple: {
          50: 'var(--accent-soft)',
          100: 'var(--accent-soft)',
          200: 'rgb(var(--accent-rgb) / <alpha-value>)',
          300: 'rgb(var(--accent-rgb) / <alpha-value>)',
          400: 'rgb(var(--accent-rgb) / <alpha-value>)',
          500: 'rgb(var(--accent-rgb) / <alpha-value>)',
          600: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
          700: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
        },
        cyan: {
          300: 'rgb(var(--accent-rgb) / <alpha-value>)',
          400: 'rgb(var(--accent-rgb) / <alpha-value>)',
          500: 'rgb(var(--accent-rgb) / <alpha-value>)',
          600: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
        },
        // 成功/绿色系旧类名也统一收敛到强调色（用户要求去除绿色）
        green: {
          300: 'rgb(var(--accent-rgb) / <alpha-value>)',
          400: 'rgb(var(--accent-rgb) / <alpha-value>)',
          500: 'rgb(var(--accent-rgb) / <alpha-value>)',
          600: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
          700: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
        },
        emerald: {
          300: 'rgb(var(--accent-rgb) / <alpha-value>)',
          400: 'rgb(var(--accent-rgb) / <alpha-value>)',
          500: 'rgb(var(--accent-rgb) / <alpha-value>)',
          600: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
          700: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
        },
        teal: {
          300: 'rgb(var(--accent-rgb) / <alpha-value>)',
          400: 'rgb(var(--accent-rgb) / <alpha-value>)',
          500: 'rgb(var(--accent-rgb) / <alpha-value>)',
          600: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
        },
        lime: {
          300: 'rgb(var(--accent-rgb) / <alpha-value>)',
          400: 'rgb(var(--accent-rgb) / <alpha-value>)',
          500: 'rgb(var(--accent-rgb) / <alpha-value>)',
          600: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
        },

        // 语义色
        danger: 'var(--danger)',
        warn: 'var(--warn)',
        ok: 'var(--ok)',
        info: 'var(--info)',
      },
      textColor: {
        skin: {
          base: 'var(--ink)',
          muted: 'var(--ink-2)',
          faint: 'var(--ink-3)',
          accent: 'var(--accent)',
          'on-accent': 'var(--on-accent)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', 'Microsoft YaHei', 'sans-serif'],
        display: ['Chakra Petch', 'Noto Sans SC', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        none: '0',
        sm: '2px',
        DEFAULT: '2px',
        md: '2px',
        lg: '3px',
        xl: '4px',
        '2xl': '4px',
        '3xl': '6px',
      },
      letterSpacing: {
        tech: '0.18em',
        wider2: '0.22em',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
        'gradient': 'gradient 8s ease infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'bounce-gentle': 'bounceGentle 2s ease-in-out infinite',
        'blink': 'blink-cursor 1.1s steps(2, start) infinite',
        'marquee': 'marquee-scroll 30s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      },
      backgroundSize: {
        '300%': '300%',
      },
      boxShadow: {
        'glow': 'var(--glow)',
        'glow-strong': 'var(--glow-strong)',
        'glow-blue': 'var(--glow)',
        'card': 'var(--shadow-card)',
        'card-hover': 'var(--glow)',
        'glass': 'var(--shadow-card)',
        'glass-inset': 'inset 0 1px 1px 0 var(--glass-bg-hover)',
      },
      backdropBlur: {
        'glass': '20px',
      },
      backgroundColor: {
        'glass': 'var(--glass-bg)',
        'glass-hover': 'var(--glass-bg-hover)',
        'glass-active': 'var(--glass-bg-active)',
        'glass-dark': 'var(--overlay)',
      },
      borderColor: {
        'glass': 'var(--line)',
        'glass-light': 'var(--line)',
        'glass-strong': 'var(--line-strong)',
      },
    },
  },
  plugins: [],
};

export default config;
