import { useState, useRef, useEffect } from 'react'
import { useTheme } from '../ThemeContext'
import MessageBubble from './MessageBubble'
import InputBox from './InputBox'

const INITIAL_MESSAGES = [
  { id: 1, type: 'assistant', content: '你好！我是小智数码助手，可以为您提供深度搜索、方言朗读以及智能问答服务。有什么我可以帮助你的吗？' }
]

export default function ChatWindow() {
  const { theme } = useTheme()
  const [messages, setMessages] = useState(INITIAL_MESSAGES)
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (message) => {
    if (!message.trim()) return

    const userMsg = { id: Date.now(), type: 'user', content: message }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    const assistantId = Date.now() + 1
    setMessages(prev => [...prev, { id: assistantId, type: 'assistant', content: '', thinking: true }])

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversation_id: conversationId })
      })

      if (!response.ok) throw new Error('请求失败')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const lines = decoder.decode(value).split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.error) {
              setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, content: `错误: ${data.error}`, error: true, thinking: false } : m
              ))
              return
            }
            if (data.chunk) {
              fullContent += data.chunk
              setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, content: fullContent, thinking: false } : m
              ))
            }
            if (data.done) setConversationId(conversationId || 'default')
          } catch {}
        }
      }
    } catch {
      setMessages(prev => prev.map(m =>
        m.id === assistantId
          ? { ...m, content: '抱歉，发生了错误，请稍后再试。', error: true, thinking: false }
          : m
      ))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="px-6 pb-4 pt-3" style={{ borderTop: `1px solid ${theme.border}` }}>
        <InputBox onSendMessage={handleSendMessage} disabled={loading} />
        <div className="text-center mt-2 text-xs" style={{ color: theme.textFaint }}>
          POWERED BY QWEN-MAX · 深度搜索模式已开启
        </div>
      </div>
    </div>
  )
}
