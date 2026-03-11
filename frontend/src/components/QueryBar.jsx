import { useRef } from 'react'

export default function QueryBar({
  statusMessage,
  question,
  onQuestionChange,
  onAsk,
  ingestInProgress,
  runIngest,
  uploadedFiles = [],
}) {
  const fileInputRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    onAsk()
  }

  const handleFileChange = () => {
    const input = fileInputRef.current
    if (!input?.files?.length || !runIngest) return
    runIngest(Array.from(input.files))
  }

  const triggerFileInput = () => fileInputRef.current?.click()

  return (
    <div className="query-bar">
      <div className="query-main">
        {uploadedFiles.length > 0 && (
          <div className="query-documents">
            <div className="query-documents-tabs">
              {uploadedFiles.map((name, i) => (
                <span key={i} className="query-doc-tab">{name}</span>
              ))}
            </div>
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="query-row">
            <textarea
              className="query-input"
              placeholder="What is in the documents?"
              value={question}
              onChange={(e) => onQuestionChange(e.target.value)}
              aria-label="Ask a question"
            />
            <div className="query-actions">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.md,.html,.csv,.docx"
                aria-label="Upload documents"
                onChange={handleFileChange}
                className="query-file-input"
              />
              <button
                type="button"
                className="btn btn-add"
                onClick={triggerFileInput}
                title="Upload documents"
                aria-label="Upload documents"
              >
                +
              </button>
              <button type="submit" className="btn btn-primary">
                Ask
              </button>
            </div>
          </div>
        </form>
        <div className={`query-status ${statusMessage === 'Getting answer...' || statusMessage === 'Ingesting in background...' ? 'loading' : ''}`}>
          {statusMessage || '\u00A0'}
        </div>
      </div>
    </div>
  )
}
