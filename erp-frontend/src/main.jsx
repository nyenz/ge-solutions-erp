// PATH: erp-frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

/**
 * GOLDEN SEED - MAIN BOOTSTRAPPER
 * Initializes the React environment with strict hardware rendering.
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)