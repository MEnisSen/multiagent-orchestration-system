import React, { useState, useEffect } from 'react'
import AgentDiagram from './components/AgentDiagram'
import MessageLog from './components/MessageLog'
import TaskList from './components/TaskList'
import HeroPrompt from './components/HeroPrompt'
import FilesBar from './components/FilesBar'

const API_BASE = 'http://localhost:8000'

function App() {
  const [agents, setAgents] = useState([])
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState({})
  const [pausePolling, setPausePolling] = useState(false)
  const [tasks, setTasks] = useState([])
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0)
  const [workflowStatus, setWorkflowStatus] = useState('idle') // idle, planning, coding, testing, completed
  const [generatedFiles, setGeneratedFiles] = useState([])
  const [isUpdating, setIsUpdating] = useState(false)
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const [submittedPrompt, setSubmittedPrompt] = useState('')
  const [submittedDocuments, setSubmittedDocuments] = useState([])
  const [topBarActive, setTopBarActive] = useState(false)

  // Fetch agents on component mount and ensure they're always visible
  useEffect(() => {
    // Set default agents immediately to ensure visualization is never empty
    setDefaultAgents()
    // Then try to fetch live data
    fetchAgents()
    fetchSystemStatus()
  }, [])

  // Poll periodically for updates (reduce frequency to lower backend load)
  useEffect(() => {
    const interval = setInterval(async () => {
      if (!pausePolling) {
        setIsUpdating(true)
        try {
          await Promise.all([
            fetchMessages(),
            fetchTasks(),
            fetchGeneratedFiles()
          ])
        } finally {
          setTimeout(() => setIsUpdating(false), 250)
        }
      }
    }, 1500)

    return () => clearInterval(interval)
  }, [pausePolling])

  // Activate top bar visuals with a slight delay after submit
  useEffect(() => {
    if (hasSubmitted) {
      const timer = setTimeout(() => setTopBarActive(true), 350)
      return () => clearTimeout(timer)
    } else {
      setTopBarActive(false)
    }
  }, [hasSubmitted])

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/agents`)
      const data = await response.json()
      if (data.status === 'success') {
        setAgents(data.agents)
      } else {
        // Fallback to default agents if fetch fails
        setDefaultAgents()
      }
    } catch (error) {
      console.error('Error fetching agents:', error)
      // Fallback to default agents if fetch fails
      setDefaultAgents()
    }
  }

  const setDefaultAgents = () => {
    const defaultAgents = [
      {
        id: "orchestrator",
        capabilities: ["coordinate_workflow", "parse_requests", "manage_tasks", "finalize_functions"],
        model: {
          provider: "openai",
          id: "gpt-4o-mini"
        },
        tools: ["read_file", "list_directory", "finalize_function", "create_task_list", "transfer_to_coder_agent", "transfer_to_tester_agent", "transfer_to_database_agent", "transfer_to_research_agent"],
        description: "Manages the entire coding workflow and coordinates between other agents"
      },
      {
        id: "coder", 
        capabilities: ["implement_functions", "fix_code", "write_documentation"],
        model: {
          provider: "openai",
          id: "gpt-4o-mini"
        },
        tools: ["create_function", "fix_function", "transfer_to_orchestrator_agent"],
        description: "Implements functions and fixes code issues based on specifications"
      },
      {
        id: "tester",
        capabilities: ["write_tests", "run_tests", "setup_environment", "analyze_failures"],
        model: {
          provider: "openai", 
          id: "gpt-4o-mini"
        },
        tools: ["setup_test_environment", "write_unit_tests", "run_unit_tests", "transfer_to_orchestrator_agent"],
        description: "Writes comprehensive unit tests and validates code functionality"
      },
      {
        id: "research",
        capabilities: ["web_search", "gather_information", "research"],
        model: {
          provider: "openai",
          id: "gpt-4o-mini"
        },
        tools: ["web_search", "transfer_to_orchestrator_agent"],
        description: "Searches the web and gathers current information from online sources"
      },
      {
        id: "database",
        capabilities: ["update_knowledge_graph", "retrieve_from_graph"],
        model: {
          provider: "openai",
          id: "gpt-4o-mini"
        },
        tools: ["kg_updater", "kg_retriever", "transfer_to_orchestrator_agent"],
        description: "Manages Neo4j knowledge graph updates and retrievals"
      }
    ]
    setAgents(defaultAgents)
  }

  const fetchMessages = async () => {
    try {
      const response = await fetch(`${API_BASE}/messages?limit=100`)  // Increased limit for better history
      const data = await response.json()
      if (data.status === 'success') {
        const newMessages = data.messages
        
        // Only update if we have new messages or if the count has changed
        if (newMessages.length !== messages.length || 
            (newMessages.length > 0 && messages.length > 0 && 
             newMessages[0].id !== messages[0].id)) {
          setMessages(newMessages)
        }
      }
    } catch (error) {
      console.error('Error fetching messages:', error)
    }
  }

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/status`)
      const data = await response.json()
      if (data.status === 'success') {
        setSystemStatus(data.system_status)
      }
    } catch (error) {
      console.error('Error fetching system status:', error)
    }
  }

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/tasks`)
      const data = await response.json()
      if (data.status === 'success') {
        const newTasks = data.tasks || []
        const newCurrentTaskIndex = data.currentTaskIndex || 0
        const newWorkflowStatus = data.workflowStatus || 'idle'
        
        // Update tasks if they've changed
        if (JSON.stringify(newTasks) !== JSON.stringify(tasks)) {
          setTasks(newTasks)
        }
        
        // Update current task index if it's changed
        if (newCurrentTaskIndex !== currentTaskIndex) {
          setCurrentTaskIndex(newCurrentTaskIndex)
        }
        
        // Update workflow status if it's changed
        if (newWorkflowStatus !== workflowStatus) {
          setWorkflowStatus(newWorkflowStatus)
        }
      }
    } catch (error) {
      console.error('Error fetching tasks:', error)
    }
  }

  const fetchGeneratedFiles = async () => {
    try {
      const response = await fetch(`${API_BASE}/files`)
      const data = await response.json()
      if (data.status === 'success') {
        const newFiles = data.files || []
        
        // Only update if files have actually changed (by comparing length and latest modification times)
        if (newFiles.length !== generatedFiles.length ||
            (newFiles.length > 0 && generatedFiles.length > 0 &&
             newFiles[0].modified !== generatedFiles[0].modified)) {
          setGeneratedFiles(newFiles)
        }
      }
    } catch (error) {
      console.error('Error fetching generated files:', error)
    }
  }

  const handlePromptSubmit = async (prompt, documents = []) => {
    setIsLoading(true)
    setWorkflowStatus('planning')
    try {
      const response = await fetch(`${API_BASE}/submit-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          prompt,
          documents: documents.length > 0 ? documents : undefined
        })
      })
      const data = await response.json()
      console.log('Prompt submission result:', data)
      if (data.status !== 'success') {
        const msg = data.message || 'Failed to start workflow.'
        alert(msg)
        setWorkflowStatus('idle')
        return
      }
      setHasSubmitted(true)
      setSubmittedPrompt(prompt)
      setSubmittedDocuments(documents || [])
      
      // Refresh data after prompt submission
      setTimeout(() => {
        fetchMessages()
        fetchTasks()
        fetchSystemStatus()
      }, 1000)
    } catch (error) {
      console.error('Error submitting prompt:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const triggerAction = async (action) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      })
      const data = await response.json()
      console.log(`${action} result:`, data)
      
      // Handle special actions
      if (action === 'reset-workflow') {
        setTasks([])
        setCurrentTaskIndex(0)
        setWorkflowStatus('idle')
        setGeneratedFiles([])
      }
      
      // Refresh messages, tasks, and files after action
      setTimeout(() => {
        fetchMessages()
        fetchTasks()
        fetchGeneratedFiles()
        fetchSystemStatus()
      }, 1000)
    } catch (error) {
      console.error(`Error triggering ${action}:`, error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMessageClick = (messageId) => {
    // Highlight the corresponding arrow in the diagram
    const message = messages.find(m => m.id === messageId)
    if (message) {
      console.log('Selected message:', message)
    }
  }

  const handleReset = async () => {
    if (!confirm('Reset the entire system? This will clear all messages, files, and return to the initial screen.')) {
      return
    }
    
    try {
      // Call backend reset endpoint
      const response = await fetch(`${API_BASE}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        // Reset frontend state
        setMessages([])
        setTasks([])
        setGeneratedFiles([])
        setHasSubmitted(false)
        setSubmittedPrompt('')
        setSubmittedDocuments([])
        setWorkflowStatus('idle')
        setCurrentTaskIndex(0)
        
        // Refresh data
        setTimeout(() => {
          fetchAgents()
          fetchSystemStatus()
        }, 500)
      }
    } catch (error) {
      console.error('Error resetting system:', error)
      alert('Failed to reset system. Please refresh the page.')
    }
  }

  // Compute sliding window available height (viewport minus sticky bars)
  const topBarPx = topBarActive ? 96 : 0 // approx sticky header height when active
  const bottomBarPx = hasSubmitted && generatedFiles.length > 0 ? 80 : 0 // approx sticky footer height
  const slidingWindowHeight = `calc(100vh - ${topBarPx + bottomBarPx + 32}px)` // extra spacing

  return (
    <div className="min-h-screen bg-white flex flex-col">
      
      {/* Top Right Corner - Reset Button and Live Update Indicator */}
      <div className="fixed top-4 right-4 z-50 flex items-center gap-3">
        {/* Reset Button */}
        <button
          onClick={handleReset}
          className="group relative px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg shadow-lg transition-all duration-200 hover:shadow-xl"
          title="Reset system"
        >
          <span className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Reset
          </span>
        </button>

        {/* Live Update Indicator */}
        <div className="relative">
          <div className={`
            w-3 h-3 rounded-full transition-all duration-300 shadow-lg
            ${isUpdating 
              ? 'bg-blue-500 animate-pulse shadow-blue-300 shadow-lg' 
              : 'bg-gray-400 shadow-gray-300'
            }
          `}>
            <div className={`
              absolute inset-0 rounded-full transition-all duration-1000
              ${isUpdating 
                ? 'bg-blue-400 animate-ping opacity-75' 
                : 'opacity-0'
              }
            `}></div>
          </div>
          {/* Tooltip on hover */}
          <div className="absolute top-full right-0 mt-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            {isUpdating ? 'Live updates active' : 'Monitoring...'}
          </div>
        </div>
      </div>

      {/* Sticky Top: Prompt bar (hidden styling before submit) */}
      <div className={`sticky top-0 z-40 ${topBarActive ? 'bg-white/90 backdrop-blur border-b' : 'bg-transparent border-b-0'}`}>
        <div className={`container mx-auto px-4 ${topBarActive ? 'py-3' : 'py-0'}`}>
          <div
            className="transition-transform duration-700 ease-in-out"
            style={{ transform: hasSubmitted ? 'translateY(0)' : 'translateY(calc(50vh - 120px))' }}
          >
            <HeroPrompt
              onSubmitPrompt={handlePromptSubmit}
              isLoading={isLoading || workflowStatus !== 'idle'}
              isSubmitted={hasSubmitted}
              submittedPrompt={submittedPrompt}
              submittedDocuments={submittedDocuments}
            />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 flex-1 flex flex-col">

        {/* Status Bar under title area */}
        

        {/* Sliding content area (no background) shows after submit */}
        {hasSubmitted && (
          <div className="mt-6 min-h-0 overflow-y-auto" style={{ height: slidingWindowHeight }}>
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-0 overflow-visible">
              {/* Task List (left) */}
              <div className="lg:col-span-3 animate-fade-in-up animate-fade-in-up-delay-1 h-full min-h-0">
                <div className="bg-white rounded-2xl shadow-lg p-6 h-full flex flex-col min-h-0">
                  <h2 className="text-2xl font-semibold text-gray-800 mb-4">Task List</h2>
                  <div className="flex-1 overflow-y-auto min-h-0">
                    <TaskList 
                      tasks={tasks}
                      currentTaskIndex={currentTaskIndex}
                      embedded={true}
                    />
                  </div>
                </div>
              </div>

              {/* Agent Diagram (center) */}
              <div className="lg:col-span-6 animate-fade-in-up animate-fade-in-up-delay-2 h-full min-h-0 overflow-visible">
                <div className="bg-white rounded-2xl shadow-lg p-6 h-full flex flex-col min-h-0 overflow-visible">
                  <h2 className="text-2xl font-semibold text-gray-800 mb-4">Agent Network</h2>
                  <div className="w-full flex-1 min-h-0 overflow-visible">
                    <AgentDiagram 
                      agents={agents}
                      messages={messages}
                      onMessageHover={(message) => console.log('Hovered message:', message)}
                    />
                  </div>
                </div>
              </div>

              {/* Recent Messages (right) */}
              <div className="lg:col-span-3 animate-fade-in-up animate-fade-in-up-delay-3 h-full min-h-0 overflow-visible">
                <div className="bg-white rounded-2xl shadow-lg p-6 h-full flex flex-col min-h-0 overflow-visible">
                  <h2 className="text-2xl font-semibold text-gray-800 mb-4">Recent Messages</h2>
                  <div className="flex-1 overflow-y-auto min-h-0" style={{ overflowX: 'visible' }}>
                    <MessageLog 
                      messages={messages.slice(0, 50)}
                      allMessages={messages}
                      onMessageClick={handleMessageClick}
                      pausePolling={pausePolling}
                      onTogglePause={() => setPausePolling(!pausePolling)}
                    />
                  </div>
                </div>
              </div>
            </div>
            {/* Files bar is sticky at bottom outside this scroll area */}
          </div>
        )}
      </div>

      {/* Sticky Bottom: Generated files bar */}
      {hasSubmitted && generatedFiles.length > 0 && (
        <div className="sticky bottom-0 z-40 bg-white/90 backdrop-blur border-t">
          <div className="container mx-auto px-4 py-3">
            <FilesBar files={generatedFiles} />
          </div>
        </div>
      )}
    </div>
  )
}

export default App
