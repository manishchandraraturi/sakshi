import React, { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from './App'
import Landing from './pages/Landing'
import Interview from './pages/Interview'
import { Skeleton } from './components/ui/Skeleton'

// Page loading fallback skeleton
function PageFallback() {
  return (
    <div className="min-h-screen bg-paper flex flex-col justify-between max-w-xl mx-auto px-4 py-8 space-y-6">
      <div className="space-y-3">
        <Skeleton className="h-8 w-44 rounded-xl" />
        <Skeleton className="h-4 w-64 rounded-md" />
      </div>
      <div className="space-y-4 flex-1 my-6">
        <Skeleton className="h-48 w-full rounded-2xl" />
        <Skeleton className="h-28 w-full rounded-2xl" />
        <Skeleton className="h-20 w-full rounded-2xl" />
      </div>
      <Skeleton className="h-14 w-full rounded-xl" />
    </div>
  )
}

const withSuspense = (Component: React.ComponentType) => (
  <Suspense fallback={<PageFallback />}>
    <Component />
  </Suspense>
)

// Code-split pages (Landing and Interview remain statically loaded for instant start)
const Language = lazy(() => import('./pages/Language'))
const SkillPick = lazy(() => import('./pages/SkillPick'))
const Record = lazy(() => import('./pages/Record'))
const Review = lazy(() => import('./pages/Review'))
const Witnesses = lazy(() => import('./pages/Witnesses'))
const WitnessVouch = lazy(() => import('./pages/WitnessVouch'))
const Credential = lazy(() => import('./pages/Credential'))
const PublicProfile = lazy(() => import('./pages/PublicProfile'))
const Directory = lazy(() => import('./pages/Directory'))
const Dashboard = lazy(() => import('./pages/Dashboard'))

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Landing /> },
      { path: '/start', element: withSuspense(Language) },
      { path: '/skill', element: withSuspense(SkillPick) },
      { path: '/interview/:attemptId', element: <Interview /> },
      { path: '/record/:attemptId', element: withSuspense(Record) },
      { path: '/review/:attemptId', element: withSuspense(Review) },
      { path: '/witnesses/:attemptId', element: withSuspense(Witnesses) },
      { path: '/credential/:id', element: withSuspense(Credential) },
      { path: '/c/:id', element: withSuspense(PublicProfile) },
      { path: '/w/:token', element: withSuspense(WitnessVouch) },
      { path: '/directory', element: withSuspense(Directory) },
      { path: '/dashboard', element: withSuspense(Dashboard) },
    ],
  },
])
