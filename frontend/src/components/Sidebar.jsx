import { useTheme } from '../ThemeContext'

const DIALECTS = ['普通话', '闽南语', '东北话', '陕西话']

export default function Sidebar() {
  const { theme } = useTheme()

  return (
    <aside
      className="shrink-0 flex flex-col items-center py-8 px-4 gap-4"
      style={{ width: '30%', background: theme.panel, borderRight: `1px solid ${theme.border}` }}
    >
      {/* 数字人矩形框 */}
      <div
        className="flex items-center justify-center rounded-2xl"
        style={{
          width: '85%',
          height: '420px',
          background: theme.avatarBg,
          border: `1px solid ${theme.avatarBorder}`
        }}
      >
        <svg width="100" height="120" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="8" r="4" fill="#4a90d9" />
          <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" fill="#4a90d9" />
        </svg>
      </div>

      {/* 在线标签 */}
      <div
        className="px-3 py-0.5 rounded-full text-xs font-medium"
        style={{ background: theme.tagBg, color: theme.tagColor, border: `1px solid ${theme.tagBorder}` }}
      >
        小智在线
      </div>

      {/* 名称 */}
      <div className="text-center">
        <div className="font-bold text-lg" style={{ color: theme.text }}>你好，我是小智</div>
        <div className="text-xs mt-1 leading-relaxed" style={{ color: theme.textMuted }}>
          我可以为您提供深度搜索、方言朗读以及智能问答服务。
        </div>
      </div>

      {/* 方言标签 */}
      <div className="flex flex-wrap gap-2 justify-center mt-1">
        {DIALECTS.map(d => (
          <button
            key={d}
            className="px-3 py-1 rounded-full text-xs transition-colors"
            style={{ background: theme.dialectBg, color: theme.dialectColor, border: `1px solid ${theme.dialectBorder}` }}
            onMouseEnter={e => {
              e.currentTarget.style.background = '#1d6fe8'
              e.currentTarget.style.color = '#fff'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = theme.dialectBg
              e.currentTarget.style.color = theme.dialectColor
            }}
          >
            {d}
          </button>
        ))}
      </div>
    </aside>
  )
}
