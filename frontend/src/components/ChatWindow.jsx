import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import MessageBubble from './MessageBubble'
import InputBox from './InputBox'

export default function ChatWindow() {
  const [messages, setMessages] = useState([
    { id: 1, type: 'assistant', content: '你好！我是小智数码助手。有什么我可以帮助你的吗？' }
  ])
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (message) => {
    if (!message.trim()) return

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: message
    }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    try {
      // Create assistant message placeholder
      const assistantMessageId = messages.length + 2
      const assistantMessage = {
        id: assistantMessageId,
        type: 'assistant',
        content: ''
      }
      setMessages(prev => [...prev, assistantMessage])

      // Call streaming API
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          conversation_id: conversationId
        })
      })

      if (!response.ok) {
        throw new Error('Stream request failed')
      }

      // Read stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.error) {
                console.error('Stream error:', data.error)
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: `错误: ${data.error}`, error: true }
                      : msg
                  )
                )
                break
              }
              
              if (data.chunk) {
                fullContent += data.chunk
                // Update message content in real-time
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: fullContent }
                      : msg
                  )
                )
              }
              
              if (data.done) {
                setConversationId(conversationId || 'default')
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: messages.length + 2,
        type: 'assistant',
        content: '抱歉，发生了错误。请稍后再试。',
        error: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setMessages([
      { id: 1, type: 'assistant', content: '你好！我是小智数码助手。有什么我可以帮助你的吗？' }
    ])
    setConversationId(null)
  }

  return (
    <div className="flex flex-col h-full max-w-6xl mx-auto">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {loading && (
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Container */}
      <div className="border-t bg-white p-4">
        <InputBox
          onSendMessage={handleSendMessage}
          onClear={handleClear}
          disabled={loading}
        />
      </div>
    </div>
  )
}
