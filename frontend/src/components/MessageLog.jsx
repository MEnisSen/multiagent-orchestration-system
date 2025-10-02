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
          {onTogglePause && (
            <button
              onClick={onTogglePause}
              className={`text-sm px-3 py-1 rounded-lg transition-colors ${
                pausePolling 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'bg-orange-100 text-orange-700 hover:bg-orange-200'
              }`}
            >
              {pausePolling ? '▶️ Resume' : '⏸️ Pause'}
            </button>
          )}
        </div>
      </div>
      
      {/* Horizontal Scrolling Message Cards */}
      {displayMessages.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-4">💬</div>
          <div className="text-lg">No messages yet</div>
          <div className="text-sm text-gray-400 mt-2">
            Trigger an action to see agent communication
          </div>
        </div>
      ) : (
        <div className="relative">
          {/* Scroll container */}
          <div className="flex gap-4 overflow-x-auto pb-4 min-h-[280px]" style={{ scrollbarWidth: 'thin' }}>
            {displayMessages.map((message, index) => (
              <div
                key={message.id || index}
                className="flex-shrink-0 w-80 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:shadow-md"
                onClick={() => {
                  toggleExpanded(message.id)
                  onMessageClick?.(message.id)
                }}
              >
                <div className="p-4 h-full flex flex-col">
                  
                  {/* Message header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                        {message.id?.substring(0, 8) || 'unknown'}
                      </span>
                      <span className="text-xs">{getStatusIcon(message.status)}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>

                  {/* Agent communication flow */}
                  <div className="flex items-center justify-center mb-3 p-2 bg-gray-50 rounded-lg">
                    <span className={`text-sm font-semibold ${getAgentColor(message.from)}`}>
                      {message.from}
                    </span>
                    <span className="mx-2 text-gray-400">→</span>
                    <span className={`text-sm font-semibold ${message.type === 'tool_call' ? 'text-teal-600' : getAgentColor(message.to)}`}>
                      {message.to}
                    </span>
                  </div>

                  {/* Message type */}
                  <div className="mb-3 text-center">
                    <span className={`text-sm px-3 py-1 rounded-full font-medium ${getMessageTypeColor(message.type)}`}>
                      {message.type}
                    </span>
                  </div>

                  {/* Tools used */}
                  {message.tools_used && message.tools_used.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs font-medium text-gray-600 mb-1">Tools Used:</div>
                      <div className="flex flex-wrap gap-1">
                        {message.tools_used.slice(0, 3).map((tool, i) => (
                          <span key={i} className={`text-xs px-2 py-1 rounded ${message.type === 'tool_call' ? 'bg-teal-50 text-teal-700' : 'bg-blue-50 text-blue-600'}`}>
                            🔧 {tool}
                          </span>
                        ))}
                        {message.tools_used.length > 3 && (
                          <span className="text-xs text-gray-500 px-2 py-1">
                            +{message.tools_used.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Capabilities used (fallback) */}
                  {message.capabilities_used && message.capabilities_used.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs font-medium text-gray-600 mb-1">Capabilities:</div>
                      <div className="flex flex-wrap gap-1">
                        {message.capabilities_used.slice(0, 3).map((cap, i) => (
                          <span key={i} className="text-xs bg-green-50 text-green-600 px-2 py-1 rounded">
                            ⚡ {cap}
                          </span>
                        ))}
                        {message.capabilities_used.length > 3 && (
                          <span className="text-xs text-gray-500 px-2 py-1">
                            +{message.capabilities_used.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Content preview */}
                  <div className="flex-1 text-xs text-gray-600 space-y-2">
                    {message.content && (
                      <div className="p-2 bg-gray-50 rounded">
                        <span className="font-medium text-gray-800">Content:</span>
                        <div className="mt-1 text-gray-700 break-words">
                          {typeof message.content === 'string' 
                            ? message.content.substring(0, 150) + (message.content.length > 150 ? '...' : '')
                            : JSON.stringify(message.content).substring(0, 150) + '...'
                          }
                        </div>
                      </div>
                    )}
                    {message.payload?.goal && (
                      <div className="p-2 bg-blue-50 rounded">
                        <span className="font-medium text-blue-800">Goal:</span>
                        <div className="mt-1 text-blue-700">{message.payload.goal}</div>
                      </div>
                    )}
                    {message.payload?.result && (
                      <div className="p-2 bg-green-50 rounded">
                        <span className="font-medium text-green-800">Result:</span>
                        <div className="mt-1 text-green-700">{message.payload.result}</div>
                      </div>
                    )}
                    {message.payload?.error && (
                      <div className="p-2 bg-red-50 rounded">
                        <span className="font-medium text-red-800">Error:</span>
                        <div className="mt-1 text-red-700">{message.payload.error}</div>
                      </div>
                    )}
                    {message.function_name && (
                      <div className="p-2 bg-purple-50 rounded">
                        <span className="font-medium text-purple-800">Function:</span>
                        <div className="mt-1 text-purple-700 font-mono">{message.function_name}</div>
                      </div>
                    )}
                  </div>

                  {/* Model info */}
                  {message.model && (
                    <div className="mt-3 pt-2 border-t border-gray-100 text-xs text-gray-500">
                      <div className="font-medium">Model: {message.model.id}</div>
                      {message.model.params && (
                        <div className="mt-1">
                          Temp: {message.model.params.temperature} • 
                          Tokens: {message.model.params.max_new_tokens}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Click hint */}
                  <div className="text-xs text-gray-400 mt-3 text-center py-1 border-t border-gray-100">
                    {expandedMessage === message.id ? 'Click to collapse' : 'Click for full JSON'}
                  </div>

                </div>

                {/* Expanded view overlay */}
                {expandedMessage === message.id && (
                  <div className="absolute inset-0 bg-white border border-gray-300 rounded-lg shadow-lg z-10 overflow-auto">
                    <div className="p-4">
                      <div className="flex justify-between items-center mb-3">
                        <div className="text-sm font-medium text-gray-700">Full Message JSON</div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setExpandedMessage(null)
                          }}
                          className="text-gray-400 hover:text-gray-600 text-lg"
                        >
                          ✕
                        </button>
                      </div>
                      <pre className="json-block text-xs overflow-auto max-h-64">
                        {JSON.stringify(message, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

              </div>
            ))}
          </div>

          {/* Scroll indicator */}
          {displayMessages.length > 3 && (
            <div className="text-center mt-2">
              <span className="text-xs text-gray-400">
                ← Scroll horizontally to see all messages →
              </span>
            </div>
          )}
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
