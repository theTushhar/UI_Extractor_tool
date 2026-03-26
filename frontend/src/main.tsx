import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './main.css' // Import Bulma styles and custom global styles
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
