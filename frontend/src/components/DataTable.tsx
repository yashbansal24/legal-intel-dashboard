import { memo } from 'react'

type Props = { columns: string[], rows: Record<string, any>[], height?: number }

export default memo(function DataTable({columns, rows, height=360}: Props){
  return (
    <div className="card" style={{overflow:'auto', maxHeight: height}}>
      <table>
        <thead><tr>{columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {columns.map(c => <td key={c}>{String(r[c] ?? '')}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
})
