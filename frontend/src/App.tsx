import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { MainLayout } from './layouts/MainLayout'
import { HomePage } from './pages/HomePage'
import { AssessmentPage } from './pages/AssessmentPage'
import { DashboardPage } from './pages/DashboardPage'
import { LocationPage } from './pages/LocationPage'
import { AdvisorPage } from './pages/AdvisorPage'

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/assess" element={<AssessmentPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/:assessmentId" element={<DashboardPage />} />
          <Route path="/location" element={<LocationPage />} />
          <Route path="/advisor" element={<AdvisorPage />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  )
}

export default App
