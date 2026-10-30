// PATH: erp-frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import PreferencesProvider from './context/PreferencesProvider'
import './index.css'
import './styles/gesday.css'   // fix256: GES DAY page skins (only active when the theme is GES DAY)
import './styles/midnight.css'   // fix280: the same skins at night (only active when the theme is MIDNIGHT)

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