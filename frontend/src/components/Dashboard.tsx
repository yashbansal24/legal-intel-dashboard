import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Dashboard } from '../api/types'
import { PieChart, Pie, Tooltip, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend, ResponsiveContainer } from 'recharts'

export default function Dashboard(){
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<Dashboard>('/dashboard')).data,
    refetchOnReconnect: true
  })

  if(isLoading) return <div className="card"><div className="skeleton" style={{height:200}}/></div>
  if(error) return <div className="card"><p style={{color:'#b91c1c'}}>Failed to load dashboard. <button className="button ghost" onClick={()=> refetch()} disabled={isFetching}>Retry</button></p></div>
  if(!data) return null

  const barData = Object.entries(data.agreement_types).map(([name, value]) => ({ name, value }))
  const pieData = Object.entries(data.jurisdictions).map(([name, value]) => ({ name, value }))

  return (
    <div className="row row-2">
      <div className="card">
        <h3>Agreements by Type</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" name="Count" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="card">
        <h3>Governing Law Breakdown</h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={pieData} dataKey="value" nameKey="name" label />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="card" style={{gridColumn:'1 / -1'}}>
        <h3>Coverage</h3>
        <table>
          <thead><tr><th>Industry</th><th>Count</th><th>Geography</th><th>Count</th></tr></thead>
          <tbody>
            {Object.entries(data.industries).map(([k,v],i)=> (
              <tr key={'i'+i}><td>{k}</td><td>{v}</td><td>{Object.keys(data.geographies)[i] ?? ''}</td><td>{Object.values(data.geographies)[i] ?? ''}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
