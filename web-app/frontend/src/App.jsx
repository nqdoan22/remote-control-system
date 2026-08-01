import React from 'react'; // 👈 BẮT BUỘC PHẢI CÓ DÒNG NÀY Ở DÒNG ĐẦU TIÊN
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import MachinePage from './pages/MachinePage';

// =========================================================================
// 🛡️ COMPONENT BẢO VỆ (Chỉ cho phép truy cập khi ĐÃ ĐĂNG NHẬP)
// =========================================================================
const ProtectedRoute = ({ children }) => {
  // Kiểm tra xem có token trong bộ nhớ trình duyệt không
  const token = localStorage.getItem('access_token');

  // Nếu KHÔNG có token -> Đá về trang /login ngay lập tức
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Nếu CÓ token -> Cho phép hiển thị Màn hình bên trong (children)
  return children;
};

// =========================================================================
// 🔓 COMPONENT CÔNG KHAI (Chặn người đã đăng nhập quay lại trang Login)
// =========================================================================
const PublicRoute = ({ children }) => {
  const token = localStorage.getItem('access_token');

  // Nếu ĐÃ đăng nhập rồi mà cố vào /login -> Chuyển thẳng tới /dashboard
  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Trang chủ: Tự động điều hướng về /dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Trang Đăng nhập (Công khai) */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        {/* Các trang Yêu cầu Bảo mật (Cần có Token) */}
        <Route
          path="/dashboard"
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

        {/* Route bắt lỗi 404: Mọi đường dẫn lạ đều đẩy về /dashboard (nếu chưa login sẽ tự văng về /login) */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;