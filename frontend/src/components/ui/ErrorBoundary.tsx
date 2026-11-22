import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in component tree:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-paper">
          <div className="max-w-md mx-auto space-y-6">
            <h1 className="text-4xl md:text-5xl font-display font-extrabold text-ink leading-tight">
              Something went wrong<span className="text-accent">.</span>
            </h1>
            <p className="font-body text-muted text-sm md:text-base">
              An unexpected error occurred. Please try reloading the page.
            </p>
            {this.state.error && (
              <div className="p-4 bg-paper-2 rounded-xl text-left font-mono text-xs text-danger overflow-auto max-h-40 border border-line">
                {this.state.error.message}
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="px-6 py-3 bg-ink text-paper rounded-pill font-body font-medium hover:bg-ink-2 transition shadow-sm cursor-pointer"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
