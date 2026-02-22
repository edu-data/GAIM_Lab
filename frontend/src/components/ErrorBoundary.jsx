import React from 'react'

/**
 * GAIM Lab v8.0 — 글로벌 에러 바운더리
 * 
 * 에러 #4 방지: undefined 프로퍼티 접근 등 런타임 에러에서
 * 화면 블랙아웃 대신 리트라이 가능한 fallback UI를 표시
 */

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null, errorInfo: null }
        this._handleUnhandledRejection = this._handleUnhandledRejection.bind(this)
        this._handleGlobalError = this._handleGlobalError.bind(this)
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidMount() {
        window.addEventListener('unhandledrejection', this._handleUnhandledRejection)
        window.addEventListener('error', this._handleGlobalError)
    }

    componentWillUnmount() {
        window.removeEventListener('unhandledrejection', this._handleUnhandledRejection)
        window.removeEventListener('error', this._handleGlobalError)
    }

    _handleUnhandledRejection(event) {
        event.preventDefault()
        const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
        console.error('[ErrorBoundary] Unhandled Promise rejection:', error)
        this.setState({ hasError: true, error, errorInfo: { componentStack: error.stack || '' } })
    }

    _handleGlobalError(event) {
        if (event.error) {
            console.error('[ErrorBoundary] Global error:', event.error)
            this.setState({ hasError: true, error: event.error, errorInfo: { componentStack: event.error.stack || '' } })
        }
    }

    componentDidCatch(error, errorInfo) {
        this.setState({ errorInfo })
        console.error('[ErrorBoundary]', error, errorInfo)
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null, errorInfo: null })
    }

    handleGoHome = () => {
        this.setState({ hasError: false, error: null, errorInfo: null })
        window.location.hash = '#/'
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    minHeight: '50vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '2rem',
                }}>
                    <div style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        backdropFilter: 'blur(20px)',
                        borderRadius: '1.5rem',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        padding: '3rem',
                        maxWidth: '500px',
                        width: '100%',
                        textAlign: 'center',
                    }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
                        <h2 style={{
                            fontSize: '1.5rem',
                            fontWeight: 700,
                            marginBottom: '0.75rem',
                            color: 'var(--text-primary, #e2e8f0)',
                        }}>
                            문제가 발생했습니다
                        </h2>
                        <p style={{
                            color: 'var(--text-secondary, #94a3b8)',
                            marginBottom: '1.5rem',
                            fontSize: '0.95rem',
                            lineHeight: 1.6,
                        }}>
                            {this.state.error?.message || '알 수 없는 오류가 발생했습니다.'}
                        </p>
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
                            <button
                                onClick={this.handleRetry}
                                style={{
                                    padding: '0.75rem 1.5rem',
                                    borderRadius: '0.75rem',
                                    border: 'none',
                                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                                    color: '#fff',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    fontSize: '0.9rem',
                                }}
                            >
                                🔄 다시 시도
                            </button>
                            <button
                                onClick={this.handleGoHome}
                                style={{
                                    padding: '0.75rem 1.5rem',
                                    borderRadius: '0.75rem',
                                    border: '1px solid rgba(255, 255, 255, 0.15)',
                                    background: 'transparent',
                                    color: 'var(--text-secondary, #94a3b8)',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    fontSize: '0.9rem',
                                }}
                            >
                                🏠 홈으로
                            </button>
                        </div>
                        {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                            <details style={{
                                marginTop: '1.5rem',
                                textAlign: 'left',
                                fontSize: '0.75rem',
                                color: 'var(--text-muted, #64748b)',
                            }}>
                                <summary style={{ cursor: 'pointer', marginBottom: '0.5rem' }}>
                                    🛠 개발자 디버그 정보
                                </summary>
                                <pre style={{
                                    overflow: 'auto',
                                    maxHeight: '200px',
                                    padding: '0.5rem',
                                    background: 'rgba(0,0,0,0.3)',
                                    borderRadius: '0.5rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-all',
                                }}>
                                    {this.state.error?.stack}
                                    {'\n\n'}
                                    {this.state.errorInfo?.componentStack}
                                </pre>
                            </details>
                        )}
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary
