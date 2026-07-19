// web-app/frontend/src/components/modules/Processes.jsx
import React, { useState, useEffect } from 'react';

function Processes({ machineId }) {
  // --- 🧠 QUẢN LÝ TRẠNG THÁI (STATE) ---
  const [processes, setProcesses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // --- 🔄 LẤY DỮ LIỆU ĐỒNG BỘ THEO ĐẶC TẢ ---
  const fetchProcesses = () => {
    setIsLoading(true);
    
    // Giả lập nhận dữ liệu JSON dùng định dạng camelCase theo tài liệu Tech Stack
    setTimeout(() => {
      const mockData = [
        { pid: 1024, processName: 'chrome.exe', cpuUsage: 1.2, ramUsage: 250.5 },
        { pid: 432, processName: 'svchost.exe', cpuUsage: 0.1, ramUsage: 15.2 },
        { pid: 8890, processName: 'Code.exe', cpuUsage: 4.5, ramUsage: 512.0 },
        { pid: 1120, processName: 'explorer.exe', cpuUsage: 0.5, ramUsage: 80.1 },
        { pid: 5040, processName: 'agent.exe', cpuUsage: 0.0, ramUsage: 12.4 },
        { pid: 7612, processName: 'Discord.exe', cpuUsage: 2.1, ramUsage: 180.3 },
      ];
      setProcesses(mockData);
      setIsLoading(false);
    }, 1000);
  };

  useEffect(() => {
    fetchProcesses();
  }, [machineId]);

  // --- 🔍 LOGIC LỌC TÌM KIẾM ---
  const filteredProcesses = processes.filter(p => 
    p.processName.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.pid.toString().includes(searchTerm)
  );

  // --- ☠️ DIỆT TIẾN TRÌNH (LỆNH: process.kill) ---
  const handleKillProcess = (pid, processName) => {
    const isConfirm = window.confirm(`⚠️ CẢNH BÁO AN TOÀN:\nBạn có chắc chắn muốn buộc dừng tiến trình [${processName} - PID: ${pid}] không?`);
    
    if (isConfirm) {
      alert(`Đã phát lệnh điều khiển loại: "process.kill" cho PID: ${pid}`);
      
      // Tạm thời tối ưu giao diện UI phía client
      setProcesses(processes.filter(p => p.pid !== pid));

      /* 
      // THỰC TẾ TRUYỀN THÔNG WEBSOCKET ĐỒNG BỘ:
      const messageEnvelope = {
        messageId: crypto.randomUUID(),
        type: "process.kill",
        timestamp: Math.floor(Date.now() / 1000),
        source: "web-app",
        destination: machineId,
        payload: { pid: pid }
      };
      ws.send(JSON.stringify(messageEnvelope));
      */
    }
  };

  return (
    <div style={styles.container}>
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

      <div style={styles.searchBarContainer}>
        <input 
          type="text" 
          placeholder="🔍 Tìm nhanh theo Tên tiến trình hoặc PID..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.searchInput}
        />
        <span style={styles.processCount}>Đang chạy: <strong>{filteredProcesses.length}</strong> tiến trình</span>
      </div>

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
                  <td style={{...styles.tableCell, fontWeight: '500', color: '#1e293b'}}>{process.processName}</td>
                  <td style={{...styles.tableCell, textAlign: 'right'}}>{process.cpuUsage}%</td>
                  <td style={{...styles.tableCell, textAlign: 'right'}}>{process.ramUsage} MB</td>
                  <td style={{...styles.tableCell, textAlign: 'center'}}>
                    <button 
                      onClick={() => handleKillProcess(process.pid, process.processName)}
                      style={styles.killBtn}
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

const styles = {
  container: { padding: '1rem' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' },
  title: { fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', margin: '0 0 0.25rem 0' },
  subtitle: { fontSize: '0.95rem', color: '#64748b', margin: 0 },
  refreshBtn: { backgroundColor: '#10b981', color: 'white', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '0.9rem' },
  searchBarContainer: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', backgroundColor: '#f1f5f9', padding: '1rem', borderRadius: '8px' },
  searchInput: { flex: 1, maxWidth: '400px', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', fontSize: '0.9rem' },
  processCount: { fontSize: '0.9rem', color: '#475569' },
  tableContainer: { backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', overflowX: 'auto', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left' },
  tableHeadRow: { backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' },
  tableHeadCell: { padding: '1rem', fontSize: '0.85rem', fontWeight: 'bold', color: '#64748b', textTransform: 'uppercase' },
  tableRow: { borderBottom: '1px solid #f1f5f9' },
  tableCell: { padding: '0.75rem 1rem', fontSize: '0.9rem', color: '#475569' },
  killBtn: { backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontWeight: '600', fontSize: '0.8rem' },
  loadingCell: { padding: '3rem', textAlign: 'center', color: '#64748b', fontWeight: '500' },
  emptyCell: { padding: '2rem', textAlign: 'center', color: '#ef4444', fontStyle: 'italic' }
};

export default Processes;