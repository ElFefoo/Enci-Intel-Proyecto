import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { useAuthStore } from './store/authStore'
import './index.css'

function Root() {
  const init = useAuthStore((s) => s.init)

  useEffect(() => {
    // Inicializa el listener de Firebase Auth al montar la app
    const unsubscribe = init()
    return unsubscribe
  }, [init])

  return <App />
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Root />
    </BrowserRouter>
  </React.StrictMode>
)
