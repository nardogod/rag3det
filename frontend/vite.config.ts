import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // monstros.json (2.4MB) em chunk separado
          if (id.includes('monstros.json') || id.includes('BestiarioPage')) {
            return 'bestiario';
          }
          if (id.includes('FichaPersonagemPage') || id.includes('itens_3dt') || id.includes('vantagens_turbinado')) {
            return 'ficha';
          }
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
})
