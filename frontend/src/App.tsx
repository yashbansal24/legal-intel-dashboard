import Upload from './components/Upload'
import Query from './components/Query'
import Dashboard from './components/Dashboard'
import ErrorBoundary from './components/ErrorBoundary'

export default function App(){
  return (
    <div className="container">
      <header style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
        <h2>Legal Documents Dashboard</h2>
        <nav style={{display:'flex', gap:10, alignItems:'center'}}>
          <a className="badge" href="/docs" onClick={(e)=>{e.preventDefault(); window.open('http://127.0.0.1:8000/docs','_blank')}}>API Docs</a>
        </nav>
      </header>
      <ErrorBoundary>
        <Upload />
        <Query />
        <div style={{marginTop:16}}>
          <Dashboard />
        </div>
      </ErrorBoundary>
    </div>
  )
}
