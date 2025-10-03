import React, { useState } from 'react'

const MessageLog = ({ messages, allMessages = [], onMessageClick, pausePolling = false, onTogglePause }) => {
  const [expandedMessage, setExpandedMessage] = useState(null)
  const [showAll, setShowAll] = useState(false)

  const getMessageTypeColor = (type) => {
    const colors = {
      plan: 'bg-blue-100 text-blue-800',
      request: 'bg-green-100 text-green-800',
      response: 'bg-purple-100 text-purple-800',
      error: 'bg-red-100 text-red-800',
      test_report: 'bg-amber-100 text-amber-800',
      patch: 'bg-indigo-100 text-indigo-800',
      broadcast: 'bg-gray-100 text-gray-800',
      tool_call: 'bg-teal-100 text-teal-800'
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const getStatusIcon = (status) => {
    const icons = {
      ok: '✅',
      warn: '⚠️',
      fail: '❌'
    }
    return icons[status] || '❓'
  }

  const getAgentColor = (agentId) => {
    const colors = {
      orchestrator: 'text-blue-600',
      coder: 'text-green-600',
      tester: 'text-amber-600',
      user: 'text-purple-600'
    }
    return colors[agentId] || 'text-gray-600'
  }

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString()
    } catch {
      return timestamp
    }
  }

  const truncatePayload = (payload, maxLength = 100) => {
    const str = JSON.stringify(payload)
    return str.length > maxLength ? str.substring(0, maxLength) + '...' : str
  }

  const toggleExpanded = (messageId) => {
    setExpandedMessage(expandedMessage === messageId ? null : messageId)
  }

  const displayMessages = showAll ? allMessages : messages
  const hasMoreMessages = allMessages.length > messages.length

  return (
    <div className="space-y-4">
      {/* Controls Header */}
      <div className="flex justify-between items-center pb-3 border-b border-gray-200">
        <span className="text-sm text-gray-600">
          {hasMoreMessages ? `Showing ${displayMessages.length} of ${allMessages.length} messages` : `${displayMessages.length} messages`}
        </span>
        <div className="flex space-x-2">
          {hasMoreMessages && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
            >
              {showAll ? 'Show Recent' : 'Show All'}
            </button>
          )}
        </div>
      </div>
      
      {/* Vertical scrolling compact list */}
      {displayMessages.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-4">💬</div>
          <div className="text-lg">No messages yet</div>
          <div className="text-sm text-gray-400 mt-2">Trigger an action to see agent communication</div>
        </div>
      ) : (
        <div className="max-h-full overflow-y-auto" style={{ scrollbarWidth: 'thin' }}>
          <ul className="space-y-2">
            {displayMessages.map((message, index) => {
              const contentStr = typeof message.content === 'string' ? message.content : (message.payload?.goal || message.payload?.result || '')
              return (
                <li key={message.id || index} className="px-3 py-2 rounded-md border border-gray-200 bg-white">
                  <div className="flex items-center text-xs">
                    <span className={`font-semibold mr-2 ${getAgentColor(message.from)}`}>{message.from}</span>
                    <span className="mx-1 text-gray-400">→</span>
                    <span className={`font-semibold mr-2 ${message.type === 'tool_call' ? 'text-teal-600' : getAgentColor(message.to)}`}>{message.to}</span>
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-[10px] ${getMessageTypeColor(message.type)}`}>{message.type}</span>
                    <span className="ml-auto text-[10px] text-gray-400 whitespace-nowrap">{formatTimestamp(message.timestamp)}</span>
                  </div>
                  <div 
                    className="mt-1 text-[11px] text-gray-700 truncate cursor-pointer relative group"
                    title={contentStr}
                  >
                    {contentStr}
                    {/* Hover preview tooltip */}
                    <div className="absolute bottom-full left-0 mb-2 w-80 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
                      <div className="whitespace-pre-wrap break-words">{contentStr}</div>
                      {/* Arrow pointing down */}
                      <div className="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {/* Message count info */}
      {!showAll && hasMoreMessages && (
        <div className="text-center py-3 border-t border-gray-100">
          <span className="text-sm text-gray-500">
            Showing latest {messages.length} messages • {allMessages.length - messages.length} more available
          </span>
        </div>
      )}

    </div>
  )
}

export default MessageLog
