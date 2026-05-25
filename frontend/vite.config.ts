import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],

  // ---- Path Aliases ----
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },

  // ---- Dev Server ----
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },

  // ---- Production Build ----
  build: {
    // Output directory
    outDir: 'dist',
    // Generate sourcemaps for debugging (disable in production for smaller size)
    sourcemap: false,
    // Target browsers (modern only — reduces polyfill bloat)
    target: 'es2020',
    // Chunk size warning threshold (KB)
    chunkSizeWarningLimit: 800,
    // Minify with esbuild (faster than terser)
    minify: 'esbuild',

    rollupOptions: {
      output: {
        // ---- Code Splitting Strategy ----
        manualChunks(id) {
          // Vendor chunks
          if (id.includes('node_modules/react') ||
              id.includes('node_modules/react-dom') ||
              id.includes('node_modules/react-router-dom')) {
            return 'vendor-react'
          }
          if (id.includes('node_modules/antd') ||
              id.includes('node_modules/@ant-design')) {
            return 'vendor-antd'
          }
          if (id.includes('node_modules/echarts') ||
              id.includes('node_modules/echarts-for-react') ||
              id.includes('node_modules/zrender')) {
            return 'vendor-charts'
          }
          if (id.includes('node_modules/axios')) {
            return 'vendor-axios'
          }
          if (id.includes('node_modules/zustand')) {
            return 'vendor-state'
          }
          if (id.includes('node_modules/react-quill') ||
              id.includes('node_modules/quill')) {
            return 'vendor-editor'
          }
          if (id.includes('node_modules/dayjs') ||
              id.includes('node_modules/classnames')) {
            return 'vendor-utils'
          }
          // All other node_modules
          if (id.includes('node_modules')) {
            return 'vendor-common'
          }
        },

        // ---- Asset Naming ----
        entryFileNames: 'assets/[name]-[hash:8].js',
        chunkFileNames: 'assets/[name]-[hash:8].js',
        assetFileNames: 'assets/[name]-[hash:8].[ext]',
      },
    },

    // CSS options
    cssCodeSplit: true,
    cssMinify: 'esbuild',
  },

  // ---- Preview Server (for prod build testing) ----
  preview: {
    port: 4173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
