import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// 1. IMPORT HÀM KẾT NỐI BACKEND TỪ FILE api.js
import { loginApi } from '../services/api';

const LoginPage = () => {
  // =========================================================================
  // STATE MANAGEMENT (Quản lý dữ liệu & trạng thái giao diện)
  // =========================================================================
  
  // Lưu trữ chuỗi người dùng gõ vào ô Username và Password
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Lưu thông báo lỗi nếu đăng nhập thất bại (để hiển thị dòng chữ màu đỏ)
  const [error, setError] = useState('');

  // Trạng thái chờ (Đang gửi request lên server thì hiệu ứng loading bật lên)
  const [loading, setLoading] = useState(false);

  // Hook dùng để chuyển hướng trang của thư viện react-router-dom
  const navigate = useNavigate();

  // =========================================================================
  // HANDLER (Hàm xử lý sự kiện khi Admin bấm nút "Đăng nhập")
  // =========================================================================
  const handleSubmit = async (e) => {
    // Chặn hành vi mặc định của Form (chặn việc trình duyệt tự reload lại trang)
    e.preventDefault();

    // Làm sạch thông báo lỗi cũ và bật trạng thái đang xử lý (Loading)
    setError('');
    setLoading(true);

    try {
      /* 
        🚀 GỌI API BACKEND: 
        Gửi Object { username, password } xuống FastAPI.
        Khớp 100% với LoginRequest Schema trong backend/schemas/auth.py
      */
      const response = await loginApi({ username, password });

      /* 
        🔑 XỬ LÝ KẾT QUẢ TRẢ VỀ:
        Backend phản hồi theo Token Schema: { access_token: "eyJhbG...", token_type: "bearer" }
      */
      if (response && response.access_token) {
        // 1. Lưu JWT Token vào bộ nhớ Trình duyệt (localStorage) để dùng cho các request tiếp theo
        localStorage.setItem('access_token', response.access_token);

        // 2. Chuyển hướng Admin vào thẳng trang Dashboard (Trang tổng quan)
        navigate('/');
      }
    } catch (err) {
      /* 
        ❌ XỬ LÝ LỖI:
        Nếu Backend trả về lỗi status 401 (sai pass), lỗi 500 hoặc mất mạng
      */
      console.error('Lỗi đăng nhập:', err);

      // Ưu tiên lấy câu thông báo lỗi từ Backend trả về, nếu không có thì xài câu mặc định
      const errorMessage =
        err.detail || err.message || 'Tên đăng nhập hoặc mật khẩu không chính xác!';
      
      setError(errorMessage);
    } finally {
      // Dù đăng nhập Thành công hay Thất bại thì cũng tắt trạng thái Loading
      setLoading(false);
    }
  };

  // =========================================================================
  // JSX INTERFACE (Phần giao diện hiển thị ra màn hình)
  // =========================================================================
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* Tiêu đề Trang */}
        <div style={styles.header}>
          <h2 style={styles.title}>HỆ THỐNG QUẢN TRỊ RAT</h2>
          <p style={styles.subtitle}>Đăng nhập dành cho Administrator</p>
        </div>

        {/* Thông báo lỗi nếu Đăng nhập thất bại */}
        {error && <div style={styles.errorAlert}>{error}</div>}

        {/* Form Đăng nhập */}
        <form onSubmit={handleSubmit} style={styles.form}>
          {/* Ô nhập Tài khoản */}
          <div style={styles.inputGroup}>
            <label style={styles.label}>Tên tài khoản</label>
            <input
              type="text"
              required
              placeholder="Nhập username..."
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              disabled={loading}
            />
          </div>

          {/* Ô nhập Mật khẩu */}
          <div style={styles.inputGroup}>
            <label style={styles.label}>Mật khẩu</label>
            <input
              type="password"
              required
              placeholder="Nhập mật khẩu..."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              disabled={loading}
            />
          </div>

          {/* Nút Submit Đăng nhập */}
          <button
            type="submit"
            disabled={loading}
            style={{
              ...styles.button,
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Đang xác thực...' : 'ĐĂNG NHẬP'}
          </button>
        </form>
      </div>
    </div>
  );
};

// =========================================================================
// INLINE STYLES (Style thuần giúp giao diện gọn đẹp ngay lập tức)
// (Bạn có thể chuyển sang Tailwind CSS hoặc CSS Module sau nếu muốn)
// =========================================================================
const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#0f172a', // Màu nền tối Cyberpunk/Admin
    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
  },
  card: {
    width: '100%',
    maxWidth: '400px',
    padding: '32px',
    backgroundColor: '#1e293b',
    borderRadius: '12px',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
    border: '1px solid #334155',
  },
  header: {
    textAlign: 'center',
    marginBottom: '24px',
  },
  title: {
    color: '#38bdf8',
    fontSize: '22px',
    margin: '0 0 8px 0',
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#94a3b8',
    fontSize: '14px',
    margin: 0,
  },
  errorAlert: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    color: '#f87171',
    border: '1px solid #ef4444',
    padding: '10px 14px',
    borderRadius: '6px',
    fontSize: '14px',
    marginBottom: '20px',
    textAlign: 'center',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    color: '#cbd5e1',
    fontSize: '14px',
  },
  input: {
    padding: '10px 12px',
    borderRadius: '6px',
    border: '1px solid #475569',
    backgroundColor: '#0f172a',
    color: '#ffffff',
    fontSize: '14px',
    outline: 'none',
  },
  button: {
    marginTop: '8px',
    padding: '12px',
    borderRadius: '6px',
    border: 'none',
    backgroundColor: '#0284c7',
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: '15px',
    transition: 'background-color 0.2s',
  },
};

export default LoginPage;