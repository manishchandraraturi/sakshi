import React from 'react'
import { RouterProvider, useLocation, useOutlet } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { router } from './router'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { ToastContainer } from './components/ui/Toast'

export function AppLayout() {
  const location = useLocation()
  const outlet = useOutlet()

  return (
    <>
      <AnimatePresence mode="wait">
        {outlet && React.cloneElement(outlet, { key: location.pathname })}
      </AnimatePresence>
      <ToastContainer />
    </>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <RouterProvider router={router} />
    </ErrorBoundary>
  )
}
