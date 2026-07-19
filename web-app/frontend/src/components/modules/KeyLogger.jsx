// web-app/frontend/src/components/modules/KeyLogger.jsx
import React, { useState, useEffect } from 'react';
import ModulePanel from '../shared/ModulePanel';

function KeyLogger({ machineId }) {
  const [status, setStatus] = useState('disabled'); 
  const [logs, setLogs] = useState([]); 
  const [isLoading, setIsLoading] = useState(false); 
  const [filterText, setFilterText] = useState(''); 

  const fetchKeyLogs = async () => {
    if (status !== 'active') return;
    setIsLoading(true);
    setTimeout(() => {
      setLogs([{ timestamp: "19:45:12", window: "Chrome", content: "hello world" }]);
      setIsLoading(false);
    }, 600);
  };

  useEffect(() => {
    let intervalId;
    if (status === 'active') {
      fetchKeyLogs();
      intervalId = setInterval(fetchKeyLogs, 5000);
    }
    return () => { if (intervalId) clearInterval(intervalId); };
  }, [status, machineId]);

  const handleStartLogging = () => {
    if (window.confirm("Xin quyền ghi phím?")) {
      setStatus('pending');
      setTimeout(() => { setStatus('active'); }, 3000);
    }
  };

  const handleStopLogging = () => {
    if (window.confirm("Tắt Keylogger?")) {
      setStatus('disabled');
      setLogs([]);
    }
  };

  const filteredLogs = logs.filter(item => item.content.toLowerCase().includes(filterText.toLowerCase()));

  // NHÓM CÁC NÚT ĐIỀU KHIỂN VÀO ACTION BUTTONS
  const actionBtns = (
    <div style={{ display: 'flex', gap: '0.5rem' }}>
      {status === 'disabled' && (
        <button onClick={handleStartLogging} style={{...styles.btn, backgroundColor: '#2563eb'}}>🚀 Kích Hoạt</button>
      )}
      {(status === 'active' || status === 'pending') && (
        <button onClick={handleStopLogging} style={{...styles.btn, backgroundColor: '#ef4444'}}>🛑 Tắt</button>
      )}
      {status === 'active' && (
        <button onClick={fetchKeyLogs} disabled={isLoading} style={{...styles.btn, backgroundColor: '#10b981'}}>
          {isLoading ? '⏳...' : '🔄 Làm mới'}
        </button>
      )}
    </div>
  );

  const descText = status === 'active' ? '🟢 ĐANG HOẠT ĐỘNG' : status === 'pending' ? '🟡 ĐANG CHỜ DUYỆT...' : '🔴 ĐÃ TẮT';

  return (
    <ModulePanel 
      title="⌨️ Hệ Thống Giám Sát Bàn Phím" 
      description={`Trạng thái: ${descText}`}
      actionButtons={actionBtns}
    >
      {status === 'active' && (
        <div style={styles.tableContainer}>
          <input 
            type="text" 
            placeholder="🔍 Tìm nhanh nội dung..." 
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={styles.searchInput}
          />
          <table style={styles.table}>
            <thead>
              <tr style={styles.tableHeadRow}>
                <th style={styles.tableHeadCell}>Thời Gian</th>
                <th style={styles.tableHeadCell}>Ứng Dụng</th>
                <th style={styles.tableHeadCell}>Nội Dung</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((item, idx) => (
                <tr key={idx} style={styles.tableRow}>
                  <td style={styles.tableCell}><code>{item.timestamp}</code></td>
                  <td style={{...styles.tableCell, color: '#0369a1'}}>{item.window}</td>
                  <td style={{...styles.tableCell, fontFamily: 'monospace'}}>{item.content}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </ModulePanel>
  );
}

const styles = {
  btn: { color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' },
  tableContainer: { padding: '1rem 0' },
  searchInput: { width: '100%', maxWidth: '400px', padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', marginBottom: '1rem' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left' },
  tableHeadRow: { backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' },
  tableHeadCell: { padding: '1rem', fontSize: '0.85rem', fontWeight: 'bold', color: '#64748b' },
  tableRow: { borderBottom: '1px solid #f1f5f9' },
  tableCell: { padding: '0.75rem 1rem', fontSize: '0.9rem', color: '#475569' }
};

export default KeyLogger;