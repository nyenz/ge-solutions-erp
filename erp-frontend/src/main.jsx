// PATH: erp-frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import PreferencesProvider from './context/PreferencesProvider'
import './index.css'

/**
 * GOLDEN SEED - MAIN BOOTSTRAPPER
 * Initializes the React environment with strict hardware rendering.
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Outermost on purpose: it writes onto <html> before anything renders,
        so the first paint is already at the user's chosen size and theme. */}
    <PreferencesProvider>
      <App />
    </PreferencesProvider>
  </React.StrictMode>,
)