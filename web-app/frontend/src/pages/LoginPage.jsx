// web-app/frontend/src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // BẢO MẬT: Kiểm tra dữ liệu đầu vào cơ bản ở client
    if (!username || !password) {
      setError('Vui lòng nhập đầy đủ tài khoản và mật khẩu!');
      setIsLoading(false);
      return;
    }

    try {
      // ⚠️ ĐOẠN NÀY LÀ MOCK DATA (GIẢ LẬP) ĐỂ BẠN TEST TRƯỚC UI
      // Sau này khi làm Backend xong, ta sẽ thay đoạn này bằng axios.post('/api/auth/login')
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Giả lập delay mạng 1s

      if (username === 'admin' && password === 'admin123') {
        // Đăng nhập thành công -> Lưu token giả lập vào localStorage
        localStorage.setItem('token', 'mock-jwt-token-xyz');
        localStorage.setItem('user', JSON.stringify({ username: 'admin', role: 'root' }));
        
        // Chuyển hướng sang trang Dashboard
        navigate('/dashboard');
      } else {
        setError('Tài khoản hoặc mật khẩu không chính xác!');
      }
    } catch (err) {
      setError('Có lỗi xảy ra kết nối đến server. Vui lòng thử lại!');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <h2 style={styles.title}>REMOTE CONTROL SYSTEM</h2>
          <p style={styles.subtitle}>Đồ án Mạng Máy Tính - Hệ thống điều khiển từ xa</p>
        </div>

        <form onSubmit={handleLogin} style={styles.form}>
          {error && <div style={styles.errorAlert}>{error}</div>}

          <div style={styles.inputGroup}>
            <label style={styles.label}>Tài khoản Admin</label>
            <input
              type="text"
              placeholder="Nhập tài khoản..."
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              disabled={isLoading}
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>Mật khẩu</label>
            <input
              type="password"
              placeholder="Nhập mật khẩu..."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              disabled={isLoading}
            />
          </div>

          <button type="submit" style={styles.button} disabled={isLoading}>
            {isLoading ? 'Đang xác thực...' : 'Đăng Nhập Hệ Thống'}
          </button>
        </form>

        <div style={styles.footer}>
          <p>⚠️ Lưu ý: Mọi hoạt động điều khiển đều được ghi lại log bảo mật.</p>
        </div>
      </div>
    </div>
  );
}

// Inline CSS style cơ bản để giao diện nhìn gọn gàng ngay lập tức (Bạn có thể đổi sang Tailwind sau nhé)
const styles = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#f0f2f5', fontFamily: 'Segoe UI, sans-serif' },
  card: { width: '100%', maxVerticalWidth: '400px', padding: '2.5rem', borderRadius: '12px', backgroundColor: '#ffffff', boxShadow: '0 8px 24px rgba(0,0,0,0.1)' },
  header: { textAlign: 'center', marginBottom: '2rem' },
  title: { color: '#1e3a8a', margin: '0 0 0.5rem 0', fontSize: '1.6rem', fontWeight: 'bold', letterSpacing: '0.5px' },
  subtitle: { color: '#6b7280', margin: 0, fontSize: '0.9rem' },
  form: { display: 'flex', flexDirection: 'column', gap: '1.2rem' },
  inputGroup: { display: 'flex', flexDirection: 'column', gap: '0.4rem' },
  label: { fontSize: '0.875rem', fontWeight: '600', color: '#374151' },
  input: { padding: '0.75rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '1rem', outline: 'none', transition: 'border 0.2s' },
  button: { padding: '0.75rem', borderRadius: '6px', border: 'none', backgroundColor: '#2563eb', color: '#ffffff', fontSize: '1rem', fontWeight: '600', cursor: 'pointer', transition: 'background 0.2s' },
  errorAlert: { padding: '0.75rem', borderRadius: '6px', backgroundColor: '#fee2e2', color: '#dc2626', fontSize: '0.875rem', border: '1px solid #fca5a5' },
  footer: { marginTop: '2rem', textAlign: 'center', fontSize: '0.8rem', color: '#9ca3af' }
};

export default LoginPage;
