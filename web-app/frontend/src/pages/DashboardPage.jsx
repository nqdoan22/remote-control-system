// web-app/frontend/src/pages/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import MachineList from '../components/shared/MachineList'; // 🚀 IMPORT COMPONENT ĐÃ VIẾT

function DashboardPage() {
  const navigate = useNavigate();
  const [machines, setMachines] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchMachines = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('http://127.0.0.1:8000/api/machines/');
        if (response.data.status === 'success') {
          setMachines(response.data.data);
        }
      } catch (err) {
        console.error(err);
        setError('Không thể kết nối đến máy chủ Backend để lấy danh sách máy!');
      } finally {
        setIsLoading(false);
      }
    };
    fetchMachines();
  }, []);

  // 🔍 Lọc danh sách máy dựa trên thanh tìm kiếm
  const filteredMachines = machines.filter(machine => 
    machine.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    machine.ip.includes(searchTerm)
  );

  // 🔄 Đồng bộ hóa cấu trúc dữ liệu Backend sang Props của MachineList
  const readyMachinesData = filteredMachines.map(m => ({
    id: m.id,
    status: m.status,
    os: m.os,
    ip_address: m.ip, // Đồng bộ hóa: chuyển m.ip thành ip_address cho khớp MachineList
    last_seen: m.last_seen || 'Vừa xong'
  }));

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div style={styles.container}>
      {/* NAVBAR TỔNG */}
      <nav style={styles.navbar}>
        <h2 style={styles.logo}>🛡️ Trung Tâm Giám Sát Mạng LAN</h2>
        <div style={styles.navRight}>
          <span style={styles.adminInfo}>Xin chào, <strong>Admin</strong></span>
          <button onClick={handleLogout} style={styles.logoutBtn}>Đăng Xuất 🚪</button>
        </div>
      </nav>

      {/* THÔNG TIN CHUNG & THANH TÌM KIẾM */}
      <div style={styles.mainContent}>
        <div style={styles.dashboardHeader}>
          <div>
            <h3 style={{ margin: 0, color: '#1e293b' }}>Danh Sách Các Máy Agent</h3>
            <p style={styles.subTitle}>Tổng số máy quản lý: {machines.length}</p>
          </div>
          <input 
            type="text" 
            placeholder="🔍 Tìm kiếm nhanh bằng Tên hoặc IP..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
          />
        </div>

        {/* TRẠNG THÁI TẢI / LỖI */}
        {isLoading && <div style={styles.message}>🔄 Đang tải danh sách thiết bị từ Backend...</div>}
        {error && <div style={{...styles.message, color: '#ef4444'}}>{error}</div>}

        {/* 💻 GỌI COMPONENT MACHINELIST DÙNG CHUNG */}
        {!isLoading && !error && (
          <MachineList 
            machines={readyMachinesData} 
            onMachineClick={(machineId) => navigate(`/machine/${machineId}`)} 
          />
        )}
      </div>
    </div>
  );
}

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
  message: { textAlign: 'center', padding: '3rem', fontSize: '1.1rem', color: '#64748b', fontWeight: '500' }
};

export default DashboardPage;