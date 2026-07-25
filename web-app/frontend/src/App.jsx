// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import MachinePage from './pages/MachinePage';

// Component bọc (Wrapper) để bảo vệ các trang yêu cầu đăng nhập
const ProtectedRoute = ({ children }) => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
        // Nếu không có token, đá văng ra trang Login
        return <Navigate to="/login" replace />;
    }
    return children;
};

function App() {
    return (
        <Router>
            <Routes>
                {/* Route Public (Không cần đăng nhập) */}
                <Route path="/login" element={<LoginPage />} />

                {/* Các Routes Private (Phải có JWT Token) */}
                <Route 
                    path="/" 
                    element={
                        <ProtectedRoute>
                            <DashboardPage />
                        </ProtectedRoute>
                    } 
                />
                
                <Route 
                    path="/machine/:machineId" 
                    element={
                        <ProtectedRoute>
                            <MachinePage />
                        </ProtectedRoute>
                    } 
                />

                {/* Chặn bắt các đường dẫn tào lao, gom về trang chủ */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Router>
    );
}

export default App;