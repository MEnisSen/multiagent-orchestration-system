import React, { useState, useEffect, useRef } from 'react'

const AgentDiagram = ({ agents, messages, onMessageHover }) => {
  const [hoveredElement, setHoveredElement] = useState(null)
  const [tooltip, setTooltip] = useState({ show: false, content: '', x: 0, y: 0 })
  const [pinnedTooltip, setPinnedTooltip] = useState({ show: false, content: '', x: 0, y: 0, type: null })
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)
  const containerRef = useRef(null)

  // Click-away detection for pinned tooltips
  useEffect(() => {
    const handleClickAway = (event) => {
      if (pinnedTooltip.show && containerRef.current && !containerRef.current.contains(event.target)) {
        setPinnedTooltip({ show: false, content: '', x: 0, y: 0, type: null })
      }
    }

    document.addEventListener('mousedown', handleClickAway)
    return () => {
      document.removeEventListener('mousedown', handleClickAway)
    }
  }, [pinnedTooltip.show])

  // Responsive positions for agents in the diagram (using viewBox coordinates)
  // Layout: Orchestrator at top center, Coder/Tester form triangle below
  const viewBox = { width: 800, height: 600 }
  const agentPositions = {
    orchestrator: { x: viewBox.width * 0.5, y: viewBox.height * 0.25, color: '#3B82F6' }, // Top center
    coder: { x: viewBox.width * 0.25, y: viewBox.height * 0.75, color: '#10B981' },       // Bottom left  
    tester: { x: viewBox.width * 0.75, y: viewBox.height * 0.75, color: '#F59E0B' }       // Bottom right
  }

  // Filter messages to include user messages and agent-to-agent communications
  // Reverse order so newest messages come first (index 0 = latest)
  const agentMessages = messages.filter(message => {
    const from = message.from
    const to = message.to
    
    // Include user messages to agents
    if (from === 'user' && agentPositions[to]) {
      return true
    }
    
    // Include agent-to-agent communications
    return agentPositions[from] && agentPositions[to] && from !== to
  }).reverse()

  // Auto-update current message index to show latest message (now index 0)
  useEffect(() => {
    if (agentMessages.length > 0) {
      // Always show the latest message (index 0) when new messages arrive
      setCurrentMessageIndex(0)
    }
  }, [agentMessages.length])

  // Get current message flow for display
  const getCurrentMessageFlow = () => {
    if (agentMessages.length === 0) return []
    
    const currentMessage = agentMessages[currentMessageIndex]
    if (!currentMessage) return []
    
    return [{
      from: currentMessage.from,
      to: currentMessage.to,
      message: currentMessage,
      opacity: 1.0,
      isActive: true
    }]
  }

  // Navigation functions (reversed: index 0 = latest, higher index = older)
  const goToNewerMessage = () => {
    if (currentMessageIndex > 0) {
      setCurrentMessageIndex(currentMessageIndex - 1)
    }
  }

  const goToOlderMessage = () => {
    if (currentMessageIndex < agentMessages.length - 1) {
      setCurrentMessageIndex(currentMessageIndex + 1)
    }
  }

  const goToLatestMessage = () => {
    if (agentMessages.length > 0) {
      setCurrentMessageIndex(0)  // Index 0 is now the latest message
    }
  }

  const createAgentTooltipContent = (agent) => (
    <div className="space-y-2">
      <div className="font-semibold text-white">{agent.id.toUpperCase()}</div>
      <div className="text-sm text-gray-300">{agent.description}</div>
      <div className="text-xs">
        <div><strong>Model:</strong> {agent.model?.id || 'Unknown'}</div>
        <div><strong>Capabilities:</strong> {agent.capabilities?.join(', ') || 'None'}</div>
        <div><strong>Tools:</strong> {agent.tools?.join(', ') || 'None'}</div>
      </div>
    </div>
  )

  const handleAgentHover = (agent, event) => {
    if (!agent || pinnedTooltip.show) return
    
    const content = createAgentTooltipContent(agent)
    
    // Get coordinates relative to the container
    const containerRect = containerRef.current?.getBoundingClientRect()
    if (!containerRect) return
    
    const relativeX = event.clientX - containerRect.left
    const relativeY = event.clientY - containerRect.top
    
    setTooltip({
      show: true,
      content,
      x: relativeX + 10,
      y: relativeY + 10
    })
  }

  const handleAgentClick = (agent, event) => {
    if (!agent) return
    event.stopPropagation()
    
    const content = createAgentTooltipContent(agent)
    
    // Get coordinates relative to the container
    const containerRect = containerRef.current?.getBoundingClientRect()
    if (!containerRect) return
    
    const relativeX = event.clientX - containerRect.left
    const relativeY = event.clientY - containerRect.top
    
    setPinnedTooltip({
      show: true,
      content,
      x: relativeX + 10,
      y: relativeY + 10,
      type: 'agent'
    })
    
    // Hide hover tooltip when pinning
    setTooltip({ show: false, content: '', x: 0, y: 0 })
  }

  const createMessageTooltipContent = (message) => {
    const truncatedPayload = JSON.stringify(message, null, 2)
      .substring(0, 400) + (JSON.stringify(message).length > 400 ? '...' : '')
    
    return (
      <div className="space-y-2 max-w-md">
        <div className="font-semibold text-white">
          {message.from} → {message.to}
        </div>
        <div className="text-xs text-gray-300">
          Type: {message.type} | Status: {message.status}
        </div>
        <pre className="text-xs bg-gray-900 p-2 rounded text-green-400 overflow-auto max-h-40">
          {truncatedPayload}
        </pre>
      </div>
    )
  }

  const handleMessageHover = (messageFlow, event) => {
    if (!messageFlow || pinnedTooltip.show) return
    
    const { message } = messageFlow
    const content = createMessageTooltipContent(message)
    
    // Get coordinates relative to the container
    const containerRect = containerRef.current?.getBoundingClientRect()
    if (!containerRect) return
    
    const relativeX = event.clientX - containerRect.left
    const relativeY = event.clientY - containerRect.top
    
    setTooltip({
      show: true,
      content,
      x: relativeX + 10,
      y: relativeY + 10
    })
    
    onMessageHover?.(message)
  }

  const handleMessageClick = (messageFlow, event) => {
    if (!messageFlow) return
    event.stopPropagation()
    
    const { message } = messageFlow
    const content = createMessageTooltipContent(message)
    
    // Get coordinates relative to the container
    const containerRect = containerRef.current?.getBoundingClientRect()
    if (!containerRect) return
    
    const relativeX = event.clientX - containerRect.left
    const relativeY = event.clientY - containerRect.top
    
    setPinnedTooltip({
      show: true,
      content,
      x: relativeX + 10,
      y: relativeY + 10,
      type: 'message'
    })
    
    // Hide hover tooltip when pinning
    setTooltip({ show: false, content: '', x: 0, y: 0 })
    
    onMessageHover?.(message)
  }

  const hideTooltip = () => {
    if (!pinnedTooltip.show) {
      setTooltip({ show: false, content: '', x: 0, y: 0 })
    }
  }

  const createArrowPath = (from, to) => {
    const toPos = agentPositions[to]
    
    // Handle user messages (from user to agent)
    if (from === 'user') {
      if (!toPos) return ''
      // Start from top-left corner for user messages
      const userStartX = viewBox.width * 0.05
      const userStartY = viewBox.height * 0.05
      
      const dx = toPos.x - userStartX
      const dy = toPos.y - userStartY
      const distance = Math.sqrt(dx * dx + dy * dy)
      
      // Create curved path from user position
      const midX = (userStartX + toPos.x) / 2 + (dy / distance) * 30
      const midY = (userStartY + toPos.y) / 2 - (dx / distance) * 30
      
      return `M ${userStartX} ${userStartY} Q ${midX} ${midY} ${toPos.x} ${toPos.y}`
    }
    
    // Handle agent-to-agent messages
    const fromPos = agentPositions[from]
    
    if (!fromPos || !toPos) return ''
    
    const dx = toPos.x - fromPos.x
    const dy = toPos.y - fromPos.y
    const distance = Math.sqrt(dx * dx + dy * dy)
    
    // Create a curved path
    const midX = (fromPos.x + toPos.x) / 2 + (dy / distance) * 50
    const midY = (fromPos.y + toPos.y) / 2 - (dx / distance) * 50
    
    return `M ${fromPos.x} ${fromPos.y} Q ${midX} ${midY} ${toPos.x} ${toPos.y}`
  }

  const messageFlows = getCurrentMessageFlow()

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <svg 
        viewBox={`0 0 ${viewBox.width} ${viewBox.height}`}
        className="w-full h-full border rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50"
        preserveAspectRatio="xMidYMid meet"
      >
        
        {/* Arrows for message flows */}
        {messageFlows.map((flow, index) => (
          <g key={`${flow.from}-${flow.to}-${index}`}>
            <path
              d={createArrowPath(flow.from, flow.to)}
              stroke={agentPositions[flow.from]?.color || '#6B7280'}
              strokeWidth="3"
              fill="none"
              opacity={flow.opacity}
              className="message-arrow cursor-pointer"
              onMouseEnter={(e) => handleMessageHover(flow, e)}
              onMouseLeave={hideTooltip}
              onClick={(e) => handleMessageClick(flow, e)}
              markerEnd="url(#arrowhead)"
            />
          </g>
        ))}
        
        {/* Arrow marker definition */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#6B7280"
            />
          </marker>
        </defs>
        
        {/* User icon in top-left corner */}
        <g transform={`translate(${viewBox.width * 0.05}, ${viewBox.height * 0.05})`}>
          <circle
            cx="0"
            cy="0"
            r="20"
            fill="#6366F1"
            opacity="0.2"
            className="animate-pulse"
          />
          <circle
            cx="0"
            cy="0"
            r="15"
            fill="#6366F1"
            className="cursor-pointer"
          />
          <text
            x="0"
            y="5"
            textAnchor="middle"
            className="fill-white text-xs font-semibold pointer-events-none"
          >
            USER
          </text>
        </g>
        
        {/* Agent nodes with tools */}
        {agents.map((agent) => {
          const position = agentPositions[agent.id]
          if (!position) return null
          
          const tools = agent.tools || []
          const toolRadius = 80
          const toolAngleStep = (2 * Math.PI) / Math.max(tools.length, 1)
          
          return (
            <g key={agent.id}>
              {/* Tool indicators around agent */}
              {tools.map((tool, index) => {
                const angle = index * toolAngleStep - Math.PI / 2 // Start from top
                const toolX = position.x + Math.cos(angle) * toolRadius
                const toolY = position.y + Math.sin(angle) * toolRadius
                
                return (
                  <g key={`${agent.id}-tool-${index}`}>
                    {/* Tool connection line */}
                    <line
                      x1={position.x + Math.cos(angle) * 40}
                      y1={position.y + Math.sin(angle) * 40}
                      x2={toolX}
                      y2={toolY}
                      stroke={position.color}
                      strokeWidth="1"
                      opacity="0.3"
                      strokeDasharray="2,2"
                    />
                    
                    {/* Tool circle */}
                    <circle
                      cx={toolX}
                      cy={toolY}
                      r="12"
                      fill={position.color}
                      opacity="0.7"
                      className="cursor-pointer hover:opacity-100 transition-opacity"
                      onMouseEnter={(e) => {
                        if (!pinnedTooltip.show) {
                          const containerRect = containerRef.current?.getBoundingClientRect()
                          if (containerRect) {
                            const relativeX = e.clientX - containerRect.left
                            const relativeY = e.clientY - containerRect.top
                            setTooltip({
                              show: true,
                              content: (
                                <div className="space-y-1">
                                  <div className="font-semibold text-white">{tool}</div>
                                  <div className="text-xs text-gray-300">Tool for {agent.id}</div>
                                </div>
                              ),
                              x: relativeX + 10,
                              y: relativeY + 10
                            })
                          }
                        }
                      }}
                      onMouseLeave={hideTooltip}
                    />
                    
                    {/* Tool icon/text */}
                    <text
                      x={toolX}
                      y={toolY + 2}
                      textAnchor="middle"
                      className="fill-white font-bold text-xs pointer-events-none"
                      fontSize="8"
                    >
                      🔧
                    </text>
                  </g>
                )
              })}
              
              {/* Agent circle with glow effect */}
              <circle
                cx={position.x}
                cy={position.y}
                r="45"
                fill={position.color}
                opacity="0.2"
                className="animate-pulse"
              />
              <circle
                cx={position.x}
                cy={position.y}
                r="35"
                fill={position.color}
                className="cursor-pointer hover:r-40 transition-all duration-200"
                onMouseEnter={(e) => handleAgentHover(agent, e)}
                onMouseLeave={hideTooltip}
                onClick={(e) => handleAgentClick(agent, e)}
              />
              
              {/* Agent label */}
              <text
                x={position.x}
                y={position.y + 5}
                textAnchor="middle"
                className="fill-white font-semibold text-sm pointer-events-none"
              >
                {agent.id.toUpperCase()}
              </text>
              
              {/* Status indicator */}
              <circle
                cx={position.x + 30}
                cy={position.y - 30}
                r="8"
                fill="#10B981"
                className="animate-pulse"
              />
              
              {/* Tool count indicator */}
              {tools.length > 0 && (
                <g>
                  <circle
                    cx={position.x - 30}
                    cy={position.y - 30}
                    r="10"
                    fill="#6366F1"
                    opacity="0.8"
                  />
                  <text
                    x={position.x - 30}
                    y={position.y - 26}
                    textAnchor="middle"
                    className="fill-white font-bold text-xs pointer-events-none"
                  >
                    {tools.length}
                  </text>
                </g>
              )}
            </g>
          )
        })}
        
        {/* Legend */}
        
      </svg>
      
      {/* Hover Tooltip */}
      {tooltip.show && (
        <div 
          className="absolute pointer-events-none bg-gray-800 text-white p-3 rounded-lg shadow-xl border border-gray-600 max-w-sm"
          style={{ 
            left: `${tooltip.x}px`, 
            top: `${tooltip.y}px`,
            zIndex: 1000
          }}
        >
          {tooltip.content}
        </div>
      )}

      {/* Pinned Tooltip */}
      {pinnedTooltip.show && (
        <div 
          className="absolute bg-gray-900 text-white p-4 rounded-lg shadow-2xl border-2 border-blue-400 max-w-sm"
          style={{ 
            left: `${pinnedTooltip.x}px`, 
            top: `${pinnedTooltip.y}px`,
            zIndex: 1001
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-blue-400 text-xs font-semibold">
              📌 PINNED {pinnedTooltip.type?.toUpperCase()}
            </span>
            <button
              onClick={() => setPinnedTooltip({ show: false, content: '', x: 0, y: 0, type: null })}
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>
          {pinnedTooltip.content}
        </div>
      )}

      {/* Navigation Controls */}
      <div className="flex items-center justify-center mt-4 space-x-4 bg-white rounded-lg p-3 shadow-md border">
        <button
          onClick={goToNewerMessage}
          disabled={currentMessageIndex <= 0}
          className={`flex items-center px-3 py-2 rounded-lg transition-all ${
            currentMessageIndex <= 0 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
          }`}
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Newer
        </button>

        <div className="flex items-center space-x-2 bg-gray-50 px-4 py-2 rounded-lg">
          <span className="text-sm text-gray-600">Communication:</span>
          <span className="font-semibold text-gray-800">
            {agentMessages.length === 0 ? '0' : currentMessageIndex + 1}
          </span>
          <span className="text-sm text-gray-600">of</span>
          <span className="font-semibold text-gray-800">{agentMessages.length}</span>
        </div>

        <button
          onClick={goToOlderMessage}
          disabled={currentMessageIndex >= agentMessages.length - 1}
          className={`flex items-center px-3 py-2 rounded-lg transition-all ${
            currentMessageIndex >= agentMessages.length - 1
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
          }`}
        >
          Older
          <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        <button
          onClick={goToLatestMessage}
          disabled={currentMessageIndex <= 0}
          className={`flex items-center px-2 py-2 rounded-lg transition-all ${
            currentMessageIndex <= 0
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-green-500 hover:bg-green-600 text-white shadow-md hover:shadow-lg'
          }`}
          title="Go to latest communication"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Current Message Info */}
      {agentMessages.length > 0 && (
        <div className="mt-3 bg-gray-50 rounded-lg p-3 border">
          <div className="flex items-center justify-between text-sm">
            <div className="font-medium text-gray-700">
              {agentMessages[currentMessageIndex]?.from?.toUpperCase()} → {agentMessages[currentMessageIndex]?.to?.toUpperCase()}
            </div>
            <div className="text-gray-500">
              {agentMessages[currentMessageIndex]?.type} | {new Date(agentMessages[currentMessageIndex]?.timestamp).toLocaleTimeString()}
            </div>
          </div>
          <div className="mt-1 text-xs text-gray-600">
            {agentMessages[currentMessageIndex]?.payload?.goal || 'Agent communication'}
          </div>
        </div>
      )}
    </div>
  )
}

export default AgentDiagram
