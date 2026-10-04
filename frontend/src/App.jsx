import { Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import ComingSoon from './pages/ComingSoon'
import Dashboard from './pages/Dashboard'
import Map from './pages/Map'
import Incidents from './pages/Incidents'
import IncidentDetail from './pages/IncidentDetail'
import Resources from './pages/Resources'
import DuplicateReview from './pages/DuplicateReview'
import AIActivity from './pages/AIActivity'
import ReportEmergency from './pages/ReportEmergency'
import ResponsePlan from './pages/ResponsePlan'
import Assignments from './pages/Assignments'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>

        <Route index element={<Dashboard />} />

        <Route path="map" element={<Map />} />

        <Route path="incidents" element={<Incidents />} />

        <Route
          path="incidents/:incidentId"
          element={<IncidentDetail />}
        />

        <Route
          path="incidents/:incidentId/response-plan"
          element={<ResponsePlan />}
        />

        <Route
          path="resources"
          element={<Resources />}
        />
        
        <Route
             path="assignments"
             element={<Assignments />}
            />

        <Route
          path="duplicates"
          element={<DuplicateReview />}
        />

        <Route
          path="ai-activity"
          element={<AIActivity />}
        />

        <Route
          path="report"
          element={<ReportEmergency />}
        />

        <Route
          path="*"
          element={
            <ComingSoon
              title="Page not found"
              description="This page does not exist."
            />
          }
        />

      </Route>
    </Routes>
  )
}      
     
