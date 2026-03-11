export default function ChatHistory({ turns }) {
  if (!turns?.length) return null

  return (
    <section className="chat-history" aria-label="Chat">
      {turns.map((turn, i) => (
        <div key={i} className="chat-turn">
          <p className="chat-question">Q: {turn.question}</p>
          <div className="chat-answer">{turn.answer}</div>
          {turn.sources?.length > 0 && (
            <details className="chat-sources">
              <summary>Sources ({turn.sources.length})</summary>
              {turn.sources.map((src, j) => (
                <div key={j} className="chat-sources-detail">
                  <div className="source-meta">Source {j + 1}: {src?.metadata?.source ?? '-'}</div>
                  <div className="source-doc">{src?.document ?? ''}</div>
                </div>
              ))}
            </details>
          )}
        </div>
      ))}
    </section>
  )
}
