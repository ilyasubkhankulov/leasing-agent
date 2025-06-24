'use client'

import { useState, useRef, useEffect } from 'react'

interface Lead {
  name: string
  email: string
}

interface Preferences {
  bedrooms: number
  move_in: string
}

interface Message {
  id: string
  content: string
  sender: 'user' | 'agent'
  timestamp: Date
  isStreaming?: boolean
}

interface StreamEvent {
  type: string
  data: any
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [lead] = useState<Lead>({
    name: 'Sarah Johnson',
    email: 'sarah.johnson@email.com'
  })
  const [preferences] = useState<Preferences>({
    bedrooms: 2,
    move_in: '2025-02-01'
  })
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const currentStreamingMessageRef = useRef<string>('')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: currentMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setCurrentMessage('')
    setIsLoading(true)

    const agentMessageId = (Date.now() + 1).toString()
    const agentMessage: Message = {
      id: agentMessageId,
      content: '',
      sender: 'agent',
      timestamp: new Date(),
      isStreaming: true
    }

    setMessages(prev => [...prev, agentMessage])
    currentStreamingMessageRef.current = ''

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/reply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lead,
          message: currentMessage,
          preferences,
          community_id: 'community_123'
        })
      })

      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6)) as StreamEvent
              
              if (eventData.type === 'content_delta') {
                currentStreamingMessageRef.current += eventData.data.content
                
                setMessages(prev => prev.map(msg => 
                  msg.id === agentMessageId 
                    ? { ...msg, content: currentStreamingMessageRef.current }
                    : msg
                ))
              } else if (eventData.type === 'action_determined') {
                console.log('Action determined:', eventData.data)
              } else if (eventData.type === 'response_complete') {
                setMessages(prev => prev.map(msg => 
                  msg.id === agentMessageId 
                    ? { ...msg, content: eventData.data.reply, isStreaming: false }
                    : msg
                ))
                console.log('Response complete:', eventData.data)
              } else if (eventData.type === 'error') {
                console.error('Stream error:', eventData.data.error)
                setMessages(prev => prev.map(msg => 
                  msg.id === agentMessageId 
                    ? { ...msg, content: 'Sorry, there was an error processing your request.', isStreaming: false }
                    : msg
                ))
              }
            } catch (error) {
              console.error('Error parsing event data:', error)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === agentMessageId 
          ? { ...msg, content: 'Sorry, there was an error connecting to the server.', isStreaming: false }
          : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white">
      <div className="bg-blue-600 text-white p-4">
        <h1 className="text-xl font-semibold">Leasing Agent Chat</h1>
        <p className="text-blue-100 text-sm">
          Chatting as {lead.name} • Looking for {preferences.bedrooms}-bedroom • Move-in: {preferences.move_in}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              {message.isStreaming && (
                <div className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></div>
              )}
              <p className="text-xs mt-1 opacity-70">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t p-4">
        <div className="flex space-x-2">
          <textarea
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!currentMessage.trim() || isLoading}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}
