import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { Button, Textarea } from '@/components/ui'

interface ChatInputProps {
  onSend: (message: string) => void
  isDisabled?: boolean
  placeholder?: string
}

export default function ChatInput({
  onSend,
  isDisabled = false,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isDisabled) {
      onSend(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-end gap-2 p-4 bg-white border-t border-gray-200">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isDisabled}
          rows={1}
          className="min-h-[44px] max-h-[150px] resize-none py-3 pr-12"
        />
        <Button
          type="submit"
          size="md"
          disabled={!message.trim() || isDisabled}
          className="flex-shrink-0 h-11 w-11 p-0"
        >
          <Send className="w-5 h-5" />
        </Button>
      </div>
    </form>
  )
}
