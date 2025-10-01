import React, { useState } from 'react'

const UserPromptInput = ({ onSubmitPrompt, isLoading }) => {
  const [prompt, setPrompt] = useState('')
  const [examples] = useState([
    "Create a basic calculator with 4 main operations + - / x"
  ])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (prompt.trim()) {
      await onSubmitPrompt(prompt.trim())
      setPrompt('')
    }
  }

  const handleExampleClick = (example) => {
    setPrompt(example)
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        🎯 Project Prompt
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
            Describe what you want the agents to build:
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., Create a calculator with basic math operations, error handling, and unit tests..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={4}
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={!prompt.trim() || isLoading}
          className={`w-full py-3 px-4 rounded-lg font-semibold transition-all duration-200 ${
            !prompt.trim() || isLoading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
          }`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              <span>Processing...</span>
            </div>
          ) : (
            '🚀 Start Agent Workflow'
          )}
        </button>
      </form>

      {/* Example prompts */}
      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">💡 Example prompts:</h3>
        <div className="space-y-2">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              className="w-full text-left p-3 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
              disabled={isLoading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="text-xs text-blue-700">
          <div className="font-medium mb-1">🤖 How it works:</div>
          <ol className="list-decimal list-inside space-y-1 text-xs">
            <li>Enter your project description above</li>
            <li>Orchestrator breaks it into tasks</li>
            <li>Coder implements each task sequentially</li>
            <li>Tester validates the final code</li>
          </ol>
        </div>
      </div>
    </div>
  )
}

export default UserPromptInput
