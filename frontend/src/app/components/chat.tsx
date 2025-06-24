'use client'

import { useState, useRef, useEffect } from 'react'

interface Lead {
  name: string
  email: string
  phone?: string
}

interface Preferences {
  bedrooms: number
  move_in: string
}

interface Community {
  id: string
  name: string
  address: string
  phone?: string
  email?: string
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
  const [isSetupComplete, setIsSetupComplete] = useState(false)
  const [communities, setCommunities] = useState<Community[]>([])
  const [loadingCommunities, setLoadingCommunities] = useState(true)
  
  const [leadName, setLeadName] = useState('')
  const [leadEmail, setLeadEmail] = useState('')
  const [leadPhone, setLeadPhone] = useState('')
  const [leadId, setLeadId] = useState('')
  const [conversationId, setConversationId] = useState('')
  
  const [selectedCommunityId, setSelectedCommunityId] = useState('')
  const [bedrooms, setBedrooms] = useState(1)
  const [moveInDate, setMoveInDate] = useState('')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const currentStreamingMessageRef = useRef<string>('')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    fetchCommunities()
    
    const defaultDate = new Date()
    defaultDate.setDate(defaultDate.getDate() + 30)
    setMoveInDate(defaultDate.toISOString().split('T')[0])
  }, [])

  const fetchCommunities = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/communities`)
      if (response.ok) {
        const data = await response.json()
        setCommunities(data)
        if (data.length > 0) {
          setSelectedCommunityId(data[0].id)
        }
      }
    } catch (error) {
      console.error('Error fetching communities:', error)
    } finally {
      setLoadingCommunities(false)
    }
  }

  const startChat = async () => {
    if (!selectedCommunityId || !moveInDate || !leadName.trim() || !leadEmail.trim()) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lead: {
            name: leadName,
            email: leadEmail,
            phone: leadPhone || null
          },
          preferences: {
            bedrooms,
            move_in: moveInDate
          },
          community_id: selectedCommunityId
        })
      })

      if (response.ok) {
        const data = await response.json()
        setLeadId(data.lead_id)
        setConversationId(data.conversation_id)
        
        const welcomeMessage: Message = {
          id: Date.now().toString(),
          content: data.message,
          sender: 'agent',
          timestamp: new Date()
        }
        setMessages([welcomeMessage])
        setIsSetupComplete(true)
      } else {
        console.error('Error starting chat:', response.statusText)
      }
    } catch (error) {
      console.error('Error starting chat:', error)
    }
  }

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
          lead_id: leadId,
          conversation_id: conversationId,
          message: currentMessage
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

  const selectedCommunity = communities.find(c => c.id === selectedCommunityId)

  if (!isSetupComplete) {
    return (
      <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white">
        <div className="bg-blue-600 text-white p-4">
          <h1 className="text-xl font-semibold">Leasing Agent Chat</h1>
          <p className="text-blue-100 text-sm">Fill out your information to start chatting</p>
        </div>

        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-md space-y-6">
            <h2 className="text-2xl font-bold text-center text-gray-800">Get Started</h2>
            
            {loadingCommunities ? (
              <div className="text-center text-gray-600">Loading communities...</div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Name *
                  </label>
                  <input
                    type="text"
                    value={leadName}
                    onChange={(e) => setLeadName(e.target.value)}
                    placeholder="Enter your full name"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    value={leadEmail}
                    onChange={(e) => setLeadEmail(e.target.value)}
                    placeholder="Enter your email address"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number (Optional)
                  </label>
                  <input
                    type="tel"
                    value={leadPhone}
                    onChange={(e) => setLeadPhone(e.target.value)}
                    placeholder="Enter your phone number"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Community *
                  </label>
                  <select
                    value={selectedCommunityId}
                    onChange={(e) => setSelectedCommunityId(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {communities.map((community) => (
                      <option key={community.id} value={community.id}>
                        {community.name}
                      </option>
                    ))}
                  </select>
                  {selectedCommunity && (
                    <p className="text-sm text-gray-600 mt-1">{selectedCommunity.address}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Bedrooms *
                  </label>
                  <select
                    value={bedrooms}
                    onChange={(e) => setBedrooms(parseInt(e.target.value))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={1}>1 Bedroom</option>
                    <option value={2}>2 Bedrooms</option>
                    <option value={3}>3 Bedrooms</option>
                    <option value={4}>4+ Bedrooms</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preferred Move-in Date *
                  </label>
                  <input
                    type="date"
                    value={moveInDate}
                    onChange={(e) => setMoveInDate(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  onClick={startChat}
                  disabled={!selectedCommunityId || !moveInDate || !leadName.trim() || !leadEmail.trim()}
                  className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
                >
                  Start Chat
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white">
      <div className="bg-blue-600 text-white p-4">
        <h1 className="text-xl font-semibold">Leasing Agent Chat</h1>
        <p className="text-blue-100 text-sm">
          Chatting as {leadName} • {selectedCommunity?.name} • {bedrooms}-bedroom • Move-in: {moveInDate}
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
