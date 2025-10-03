import React, { useState, useRef } from 'react'

const HeroPrompt = ({ onSubmitPrompt, isLoading, isSubmitted = false, submittedPrompt = '', submittedDocuments = [] }) => {
  const [prompt, setPrompt] = useState('')
  const [uploadedDocuments, setUploadedDocuments] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef(null)

  const handleSubmit = async (e) => {
    e?.preventDefault?.()
    if (!prompt.trim() || isLoading || isUploading) return
    await onSubmitPrompt(prompt.trim(), uploadedDocuments)
    setUploadedDocuments([])
    setPrompt('')
  }

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return

    setIsUploading(true)
    try {
      const formData = new FormData()
      files.forEach((file) => formData.append('files', file))
      const response = await fetch('http://localhost:8000/upload-documents', {
        method: 'POST',
        body: formData
      })
      const result = await response.json()
      if (result.status === 'success') {
        setUploadedDocuments((prev) => [...prev, ...result.documents])
      } else {
        alert(`Error uploading documents: ${result.message}`)
      }
    } catch (error) {
      alert(`Error uploading documents: ${error.message}`)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const removeDocument = (index) => {
    setUploadedDocuments((prev) => prev.filter((_, i) => i !== index))
  }

  const getDocName = (doc, index) => {
    return (doc && (doc.name || doc.filename || doc.original_name || doc.path || doc.title)) || `Document ${index + 1}`
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (isLoading || isUploading)) {
      e.preventDefault()
    }
  }

  return (
    <div className="w-full flex flex-col items-center">
      {!isSubmitted && (
        <div className="text-center mb-4">
          <h1 className="text-3xl font-semibold text-gray-800">How can I help?</h1>
        </div>
      )}

      {!isSubmitted ? (
      <form onSubmit={handleSubmit} className="w-full max-w-3xl">
        <div className="relative flex items-stretch w-full">
          {/* Upload Button (left circle) */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.txt,.md,.rtf,.png,.jpg,.jpeg,.gif,.bmp,.tiff,.html,.htm,.xml"
            className="hidden"
            onChange={handleFileUpload}
            disabled={isLoading || isUploading}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || isUploading}
            className={`flex items-center justify-center aspect-square rounded-full mr-3 transition-all h-14 ${
              isLoading || isUploading
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gray-900 text-white hover:opacity-90'
            }`}
            title="Attach documents"
          >
            {isUploading ? '…' : '📎'}
          </button>

          {/* Prompt input */}
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask for a feature, tool, or change..."
            disabled={isLoading || isUploading}
            className="flex-1 h-14 px-5 rounded-full border border-gray-300 focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900 placeholder-gray-400"
          />

          {/* Send Button (right circle) */}
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading || isUploading}
            className={`flex items-center justify-center aspect-square rounded-full ml-3 h-14 transition-all ${
              !prompt.trim() || isLoading || isUploading
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gray-900 text-white hover:opacity-90'
            }`}
            title={isUploading ? "Please wait for file processing to complete" : "Send"}
          >
            {isLoading || isUploading ? '…' : (
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M3.27 6.96L19.2 3.05c1.66-.4 3.08 1.02 2.68 2.68l-3.91 15.93c-.37 1.51-2.3 1.95-3.25.69l-3.57-4.67a1 1 0 0 1 .18-1.4l5.02-4.02a.25.25 0 0 0-.29-.4l-6.35 2.64a1 1 0 0 1-1.23-.4L2.58 9.58c-.77-1.15-.2-2.7 1.13-3.03z"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  fill="currentColor"
                  fillOpacity="0.15"
                />
              </svg>
            )}
          </button>
        </div>

        {/* Attached documents preview */}
        {uploadedDocuments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {uploadedDocuments.map((doc, index) => (
              <div key={index} className="flex items-center gap-2 px-3 py-1 rounded-full border border-gray-300 bg-white shadow-sm">
                <span className="text-sm">📄 Doc {index + 1}</span>
                <button
                  type="button"
                  onClick={() => removeDocument(index)}
                  className="text-gray-400 hover:text-gray-600"
                  disabled={isLoading}
                  aria-label="Remove document"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </form>
      ) : (
        <div className="w-full max-w-3xl">
          <div className="flex items-center">
            {/* Documents on the left of the prompt display */}
            {submittedDocuments.length > 0 && (
              <div className="mr-3 flex flex-wrap gap-2 max-w-[40%] items-center">
                {submittedDocuments.map((doc, index) => (
                  <div key={index} className="relative group">
                    <div className="w-10 h-10 rounded-full border border-gray-300 bg-white shadow-sm flex items-center justify-center">
                      <span aria-hidden="true">📄</span>
                    </div>
                    <div className="absolute left-1/2 -translate-x-1/2 top-full mt-1 px-2 py-1 bg-gray-900 text-white text-xs rounded shadow opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none z-10">
                      {getDocName(doc, index)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Prompt echo on the right */}
            <div className="flex-1 h-14 px-5 rounded-full border border-gray-300 bg-gray-50 text-gray-800 flex items-center">
              <span className="truncate" title={submittedPrompt}>{submittedPrompt}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default HeroPrompt


