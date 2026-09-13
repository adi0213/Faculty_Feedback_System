import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Login from './pages/Login/Login';
import DashboardLayout from './components/DashboardLayout/DashboardLayout';
import StudentFeedback from './pages/Student/StudentFeedback';
import FacultyDashboard from './pages/Faculty/FacultyDashboard';
import HoDDashboard from './pages/HoD/HoDDashboard';
import PrincipalDashboard from './pages/Principal/PrincipalDashboard';
import UniversityDashboard from './pages/University/UniversityDashboard';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        
        {/* Student Portal */}
        <Route element={<DashboardLayout allowedRoles={['student']} />}>
          <Route path="/student" element={<StudentFeedback />} />
        </Route>

        {/* Faculty Portal */}
        <Route element={<DashboardLayout allowedRoles={['faculty']} />}>
          <Route path="/faculty/*" element={<FacultyDashboard />} />
        </Route>

        {/* HoD Portal */}
        <Route element={<DashboardLayout allowedRoles={['hod']} />}>
          <Route path="/hod/*" element={<HoDDashboard />} />
        </Route>

        {/* Principal Portal */}
        <Route element={<DashboardLayout allowedRoles={['principal']} />}>
          <Route path="/principal/*" element={<PrincipalDashboard />} />
        </Route>

        {/* University Portal */}
        <Route element={<DashboardLayout allowedRoles={['university']} />}>
          <Route path="/university/*" element={<UniversityDashboard />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
