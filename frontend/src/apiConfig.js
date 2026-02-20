/**
 * API Base URL Configuration
 * - Development (localhost): uses relative path → Vite proxy to localhost:8000
 * - Production (GitHub Pages): uses Cloud Run URL
 */

const isLocalhost = typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

// Cloud Run URL — update after deployment
const CLOUD_RUN_URL = import.meta.env.VITE_API_URL || 'https://gaim-lab-api-178873306962.asia-northeast3.run.app'

export const API_HOST = isLocalhost ? '' : CLOUD_RUN_URL
export const API_BASE = `${API_HOST}/api/v1`
export const AUTH_BASE = `${API_HOST}/api/v1/auth`
