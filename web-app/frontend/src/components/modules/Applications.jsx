// web-app/frontend/src/components/modules/Applications.jsx
import React, { useState, useEffect } from 'react';
// import { moduleService } from '../../services/api'; // Mở comment này khi nối API thật

function Applications({ machineId }) {
  const [apps, setApps] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [newAppName, setNewAppName] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  // --- MÔ PHỎNG LẤY DỮ LIỆU ---
  const fetchApps = () => {
    setIsLoading(true);
    setTimeout(() => {
      const mockData = [
        { pid: 1024, name: 'chrome.exe', title: 'Đồ án mạng máy tính - Google Chrome', cpu: '2.5', ram: '450.5' },
        { pid: 8890, name: 'Code.exe', title: 'Applications.jsx - VS Code', cpu: '1.2', ram: '312.0' },
        { pid: 7612, name: 'Discord.exe', title: 'Kênh chat chung - Discord', cpu: '0.8', ram: '150.3' },
        { pid: 1120, name: 'WINWORD.EXE', title: 'Báo_Cáo_Đồ_Án.docx - Word', cpu: '0.5', ram: '80.1' },
      ];
      setApps(mockData);
      setIsLoading(false);
    }, 1000);
  };

  useEffect(() => {
    fetchApps();
  }, [machineId]);

  const filteredApps = apps.filter(app => 
    app.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    app.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // --- LOGIC ĐÓNG ỨNG DỤNG ---
  const handleStopApp = async (appName, title) => {
    const isConfirm = window.confirm(`Bạn có chắc chắn muốn đóng ứng dụng đang mở [${title}] không?`);
    if (isConfirm) {
      alert(`Đã gửi lệnh STOP ứng dụng ${appName}`);
      setApps(apps.filter(app => app.name !== appName));
      // await moduleService.stopApplication(machineId, appName);
    }
  };

  // --- LOGIC KHỞI CHẠY ỨNG DỤNG MỚI ---
  const handleStartApp = async (e) => {
    e.preventDefault();
    if (!newAppName.trim()) return;

    setIsStarting(true);
    alert(`Đã gửi lệnh START ứng dụng: ${newAppName}`);
    
    // Giả lập sau khi gọi API thành công thì làm mới danh sách
    // await moduleService.startApplication(machineId, newAppName);
    
    setTimeout(() => {
      setNewAppName('');
      setIsStarting(false);
      fetchApps(); // Tải lại danh sách để thấy app mới bật lên
    }, 1500);
  };

  return (
    <div style={styles.container}>
      {/* 🧭 HEADER */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>🖥️ Ứng Dụng Đang Chạy (Applications)</h2>
          <p style={styles.subtitle}>Quản lý các phần mềm hiển thị trên màn hình người dùng.</p>
        </div>
        <button onClick={fetchApps} disabled={isLoading} style={{...styles.refreshBtn, opacity: isLoading ? 0.7 : 1}}>
          {isLoading ? '⏳ Đang quét...' : '🔄 Làm mới'}
        </button>
      </div>

      {/* 🚀 THANH KHỞI CHẠY ỨNG DỤNG */}
      <div style={styles.startAppContainer}>
        <form onSubmit={handleStartApp} style={styles.startForm}>
          <input 
            type="text" 
            placeholder="Nhập tên file để chạy (VD: notepad.exe, calc.exe, chrome.exe)..." 
            value={newAppName}
            onChange={(e) => setNewAppName(e.target.value)}
            style={styles.startInput}
            required
          />
          <button type="submit" disabled={isStarting} style={styles.startBtn}>
            {isStarting ? '⏳ Đang mở...' : '🚀 Khởi chạy từ xa'}
          </button>
        </form>
      </div>

      {/* 🔍 THANH TÌM KIẾM */}
      <div style={styles.searchBarContainer}>
        <input 
          type="text" 
          placeholder="🔍 Tìm theo Tên phần mềm hoặc Tiêu đề cửa sổ..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.searchInput}
        />
        <span style={styles.processCount}>Đang mở: <strong>{filteredApps.length}</strong> ứng dụng</span>
      </div>

      {/* 📊 BẢNG HIỂN THỊ */}
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.tableHeadRow}>
              <th style={styles.tableHeadCell}>Tên File (Exe)</th>
              <th style={styles.tableHeadCell}>Tiêu Đề Cửa Sổ Đang Mở</th>
              <th style={{...styles.tableHeadCell, textAlign: 'right'}}>CPU (%)</th>
              <th style={{...styles.tableHeadCell, textAlign: 'right'}}>RAM (MB)</th>
              <th style={{...styles.tableHeadCell, textAlign: 'center'}}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="5" style={styles.loadingCell}>🔄 Đang tải dữ liệu ứng dụng từ Agent...</td>
              </tr>
            ) : filteredApps.length > 0 ? (
              filteredApps.map((app) => (
                <tr key={app.pid} style={styles.tableRow}>
                  <td style={{...styles.tableCell, fontWeight: 'bold'}}>{app.name}</td>
                  <td style={{...styles.tableCell, color: '#0369a1'}}>{app.title}</td>
                  <td style={{...styles.tableCell, textAlign: 'right'}}>{app.cpu}%</td>
                  <td style={{...styles.tableCell, textAlign: 'right'}}>{app.ram} MB</td>
                  <td style={{...styles.tableCell, textAlign: 'center'}}>
                    <button 
                      onClick={() => handleStopApp(app.name, app.title)}
                      style={styles.stopBtn}
                      title="Đóng ứng dụng này"
                    >
                      Đóng (Stop) 🛑
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={styles.emptyCell}>Không tìm thấy ứng dụng nào đang mở.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Bổ sung thêm CSS cho phần Khởi chạy ứng dụng (giữ lại các style cũ của bạn)
const styles = {
  // ... (Gắn toàn bộ các style cũ từ file Processes.jsx của bạn vào đây)
  container: { padding: '1rem' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' },
  title: { fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', margin: '0 0 0.25rem 0' },
  subtitle: { fontSize: '0.95rem', color: '#64748b', margin: 0 },
  refreshBtn: { backgroundColor: '#10b981', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' },
  
  startAppContainer: { backgroundColor: '#f0fdf4', padding: '1rem', borderRadius: '8px', border: '1px solid #bbf7d0', marginBottom: '1rem' },
  startForm: { display: 'flex', gap: '1rem' },
  startInput: { flex: 1, padding: '0.6rem 1rem', borderRadius: '6px', border: '1px solid #86efac', outline: 'none' },
  startBtn: { backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '0.6rem 1.5rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', whiteSpace: 'nowrap' },

  searchBarContainer: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', backgroundColor: '#f1f5f9', padding: '1rem', borderRadius: '8px' },
  searchInput: { flex: 1, maxWidth: '400px', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none' },
  processCount: { fontSize: '0.9rem', color: '#475569' },

  tableContainer: { backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', overflowX: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left' },
  tableHeadRow: { backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' },
  tableHeadCell: { padding: '1rem', fontSize: '0.85rem', fontWeight: 'bold', color: '#64748b' },
  tableRow: { borderBottom: '1px solid #f1f5f9' },
  tableCell: { padding: '0.75rem 1rem', fontSize: '0.9rem', color: '#475569' },
  
  stopBtn: { backgroundColor: '#f59e0b', color: 'white', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontWeight: '600' },
  loadingCell: { padding: '3rem', textAlign: 'center', color: '#64748b' },
  emptyCell: { padding: '2rem', textAlign: 'center', color: '#ef4444' }
};

export default Applications;