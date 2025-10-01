import React from 'react'

const StatusBar = ({ status }) => {
  const getSystemStatusColor = (systemStatus) => {
    switch (systemStatus) {
      case 'healthy':
        return 'bg-green-500'
      case 'active':
        return 'bg-blue-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getSystemStatusText = (systemStatus) => {
    switch (systemStatus) {
      case 'healthy':
        return 'All systems operational'
      case 'active':
        return 'Agents are processing'
      case 'warning':
        return 'Some issues detected'
      case 'error':
        return 'System errors present'
      default:
        return 'Status unknown'
    }
  }

  if (!status || Object.keys(status).length === 0) {
    return (
      <div className="bg-gray-100 rounded-lg p-3 mt-4">
        <div className="flex items-center justify-center space-x-2">
          <div className="status-indicator bg-gray-400"></div>
          <span className="text-sm text-gray-600">Loading system status...</span>
        </div>
      </div>
    )
  }

  const systemColor = getSystemStatusColor(status.system)
  const systemText = getSystemStatusText(status.system)
  const hasErrors = status.messages?.recent_errors > 0

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 mt-4">
      
      {/* Main system status */}
      <div className="flex items-center justify-center space-x-3 mb-4">
        <div className={`status-indicator ${systemColor} animate-pulse`}></div>
        <span className="text-sm font-medium text-gray-700">{systemText}</span>
        {hasErrors && (
          <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
            {status.messages.recent_errors} errors
          </span>
        )}
      </div>

      {/* Detailed status grid */}
      <div className="grid grid-cols-3 gap-4 text-center text-xs">
        
        {/* Agents */}
        <div className="space-y-1">
          <div className="font-medium text-gray-600">Agents</div>
          <div className="flex items-center justify-center space-x-1">
            <div className="status-indicator bg-green-500"></div>
            <span>{status.agents?.active || 0}/{status.agents?.total || 0}</span>
          </div>
          <div className="text-gray-500">Active</div>
        </div>

        {/* RAG System */}
        <div className="space-y-1">
          <div className="font-medium text-gray-600">Knowledge</div>
          <div className="flex items-center justify-center space-x-1">
            <div className={`status-indicator ${status.rag?.indexed ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
            <span>{status.rag?.nodes || 0} nodes</span>
          </div>
          <div className="text-gray-500">Indexed</div>
        </div>

        {/* Messages */}
        <div className="space-y-1">
          <div className="font-medium text-gray-600">Messages</div>
          <div className="flex items-center justify-center space-x-1">
            <div className={`status-indicator ${hasErrors ? 'bg-red-500' : 'bg-green-500'}`}></div>
            <span>{status.messages?.total || 0}</span>
          </div>
          <div className="text-gray-500">Total</div>
        </div>

      </div>

      {/* Additional info */}
      {status.rag && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex justify-center space-x-6 text-xs text-gray-500">
            <span>RAG Edges: {status.rag.edges || 0}</span>
            <span>Graph: {status.rag.indexed ? 'Ready' : 'Building'}</span>
          </div>
        </div>
      )}


    </div>
  )
}

export default StatusBar
