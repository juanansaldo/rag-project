import { useState, useRef, useCallback } from 'react'
import { ingestFiles, query, clearSession } from './api'
import Header from './components/Header.jsx'
import ChatHistory from './components/ChatHistory.jsx'
import QueryBar from './components/QueryBar.jsx'
import Options from './components/Options.jsx'

function generateSessionId() {
  return crypto.randomUUID?.() ?? `session-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

const MODELS = ['mistral', 'llama3.2', 'llama3.1', 'phi3', 'gemma2']

export default function App() {
  const [sessionId, setSessionId] = useState(() => generateSessionId())
  const [chatHistory, setChatHistory] = useState([])
  const [confirmNewSession, setConfirmNewSession] = useState(false)
  const [question, setQuestion] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [optionsOpen, setOptionsOpen] = useState(false)
  const [chunkByWords, setChunkByWords] = useState(false)
  const [chunkSize, setChunkSize] = useState(512)
  const [chunkOverlap, setChunkOverlap] = useState(100)
  const [topK, setTopK] = useState(4)
  const [model, setModel] = useState('mistral')
  const [ingestInProgress, setIngestInProgress] = useState(false)
  const [lastIngestedResult, setLastIngestedResult] = useState(null)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [askError, setAskError] = useState(null)

  const ingestPromiseRef = useRef(null)
  const lastFingerprintRef = useRef(null)
  const lastIngestedSummaryRef = useRef('')

  const runIngest = useCallback(
    async (files) => {
      if (!files?.length) return
      const fingerprint = files
        .slice()
        .sort((a, b) => a.name.localeCompare(b.name))
        .map((f) => [f.name, f.size])
        .join(',')
      if (fingerprint === lastFingerprintRef.current && !ingestInProgress) return
      lastFingerprintRef.current = fingerprint
      setIngestInProgress(true)
      setStatusMessage('Ingesting in background...')
      const promise = ingestFiles(sessionId, files, {
        chunkSize,
        chunkOverlap,
        chunkByWords,
      })
      ingestPromiseRef.current = promise
      try {
        const data = await promise
        const total = data?.total_chunks ?? 0
        const nFiles = data?.files?.length ?? 0
        const summary = data?.ok
          ? `Ingested ${total} chunks from ${nFiles} file(s).`
          : ''
        lastIngestedSummaryRef.current = summary
        setLastIngestedResult(
          data?.ok
            ? { summary }
            : null
        )
        if (data?.ok && data?.files?.length) {
          setUploadedFiles(data.files.map((f) => f.filename ?? f.name ?? 'File'))
        }
        setStatusMessage(summary)
      } catch {
        setLastIngestedResult(null)
        setUploadedFiles([])
        setStatusMessage('')
      } finally {
        setIngestInProgress(false)
        ingestPromiseRef.current = null
      }
    },
    [sessionId, chunkSize, chunkOverlap, chunkByWords, ingestInProgress]
  )

  const handleAsk = useCallback(async () => {
    const q = question.trim()
    if (!q) {
      setAskError('Enter a question.')
      return
    }
    setAskError(null)
    setStatusMessage('Getting answer...')
    try {
      if (ingestPromiseRef.current) {
        await ingestPromiseRef.current
        setStatusMessage(lastIngestedSummaryRef.current || 'Getting answer...')
      }
      const data = await query(sessionId, {
        question: q,
        topK,
        model: MODELS.includes(model) ? model : undefined,
      })
      if (data.error) {
        setAskError(data.error)
        setStatusMessage('')
        setQuestion('')
        return
      }
      setChatHistory((prev) => [
        ...prev,
        {
          question: q,
          answer: data.answer ?? '',
          sources: data.sources ?? [],
        },
      ])
      setQuestion('')
      setStatusMessage(lastIngestedSummaryRef.current || '')
    } catch (err) {
      setAskError(err.message ?? 'Request failed')
      setStatusMessage('')
      setQuestion('')
    }
  }, [question, sessionId, topK, model])

  const handleStartNewSession = () => setConfirmNewSession(true)
  const handleConfirmCancel = () => setConfirmNewSession(false)
  const handleConfirmYes = useCallback(async () => {
    try {
      await clearSession(sessionId)
    } catch {}
    setSessionId(generateSessionId())
    setChatHistory([])
    setLastIngestedResult(null)
    setIngestInProgress(false)
    setUploadedFiles([])
    ingestPromiseRef.current = null
    lastFingerprintRef.current = null
    lastIngestedSummaryRef.current = ''
    setConfirmNewSession(false)
    setStatusMessage('')
    setAskError(null)
  }, [sessionId])

  const handleChunkByWordsChange = (words) => {
    setChunkByWords(words)
    if (words) {
      setChunkSize(100)
      setChunkOverlap(20)
    } else {
      setChunkSize(512)
      setChunkOverlap(100)
    }
  }

  const displayStatus =
    statusMessage ||
    (ingestInProgress ? 'Ingesting in background...' : lastIngestedResult?.summary ?? '')

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <Options
          open={optionsOpen}
          onToggle={() => setOptionsOpen((o) => !o)}
          chunkByWords={chunkByWords}
          onChunkByWordsChange={handleChunkByWordsChange}
          chunkSize={chunkSize}
          onChunkSizeChange={setChunkSize}
          chunkOverlap={chunkOverlap}
          onChunkOverlapChange={setChunkOverlap}
          topK={topK}
          onTopKChange={setTopK}
          model={model}
          onModelChange={setModel}
        />
      </aside>
      <div className="app-center">
        <header className="app-header-wrap">
          <Header
            sessionId={sessionId}
            confirmNewSession={confirmNewSession}
            onStartNewSession={handleStartNewSession}
            onConfirmYes={handleConfirmYes}
            onConfirmCancel={handleConfirmCancel}
          />
        </header>
        <main className="app-main">
          {askError && (
            <div className="alert alert-error" role="alert">
              {askError}
            </div>
          )}
          <ChatHistory turns={chatHistory} />
        </main>
        <div className="query-bar-wrap">
          <QueryBar
            sessionId={sessionId}
            statusMessage={displayStatus}
            question={question}
            onQuestionChange={setQuestion}
            onAsk={handleAsk}
            ingestInProgress={ingestInProgress}
            runIngest={runIngest}
            uploadedFiles={uploadedFiles}
          />
        </div>
      </div>
    </div>
  )
}
