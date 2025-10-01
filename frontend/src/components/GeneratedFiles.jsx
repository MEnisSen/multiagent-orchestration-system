import React, { useState } from 'react'

const GeneratedFiles = ({ files }) => {
  const [selectedFile, setSelectedFile] = useState(null)

  const handleFileClick = (file) => {
    setSelectedFile(file)
  }

  const getFileIcon = (fileType) => {
    const icons = {
      python: '🐍',
      javascript: '📜',
      typescript: '📘',
      json: '📋',
      markdown: '📝',
      text: '📄'
    }
    return icons[fileType] || '📄'
  }

  const getFileTypeColor = (fileType) => {
    const colors = {
      python: 'bg-green-100 text-green-800 border-green-200',
      javascript: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      typescript: 'bg-blue-100 text-blue-800 border-blue-200',
      json: 'bg-purple-100 text-purple-800 border-purple-200',
      markdown: 'bg-gray-100 text-gray-800 border-gray-200',
      text: 'bg-gray-100 text-gray-800 border-gray-200'
    }
    return colors[fileType] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (!files || files.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">
          📁 Generated Files
        </h2>
        <div className="text-center py-8">
          <div className="text-6xl mb-4">📄</div>
          <p className="text-gray-500 text-lg">No files generated yet</p>
          <p className="text-gray-400 text-sm mt-2">Files will appear here when the agents create them</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        📁 Generated Files ({files.length})
      </h2>
      
      {/* Side-by-side layout */}
      <div className="flex gap-6 h-96">
        
        {/* File List Panel - Left Side */}
        <div className="w-1/3 border-r border-gray-200 pr-4">
          <h3 className="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">
            Files ({files.length})
          </h3>
          <div className="space-y-2 max-h-full overflow-y-auto">
            {files.map((file, index) => (
              <div
                key={`${file.path}-${index}`}
                className={`p-3 rounded-lg border transition-all duration-200 cursor-pointer hover:shadow-sm ${
                  selectedFile?.path === file.path 
                    ? 'border-blue-400 bg-blue-50 shadow-md' 
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => handleFileClick(file)}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-xl">{getFileIcon(file.type)}</span>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-gray-800 truncate">{file.name}</h4>
                    <div className="flex items-center justify-between mt-1">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium border ${getFileTypeColor(file.type)}`}>
                        {file.type}
                      </span>
                      <span className="text-xs text-gray-500">{formatFileSize(file.size)}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* File Content Viewer - Right Side */}
        <div className="w-2/3 flex flex-col">
          {selectedFile ? (
            <>
              {/* File Header */}
              <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg border">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getFileIcon(selectedFile.type)}</span>
                  <div>
                    <h3 className="font-semibold text-gray-800">{selectedFile.name}</h3>
                    <p className="text-sm text-gray-500">{selectedFile.path}</p>
                  </div>
                </div>
                <div className="text-right text-sm text-gray-500">
                  <div>{selectedFile.lines} lines</div>
                  <div>{formatDate(selectedFile.modified)}</div>
                </div>
              </div>

              {/* File Content */}
              <div className="flex-1 bg-gray-900 rounded-lg p-4 overflow-auto">
                <pre className="text-sm font-mono text-green-400 whitespace-pre-wrap">
                  {selectedFile.content}
                </pre>
              </div>
            </>
          ) : (
            /* No File Selected */
            <div className="flex-1 flex items-center justify-center text-center border-2 border-dashed border-gray-300 rounded-lg">
              <div>
                <div className="text-4xl mb-4">👈</div>
                <p className="text-gray-500 text-lg">Select a file to view its contents</p>
                <p className="text-gray-400 text-sm mt-2">Click on any file from the list to see its code</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default GeneratedFiles
