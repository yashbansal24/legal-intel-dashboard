import React from 'react'

type Props = { children: React.ReactNode }
type State = { hasError: boolean, message?: string }

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props){ super(props); this.state = { hasError: false } }
  static getDerivedStateFromError(err: any){ return { hasError: true, message: String(err) } }
  componentDidCatch(error: any, info: any){ console.error('ErrorBoundary', error, info) }
  render(){
    if(this.state.hasError){
      return <div className="card"><h3>Something went wrong</h3><p>{this.state.message}</p></div>
    }
    return this.props.children
  }
}
