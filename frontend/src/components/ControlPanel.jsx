import React, { useState } from 'react'

const ControlPanel = ({ onAction, isLoading, workflowStatus = 'idle' }) => {
  const [lastAction, setLastAction] = useState('')

  const getButtonsForStatus = (status) => {
    switch (status) {
      case 'idle':
        return []
      case 'planning':
        return []
      case 'coding':
        return [
          {
            id: 'next-task',
            label: 'Next Task (Debug)',
            description: 'Manual override - tasks now auto-progress',
            color: 'bg-gray-500 hover:bg-gray-600',
            icon: '🔧'
          }
        ]
      case 'testing':
        return [
          {
            id: 'test',
            label: 'Run Tests',
            description: 'Validate completed code',
            color: 'bg-amber-500 hover:bg-amber-600',
            icon: '🧪'
          }
        ]
      case 'completed':
        return [
          {
            id: 'reset-workflow',
            label: 'New Project',
            description: 'Start a new workflow',
            color: 'bg-blue-500 hover:bg-blue-600',
            icon: '🔄'
          }
        ]
      default:
        return []
    }
  }

  const buttons = getButtonsForStatus(workflowStatus)

  const handleAction = async (actionId) => {
    setLastAction(actionId)
    await onAction(actionId)
  }

  const handleReset = async () => {
    setLastAction('reset')
    await onAction('reset')
  }

  const handleFullCycle = async () => {
    setLastAction('full-cycle')
    await onAction('demo/full-cycle')
  }

  return (
    <div className="space-y-4">
      
      {/* Main action buttons */}
      <div className="grid grid-cols-2 gap-3">
        {buttons.map((button) => (
          <button
            key={button.id}
            onClick={() => handleAction(button.id)}
            disabled={isLoading}
            className={`
              control-button text-white text-sm flex flex-col items-center p-3
              ${button.color} 
              ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
              ${lastAction === button.id ? 'ring-2 ring-offset-2 ring-blue-400' : ''}
            `}
          >
            <span className="text-lg mb-1">{button.icon}</span>
            <span className="font-semibold">{button.label}</span>
            <span className="text-xs opacity-80 text-center leading-tight">
              {button.description}
            </span>
          </button>
        ))}
      </div>

      {/* Separator */}
      <div className="border-t border-gray-200 my-4"></div>

      {/* Additional controls */}
      <div className="space-y-2">
        
        {/* Full cycle button */}
        <button
          onClick={handleFullCycle}
          disabled={isLoading}
          className={`
            w-full control-button bg-gradient-to-r from-blue-500 to-purple-600 
            hover:from-blue-600 hover:to-purple-700 text-white text-sm
            ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
            ${lastAction === 'full-cycle' ? 'ring-2 ring-offset-2 ring-blue-400' : ''}
          `}
        >
          <div className="flex items-center justify-center space-x-2">
            <span>🚀</span>
            <span className="font-semibold">Run Full Demo Cycle</span>
          </div>
          <div className="text-xs opacity-80 mt-1">
            Plan → Generate → Test → Auto-Fix
          </div>
        </button>

        {/* Reset button */}
        <button
          onClick={handleReset}
          disabled={isLoading}
          className={`
            w-full control-button bg-gray-500 hover:bg-gray-600 text-white text-sm
            ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
            ${lastAction === 'reset' ? 'ring-2 ring-offset-2 ring-blue-400' : ''}
          `}
        >
          <div className="flex items-center justify-center space-x-2">
            <span>🔄</span>
            <span className="font-semibold">Reset System</span>
          </div>
          <div className="text-xs opacity-80 mt-1">
            Clear messages & re-index RAG
          </div>
        </button>
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="flex items-center justify-center space-x-2 py-2">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
          <span className="text-sm text-gray-600">Processing...</span>
        </div>
      )}

      {/* Last action indicator */}
      {lastAction && !isLoading && (
        <div className="text-center py-2">
          <span className="text-xs text-gray-500">
            Last action: <span className="font-semibold">{lastAction}</span>
          </span>
        </div>
      )}

      {/* Workflow Status and Instructions */}
      <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
        <div className="font-semibold mb-2 flex items-center">
          🔄 Workflow Status: 
          <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
            workflowStatus === 'idle' ? 'bg-gray-200 text-gray-700' :
            workflowStatus === 'planning' ? 'bg-blue-100 text-blue-700' :
            workflowStatus === 'coding' ? 'bg-green-100 text-green-700' :
            workflowStatus === 'testing' ? 'bg-amber-100 text-amber-700' :
            workflowStatus === 'completed' ? 'bg-purple-100 text-purple-700' :
            'bg-gray-200 text-gray-700'
          }`}>
            {workflowStatus === 'idle' ? 'Ready' :
             workflowStatus === 'planning' ? 'Planning Tasks' :
             workflowStatus === 'coding' ? 'Coding' :
             workflowStatus === 'testing' ? 'Testing' :
             workflowStatus === 'completed' ? 'Completed' :
             workflowStatus.charAt(0).toUpperCase() + workflowStatus.slice(1)
            }
          </span>
        </div>

        {workflowStatus === 'idle' && (
          <div className="text-xs">
            <div className="font-medium mb-1">📝 How to start:</div>
            <ol className="list-decimal list-inside space-y-1">
              <li>Enter your project description above</li>
              <li>Click "Start Agent Workflow"</li>
              <li>Watch agents break down and execute tasks</li>
            </ol>
          </div>
        )}

        {workflowStatus === 'planning' && (
          <div className="text-xs text-blue-700">
            🤖 Orchestrator is analyzing your prompt and creating a task breakdown...
          </div>
        )}

        {workflowStatus === 'coding' && (
          <div className="text-xs text-green-700">
            ⚡ Tasks auto-progress automatically. "Next Task (Debug)" is for manual override only.
          </div>
        )}

        {workflowStatus === 'testing' && (
          <div className="text-xs text-amber-700">
            🧪 Ready for testing phase. Click "Run Tests" to validate the implemented code.
          </div>
        )}

        {workflowStatus === 'completed' && (
          <div className="text-xs text-purple-700">
            ✅ Workflow completed! Review the results and start a new project when ready.
          </div>
        )}
      </div>

    </div>
  )
}

export default ControlPanel
