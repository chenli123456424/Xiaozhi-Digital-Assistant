import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import Header from './components/Header'

export default function App() {
  const [theme, setTheme] = useState('light')

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-slate-900">
      <Header onToggleTheme={toggleTheme} />
      <main className="flex-1 overflow-hidden">
        <ChatWindow />
      </main>
    </div>
  )
}
