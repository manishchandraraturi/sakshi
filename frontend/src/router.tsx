import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from './App'
import Landing from './pages/Landing'
import Language from './pages/Language'
import SkillPick from './pages/SkillPick'
import Interview from './pages/Interview'
import Record from './pages/Record'

const Placeholder = ({ name }: { name: string }) => (
  <div className="min-h-screen flex items-center justify-center font-mono text-ink">
    {name} (Placeholder)
  </div>
)

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Landing /> },
      { path: '/start', element: <Language /> },
      { path: '/skill', element: <SkillPick /> },
      { path: '/interview/:attemptId', element: <Interview /> },
      { path: '/record/:attemptId', element: <Record /> },
      { path: '/review/:attemptId', element: <Placeholder name="Review" /> },
      { path: '/witnesses/:attemptId', element: <Placeholder name="Witnesses" /> },
      { path: '/credential/:id', element: <Placeholder name="Credential" /> },
      { path: '/c/:id', element: <Placeholder name="Public Profile" /> },
      { path: '/w/:token', element: <Placeholder name="Witness" /> },
      { path: '/directory', element: <Placeholder name="Directory" /> },
      { path: '/dashboard', element: <Placeholder name="Dashboard" /> },
    ],
  },
])
