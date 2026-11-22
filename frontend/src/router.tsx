import { createBrowserRouter } from 'react-router-dom'
import Landing from './pages/Landing'

const Placeholder = ({ name }: { name: string }) => (
  <div className="min-h-screen flex items-center justify-center font-mono text-ink">
    {name} (Placeholder)
  </div>
)

export const router = createBrowserRouter([
  { path: '/', element: <Landing /> },
  { path: '/start', element: <Placeholder name="Start" /> },
  { path: '/skill', element: <Placeholder name="SkillPick" /> },
  { path: '/interview/:attemptId', element: <Placeholder name="Interview" /> },
  { path: '/record/:attemptId', element: <Placeholder name="Record" /> },
  { path: '/review/:attemptId', element: <Placeholder name="Review" /> },
  { path: '/witnesses/:attemptId', element: <Placeholder name="Witnesses" /> },
  { path: '/credential/:id', element: <Placeholder name="Credential" /> },
  { path: '/c/:id', element: <Placeholder name="Public Profile" /> },
  { path: '/w/:token', element: <Placeholder name="Witness" /> },
  { path: '/directory', element: <Placeholder name="Directory" /> },
  { path: '/dashboard', element: <Placeholder name="Dashboard" /> },
])
