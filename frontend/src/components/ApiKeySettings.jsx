import { useState, useEffect } from 'react'
import { getStoredApiKey, setStoredApiKey, validateApiKey } from '../lib/clientAnalyzer'
import './ApiKeySettings.css'

function ApiKeySettings({ open, onClose, onSave }) {
    const [key, setKey] = useState('')
    const [showKey, setShowKey] = useState(false)
    const [error, setError] = useState('')
    const [saved, setSaved] = useState(false)

    useEffect(() => {
        if (open) {
            setKey(getStoredApiKey())
            setError('')
            setSaved(false)
        }
    }, [open])

    const handleSave = () => {
        const trimmed = key.trim()
        if (!trimmed) {
            setError('API Key를 입력해주세요.')
            return
        }
        if (!validateApiKey(trimmed)) {
            setError('유효하지 않은 API Key 형식입니다. AIza...로 시작하는 키를 입력하세요.')
            return
        }
        setStoredApiKey(trimmed)
        setSaved(true)
        setError('')
        onSave?.(trimmed)
        setTimeout(() => onClose?.(), 600)
    }

    if (!open) return null

    return (
        <div className="apikey-overlay" onClick={(e) => e.target === e.currentTarget && onClose?.()}>
            <div className="apikey-modal">
                <div className="apikey-header">
                    <h2>🔑 Google API Key 설정</h2>
                    <button className="apikey-close" onClick={onClose}>✕</button>
                </div>

                <div className="apikey-body">
                    <p className="apikey-desc">
                        GitHub Pages에서 수업 분석을 실행하려면<br />
                        Google Gemini API Key가 필요합니다.
                    </p>

                    <div className="apikey-info-box">
                        <span className="apikey-info-icon">ℹ️</span>
                        <div>
                            <a
                                href="https://aistudio.google.com/apikey"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Google AI Studio
                            </a>
                            에서 무료로 API Key를 발급받을 수 있습니다.
                        </div>
                    </div>

                    <div className="apikey-input-group">
                        <label className="apikey-label">API Key</label>
                        <div className="apikey-input-wrap">
                            <input
                                type={showKey ? 'text' : 'password'}
                                className="apikey-input"
                                value={key}
                                onChange={(e) => { setKey(e.target.value); setError(''); setSaved(false) }}
                                placeholder="AIza..."
                                spellCheck={false}
                                autoComplete="off"
                            />
                            <button
                                className="apikey-toggle"
                                onClick={() => setShowKey(!showKey)}
                                title={showKey ? '숨기기' : '보기'}
                            >
                                {showKey ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    {error && <div className="apikey-error">{error}</div>}
                    {saved && <div className="apikey-success">✅ 저장되었습니다!</div>}

                    <div className="apikey-security">
                        <span>🔒</span>
                        <span>API Key는 브라우저 localStorage에만 저장되며, 서버로 전송되지 않습니다.</span>
                    </div>
                </div>

                <div className="apikey-footer">
                    <button className="btn btn-secondary" onClick={onClose}>취소</button>
                    <button className="btn btn-primary" onClick={handleSave}>저장</button>
                </div>
            </div>
        </div>
    )
}

export default ApiKeySettings
