// web-app/frontend/src/components/modules/Applications.jsx
import React, { useState, useEffect } from 'react';
import ModulePanel from '../shared/ModulePanel';

function Applications({ machineId }) {
  const [apps, setApps] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [newAppName, setNewAppName] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  const fetchApps = () => {
    setIsLoading(true);
    setTimeout(() => {
      const mockData = [
        { pid: 1024, name: 'chrome.exe', title: 'Đồ án mạng máy tính - Google Chrome', cpu: '2.5', ram: '450.5' },
        { pid: 8890, name: 'Code.exe', title: 'Applications.jsx - VS Code', cpu: '1.2', ram: '312.0' },
      ];
      setApps(mockData);
      setIsLoading(false);
    }, 1000);
  };

  useEffect(() => { fetchApps(); }, [machineId]);

  const filteredApps = apps.filter(app => 
    app.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    app.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleStopApp = async (appName, title) => {
    if (window.confirm(`Bạn có chắc chắn muốn đóng ứng dụng đang mở [${title}] không?`)) {
      alert(`Đã gửi lệnh STOP ứng dụng ${appName}`);
      setApps(apps.filter(app => app.name !== appName));
    }
  };

  const handleStartApp = async (e) => {
    e.preventDefault();
    if (!newAppName.trim()) return;
    setIsStarting(true);
    setTimeout(() => {
      setNewAppName('');
      setIsStarting(false);
      fetchApps();
    }, 1500);
  };

  // NÚT LÀM MỚI ĐƯỢC ĐƯA VÀO ĐÂY
  const actionBtns = (
    <button onClick={fetchApps} disabled={isLoading} style={{...styles.refreshBtn, opacity: isLoading ? 0.7 : 1}}>
      {isLoading ? '⏳ Đang quét...' : '🔄 Làm mới'}
    </button>
  );

  return (
    <ModulePanel 
      title="🖥️ Ứng Dụng Đang Chạy (Applications)" 
      description="Quản lý các phần mềm hiển thị trên màn hình người dùng."
      actionButtons={actionBtns}
    >
      <div style={styles.startAppContainer}>
        <form onSubmit={handleStartApp} style={styles.startForm}>
          <input type="text" placeholder="Nhập tên file để chạy (VD: notepad.exe)..." value={newAppName} onChange={(e) => setNewAppName(e.target.value)} style={styles.startInput} required />
          <button type="submit" disabled={isStarting} style={styles.startBtn}>{isStarting ? '⏳ Đang mở...' : '🚀 Khởi chạy từ xa'}</button>
        </form>
      </div>

      <div style={styles.searchBarContainer}>
        <input type="text" placeholder="🔍 Tìm theo Tên phần mềm..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} style={styles.searchInput} />
        <span style={styles.processCount}>Đang mở: <strong>{filteredApps.length}</strong> ứng dụng</span>
      </div>

      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.tableHeadRow}>
              <th style={styles.tableHeadCell}>Tên File (Exe)</th>
              <th style={styles.tableHeadCell}>Tiêu Đề Cửa Sổ Đang Mở</th>
              <th style={{...styles.tableHeadCell, textAlign: 'center'}}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan="3" style={styles.loadingCell}>🔄 Đang tải dữ liệu...</td></tr>
            ) : filteredApps.length > 0 ? (
              filteredApps.map((app) => (
                <tr key={app.pid} style={styles.tableRow}>
                  <td style={{...styles.tableCell, fontWeight: 'bold'}}>{app.name}</td>
                  <td style={{...styles.tableCell, color: '#0369a1'}}>{app.title}</td>
                  <td style={{...styles.tableCell, textAlign: 'center'}}>
                    <button onClick={() => handleStopApp(app.name, app.title)} style={styles.stopBtn}>Đóng (Stop) 🛑</button>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="3" style={styles.emptyCell}>Không tìm thấy ứng dụng.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </ModulePanel>
  );
}

const styles = {
  refreshBtn: { backgroundColor: '#10b981', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' },
  startAppContainer: { backgroundColor: '#f0fdf4', padding: '1rem', borderRadius: '8px', border: '1px solid #bbf7d0', marginBottom: '1rem' },
  startForm: { display: 'flex', gap: '1rem' },
  startInput: { flex: 1, padding: '0.6rem 1rem', borderRadius: '6px', border: '1px solid #86efac', outline: 'none' },
  startBtn: { backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '0.6rem 1.5rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  searchBarContainer: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', backgroundColor: '#f1f5f9', padding: '1rem', borderRadius: '8px' },
  searchInput: { flex: 1, maxWidth: '400px', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none' },
  processCount: { fontSize: '0.9rem', color: '#475569' },
  tableContainer: { border: '1px solid #e2e8f0', borderRadius: '8px', overflowX: 'auto' },
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