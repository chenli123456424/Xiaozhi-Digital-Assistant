import { createContext, useContext, useState, useRef } from 'react'

export const SpeakingContext = createContext()

export function SpeakingProvider({ children }) {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [speakingMessageId, setSpeakingMessageId] = useState(null)  // 当前朗读的消息 id
  const [ttsLang, setTtsLang] = useState('zh')
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const audioRef = useRef(null)
  const audioObjRef = useRef(null)

  const stopAudio = () => {
    if (audioObjRef.current) {
      audioObjRef.current.pause()
      audioObjRef.current.currentTime = 0
      audioObjRef.current = null
    }
    setIsSpeaking(false)
    setSpeakingMessageId(null)
  }

  return (
    <SpeakingContext.Provider value={{
      isSpeaking, setIsSpeaking,
      speakingMessageId, setSpeakingMessageId,
      ttsLang, setTtsLang,
      ttsEnabled, setTtsEnabled,
      audioRef, audioObjRef,
      stopAudio,
    }}>
      {children}
      <audio ref={audioRef} style={{ display: 'none' }} />
    </SpeakingContext.Provider>
  )
}

export const useSpeaking = () => useContext(SpeakingContext)
