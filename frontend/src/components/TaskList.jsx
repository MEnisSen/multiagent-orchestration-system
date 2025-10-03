import React from 'react'

// If embedded=true, render without the outer panel container so a parent panel can control layout/height
const TaskList = ({ tasks, currentTaskIndex, embedded = false }) => {
  const getTaskStatus = (index) => {
    if (index < currentTaskIndex) return 'completed'
    if (index === currentTaskIndex) return 'in_progress'
    return 'pending'
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅'
      case 'in_progress': return '⚙️'
      case 'pending': return '⏳'
      default: return '❓'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200'
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200 animate-pulse'
      case 'pending': return 'bg-gray-100 text-gray-600 border-gray-200'
      default: return 'bg-gray-100 text-gray-600 border-gray-200'
    }
  }

  if (!tasks || tasks.length === 0) {
    return (
      <div className={`${embedded ? '' : 'bg-white rounded-2xl shadow-lg p-6'}`}>
        {!embedded && (
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">📋 Task List</h2>
        )}
        <div className="text-center py-8 text-gray-500">
          <div className="text-3xl mb-2">📝</div>
          <div className="text-sm">No tasks yet</div>
          <div className="text-xs text-gray-400 mt-1">Submit a prompt to generate tasks</div>
        </div>
      </div>
    )
  }

  const completedTasks = tasks.filter((_, index) => getTaskStatus(index) === 'completed').length
  const totalTasks = tasks.length
  const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0

  return (
    <div className={`${embedded ? '' : 'bg-white rounded-2xl shadow-lg p-6'}`}>
      {!embedded && (
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800 flex items-center">📋 Task List</h2>
          <span className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded-full">{completedTasks}/{totalTasks}</span>
        </div>
      )}

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-600">Progress</span>
          <span className="text-xs text-gray-600">{Math.round(progressPercentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Task list */}
      <div className="space-y-3 max-h-full overflow-y-auto">
        {tasks.map((task, index) => {
          const status = getTaskStatus(index)
          const statusIcon = getStatusIcon(status)
          const statusColor = getStatusColor(status)

          return (
            <div
              key={index}
              className={`p-3 rounded-lg border ${statusColor} transition-all duration-200`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-0.5">
                  <span className="text-lg">{statusIcon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-medium truncate">
                      Task {index + 1}
                    </h3>
                    <span className="text-xs font-medium capitalize">
                      {status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 break-words">
                    {task.description || task.task || task}
                  </p>
                  {task.file && (
                    <div className="mt-1 text-xs text-blue-600 font-mono">
                      📄 {task.file}
                    </div>
                  )}
                  {status === 'completed' && task.completedAt && (
                    <div className="mt-1 text-xs text-green-600">
                      ✓ Completed at {new Date(task.completedAt).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Current task indicator */}
      {currentTaskIndex < totalTasks && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm font-medium text-blue-800 mb-1">
            🔄 Currently Working On:
          </div>
          <div className="text-xs text-blue-700">
            Task {currentTaskIndex + 1}: {tasks[currentTaskIndex]?.description || tasks[currentTaskIndex]?.task || tasks[currentTaskIndex]}
          </div>
        </div>
      )}

      {/* Completion indicator */}
      {completedTasks === totalTasks && totalTasks > 0 && (
        <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
          <div className="text-sm font-medium text-green-800 mb-1">
            🎉 All Tasks Completed!
          </div>
          <div className="text-xs text-green-700">
            Ready for testing phase
          </div>
        </div>
      )}
    </div>
  )
}

export default TaskList
