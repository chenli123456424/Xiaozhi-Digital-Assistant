import { useTheme } from '../ThemeContext'

export default function MessageBubble({ message }) {
  const { theme } = useTheme()
  const isUser = message.type === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-xs md:max-w-md px-4 py-2.5 rounded-2xl rounded-br-sm text-sm leading-relaxed"
          style={{ background: theme.userBubble, color: '#fff' }}
        >
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-xl w-full">
        {message.thinking && (
          <div className="flex items-center gap-1.5 mb-2 text-xs" style={{ color: theme.textMuted }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            深度思考过程
          </div>
        )}
        <div
          className="px-4 py-3 rounded-2xl rounded-bl-sm text-sm leading-relaxed"
          style={{
            background: message.error ? (theme.card === '#ffffff' ? '#fff0f0' : '#2d1b1b') : theme.card,
            color: message.error ? '#f85149' : theme.text,
            border: `1px solid ${message.error ? '#f8514940' : theme.border}`,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}
        >
          {message.content || (
            <span className="flex items-center gap-2" style={{ color: theme.textMuted }}>
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </span>
              思考中...
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
