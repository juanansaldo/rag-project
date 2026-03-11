export default function Header({ sessionId, confirmNewSession, onStartNewSession, onConfirmYes, onConfirmCancel }) {
  return (
    <header className="app-header">
      <div>
        <h1 className="app-title">RAG Q&A</h1>
        <p className="app-session">Session: {sessionId.slice(0, 8)}...</p>
      </div>
      <div className="app-header-actions">
        {confirmNewSession ? (
          <>
            <span className="confirm-text">Clear session?</span>
            <button type="button" className="btn btn-primary" onClick={onConfirmYes}>
              Yes, start new session
            </button>
            <button type="button" className="btn" onClick={onConfirmCancel}>
              Cancel
            </button>
          </>
        ) : (
          <button type="button" className="btn" onClick={onStartNewSession}>
            Start new session
          </button>
        )}
      </div>
    </header>
  )
}
