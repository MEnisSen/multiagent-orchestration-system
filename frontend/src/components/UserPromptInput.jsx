import React, { useState, useRef } from 'react'

const UserPromptInput = ({ onSubmitPrompt, isLoading }) => {
  const [prompt, setPrompt] = useState('')
  const [uploadedDocuments, setUploadedDocuments] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef(null)
  const [examples] = useState([
    "Create a basic calculator with 4 main operations + - / x"
  ])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (prompt.trim() && !isUploading) {
      await onSubmitPrompt(prompt.trim(), uploadedDocuments)
      setPrompt('')
      setUploadedDocuments([])
    }
  }

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    setIsUploading(true)
    try {
      const formData = new FormData()
      files.forEach(file => {
        formData.append('files', file)
      })

      const response = await fetch('http://localhost:8000/upload-documents', {
        method: 'POST',
        body: formData
      })

      const result = await response.json()
      
      if (result.status === 'success') {
        setUploadedDocuments(prev => [...prev, ...result.documents])
      } else {
        alert(`Error uploading documents: ${result.message}`)
      }
    } catch (error) {
      alert(`Error uploading documents: ${error.message}`)
    } finally {
      setIsUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const removeDocument = (index) => {
    setUploadedDocuments(prev => prev.filter((_, i) => i !== index))
  }

  const handleExampleClick = (example) => {
    setPrompt(example)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (isLoading || isUploading)) {
      e.preventDefault()
    }
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
            onKeyDown={handleKeyDown}
            placeholder="e.g., Create a calculator with basic math operations, error handling, and unit tests..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={4}
            disabled={isLoading || isUploading}
          />
        </div>

        {/* Document Upload Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📎 Attach Documents (Optional)
          </label>
          <div className="space-y-3">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.txt,.md,.rtf,.png,.jpg,.jpeg,.gif,.bmp,.tiff,.html,.htm,.xml"
              onChange={handleFileUpload}
              className="hidden"
              disabled={isLoading || isUploading}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || isUploading}
              className={`w-full py-2 px-4 rounded-lg border-2 border-dashed transition-all ${
                isLoading || isUploading
                  ? 'border-gray-300 text-gray-400 cursor-not-allowed'
                  : 'border-blue-300 text-blue-600 hover:border-blue-400 hover:bg-blue-50'
              }`}
            >
              {isUploading ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                  <span>Processing documents...</span>
                </div>
              ) : (
                '📎 Choose Documents to Upload'
              )}
            </button>
            
            {/* Display uploaded documents */}
            {uploadedDocuments.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-700">Uploaded Documents:</div>
                {uploadedDocuments.map((doc, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">📄</span>
                      <span className="text-sm text-green-800">Document {index + 1}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeDocument(index)}
                      className="text-red-500 hover:text-red-700 text-sm"
                      disabled={isLoading || isUploading}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={!prompt.trim() || isLoading || isUploading}
          className={`w-full py-3 px-4 rounded-lg font-semibold transition-all duration-200 ${
            !prompt.trim() || isLoading || isUploading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
          }`}
          title={isUploading ? "Please wait for file processing to complete" : ""}
        >
          {isLoading || isUploading ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              <span>{isUploading ? 'Processing files...' : 'Processing...'}</span>
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
              disabled={isLoading || isUploading}
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
