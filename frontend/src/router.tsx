import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from './App'
import Landing from './pages/Landing'
import Language from './pages/Language'
import SkillPick from './pages/SkillPick'
import Interview from './pages/Interview'
import Record from './pages/Record'
import Review from './pages/Review'
import Witnesses from './pages/Witnesses'
import WitnessVouch from './pages/WitnessVouch'
import Credential from './pages/Credential'
import PublicProfile from './pages/PublicProfile'
import Directory from './pages/Directory'
import Dashboard from './pages/Dashboard'

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Landing /> },
      { path: '/start', element: <Language /> },
      { path: '/skill', element: <SkillPick /> },
      { path: '/interview/:attemptId', element: <Interview /> },
      { path: '/record/:attemptId', element: <Record /> },
      { path: '/review/:attemptId', element: <Review /> },
      { path: '/witnesses/:attemptId', element: <Witnesses /> },
      { path: '/credential/:id', element: <Credential /> },
      { path: '/c/:id', element: <PublicProfile /> },
      { path: '/w/:token', element: <WitnessVouch /> },
      { path: '/directory', element: <Directory /> },
      { path: '/dashboard', element: <Dashboard /> },
    ],
  },
])
