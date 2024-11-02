import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  plugins: [react()],
  loader: { '.js': 'jsx' },
  server: {
    watch: {
     usePolling: true,
    },
    host: true,
    strictPort: true,
    port: 3000, 
  }
})