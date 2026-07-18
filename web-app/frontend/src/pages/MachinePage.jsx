// web-app/frontend/src/pages/MachinePage.jsx
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// ==========================================
// 📦 1. IMPORT CÁC MODULE CHÍNH THỨC CỦA ĐỒ ÁN
// ==========================================
import Applications from '../components/modules/Applications'; // 🚀 Tab 1: Ứng dụng
import ProcessesManager from '../components/modules/Processes'; // 📊 Tab 2: Tiến trình System
import Screenshot from '../components/modules/Screenshot';       // 📸 Tab 3: Chụp màn hình
import LiveScreen from '../components/modules/LiveScreen';       // 📺 Tab 4: Livestream màn hình
import WebcamMonitor from '../components/modules/Webcam';         // 📷 Tab 5: Giám sát Webcam
import KeyLogger from '../components/modules/KeyLogger';         // ⌨️ Tab 6: Nhật ký gõ phím
import FileDownload from '../components/modules/FileDownload';   // 📁 Tab 7: Quản lý tập tin từ xa
import PowerControl from '../components/modules/PowerControl';   // 🔌 Tab 8: Điều khiển nguồn

function MachinePage() {
  // id được lấy từ URL (Ví dụ: /machine/agent_01 -> id sẽ là "agent_01")
  const { id } = useParams();
  const navigate = useNavigate();

  // Quản lý Tab nào đang hiển thị dữ liệu trên màn hình, mặc định vào sẽ mở tab Tiến trình
  const [activeTab, setActiveTab] = useState('processes');

  // ==========================================
  // 📋 2. CẤU HÌNH DANH SÁCH MENU ĐIỀU KHIỂN (SIDEBAR) - ĐÃ CẮT BỚT TÍNH NĂNG DƯ THỪA
  // ==========================================
  const menuItems = [
    { id: 'apps', label: '1. Danh Sách Ứng Dụng', desc: 'Quét phần mềm hệ thống' },
    { id: 'processes', label: '2. Quản Lý Tiến Trình', desc: 'Task Manager & Diệt PID' },
    { id: 'screenshot', label: '3. Chụp Màn Hình', desc: 'Bản chụp ảnh từ xa (Base64)' },
    { id: 'live-screen', label: '4. Xem Trực Tiếp', desc: 'Luồng livestream màn hình' },
    { id: 'webcam', label: '5. Giám Sát Webcam', desc: 'Truyền phát camera thời gian thực' },
    { id: 'keylogger', label: '6. Nhật Ký Bàn Phím', desc: 'Theo dõi phím gõ ngầm trên RAM' },
    { id: 'files', label: '7. Quản Lý Tập Tin', desc: 'Xem, tải xuống, xóa file an toàn' },
    { id: 'power', label: '8. Điều Khiển Nguồn', desc: 'Tắt nguồn, khởi động, khóa máy' }
  ];

  // ==========================================
  // ⚙️ 3. BỘ ĐỊNH TUYẾN NỘI BỘ (RENDER CONTROLLER)
  // ==========================================
  const renderModuleContent = () => {
    switch (activeTab) {
      case 'apps':
        return <Applications machineId={id} />;
        
      case 'processes':
        return <ProcessesManager machineId={id} />;
        
      case 'screenshot':
        return <Screenshot machineId={id} />;
        
      case 'live-screen':
        return <LiveScreen machineId={id} />;
        
      case 'webcam':
        return <WebcamMonitor machineId={id} />;
        
      case 'keylogger':
        return <KeyLogger machineId={id} />;
        
      case 'files':
        return <FileDownload machineId={id} />;
        
      case 'power':
        return <PowerControl machineId={id} />;
        
      default:
        return <div style={styles.message}>Không tìm thấy tính năng yêu cầu.</div>;
    }
  };

  // ==========================================
  // 🖼️ 4. BỐ CỤC GIAO DIỆN (HTML/JSX)
  // ==========================================
  return (
    <div style={styles.container}>
      {/* 🔝 THANH ĐIỀU HƯỚNG TRÊN CÙNG (NAVBAR) */}
      <nav style={styles.navbar}>
        <div style={styles.navLeft}>
          <button onClick={() => navigate('/dashboard')} style={styles.backBtn}>⬅️ Quay Lại</button>
          <h2 style={styles.logo}>⚙️ Bảng Điều Khiển Thiết Bị</h2>
        </div>
        <div style={styles.navRight}>
          <span style={styles.machineBadge}>MÁY MỤC TIÊU: <strong style={{fontFamily: 'monospace'}}>{id}</strong></span>
        </div>
      </nav>

      {/* 🗂️ THÂN TRANG CHIA LÀM 2 BÊN: SIDEBAR VÀ PHÂN KHU NỘI DUNG */}
      <div style={styles.layoutBody}>
        {/* 🛠️ MENU CHỌN TÍNH NĂNG BÊN TRÁI */}
        <aside style={styles.sidebar}>
          <div style={styles.sidebarTitle}>DANH MỤC CHỨC NĂNG</div>
          <div style={styles.menuList}>
            {menuItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    ...styles.menuItem,
                    backgroundColor: isActive ? '#2563eb' : 'white',
                    color: isActive ? 'white' : '#1e293b',
                    borderColor: isActive ? '#2563eb' : '#e2e8f0',
                  }}
                >
                  <div style={{fontWeight: 'bold', fontSize: '0.9rem'}}>{item.label}</div>
                  <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: isActive ? '#93c5fd' : '#64748b' }}>
                    {item.desc}
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        {/* 📺 MÀN HÌNH HIỂN THỊ NỘI DUNG CHI TIẾT BÊN PHẢI */}
        <main style={styles.mainContent}>
          {renderModuleContent()}
        </main>
      </div>
    </div>
  );
}

// ==========================================
// 🎨 5. KHÔNG GIAN ĐỊNH DẠNG MỸ THUẬT (CSS-IN-JS)
// ==========================================
const styles = {
  container: { backgroundColor: '#f8fafc', minHeight: '100vh', fontFamily: 'Segoe UI, sans-serif', display: 'flex', flexDirection: 'column' },
  navbar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0f172a', padding: '1rem 2rem', color: 'white', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', zIndex: 10 },
  navLeft: { display: 'flex', alignItems: 'center', gap: '1.5rem' },
  logo: { margin: 0, fontSize: '1.2rem', fontWeight: 'bold' },
  backBtn: { backgroundColor: '#334155', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem', transition: 'background-color 0.2s' },
  navRight: { display: 'flex', alignItems: 'center' },
  machineBadge: { fontSize: '0.85rem', color: '#cbd5e1', backgroundColor: '#1e293b', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #334155' },
  layoutBody: { display: 'flex', flex: 1, flexDirection: 'row', minHeight: 'calc(100vh - 65px)' },
  sidebar: { width: '300px', backgroundColor: 'white', borderRight: '1px solid #e2e8f0', padding: '1.5rem 1rem', display: 'flex', flexDirection: 'column', gap: '1rem' },
  sidebarTitle: { fontSize: '0.75rem', fontWeight: 'bold', color: '#94a3b8', letterSpacing: '0.05em', paddingLeft: '0.5rem' },
  menuList: { display: 'flex', flexDirection: 'column', gap: '0.5rem' },
  menuItem: { width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s', display: 'flex', flexDirection: 'column' },
  mainContent: { flex: 1, padding: '2rem', overflowY: 'auto' },
  message: { textAlign: 'center', padding: '3rem', fontSize: '1.1rem', color: '#64748b', fontWeight: '500' }
};

export default MachinePage;