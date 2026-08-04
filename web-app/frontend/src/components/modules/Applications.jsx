import React, { useState, useEffect } from 'react';
import { controlApplicationsApi, isWsError, getWsErrorMessage, getWsData } from '../../services/api';

/**
 * Applications Module - Quản lý các ứng dụng đang chạy có giao diện (GUI).
 * application.list / application.start / application.stop (api_contract.md).
 *
 * @param {Object} selectedMachine - Máy Client đang chọn
 */
const Applications = ({ selectedMachine }) => {
  const [appList, setAppList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newAppPath, setNewAppPath] = useState('');
  const [filterText, setFilterText] = useState('');

  // Chỉ tự tải lại khi ĐỔI MÁY (machineId). KHÔNG dùng toàn bộ object
  // selectedMachine làm dependency vì nó được tạo lại khi isConnected
  // (WebSocket) thay đổi -> sẽ gửi 2 lệnh 'application.list' song song ngay
  // khi mở trang, lệnh đầu bị đè (pending_by_machine) -> timeout 15s giả.
  const machineId = selectedMachine?.machineId;
  useEffect(() => {
    fetchApplications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [machineId]);

  const fetchApplications = async () => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      const res = await controlApplicationsApi(selectedMachine.machineId, 'list');
      if (isWsError(res)) {
        alert('Lỗi lấy danh sách ứng dụng: ' + getWsErrorMessage(res));
      } else {
        // payload.data.applications: [{ name, pid, hwnd, cpuUsage, mainWindowTitle }] theo api_contract.md
        setAppList(getWsData(res).applications || []);
      }
    } catch (err) {
      alert('Lỗi lấy danh sách ứng dụng: ' + (err?.detail || 'Không rõ nguyên nhân'));
    } finally {
      setLoading(false);
    }
  };

  // Hàm khởi chạy một ứng dụng mới (application.start - cần đường dẫn .exe đầy đủ)
  const handleStartApp = async (e) => {
    e.preventDefault();
    if (!newAppPath.trim() || !selectedMachine) return;

    if (window.confirm(`Bạn có chắc muốn khởi chạy: "${newAppPath}"?`)) {
      try {
        const res = await controlApplicationsApi(selectedMachine.machineId, 'start', { path: newAppPath });
        if (isWsError(res)) alert('Lỗi khởi chạy ứng dụng: ' + getWsErrorMessage(res));
      } catch (err) {
        alert('Lỗi khởi chạy ứng dụng: ' + (err?.detail || 'Không rõ nguyên nhân'));
      }
      setNewAppPath('');
      setTimeout(fetchApplications, 1500);
    }
  };

  // Hàm tắt một cửa sổ ứng dụng đang chạy (application.stop).
  // Truyền kèm hwnd để Client chỉ đóng ĐÚNG cửa sổ đó (WM_CLOSE). Không truyền
  // hwnd -> Client sẽ giết cả tiến trình, làm Chrome/Edge (nhiều cửa sổ chung 1
  // PID) bị đóng hết cùng lúc.
  const handleStopApp = async (pid, hwnd, appTitle) => {
    if (window.confirm(`Bạn có chắc muốn đóng cửa sổ ứng dụng: "${appTitle}" (PID: ${pid})?`)) {
      try {
        const res = await controlApplicationsApi(selectedMachine.machineId, 'stop', { pid, hwnd });
        if (isWsError(res)) alert('Lỗi đóng ứng dụng: ' + getWsErrorMessage(res));
      } catch (err) {
        alert('Lỗi đóng ứng dụng: ' + (err?.detail || 'Không rõ nguyên nhân'));
      }
      setTimeout(fetchApplications, 1000);
    }
  };

  // Lọc danh sách ứng dụng theo tên
  const filteredApps = appList.filter(app =>
    app.mainWindowTitle?.toLowerCase().includes(filterText.toLowerCase()) ||
    app.name?.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div style={styles.container}>
      {/* BAR THAO TÁC TRÊN CÙNG */}
      <div style={styles.topBar}>
        <form onSubmit={handleStartApp} style={styles.startForm}>
          <input
            type="text"
            placeholder='Đường dẫn .exe đầy đủ (vd: C:\Windows\System32\notepad.exe)'
            value={newAppPath}
            onChange={(e) => setNewAppPath(e.target.value)}
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
                <tr key={app.hwnd ?? `${app.pid}-${app.mainWindowTitle}`} style={styles.tr}>
                  <td style={styles.td}><code>{app.pid}</code></td>
                  <td style={styles.td}><b>{app.name}</b></td>
                  <td style={styles.td}>{app.mainWindowTitle || '*(Không có tiêu đề)'}</td>
                  <td style={styles.td}>{app.cpuUsage ?? 0}%</td>
                  <td style={styles.td}>
                    <button
                      onClick={() => handleStopApp(app.pid, app.hwnd, app.mainWindowTitle || app.name)}
                      style={styles.btnDanger}
                    >
                      🛑 Đóng Cửa Sổ
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
