import React, { useState, useEffect } from 'react'
import AgentDiagram from './components/AgentDiagram'
import MessageLog from './components/MessageLog'
import StatusBar from './components/StatusBar'
import UserPromptInput from './components/UserPromptInput'
import TaskList from './components/TaskList'
import GeneratedFiles from './components/GeneratedFiles'

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

  // Fetch agents on component mount and ensure they're always visible
  useEffect(() => {
    // Set default agents immediately to ensure visualization is never empty
    setDefaultAgents()
    // Then try to fetch live data
    fetchAgents()
    fetchSystemStatus()
  }, [])

  // Poll for new messages every 500ms for more responsive updates (unless paused)
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
          setTimeout(() => setIsUpdating(false), 500) // Longer flash for debugging visibility
        }
      }
    }, 100)  // Ultra-fast polling for debugging visual lag

    return () => clearInterval(interval)
  }, [pausePolling])

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
        tools: ["read_file", "list_directory", "finalize_function", "transfer_to_coder_agent", "transfer_to_tester_agent", "transfer_to_database_agent"],
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

  const handlePromptSubmit = async (prompt) => {
    setIsLoading(true)
    setWorkflowStatus('planning')
    try {
      const response = await fetch(`${API_BASE}/submit-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt })
      })
      const data = await response.json()
      console.log('Prompt submission result:', data)
      
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      
      {/* Live Update Indicator - Top Right Corner */}
      <div className="fixed top-4 right-4 z-50">
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

      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            AI Coding Assistant System
          </h1>
          <p className="text-lg text-gray-600">
            Interactive visualization of multi-agent code generation, testing, and finalization
          </p>
          <StatusBar status={systemStatus} />
        </header>

        {/* User Prompt Input */}
        <div className="mb-8">
          <UserPromptInput 
            onSubmitPrompt={handlePromptSubmit}
            isLoading={isLoading || workflowStatus !== 'idle'}
          />
        </div>

        {/* Main Content - 3 Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Task List - Left column */}
          <div className="lg:col-span-1">
            <TaskList 
              tasks={tasks}
              currentTaskIndex={currentTaskIndex}
            />
          </div>

          {/* Agent Diagram - Center column */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg p-6 h-fit">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                Agent Network
              </h2>
              <div className="w-full" style={{ minHeight: '300px', maxHeight: '500px' }}>
                <AgentDiagram 
                  agents={agents} 
                  messages={messages}
                  onMessageHover={(message) => console.log('Hovered message:', message)}
                />
              </div>
            </div>
          </div>

          {/* Right column left empty (controls removed) */}
          <div className="lg:col-span-1"></div>
        </div>

        {/* Recent Messages Section - Full Width */}
        <div className="mt-8">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              💬 Recent Messages
            </h2>
            <MessageLog 
              messages={messages.slice(0, 15)}
              allMessages={messages}
              onMessageClick={handleMessageClick}
              pausePolling={pausePolling}
              onTogglePause={() => setPausePolling(!pausePolling)}
            />
          </div>
        </div>

        {/* Generated Files Section */}
        <div className="mt-8">
          <GeneratedFiles files={generatedFiles} />
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>
            Built with React, FastAPI, and OpenAI • 
            Multi-agent system for automated code generation and testing
          </p>
        </footer>
      </div>
    </div>
  )
}

export default App
