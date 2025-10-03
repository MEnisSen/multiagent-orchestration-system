import React, { useState } from 'react'

const FilesBar = ({ files = [] }) => {
  const [hoveredFile, setHoveredFile] = useState(null)
  const [pinnedFile, setPinnedFile] = useState(null)

  const fileToPreview = pinnedFile || hoveredFile

  const getFileIcon = (fileType) => {
    const icons = { python: '🐍', javascript: '📜', typescript: '📘', json: '📋', markdown: '📝', text: '📄' }
    return icons[fileType] || '📄'
  }

  if (!files || files.length === 0) return null

  return (
    <div
      className="w-full"
      onMouseLeave={() => {
        if (!pinnedFile) setHoveredFile(null)
      }}
    >
      {/* Bar (no background) */}
      <div className="flex gap-2 items-center">
        {files.map((file, i) => (
          <button
            key={`${file.path}-${i}`}
            className={`px-3 py-1 rounded-full border text-sm transition-colors ${
              pinnedFile?.path === file.path
                ? 'border-gray-900 text-gray-900'
                : 'border-gray-300 text-gray-700 hover:border-gray-400'
            }`}
            onMouseEnter={() => setHoveredFile(file)}
            onClick={() => setPinnedFile(pinnedFile?.path === file.path ? null : file)}
            title={file.path}
          >
            <span className="mr-2">{getFileIcon(file.type)}</span>
            {file.name}
          </button>
        ))}
      </div>

      {/* Overlay Preview (fixed, does not affect layout) */}
      {fileToPreview && (
        <div
          className="fixed left-1/2 bottom-24 -translate-x-1/2 z-50 w-[min(92vw,1000px)] max-h-[60vh] border rounded-xl shadow-2xl overflow-hidden bg-white"
          onMouseEnter={() => setHoveredFile(fileToPreview)}
          onMouseLeave={() => {
            if (!pinnedFile) setHoveredFile(null)
          }}
        >
          <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b">
            <div className="flex items-center gap-2">
              <span>{getFileIcon(fileToPreview.type)}</span>
              <div className="text-sm font-medium text-gray-800">{fileToPreview.name}</div>
              <div className="text-xs text-gray-500">{fileToPreview.path}</div>
            </div>
            {pinnedFile && (
              <button
                className="text-xs text-gray-500 hover:text-gray-700"
                onClick={() => setPinnedFile(null)}
              >
                ✕ Close
              </button>
            )}
          </div>
          <div className="max-h-[60vh] overflow-auto bg-gray-900">
            <pre className="text-green-400 text-xs p-4 whitespace-pre-wrap">{fileToPreview.content}</pre>
          </div>

          {/* Notch pointer */}
          <svg className="absolute left-1/2 bottom-[-10px] -translate-x-1/2" width="24" height="10" viewBox="0 0 24 10" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M0 0 C8 10, 16 10, 24 0" stroke="#E5E7EB" fill="#FFFFFF" />
          </svg>
        </div>
      )}
    </div>
  )
}

export default FilesBar


