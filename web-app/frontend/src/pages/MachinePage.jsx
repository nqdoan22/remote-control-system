// web-app/frontend/src/pages/MachinePage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function MachinePage() {
  const { machineId } = useParams(); // 🔍 Lấy ID của máy từ URL (Ví dụ: agent_01)
  const navigate = useNavigate();

  // --- 🧠 1. QUẢN LÝ TRẠNG THÁI (STATE) ---
  const [activeTab, setActiveTab] = useState('screen'); // Tab đang được chọn (mặc định là Live Screen)
  const [machineInfo, setMachineInfo] = useState(null); // Lưu thông tin phần cứng của máy đang điều khiển
  
  // Các State lưu dữ liệu giả lập cho từng module chức năng
  const [screenshot, setScreenshot] = useState('https://via.placeholder.com/800x450.png?text=Live+Screen+Stream+Form+Agent');
  const [processes, setProcesses] = useState([]);
  const [apps, setApps] = useState([]);
  const [keystrokes, setKeystrokes] = useState('--- Nhật ký Keylogger bắt đầu ở đây ---\n[User gõ]: facebook.com\n[User gõ]: taikhoan@gmail.com\n[User gõ]: matkhau123');

  // --- 🔄 2. HÀM TỰ ĐỘNG CHẠY KHI VÀO TRANG (LẤY CHI TIẾT CẤU HÌNH MÁY) ---
  useEffect(() => {
    // Giả lập lấy thông tin cấu hình chi tiết của máy dựa vào machineId
    setMachineInfo({
      id: machineId,
      name: machineId === 'agent_01' ? 'DESKTOP-PHONG-LAB-A' : 'LAPTOP-GIANG-VIEN',
      ip: machineId === 'agent_01' ? '192.168.1.15' : '192.168.1.20',
      cpu: 'Intel Core i7-11800H @ 2.30GHz',
      ram: '16 GB DDR4',
      os: 'Windows 11 Pro 64-bit'
    });

    // Nạp dữ liệu giả lập cho danh sách Tiến trình (Processes)
    setProcesses([
      { pid: 4122, name: 'chrome.exe', cpu: '4.2%', ram: '180 MB' },
      { pid: 1024, name: 'svchost.exe', cpu: '0.1%', ram: '24 MB' },
      { pid: 8840, name: 'python.exe (Agent)', cpu: '1.5%', ram: '45 MB' },
      { pid: 5632, name: 'explorer.exe', cpu: '0.8%', ram: '90 MB' }
    ]);

    // Nạp dữ liệu giả lập cho danh sách Ứng dụng (Applications)
    setApps([
      { name: 'Google Chrome', Developer: 'Google LLC', Version: '120.0' },
      { name: 'Python 3.10', Developer: 'Python Software Foundation', Version: '3.10.5' },
      { name: 'Visual Studio Code', Developer: 'Microsoft Corp', Version: '1.85' }
    ]);
  }, [machineId]);

  // --- 🛠️ 3. CÁC HÀM XỬ LÝ SỰ KIỆN (RA LỆNH ĐIỀU KHIỂN) ---
  
  // Hàm gửi lệnh tắt Tiến trình (Kill Process)
  const handleKillProcess = (pid, name) => {
    alert(`[LỆNH ĐÃ GỬI]: Yêu cầu Backend gửi tín hiệu Taskkill đến máy ${machineId} để tắt Tiến trình ${name} (PID: ${pid})`);
    // Cập nhật lại UI: Xóa tiến trình vừa kill ra khỏi danh sách hiển thị
    setProcesses(processes.filter(p => p.pid !== pid));
  };

  // Hàm ra lệnh chụp màn hình mới (Refresh Screen)
  const handleCaptureScreen = () => {
    alert(`[LỆNH ĐÃ GỬI]: Yêu cầu Agent ${machineId} chụp màn hình ngay lập tức!`);
    // Giả lập đổi ảnh để chứng minh tính năng hoạt động
    setScreenshot(`https://via.placeholder.com/800x450.png?text=Screen+Updated+At+${new Date().toLocaleTimeString()}`);
  };

  // Hàm ra lệnh Nguồn máy tính (Shutdown / Restart)
  const handlePowerAction = (action) => {
    const confirmAction = window.confirm(`Bạn có chắc chắn muốn gửi lệnh [${action.toUpperCase()}] đến máy tính này không?`);
    if (confirmAction) {
      alert(`[HỆ THỐNG]: Đã phát lệnh ${action.toUpperCase()} tới máy Agent thông qua kết nối Socket.`);
      if (action === 'shutdown') navigate('/dashboard'); // Nếu tắt máy thì đá admin về Dashboard
    }
  };

  if (!machineInfo) return <div style={styles.loading}>Đang thiết lập kết nối đến Agent...</div>;

  return (
    <div style={styles.container}>
      {/* 💳 PHẦN 1: HEADER - THÔNG TIN CHUNG VÀ NÚT QUAY LẠI */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <button onClick={() => navigate('/dashboard')} style={styles.backBtn}>⬅ Trở Về</button>
          <h2 style={styles.title}>Đang Điều Khiển: <span style={{color: '#38bdf8'}}>{machineInfo.name}</span></h2>
        </div>
        <div style={styles.headerSpecs}>
          <span><strong>IP:</strong> {machineInfo.ip} | <strong>CPU:</strong> {machineInfo.cpu} | <strong>RAM:</strong> {machineInfo.ram}</span>
        </div>
      </header>

      <div style={styles.mainLayout}>
        {/* 🧭 PHẦN 2: SIDEBAR - MENU CHUYỂN TAB 8 MODULE */}
        <aside style={styles.sidebar}>
          <button onClick={() => setActiveTab('screen')} style={{...styles.tabBtn, backgroundColor: activeTab === 'screen' ? '#2563eb' : 'transparent'}}>📺 Live Screen</button>
          <button onClick={() => setActiveTab('processes')} style={{...styles.tabBtn, backgroundColor: activeTab === 'processes' ? '#2563eb' : 'transparent'}}>⚙️ Processes (Tiến trình)</button>
          <button onClick={() => setActiveTab('apps')} style={{...styles.tabBtn, backgroundColor: activeTab === 'apps' ? '#2563eb' : 'transparent'}}>📦 Applications (Ứng dụng)</button>
          <button onClick={() => setActiveTab('keylogger')} style={{...styles.tabBtn, backgroundColor: activeTab === 'keylogger' ? '#2563eb' : 'transparent'}}>⌨️ Keylogger (Theo dõi gõ phím)</button>
          <button onClick={() => setActiveTab('files')} style={{...styles.tabBtn, backgroundColor: activeTab === 'files' ? '#2563eb' : 'transparent'}}>📁 File Explorer</button>
          <button onClick={() => setActiveTab('webcam')} style={{...styles.tabBtn, backgroundColor: activeTab === 'webcam' ? '#2563eb' : 'transparent'}}>📷 Webcam Live</button>
          <button onClick={() => setActiveTab('audio')} style={{...styles.tabBtn, backgroundColor: activeTab === 'audio' ? '#2563eb' : 'transparent'}}>🎙️ Audio Monitor</button>
          <button onClick={() => setActiveTab('power')} style={{...styles.tabBtn, backgroundColor: activeTab === 'power' ? '#2563eb' : 'transparent'}}>🔌 Điều Khiển Nguồn</button>
        </aside>

        {/* 🖥️ PHẦN 3: VÙNG NỘI DUNG CHI TIẾT CỦA TỪNG MODULE */}
        <section style={styles.contentArea}>
          
          {/* TAB 1: LIVE SCREEN */}
          {activeTab === 'screen' && (
            <div>
              <div style={styles.moduleHeader}>
                <h3>📺 Xem và Chụp Màn Hình Trực Tiếp</h3>
                <button onClick={handleCaptureScreen} style={styles.actionBtn}>📸 Chụp Màn Hình Mới</button>
              </div>
              <div style={styles.screenWrapper}>
                <img src={screenshot} alt="Agent Screen" style={styles.screenImg} />
              </div>
            </div>
          )}

          {/* TAB 2: PROCESSES */}
          {activeTab === 'processes' && (
            <div>
              <h3>⚙️ Quản Lý Tiến Trình Đang Chạy Ngầm (Task Manager)</h3>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>PID</th>
                    <th style={styles.th}>Tên Tiến Trình (Process Name)</th>
                    <th style={styles.th}>CPU Usage</th>
                    <th style={styles.th}>RAM Usage</th>
                    <th style={styles.th}>Hành Động</th>
                  </tr>
                </thead>
                <tbody>
                  {processes.map(p => (
                    <tr key={p.pid} style={styles.tr}>
                      <td style={styles.td}>{p.pid}</td>
                      <td style={{...styles.td, fontWeight: 'bold'}}>{p.name}</td>
                      <td style={styles.td}>{p.cpu}</td>
                      <td style={styles.td}>{p.ram}</td>
                      <td style={styles.td}>
                        <button onClick={() => handleKillProcess(p.pid, p.name)} style={styles.killBtn}>Kill Process (Tắt)</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 3: APPLICATIONS */}
          {activeTab === 'apps' && (
            <div>
              <h3>📦 Danh Sách Phần Mềm Đã Cài Đặt (Applications)</h3>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>Tên Ứng Dụng</th>
                    <th style={styles.th}>Nhà Phát Triển</th>
                    <th style={styles.th}>Phiên Bản</th>
                  </tr>
                </thead>
                <tbody>
                  {apps.map((app, index) => (
                    <tr key={index} style={styles.tr}>
                      <td style={{...styles.td, fontWeight: 'bold'}}>{app.name}</td>
                      <td style={styles.td}>{app.Developer}</td>
                      <td style={styles.td}>{app.Version}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 4: KEYLOGGER */}
          {activeTab === 'keylogger' && (
            <div>
              <h3>⌨️ Nhật Ký Gõ Phím Hệ Thống (Keylogger)</h3>
              <p style={{fontSize: '0.9rem', color: '#64748b'}}>Dữ liệu các phím bấm được Agent âm thầm ghi lại và đồng bộ theo thời gian thực.</p>
              <textarea value={keystrokes} readOnly style={styles.textarea} />
            </div>
          )}

          {/* CÁC TAB KHÁC (BẢO TOÀN BỘ KHUNG CHO ĐỒ ÁN) */}
          {activeTab === 'files' && <div><h3>📁 Tính năng File Explorer</h3><p>Giao diện cây thư mục, hỗ trợ Tải file lên (Upload) / Tải file về (Download) từ máy Agent.</p></div>}
          {activeTab === 'webcam' && <div><h3>📷 Tính năng Webcam Live Stream</h3><p>Mở và truyền phát trực tiếp luồng hình ảnh từ Camera của máy mục tiêu.</p></div>}
          {activeTab === 'audio' && <div><h3>🎙️ Tính năng Audio Monitor</h3><p>Ghi âm và giám sát âm thanh từ Microphone thu được tại máy mục tiêu.</p></div>}
          
          {/* TAB 8: POWER CONTROL */}
          {activeTab === 'power' && (
            <div>
              <h3>🔌 Điều Khiển Nguồn Máy Tính Từ Xa</h3>
              <p>Gửi tín hiệu can thiệp trực tiếp vào trạng thái hoạt động của hệ điều hành Agent.</p>
              <div style={{display: 'flex', gap: '1.5rem', marginTop: '2rem'}}>
                <button onClick={() => handlePowerAction('shutdown')} style={{...styles.powerBtn, backgroundColor: '#ef4444'}}>🔴 Tắt Máy Từ Xa (Shutdown)</button>
                <button onClick={() => handlePowerAction('restart')} style={{...styles.powerBtn, backgroundColor: '#f59e0b'}}>🔄 Khởi Động Lại (Restart)</button>
              </div>
            </div>
          )}

        </section>
      </div>
    </div>
  );
}

// --- 🖌️ CSS INLINE PHỤC VỤ HIỂN THỊ CHUYÊN NGHIỆP ---
const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#f8fafc', fontFamily: 'Segoe UI, sans-serif' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 2rem', backgroundColor: '#0f172a', color: 'white' },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '1.5rem' },
  backBtn: { backgroundColor: '#334155', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' },
  title: { margin: 0, fontSize: '1.2rem' },
  headerSpecs: { fontSize: '0.85rem', color: '#cbd5e1' },
  mainLayout: { display: 'flex', flex: 1, overflow: 'hidden' },
  sidebar: { width: '260px', backgroundColor: '#1e293b', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' },
  tabBtn: { width: '100%', color: '#cbd5e1', border: 'none', padding: '0.8rem 1rem', borderRadius: '8px', textAlignment: 'left', cursor: 'pointer', fontWeight: '500', fontSize: '0.9rem', transition: 'all 0.2s', textAlign: 'left' },
  contentArea: { flex: 1, padding: '2rem', overflowY: 'auto', backgroundColor: '#ffffff' },
  moduleHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' },
  actionBtn: { backgroundColor: '#10b981', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' },
  screenWrapper: { width: '100%', maxWidth: '800px', border: '2px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' },
  screenImg: { width: '100%', height: 'auto', display: 'block' },
  table: { width: '100%', borderCollapse: 'collapse', marginTop: '1rem', textAlign: 'left' },
  thRow: { backgroundColor: '#f1f5f9' },
  th: { padding: '0.75rem 1rem', borderBottom: '2px solid #cbd5e1', color: '#334155', fontSize: '0.9rem' },
  tr: { borderBottom: '1px solid #e2e8f0' },
  td: { padding: '0.75rem 1rem', fontSize: '0.9rem', color: '#334155' },
  killBtn: { backgroundColor: '#fee2e2', color: '#ef4444', border: '1px solid #fca5a5', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontWeight: '600', fontSize: '0.8rem' },
  textarea: { width: '100%', height: '300px', padding: '1rem', fontFamily: 'Courier New, monospace', backgroundColor: '#0f172a', color: '#38bdf8', borderRadius: '8px', border: 'none', outline: 'none', marginTop: '1rem', fontSize: '0.95rem', lineHeight: '1.5' },
  powerBtn: { color: 'white', border: 'none', padding: '1rem 2rem', borderRadius: '8px', fontSize: '1rem', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' },
  loading: { height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '1.2rem', color: '#64748b', fontWeight: '500' }
};

export default MachinePage;