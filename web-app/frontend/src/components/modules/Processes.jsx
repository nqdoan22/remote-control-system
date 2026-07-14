// web-app/frontend/src/components/modules/Processes.jsx
import React, { useState, useEffect } from 'react';

function Processes({ machineId }) {
  // --- 🧠 1. QUẢN LÝ TRẠNG THÁI (STATE) ---
  const [processes, setProcesses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // --- 🔄 2. MÔ PHỎNG LẤY DỮ LIỆU TỪ BACKEND ---
  // (Sau này chúng ta sẽ thay thế bằng hàm gọi WebSocket/API thật)
  const fetchProcesses = () => {
    setIsLoading(true);
    
    // Giả lập độ trễ mạng 1 giây
    setTimeout(() => {
      const mockData = [
        { pid: 1024, name: 'chrome.exe', cpu: '1.2', ram: '250.5' },
        { pid: 432, name: 'svchost.exe', cpu: '0.1', ram: '15.2' },
        { pid: 8890, name: 'Code.exe', cpu: '4.5', ram: '512.0' },
        { pid: 1120, name: 'explorer.exe', cpu: '0.5', ram: '80.1' },
        { pid: 5040, name: 'agent.exe', cpu: '0.0', ram: '12.4' }, // Tiến trình của đồ án
        { pid: 7612, name: 'Discord.exe', cpu: '2.1', ram: '180.3' },
      ];
      setProcesses(mockData);
      setIsLoading(false);
    }, 1000);
  };

  // Tự động tải danh sách khi vừa mở tab
  useEffect(() => {
    fetchProcesses();
  }, [machineId]);

  // --- 🔍 3. LOGIC LỌC TÌM KIẾM ---
  const filteredProcesses = processes.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.pid.toString().includes(searchTerm)
  );

  // --- ☠️ 4. LOGIC DIỆT TIẾN TRÌNH (CÓ XÁC NHẬN AN TOÀN) ---
  const handleKillProcess = (pid, name) => {
    // Thể hiện tư duy an toàn: Yêu cầu xác nhận trước khi thao tác phá hủy
    const isConfirm = window.confirm(`⚠️ CẢNH BÁO AN TOÀN:\nBạn có chắc chắn muốn buộc dừng tiến trình [${name} - PID: ${pid}] không? Việc này có thể gây mất dữ liệu chưa lưu trên máy đích.`);
    
    if (isConfirm) {
      alert(`Đã gửi lệnh KILL tiến trình ${pid} xuống máy ${machineId}`);
      // Tạm thời xóa khỏi giao diện để tạo cảm giác mượt mà (Optimistic UI)
      setProcesses(processes.filter(p => p.pid !== pid));
      // TODO: Sau này sẽ gọi API: axios.post(`/api/machines/${machineId}/processes/kill`, { pid })
    }
  };

  return (
    <div style={styles.container}>
      {/* 🧭 HEADER CỦA MODULE */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>⚙️ Quản Lý Tiến Trình (Task Manager)</h2>
          <p style={styles.subtitle}>Giám sát và điều khiển các tiến trình đang chạy trên thiết bị.</p>
        </div>
        <button 
          onClick={fetchProcesses} 
          disabled={isLoading}
          style={{...styles.refreshBtn, opacity: isLoading ? 0.7 : 1}}
        >
          {isLoading ? '⏳ Đang quét...' : '🔄 Làm mới danh sách'}
        </button>
      </div>

      {/* 🔍 THANH TÌM KIẾM */}
      <div style={styles.searchBarContainer}>
        <input 
          type="text" 
          placeholder="🔍 Tìm nhanh theo Tên tiến trình (vd: chrome) hoặc PID..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.searchInput}
        />
        <span style={styles.processCount}>Đang chạy: <strong>{filteredProcesses.length}</strong> tiến trình</span>
      </div>

      {/* 📊 BẢNG HIỂN THỊ TIẾN TRÌNH */}
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.tableHeadRow}>
              <th style={styles.tableHeadCell}>PID</th>
              <th style={styles.tableHeadCell}>Tên Tiến Trình</th>
              <th style={{...styles.tableHeadCell, textAlign: 'right'}}>CPU (%)</th>
              <th style={{...styles.tableHeadCell, textAlign: 'right'}}>RAM (MB)</th>
              <th style={{...styles.tableHeadCell, textAlign: 'center'}}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="5" style={styles.loadingCell}>🔄 Đang tải dữ liệu tiến trình từ Agent...</td>
              </tr>
            ) : filteredProcesses.length > 0 ? (
              filteredProcesses.map((process) => (
                <tr key={process.pid} style={styles.tableRow}>
                  <td style={styles.tableCell}><strong>{process.pid}</strong></td>
                  <td style={{...styles.tableCell, fontWeight: '500', color: '#1e293b'}}>{process.name}</td>
                  <td style={{...styles.tableCell, textAlign: 'right'}}>{process.cpu}%</td>
                  <td style={{...styles.tableCell, textAlign: 'right'}}>{process.ram} MB</td>
                  <td style={{...styles.tableCell, textAlign: 'center'}}>
                    <button 
                      onClick={() => handleKillProcess(process.pid, process.name)}
                      style={styles.killBtn}
                      title="Buộc dừng tiến trình này"
                    >
                      Diệt (Kill) ☠️
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={styles.emptyCell}>Không tìm thấy tiến trình nào phù hợp.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- 🖌️ CSS INLINE CHO MODULE TIẾN TRÌNH ---
const styles = {
  container: { padding: '1rem' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' },
  title: { fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', margin: '0 0 0.25rem 0' },
  subtitle: { fontSize: '0.95rem', color: '#64748b', margin: 0 },
  refreshBtn: { backgroundColor: '#10b981', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '0.9rem', transition: 'background-color 0.2s' },
  
  searchBarContainer: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', backgroundColor: '#f1f5f9', padding: '1rem', borderRadius: '8px' },
  searchInput: { flex: 1, maxWidth: '400px', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem' },
  processCount: { fontSize: '0.9rem', color: '#475569' },

  tableContainer: { backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', overflowX: 'auto', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left' },
  tableHeadRow: { backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' },
  tableHeadCell: { padding: '1rem', fontSize: '0.85rem', fontWeight: 'bold', color: '#64748b', textTransform: 'uppercase' },
  tableRow: { borderBottom: '1px solid #f1f5f9', transition: 'background-color 0.1s' },
  tableCell: { padding: '0.75rem 1rem', fontSize: '0.9rem', color: '#475569' },
  
  killBtn: { backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontWeight: '600', fontSize: '0.8rem', transition: 'background-color 0.2s' },
  
  loadingCell: { padding: '3rem', textAlign: 'center', color: '#64748b', fontWeight: '500' },
  emptyCell: { padding: '2rem', textAlign: 'center', color: '#ef4444', fontStyle: 'italic' }
};

export default Processes;