const getApiBase = () => import.meta.env.VITE_API_URL ?? ''

const headers = (sessionId) => ({ 'X-Session-ID': sessionId })

export async function ingestFiles(sessionId, files, { chunkSize, chunkOverlap, chunkByWords }) {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  form.append('chunk_size', String(chunkSize))
  form.append('chunk_overlap', String(chunkOverlap))
  form.append('chunk_by_words', chunkByWords ? 'true' : 'false')

  const res = await fetch(`${getApiBase()}/api/ingest/files`, {
    method: 'POST',
    headers: headers(sessionId),
    body: form,
  })
  if (!res.ok) throw new Error(`Ingest failed: ${res.status}`)
  return res.json()
}

export async function query(sessionId, { question, topK, model }) {
  const res = await fetch(`${getApiBase()}/api/query`, {
    method: 'POST',
    headers: { ...headers(sessionId), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      top_k: topK,
      model: model || undefined,
    }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error || `Request failed: ${res.status}`)
  return data
}

export async function clearSession(sessionId) {
  await fetch(`${getApiBase()}/api/session`, {
    method: 'DELETE',
    headers: headers(sessionId),
  })
}
