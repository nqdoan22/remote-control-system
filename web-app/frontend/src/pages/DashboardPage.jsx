// web-app/frontend/src/pages/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // 🌟 Import axios để kết nối xuống Backend Python

function DashboardPage() {
  const navigate = useNavigate();

  // --- 🧠 1. QUẢN LÝ TRẠNG THÁI (STATE) ---
  const [machines, setMachines] = useState([]); // Danh sách máy trống, sẽ nạp dữ liệu từ Backend sau
  const [searchTerm, setSearchTerm] = useState(''); // Từ khóa tìm kiếm máy
  const [isLoading, setIsLoading] = useState(true); // Trạng thái đang tải dữ liệu
  const [error, setError] = useState(''); // Trạng thái lưu lỗi nếu sập mạng

  // --- 🔄 2. HÀM TỰ ĐỘNG QUÉT VÀ LẤY DỮ LIỆU TỪ BACKEND ---
  useEffect(() => {
    const fetchMachines = async () => {
      try {
        setIsLoading(true);
        // 🔗 Gọi API thật xuống phòng machines.py ở Port 8000
        const response = await axios.get('http://127.0.0.1:8000/api/machines/');
        
        if (response.data.status === 'success') {
          setMachines(response.data.data); // Nạp danh sách máy thật vào State
        }
      } catch (err) {
        console.error(err);
        setError('Không thể kết nối đến máy chủ Backend để lấy danh sách máy!');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMachines(); // Kích hoạt hàm gọi dữ liệu
  }, []);

  // --- 🔍 3. LOGIC LỌC TÌM KIẾM MÁY NHANH (GIỮ NGUYÊN BẢN CHẤT CỦA BẠN) ---
  const filteredMachines = machines.filter(machine => 
    machine.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    machine.ip.includes(searchTerm)
  );

  // --- 🚪 4. HÀM ĐĂNG XUẤT (LOGOUT) ---
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div style={styles.container}>
      {/* 🧭 THANH ĐIỀU HƯỚNG TRÊN CÙNG */}
      <nav style={styles.navbar}>
        <h2 style={styles.logo}>🛡️ Trung Tâm Giám Sát Mạng LAN</h2>
        <div style={styles.navRight}>
          <span style={styles.adminInfo}>Xin chào, <strong>Admin</strong></span>
          <button onClick={handleLogout} style={styles.logoutBtn}>Đăng Xuất 🚪</button>
        </div>
      </nav>

      {/* 📊 KHU VỰC THÔNG SỐ TỔNG QUAN VÀ THANH TÌM KIẾM */}
      <div style={styles.mainContent}>
        <div style={styles.dashboardHeader}>
          <div>
            <h3>Danh Sách Các Máy Agent</h3>
            <p style={styles.subTitle}>Tổng số máy quản lý: {machines.length}</p>
          </div>
          {/* Ô nhập từ khóa tìm kiếm nhanh */}
          <input 
            type="text" 
            placeholder="🔍 Tìm kiếm nhanh bằng Tên hoặc IP..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
          />
        </div>

        {/* ⏳ HIỂN THỊ TRẠNG THÁI ĐANG TẢI HOẶC LỖI KẾT NỐI */}
        {isLoading && <div style={styles.message}>🔄 Đang tải danh sách thiết bị từ Backend...</div>}
        {error && <div style={{...styles.message, color: '#ef4444'}}>{error}</div>}

        {/* 💻 DANH SÁCH MÁY TÍNH HIỂN THỊ DẠNG GRID */}
        {!isLoading && !error && (
          <div style={styles.grid}>
            {filteredMachines.map((machine) => (
              <div key={machine.id} style={styles.card}>
                <div style={styles.cardHeader}>
                  <h4 style={styles.machineName}>{machine.name}</h4>
                  {/* Chấm tròn báo trạng thái xanh/xám */}
                  <span style={{
                    ...styles.statusBadge, 
                    backgroundColor: machine.status === 'online' ? '#10b981' : '#94a3b8'
                  }}>
                    {machine.status.toUpperCase()}
                  </span>
                </div>
                <div style={styles.cardBody}>
                  <p><strong>IP:</strong> {machine.ip}</p>
                  <p><strong>Hệ điều hành:</strong> {machine.os}</p>
                </div>
                {/* Nút bấm chuyển hướng sang trang điều khiển chi tiết */}
                <button 
                  onClick={() => navigate(`/machine/${machine.id}`)} 
                  disabled={machine.status === 'offline'}
                  style={{
                    ...styles.controlBtn,
                    backgroundColor: machine.status === 'online' ? '#2563eb' : '#cbd5e1',
                    cursor: machine.status === 'online' ? 'pointer' : 'not-allowed'
                  }}
                >
                  {machine.status === 'online' ? 'Vào Điều Khiển ⚙️' : 'Mất Kết Nối ❌'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// --- 🖌️ CSS INLINE CHO GIAO DIỆN (ĐÃ ĐƯỢC CHUẨN HÓA) ---
const styles = {
  container: { backgroundColor: '#f8fafc', minHeight: '100vh', fontFamily: 'Segoe UI, sans-serif' },
  navbar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0f172a', padding: '1rem 2rem', color: 'white', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' },
  logo: { margin: 0, fontSize: '1.2rem', fontWeight: 'bold' },
  navRight: { display: 'flex', alignItems: 'center', gap: '1.5rem' },
  adminInfo: { fontSize: '0.9rem', color: '#cbd5e1' },
  logoutBtn: { backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem' },
  mainContent: { padding: '2rem' },
  dashboardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' },
  subTitle: { margin: '0.2rem 0 0 0', color: '#64748b', fontSize: '0.9rem' },
  searchInput: { width: '320px', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' },
  card: { backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' },
  machineName: { margin: 0, fontSize: '1.05rem', color: '#1e293b', fontWeight: 'bold' },
  statusBadge: { color: 'white', fontSize: '0.7rem', padding: '0.25rem 0.6rem', borderRadius: '50px', fontWeight: 'bold' },
  cardBody: { fontSize: '0.85rem', color: '#475569', lineHeight: '1.6', marginBottom: '1.25rem' },
  controlBtn: { width: '100%', color: 'white', border: 'none', padding: '0.65rem', borderRadius: '6px', fontWeight: 'bold', fontSize: '0.9rem', transition: 'all 0.2s' },
  message: { textAlign: 'center', padding: '3rem', fontSize: '1.1rem', color: '#64748b', fontWeight: '500' }
};

export default DashboardPage;