import React, { useState } from 'react';
import { authService } from '../services/api';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(''); // Reset lại thông báo lỗi trước khi bấm gửi

    try {
      await authService.login(username, password);
      // Đăng nhập xong thì chuyển hướng sang dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      // 1. "Bắt quả tang" lỗi thật sự in ra màn hình Console (F12) để gỡ lỗi
      console.error("Chi tiết lỗi Đăng nhập:", err);

      // 2. Phân tách lỗi để hiển thị câu thông báo chuẩn xác lên giao diện
      if (err.response) {
        // Backend có phản hồi nhưng trả về mã lỗi (401, 400, 422,...)
        const backendMessage = err.response.data?.detail;
        setError(backendMessage || 'Đăng nhập thất bại. Vui lòng thử lại!');
      } else if (err.request) {
        // Request đã gửi đi nhưng không nhận được phản hồi (Server Backend bị sập hoặc sai IP/Port)
        setError('Không thể kết nối tới Server Backend (Đang sập hoặc lỗi kết nối mạng)!');
      } else {
        // Lỗi xảy ra khi thiết lập request trong code
        setError('Đã xảy ra lỗi hệ thống: ' + err.message);
      }
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px', border: '1px solid #ccc' }}>
      <h2>Remote Control - Login</h2>
      {error && <p style={{ color: 'red', fontWeight: 'bold' }}>{error}</p>}
      <form onSubmit={handleLogin}>
        <div>
          <label>Username:</label>
          <input 
            type="text" 
            value={username} 
            onChange={e => setUsername(e.target.value)} 
            style={{ width: '100%', marginBottom: '10px' }} 
            required
          />
        </div>
        <div>
          <label>Password:</label>
          <input 
            type="password" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
            style={{ width: '100%', marginBottom: '10px' }} 
            required
          />
        </div>
        <button type="submit" style={{ width: '100%', padding: '10px', cursor: 'pointer' }}>Đăng nhập</button>
      </form>
    </div>
  );
}

export default LoginPage;