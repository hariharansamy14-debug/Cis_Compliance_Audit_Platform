/*
Concept: React Entry Point
Why it's needed: This is the first file executed by React. It renders the main `App` component into the HTML DOM.
How it works: We import Bootstrap CSS here so it's available globally across our entire application.
*/

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import 'bootstrap/dist/css/bootstrap.min.css'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
