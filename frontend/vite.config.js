import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isGHPages = process.env.GITHUB_PAGES === 'true'

export default defineConfig({
    plugins: [react()],
    base: isGHPages ? '/GAIM_Lab/app/' : '/',
    define: {
        '__APP_VERSION__': JSON.stringify('8.3.0'),
    },
    build: {
        outDir: isGHPages ? '../docs/app' : 'dist',
        emptyOutDir: true,
    },
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        }
    }
})
