import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error(
    'Failed to find the root element. Please ensure there is a <div id="root"></div> in your HTML.'
  );
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
