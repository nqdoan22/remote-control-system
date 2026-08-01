import React, { useState, useEffect } from 'react';

/**
 * Applications Module - Quản lý các ứng dụng đang chạy có giao diện (GUI)
 * 
 * @param {Object} selectedMachine - Máy Client đang chọn
 * @param {Function} onSendMessage - Hàm gửi WebSocket message đến Gateway
 * @param {Object} lastMessage - Dữ liệu mới nhất nhận từ WebSocket
 */
const Applications = ({ selectedMachine, onSendMessage, lastMessage }) => {
  const [appList, setAppList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newAppName, setNewAppName] = useState('');
  const [filterText, setFilterText] = useState('');

  // 1. Gửi yêu cầu lấy danh sách ứng dụng khi mở Module hoặc đổi máy
  useEffect(() => {
    fetchApplications();
  }, [selectedMachine]);

  // 2. Lắng nghe phản hồi từ Agent trả về qua WebSocket
  useEffect(() => {
    if (lastMessage && lastMessage.action === 'get_applications_response') {
      setLoading(false);
      if (lastMessage.status === 'success') {
        setAppList(lastMessage.data || []);
      } else {
        alert('Lỗi lấy danh sách ứng dụng: ' + lastMessage.message);
      }
    }
  }, [lastMessage]);

  // Hàm gọi lấy danh sách ứng dụng
  const fetchApplications = () => {
    if (!selectedMachine) return;
    setLoading(true);
    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'get_applications'
    });
  };

  // Hàm khởi chạy một ứng dụng mới (Start Application)
  const handleStartApp = (e) => {
    e.preventDefault();
    if (!newAppName.trim()) return;

    if (window.confirm(`Bạn có chắc muốn khởi chạy ứng dụng: "${newAppName}"?`)) {
      onSendMessage({
        target_machine_id: selectedMachine.machineId,
        action: 'start_application',
        payload: { app_name: newAppName }
      });
      setNewAppName('');
      setTimeout(fetchApplications, 1500); // Làm mới danh sách sau 1.5s
    }
  };

  // Hàm tắt một ứng dụng đang chạy (Stop Application)
  const handleStopApp = (pid, appTitle) => {
    if (window.confirm(`Bạn có chắc muốn đóng ứng dụng: "${appTitle}" (PID: ${pid})?`)) {
      onSendMessage({
        target_machine_id: selectedMachine.machineId,
        action: 'stop_application',
        payload: { pid: pid }
      });
      setTimeout(fetchApplications, 1000);
    }
  };

  // Lọc danh sách ứng dụng theo tên
  const filteredApps = appList.filter(app => 
    app.title?.toLowerCase().includes(filterText.toLowerCase()) ||
    app.name?.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div style={styles.container}>
      {/* BAR THAO TÁC TRÊN CÙNG */}
      <div style={styles.topBar}>
        <form onSubmit={handleStartApp} style={styles.startForm}>
          <input
            type="text"
            placeholder="Nhập tên/đường dẫn ứng dụng (vd: calc, notepad)..."
            value={newAppName}
            onChange={(e) => setNewAppName(e.target.value)}
            style={styles.input}
          />
          <button type="submit" style={styles.btnPrimary}>▶ Khởi chạy App</button>
        </form>

        <div style={styles.rightActions}>
          <input
            type="text"
            placeholder="🔍 Lọc ứng dụng..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={styles.searchInput}
          />
          <button onClick={fetchApplications} disabled={loading} style={styles.btnSecondary}>
            {loading ? '🔄 Đang tải...' : '🔄 Tải lại'}
          </button>
        </div>
      </div>

      {/* BẢNG DANH SÁCH ỨNG DỤNG */}
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>PID</th>
              <th style={styles.th}>Tên Tiến Trình</th>
              <th style={styles.th}>Tiêu Đề Cửa Sổ (Window Title)</th>
              <th style={styles.th}>CPU (%)</th>
              <th style={styles.th}>Thao Tác</th>
            </tr>
          </thead>
          <tbody>
            {filteredApps.length === 0 ? (
              <tr>
                <td colSpan="5" style={styles.tdEmpty}>
                  {loading ? 'Đang truy vấn dữ liệu từ Client...' : 'Không có ứng dụng GUI nào đang chạy.'}
                </td>
              </tr>
            ) : (
              filteredApps.map((app) => (
                <tr key={app.pid} style={styles.tr}>
                  <td style={styles.td}><code>{app.pid}</code></td>
                  <td style={styles.td}><b>{app.name}</b></td>
                  <td style={styles.td}>{app.title || '*(Không có tiêu đề)'}</td>
                  <td style={styles.td}>{app.cpu_percent ?? 0}%</td>
                  <td style={styles.td}>
                    <button
                      onClick={() => handleStopApp(app.pid, app.title || app.name)}
                      style={styles.btnDanger}
                    >
                      🛑 Đóng App
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

// Style UI
const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' },
  startForm: { display: 'flex', gap: '8px', flex: 1, minWidth: '300px' },
  rightActions: { display: 'flex', gap: '8px' },
  input: { flex: 1, padding: '8px 12px', borderRadius: '6px', border: '1px solid #334155', backgroundColor: '#1e293b', color: '#fff' },
  searchInput: { padding: '8px 12px', borderRadius: '6px', border: '1px solid #334155', backgroundColor: '#1e293b', color: '#fff', width: '180px' },
  btnPrimary: { padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  btnSecondary: { padding: '8px 16px', backgroundColor: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  btnDanger: { padding: '4px 10px', backgroundColor: '#dc2626', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' },
  tableWrapper: { flex: 1, overflowY: 'auto', border: '1px solid #334155', borderRadius: '8px', backgroundColor: '#1e293b' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' },
  th: { padding: '12px', backgroundColor: '#0f172a', color: '#38bdf8', borderBottom: '1px solid #334155', position: 'sticky', top: 0 },
  td: { padding: '10px 12px', borderBottom: '1px solid #334155', color: '#f8fafc' },
  tr: { hover: { backgroundColor: '#334155' } },
  tdEmpty: { padding: '24px', textAlign: 'center', color: '#94a3b8' }
};

export default Applications;