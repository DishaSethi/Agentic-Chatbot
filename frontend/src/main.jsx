import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx' // Make sure this is importing your App

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)