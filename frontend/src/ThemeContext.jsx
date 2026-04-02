import { createContext, useContext, useState } from 'react'

export const ThemeContext = createContext()

export const themes = {
  dark: {
    bg: '#0d1117',
    panel: '#161b22',
    border: '#21262d',
    card: '#1c2128',
    input: '#21262d',
    inputBorder: '#30363d',
    text: '#e6edf3',
    textMuted: '#8b949e',
    textFaint: '#484f58',
    avatarBg: 'linear-gradient(180deg, #1a2a4a 0%, #0d1a2e 100%)',
    avatarBorder: '#1d3461',
    tagBg: '#1a3a5c',
    tagColor: '#4a90d9',
    tagBorder: '#1d6fe8',
    dialectBg: '#21262d',
    dialectColor: '#8b949e',
    dialectBorder: '#30363d',
    userBubble: '#1d6fe8',
    sendBtn: '#1d6fe8',
  },
  light: {
    bg: '#f0f4f8',
    panel: '#ffffff',
    border: '#d0d7de',
    card: '#ffffff',
    input: '#ffffff',
    inputBorder: '#d0d7de',
    text: '#1f2328',
    textMuted: '#57606a',
    textFaint: '#8c959f',
    avatarBg: 'linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%)',
    avatarBorder: '#93c5fd',
    tagBg: '#dbeafe',
    tagColor: '#1d6fe8',
    tagBorder: '#93c5fd',
    dialectBg: '#f0f4f8',
    dialectColor: '#57606a',
    dialectBorder: '#d0d7de',
    userBubble: '#1d6fe8',
    sendBtn: '#1d6fe8',
  }
}

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState('dark') 
  const toggle = () => setMode(m => m === 'dark' ? 'light' : 'dark')
  return (
    <ThemeContext.Provider value={{ theme: themes[mode], mode, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
