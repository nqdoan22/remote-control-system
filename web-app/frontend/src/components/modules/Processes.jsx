import React, { useState, useEffect } from 'react';

/**
 * Processes Module - Quản lý toàn bộ các tiến trình hệ thống (Background & Foreground)
 */
const Processes = ({ selectedMachine, onSendMessage, lastMessage }) => {
  const [processList, setProcessList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // 1. Lấy danh sách tiến trình hệ thống
  useEffect(() => {
    fetchProcesses();
  }, [selectedMachine]);

  // 2. Nhận kết quả từ WebSocket
  useEffect(() => {
    if (lastMessage && lastMessage.action === 'get_processes_response') {
      setLoading(false);
      if (lastMessage.status === 'success') {
        setProcessList(lastMessage.data || []);
      } else {
        alert('Lỗi lấy danh sách tiến trình: ' + lastMessage.message);
      }
    }
  }, [lastMessage]);

  const fetchProcesses = () => {
    if (!selectedMachine) return;
    setLoading(true);
    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'get_processes'
    });
  };

  // Hàm diệt tiến trình (Kill Process)
  const handleKillProcess = (pid, name) => {
    if (window.confirm(`⚠️ BẠN CÓ CHẮC MUỐN DIỆT TIẾN TRÌNH: ${name} (PID: ${pid})?\nThao tác này có thể làm mất dữ liệu chưa lưu trên Client!`)) {
      onSendMessage({
        target_machine_id: selectedMachine.machineId,
        action: 'kill_process',
        payload: { pid: pid }
      });
      // Làm mới lại bảng sau 1 giây
      setTimeout(fetchProcesses, 1000);
    }
  };

  // Lọc theo PID hoặc Tên Tiến Trình
  const filteredProcesses = processList.filter(p =>
    p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.pid?.toString().includes(searchTerm)
  );

  return (
    <div style={styles.container}>
      {/* THANH THAO TÁC VÀ TÌM KIẾM */}
      <div style={styles.topBar}>
        <div style={styles.infoSummary}>
          <span>Tổng số tiến trình: <b>{processList.length}</b></span>
        </div>

        <div style={styles.rightActions}>
          <input
            type="text"
            placeholder="🔍 Tìm PID hoặc tên tiến trình..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
          />
          <button onClick={fetchProcesses} disabled={loading} style={styles.btnSecondary}>
            {loading ? '🔄 Đang quét...' : '🔄 Làm mới'}
          </button>
        </div>
      </div>

      {/* BẢNG DANH SÁCH TIẾN TRÌNH */}
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>PID</th>
              <th style={styles.th}>Tên Tiến Trình (Process Name)</th>
              <th style={styles.th}>CPU Usage (%)</th>
              <th style={styles.th}>RAM Usage (MB)</th>
              <th style={styles.th}>Hành Động</th>
            </tr>
          </thead>
          <tbody>
            {filteredProcesses.length === 0 ? (
              <tr>
                <td colSpan="5" style={styles.tdEmpty}>
                  {loading ? 'Đang tải danh sách tiến trình...' : 'Không tìm thấy tiến trình nào phù hợp.'}
                </td>
              </tr>
            ) : (
              filteredProcesses.map((proc) => (
                <tr key={proc.pid}>
                  <td style={styles.td}><code>{proc.pid}</code></td>
                  <td style={styles.td}><b>{proc.name}</b></td>
                  <td style={styles.td}>{proc.cpu_percent?.toFixed(1) ?? '0.0'}%</td>
                  <td style={styles.td}>{(proc.memory_mb ?? 0).toFixed(1)} MB</td>
                  <td style={styles.td}>
                    <button
                      onClick={() => handleKillProcess(proc.pid, proc.name)}
                      style={styles.btnKill}
                    >
                      ⚡ Kill Process
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  infoSummary: { fontSize: '0.95rem', color: '#cbd5e1' },
  rightActions: { display: 'flex', gap: '8px' },
  searchInput: { padding: '8px 12px', borderRadius: '6px', border: '1px solid #334155', backgroundColor: '#1e293b', color: '#fff', width: '240px' },
  btnSecondary: { padding: '8px 16px', backgroundColor: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  btnKill: { padding: '4px 10px', backgroundColor: '#b91c1c', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 'bold' },
  tableWrapper: { flex: 1, overflowY: 'auto', border: '1px solid #334155', borderRadius: '8px', backgroundColor: '#1e293b' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' },
  th: { padding: '12px', backgroundColor: '#0f172a', color: '#38bdf8', borderBottom: '1px solid #334155', position: 'sticky', top: 0 },
  td: { padding: '10px 12px', borderBottom: '1px solid #334155', color: '#f8fafc' },
  tdEmpty: { padding: '24px', textAlign: 'center', color: '#94a3b8' }
};

export default Processes;