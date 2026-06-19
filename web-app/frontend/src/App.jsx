import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import MachinePage from './pages/MachinePage';

export default function App() {
  // Lấy đường dẫn hiện tại của trình duyệt để làm routing thô
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    // Lắng nghe sự kiện đổi URL để cập nhật giao diện (khi dùng window.location.href)
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  // Kiểm tra xem người dùng đã có token đăng nhập chưa
  const isAuthenticated = !!localStorage.getItem('token');

  // Bộ lọc bảo mật điều hướng (Route Guard)
  // Nếu chưa đăng nhập thì bắt buộc phải ở trang Login
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Luồng xử lý điều hướng khi ĐÃ đăng nhập
  // 1. Trang điều khiển chi tiết một hoặc nhiều máy: /machine/{ids}
  if (currentPath.startsWith('/machine/')) {
    // Tách lấy đoạn ID máy từ URL (Ví dụ: /machine/MOCK-01,MOCK-02 -> MOCK-01,MOCK-02)
    const machineIdsString = currentPath.replace('/machine/', '');
    return <MachinePage machineIds={machineIdsString} />;
  }

  // 2. Mặc định hiển thị Dashboard danh sách máy
  return <DashboardPage />;
}