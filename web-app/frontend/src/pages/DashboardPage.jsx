// web-app/frontend/src/pages/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function DashboardPage() {
  const navigate = useNavigate();
  
  // --- 🧠 KHU VỰC QUẢN LÝ TRẠNG THÁI (STATE) ---
  const [machines, setMachines] = useState([]);      // Lưu danh sách toàn bộ máy tính quét được trong LAN
  const [searchTerm, setSearchTerm] = useState('');  // Lưu từ khóa người dùng gõ để tìm kiếm máy
  const [isLoading, setIsLoading] = useState(true);   // Trạng thái chờ khi hệ thống đang quét mạng

  // --- 🔄 1. TỰ ĐỘNG QUÉT DANH SÁCH MÁY KHI VỪA VÀO TRANG ---
  useEffect(() => {
    const fetchMachines = async () => {
      setIsLoading(true);
      
      // Giả lập độ trễ mạng LAN (chờ server phản hồi trong 0.8 giây)
      await new Promise((resolve) => setTimeout(resolve, 800)); 
      
      // MOCK DATA: Danh sách các máy Agent chạy Windows giả lập phục vụ chấm đồ án
      const mockData = [
        { id: 'agent_01', name: 'DESKTOP-PHONG-LAB-A', ip: '192.168.1.15', status: 'online', os: 'Windows 11 Pro' },
        { id: 'agent_02', name: 'LAPTOP-GIANG-VIEN', ip: '192.168.1.20', status: 'online', os: 'Windows 10 Home' },
        { id: 'agent_03', name: 'SERVER-BACKUP-TEST', ip: '192.168.1.100', status: 'offline', os: 'Windows Server 2022' }
      ];
      
      setMachines(mockData); // Cập nhật dữ liệu vào bộ nhớ State để hiển thị lên UI
      setIsLoading(false);   // Quét xong, tắt màn hình chờ
    };

    fetchMachines();
  }, []); // Cặp ngoặc vuông trống bảo đảm hàm này chỉ tự kích hoạt ĐÚNG 1 LẦN khi tải trang

  // --- 🧹 2. HÀM PHỤ XỬ LÝ ĐĂNG XUẤT ---
  const handleLogout = () => {
    localStorage.removeItem('token'); // Xóa vé thông hành bảo mật
    localStorage.removeItem('user');
    navigate('/login');               // Đá người dùng quay lại trang Login
  };

  // --- 🔍 3. LOGIC LỌC TÌM KIẾM MÁY NHANH ---
  // Tự động lọc danh sách mỗi khi người dùng gõ chữ vào ô tìm kiếm (Không cần tải lại trang)
  const filteredMachines = machines.filter(machine => 
    machine.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    machine.ip.includes(searchTerm)
  );

  // --- 🎨 KHU VỰC GIAO DIỆN HIỂN THỊ (JSX) ---
  return (
    <div style={styles.container}>
      {/* 🧭 Thanh điều hướng trên cùng (Navbar) */}
      <header style={styles.header}>
        <h2 style={styles.logo}>🖥️ REMOTE CONTROL SYSTEMS</h2>
        <div style={styles.userInfo}>
          <span style={styles.userLabel}>Quyền hạn: Root Admin</span>
          <button onClick={handleLogout} style={styles.logoutBtn}>Đăng Xuất</button>
        </div>
      </header>

      {/* 📊 Phần nội dung chính (Main Content) */}
      <main style={styles.mainContent}>
        <div style={styles.titleSection}>
          <h3 style={styles.mainTitle}>Bảng Điều Khiển Tập Trung (LAN)</h3>
          <p style={styles.subTitle}>Hệ thống phát hiện tự động các máy Agent đang chạy trên hạ tầng mạng nội bộ.</p>
        </div>

        {/* 🔍 Thanh Tìm Kiếm Máy */}
        <div style={styles.searchBarContainer}>
          <input 
            type="text" 
            placeholder="🔍 Tìm nhanh theo Tên máy tính hoặc địa chỉ IP..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)} // Đồng bộ chữ gõ vào State searchTerm
            style={styles.searchInput}
          />
        </div>

        {/* ⏳ Hiển thị màn hình chờ nếu hệ thống đang tải */}
        {isLoading ? (
          <div style={styles.loading}>🔄 Đang quét các máy tính trong mạng LAN, vui lòng đợi...</div>
        ) : (
          /* 🗺️ Vẽ sơ đồ danh sách các máy dưới dạng lưới (Grid Layout) */
          <div style={styles.grid}>
            {filteredMachines.map((machine) => (
              <div key={machine.id} style={styles.card}>
                
                {/* Tiêu đề của từng Thẻ Máy tính */}
                <div style={styles.cardHeader}>
                  <span style={{ 
                    ...styles.statusDot, 
                    backgroundColor: machine.status === 'online' ? '#10b981' : '#9ca3af' // Xanh nếu online, Xám nếu offline
                  }}></span>
                  <h4 style={styles.machineName}>{machine.name}</h4>
                </div>
                
                {/* Nội dung thông số kỹ thuật của Máy */}
                <div style={styles.cardBody}>
                  <p style={styles.infoLine}><strong>Địa chỉ IP:</strong> {machine.ip}</p>
                  <p style={styles.infoLine}><strong>Hệ điều hành:</strong> {machine.os}</p>
                  <p style={styles.infoLine}><strong>Kết nối mạng:</strong> 
                    <span style={{ 
                      color: machine.status === 'online' ? '#10b981' : '#ef4444', 
                      marginLeft: '6px', 
                      fontWeight: 'bold' 
                    }}>
                      {machine.status === 'online' ? '● ONLINE' : '○ OFFLINE'}
                    </span>
                  </p>
                </div>

                {/* Nút bấm hành động tương tác */}
                <button 
                  disabled={machine.status === 'offline'} // BẢO MẬT: Máy offline thì không cho bấm kết nối
                  onClick={() => navigate(`/machine/${machine.id}`)} // Bấm nút sẽ chuyển sang trang điều khiển chi tiết của máy đó
                  style={{
                    ...styles.connectBtn,
                    backgroundColor: machine.status === 'online' ? '#2563eb' : '#cbd5e1',
                    cursor: machine.status === 'online' ? 'pointer' : 'not-allowed'
                  }}
                >
                  {machine.status === 'online' ? 'Vào Điều Khiển' : 'Thiết Bị Ngoại Tuyến'}
                </button>

              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

// --- 🖌️ ĐỊNH NGHĨA PHONG CÁCH GIAO DIỆN (INLINE CSS) ---
const styles = {
  container: { backgroundColor: '#f8fafc', minHeight: '100vh', fontFamily: 'Segoe UI, Arial, sans-serif' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem', backgroundColor: '#0f172a', color: '#ffffff', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' },
  logo: { margin: 0, fontSize: '1.25rem', fontWeight: 'bold', letterSpacing: '0.5px' },
  userInfo: { display: 'flex', alignItems: 'center', gap: '1.5rem' },
  userLabel: { fontSize: '0.9rem', color: '#94a3b8' },
  logoutBtn: { backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', transition: 'all 0.2s' },
  mainContent: { padding: '2.5rem' },
  titleSection: { marginBottom: '2rem' },
  mainTitle: { margin: '0 0 0.5rem 0', color: '#1e293b', fontSize: '1.5rem' },
  subTitle: { margin: 0, color: '#64748b', fontSize: '0.95rem' },
  searchBarContainer: { marginBottom: '2rem' },
  searchInput: { width: '100%', maxVerticalWidth: '450px', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.95rem', outline: 'none', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' },
  loading: { textAlign: 'center', padding: '4rem', color: '#64748b', fontSize: '1.1rem', fontWeight: '500' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '2rem' },
  card: { backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.02)', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' },
  cardHeader: { display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' },
  statusDot: { width: '10px', height: '10px', borderRadius: '50%' },
  machineName: { margin: 0, fontSize: '1.1rem', color: '#0f172a', fontWeight: '600' },
  cardBody: { fontSize: '0.9rem', color: '#334155', marginBottom: '1.5rem' },
  infoLine: { margin: '0 0 0.6rem 0' },
  connectBtn: { color: '#ffffff', border: 'none', padding: '0.8rem', borderRadius: '8px', fontSize: '0.95rem', fontWeight: '600', transition: 'background 0.2s', width: '100%' }
};

export default DashboardPage;