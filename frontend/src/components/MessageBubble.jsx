export default function MessageBubble({ message }) {
  const isUser = message.type === 'user'

  // 处理换行符：将 \n 字符串转换为真正的换行
  const formatContent = (content) => {
    if (typeof content !== 'string') return content
    return content.split('\n').map((line, index) => (
      <div key={index}>{line}</div>
    ))
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-3 rounded-lg ${
          isUser
            ? 'bg-blue-500 text-white rounded-br-none'
            : 'bg-gray-200 text-gray-900 rounded-bl-none'
        } ${message.error ? 'bg-red-200 text-red-900' : ''}`}
        style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
      >
        <div className="text-base leading-relaxed">
          {formatContent(message.content)}
        </div>
      </div>
    </div>
  )
}
