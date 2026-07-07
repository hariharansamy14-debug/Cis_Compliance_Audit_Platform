/*
Concept: Main App Routing
Why it's needed: A single-page application (SPA) needs a way to navigate between different "pages" without reloading the browser.
How it works: We use React Router DOM. We define routes (`/`, `/login`, `/dashboard`) and map them to specific components.
*/

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext, AuthProvider } from './context/AuthContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import Pages (We will create these next)
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import RunAudit from './pages/RunAudit';
import PortScanning from './pages/PortScanning';
import AuditHistory from './pages/AuditHistory';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
    const { user, loading } = useContext(AuthContext);
    if (loading) return <div>Loading...</div>;
    return user ? children : <Navigate to="/login" />;
};

function AppRoutes() {
    return (
        <Router>
            <div className="App">
                <ToastContainer position="top-right" autoClose={3000} />
                <Routes>
                    {/* Public Routes */}
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/verify-email" element={<VerifyEmail />} />
                    
                    {/* Protected Routes */}
                    <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                    <Route path="/run-audit" element={<ProtectedRoute><RunAudit /></ProtectedRoute>} />
                    <Route path="/port-scanning" element={<ProtectedRoute><PortScanning /></ProtectedRoute>} />
                    <Route path="/history" element={<ProtectedRoute><AuditHistory /></ProtectedRoute>} />
                    
                    {/* Redirect root to dashboard */}
                    <Route path="/" element={<Navigate to="/dashboard" />} />
                </Routes>
            </div>
        </Router>
    );
}

function App() {
    return (
        <AuthProvider>
            <AppRoutes />
        </AuthProvider>
    );
}

export default App;
