export default function Options({
  open,
  onToggle,
  chunkByWords,
  onChunkByWordsChange,
  chunkSize,
  onChunkSizeChange,
  chunkOverlap,
  onChunkOverlapChange,
  topK,
  onTopKChange,
  model,
  onModelChange,
}) {
  const maxOverlap = Math.max(0, chunkSize - 1)

  return (
    <div className="query-options-row">
      <button type="button" className="options-trigger" onClick={onToggle} aria-expanded={open}>
        {open ? 'Options ▼' : 'Options ▶'}
      </button>
      {open && (
        <div className="options-panel">
          <div className="options-row options-chunk-by-row">
            <label className="options-field-label">Chunk by</label>
            <div className="options-chunk-by" role="group" aria-label="Chunk by">
              <label className={`options-chunk-by-option ${!chunkByWords ? 'options-chunk-by-selected' : ''}`}>
                <input
                  type="radio"
                  name="chunkBy"
                  checked={!chunkByWords}
                  onChange={() => onChunkByWordsChange(false)}
                />
                Characters
              </label>
              <label className={`options-chunk-by-option ${chunkByWords ? 'options-chunk-by-selected' : ''}`}>
                <input
                  type="radio"
                  name="chunkBy"
                  checked={chunkByWords}
                  onChange={() => onChunkByWordsChange(true)}
                />
                Words
              </label>
            </div>
          </div>
          <div>
            <label>Chunk size</label>
            <input
              type="number"
              min={chunkByWords ? 10 : 64}
              max={chunkByWords ? 500 : 4096}
              value={chunkSize}
              onChange={(e) => onChunkSizeChange(Number(e.target.value))}
            />
          </div>
          <div>
            <label>Chunk overlap</label>
            <input
              type="number"
              min={0}
              max={maxOverlap}
              value={chunkOverlap}
              onChange={(e) => onChunkOverlapChange(Number(e.target.value))}
            />
          </div>
          <div>
            <label>Top K (results per query)</label>
            <input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => onTopKChange(Number(e.target.value))}
            />
          </div>
          <div>
            <label>LLM model</label>
            <select value={model} onChange={(e) => onModelChange(e.target.value)}>
              {['mistral', 'llama3.2', 'llama3.1', 'phi3', 'gemma2'].map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  )
}
