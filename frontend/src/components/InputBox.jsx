import { useState } from 'react'

export default function InputBox({ onSendMessage, onClear, disabled }) {
  const [input, setInput] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSendMessage(input)
      setInput('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !disabled) {
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="输入你的问题..."
        disabled={disabled}
        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-gray-100"
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors"
      >
        发送
      </button>
      <button
        type="button"
        onClick={onClear}
        disabled={disabled}
        className="px-4 py-2 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 disabled:bg-gray-100 transition-colors"
      >
        清空
      </button>
    </form>
  )
}
