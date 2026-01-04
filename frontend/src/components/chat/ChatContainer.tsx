import { useState, useEffect, useCallback, useRef } from 'react'
import { useAuth } from '@clerk/clerk-react'
import ChatWindow from './ChatWindow'
import ChatInput from './ChatInput'
import { chatService } from '@/services'
import type { ChatMessage } from '@/types'

interface ChatContainerProps {
  sessionId: string
  onProgressUpdate?: (data: {
    current_day: number
    current_topic_index: number
    is_day_complete: boolean
    is_course_complete: boolean
  }) => void
}

export default function ChatContainer({ sessionId, onProgressUpdate }: ChatContainerProps) {
  const { getToken } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const streamingContentRef = useRef('')

  // Load chat history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await chatService.getChatHistory(sessionId)
        setMessages(history.messages)
      } catch (error) {
        console.error('Failed to load chat history:', error)
      } finally {
        setIsLoadingHistory(false)
      }
    }

    loadHistory()
  }, [sessionId])

  // Send message with streaming
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return

      // Add user message
      const userMessage: ChatMessage = {
        role: 'human',
        content: content.trim(),
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])

      // Start streaming
      setIsStreaming(true)
      streamingContentRef.current = ''

      // Add placeholder for assistant message
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '', timestamp: new Date().toISOString() },
      ])

      try {
        await chatService.sendMessageStream(
          { session_id: sessionId, message: content.trim() },
          // onToken
          (token) => {
            streamingContentRef.current += token
            setMessages((prev) => {
              const updated = [...prev]
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: streamingContentRef.current,
              }
              return updated
            })
          },
          // onDone
          (metadata) => {
            setIsStreaming(false)
            if (onProgressUpdate) {
              onProgressUpdate(metadata)
            }
          },
          // onError
          (error) => {
            console.error('Chat stream error:', error)
            setIsStreaming(false)
            setMessages((prev) => {
              const updated = [...prev]
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: 'Sorry, something went wrong. Please try again.',
              }
              return updated
            })
          },
          // getToken
          getToken
        )
      } catch (error) {
        console.error('Chat error:', error)
        setIsStreaming(false)
      }
    },
    [sessionId, isStreaming, getToken, onProgressUpdate]
  )

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200 overflow-hidden">
      <ChatWindow
        messages={messages}
        isLoading={isLoadingHistory}
        isStreaming={isStreaming}
      />
      <ChatInput
        onSend={sendMessage}
        isDisabled={isStreaming}
        placeholder="Ask a question or type 'continue' to proceed..."
      />
    </div>
  )
}
