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
  // Layout: Orchestrator at top center, User same height left, Database agent right of orchestrator, Coder/Tester bottom
  const viewBox = { width: 1000, height: 650 }
  const agentPositions = {
    orchestrator: { x: viewBox.width * 0.5, y: viewBox.height * 0.25, color: '#3B82F6' }, // Top center
    database: { x: viewBox.width * 0.86, y: viewBox.height * 0.25, color: '#8B5CF6' },    // Moved further right
    coder: { x: viewBox.width * 0.25, y: viewBox.height * 0.75, color: '#10B981' },       // Bottom left  
    tester: { x: viewBox.width * 0.75, y: viewBox.height * 0.75, color: '#F59E0B' }       // Bottom right
  }

  // Position for the external DATABASE node (target of DB agent operations)
  const dbNodePos = { x: viewBox.width * 0.86, y: viewBox.height * 0.42 }
  // Position for USER node (kept in sync with the rendered USER group)
  const userNodePos = { x: viewBox.width * 0.14, y: viewBox.height * 0.25 }

  // Filter messages to include user messages, agent-to-agent communications, and tool calls
  // Keep chronological order: index 0 = earliest, last index = latest
  const agentMessages = messages.filter(message => {
    const from = message.from
    const to = message.to
    
    // Include user messages to agents
    if (from === 'user' && agentPositions[to]) {
      return true
    }
    
    // Include explicit tool calls (from agent to tool name)
    if (message.type === 'tool_call') return !!agentPositions[from]
    
    // Include agent-to-agent communications
    return agentPositions[from] && agentPositions[to] && from !== to
  })

  // Auto-set to the first (earliest) message when new messages arrive
  useEffect(() => {
    if (agentMessages.length > 0) {
      setCurrentMessageIndex(0)
    }
  }, [agentMessages.length])

  // Get current message flow for display
  const getCurrentMessageFlow = () => {
    if (agentMessages.length === 0) return []
    
    const currentMessage = agentMessages[currentMessageIndex]
    if (!currentMessage) return []
    
    // For tool calls: highlight the specific tool circle and suppress arrow
    if (currentMessage.type === 'tool_call') {
      // Special case: Database agent tool calls also draw a highlight edge to the DATABASE node
      if (currentMessage.from === 'database') {
        return [{
          from: 'database',
          to: '__db__',
          message: currentMessage,
          opacity: 1,
          isActive: true,
          isToolCall: true,
          isDbEdge: true
        }]
      }
      return [{
        from: currentMessage.from,
        to: currentMessage.to,
        message: currentMessage,
        opacity: 0,
        isActive: true,
        isToolCall: true
      }]
    }
    
    return [{ from: currentMessage.from, to: currentMessage.to, message: currentMessage, opacity: 1.0, isActive: true }]
  }

  // Active tool-call context for highlighting
  const activeToolCall = (() => {
    if (agentMessages.length === 0) return null
    const m = agentMessages[currentMessageIndex]
    if (m && m.type === 'tool_call') {
      return { agentId: m.from, toolName: m.to }
    }
    return null
  })()

  // Navigation functions (chronological: index 0 = earliest -> increasing index = newer)
  const goToNewerMessage = () => {
    if (currentMessageIndex < agentMessages.length - 1) {
      setCurrentMessageIndex(currentMessageIndex + 1)
    }
  }

  const goToOlderMessage = () => {
    if (currentMessageIndex > 0) {
      setCurrentMessageIndex(currentMessageIndex - 1)
    }
  }

  const goToLatestMessage = () => {
    if (agentMessages.length > 0) {
      setCurrentMessageIndex(agentMessages.length - 1)
    }
  }

  const goToFirstMessage = () => {
    if (agentMessages.length > 0) {
      setCurrentMessageIndex(0)
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
    const toPos = to === '__db__' ? dbNodePos : agentPositions[to]
    
    // Handle user messages (from user to agent)
    if (from === 'user') {
      if (!toPos) return ''
      // Start from actual USER node position
      const userStartX = userNodePos.x
      const userStartY = userNodePos.y
      
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
        
        {/* Arrows for message flows (hidden for tool calls) */}
        {messageFlows.map((flow, index) => (
          <g key={`${flow.from}-${flow.to}-${index}`}>
            {!flow.isToolCall && (
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
            )}
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
        
        {/* User node (same size and height as orchestrator) */}
        <g transform={`translate(${viewBox.width * 0.14}, ${viewBox.height * 0.25})`}>
          <circle cx="0" cy="0" r="45" fill="#6366F1" opacity="0.2" className="animate-pulse" />
          <circle cx="0" cy="0" r="35" fill="#6366F1" />
          <text x="0" y="5" textAnchor="middle" className="fill-white font-semibold text-sm pointer-events-none">USER</text>
        </g>

        {/* DATABASE external node */}
        <g transform={`translate(${dbNodePos.x}, ${dbNodePos.y})`}>
          <rect x="-35" y="-18" rx="6" ry="6" width="70" height="36" fill="#312E81" opacity="0.9" />
          <text x="0" y="4" textAnchor="middle" className="fill-white font-semibold text-xs pointer-events-none">DATABASE</text>
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
                const isActiveTool = !!(activeToolCall && activeToolCall.agentId === agent.id && activeToolCall.toolName === tool)
                
                return (
                  <g key={`${agent.id}-tool-${index}`}>
                    {/* Tool connection line */}
                    <line
                      x1={position.x + Math.cos(angle) * 40}
                      y1={position.y + Math.sin(angle) * 40}
                      x2={toolX}
                      y2={toolY}
                      stroke={position.color}
                      strokeWidth={isActiveTool ? 3 : 1}
                      opacity={isActiveTool ? 0.95 : 0.3}
                      strokeDasharray={isActiveTool ? undefined : "2,2"}
                    />
                    
                    {/* Tool circle */}
                    <circle
                      cx={toolX}
                      cy={toolY}
                      r="12"
                      fill={position.color}
                      opacity={isActiveTool ? 1 : 0.7}
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

                    {/* Active highlight ring for tool call */}
                    {isActiveTool && (
                      <circle
                        cx={toolX}
                        cy={toolY}
                        r="16"
                        fill="none"
                        stroke={position.color}
                        strokeWidth="3"
                        opacity="0.9"
                        className="animate-pulse"
                      />
                    )}
                    
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

      {/* Navigation Controls - overlay at bottom of diagram */}
      <div className="absolute left-1/2 -translate-x-1/2 bottom-4 z-10 flex items-center justify-center space-x-4 bg-white/90 backdrop-blur rounded-lg p-3 shadow-md border">
        <button
          onClick={goToFirstMessage}
          disabled={currentMessageIndex <= 0}
          className={`flex items-center px-2 py-2 rounded-lg transition-all ${
            currentMessageIndex <= 0
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-green-500 hover:bg-green-600 text-white shadow-md hover:shadow-lg'
          }`}
          title="Go to first communication"
        >
          &laquo;
        </button>
        <button
          onClick={goToOlderMessage}
          disabled={currentMessageIndex <= 0}
          className={`flex items-center px-3 py-2 rounded-lg transition-all ${
            currentMessageIndex <= 0 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
          }`}
        >
          &lt;
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
          onClick={goToNewerMessage}
          disabled={currentMessageIndex >= agentMessages.length - 1}
          className={`flex items-center px-3 py-2 rounded-lg transition-all ${
            currentMessageIndex >= agentMessages.length - 1
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
          }`}
        >
          &gt;
        </button>

        <button
          onClick={goToLatestMessage}
          disabled={currentMessageIndex >= agentMessages.length - 1}
          className={`flex items-center px-2 py-2 rounded-lg transition-all ${
            currentMessageIndex >= agentMessages.length - 1
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-green-500 hover:bg-green-600 text-white shadow-md hover:shadow-lg'
          }`}
          title="Go to latest communication"
        >
          &raquo;
        </button>
      </div>

      {/* Current Message Info removed per design */}
    </div>
  )
}

export default AgentDiagram
