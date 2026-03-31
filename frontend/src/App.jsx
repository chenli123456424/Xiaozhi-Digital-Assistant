import { useTheme, ThemeProvider } from './ThemeContext'
import ChatWindow from './components/ChatWindow'
import Header from './components/Header'
import Sidebar from './components/Sidebar'

function Layout() {
  const { theme } = useTheme()
  return (
    <div className="h-screen flex flex-col" style={{ background: theme.bg, color: theme.text }}>
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          <ChatWindow />
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <Layout />
    </ThemeProvider>
  )
}
