import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { DocHit } from '../api/types'
import Spinner from './Spinner'

export default function Query(){
  const [q, setQ] = useState('uae law documents')

  const { mutate, data, isPending, error } = useMutation({
    mutationFn: async () => {
      const res = await api.post<DocHit[]>('/query/documents', { question: q })
      return res.data
    }
  })

  return (
    <div className="card">
      <h3>Search Documents</h3>
      <div style={{display:'flex', gap:8}}>
        <input
          value={q}
          onChange={e=> setQ(e.target.value)}
          placeholder="Ask e.g. 'documents in dubai' or 'governed by uae law'"
          style={{flex:1, padding:10, borderRadius:8, border:'1px solid #e5e7eb'}}
          onKeyDown={(e)=> { if(e.key === 'Enter') mutate() }}
        />
        <button className="button" onClick={()=> mutate()} disabled={isPending}>
          {isPending ? 'Searching…' : 'Search'}
        </button>
      </div>

      <div style={{marginTop:12}}>
        {isPending && <Spinner label="Searching…" />}
        {error && <p style={{color:'#b91c1c'}}>Error: {(error as Error).message}</p>}

        {data && data.length > 0 && (
          <ul style={{listStyle:'none', padding:0, margin:0, display:'grid', gap:8}}>
            {data.map((hit, idx) => (
              <li key={idx} className="card" style={{padding:'10px 12px'}}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                  <strong style={{wordBreak:'break-word'}}>{hit.document}</strong>
                  {hit.governing_law && <span className="badge">{hit.governing_law}</span>}
                </div>
              </li>
            ))}
          </ul>
        )}

        {data && data.length === 0 && !isPending && !error && (
          <p>No documents matched. Try something else.</p>
        )}
      </div>
    </div>
  )
}
