export default function Header({ onToggleTheme }) {
  return (
    <header className="bg-gradient-to-r from-primary to-secondary text-white shadow-lg">
      <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="text-2xl">🤖</div>
          <div>
            <h1 className="text-xl font-bold">小智数码助手</h1>
            <p className="text-blue-100 text-sm">Xiaozhi Digital Assistant</p>
          </div>
        </div>
        <button
          onClick={onToggleTheme}
          className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-colors"
        >
          🌙
        </button>
      </div>
    </header>
  )
}
