import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// 1. Import REST API để lấy thông tin tĩnh của máy
import { getMachineDetailApi } from '../services/api';
// 2. Import Custom Hook WebSocket để điều khiển Real-time
import { useWebSocket } from '../hooks/useWebSocket';

const MachinePage = () => {
  // Lấy machineId từ URL (ví dụ: /machine/client-app-01 -> machineId = 'client-app-01')
  const { machineId } = useParams();
  const navigate = useNavigate();

  // =========================================================================
  // STATE MANAGEMENT (Quản lý trạng thái giao diện)
  // =========================================================================
  const [machineInfo, setMachineInfo] = useState(null); // Thông tin chi tiết máy
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Quản lý Tab đang mở ('info', 'processes', 'terminal', 'system')
  const [activeTab, setActiveTab] = useState('info');

  // State cho Module Tiến Trình (Process Manager)
  const [processes, setProcesses] = useState([]);

  // State cho Module Terminal (Dòng lệnh CMD/PowerShell)
  const [commandInput, setCommandInput] = useState('');
  const [terminalLogs, setTerminalLogs] = useState([
    '--- BẮT ĐẦU PHIÊN LÀM VIỆC TERMINAL ---'
  ]);

  // =========================================================================
  // 🔌 KHỞI TẠO WEBSOCKET CONNECTION TỚI MÁY CLIENT
  // =========================================================================
  const { isConnected, lastMessage, sendMessage } = useWebSocket(machineId);

  // =========================================================================
  // 🚀 REST API: Lấy thông tin cơ bản của máy khi mới mở trang
  // =========================================================================
  useEffect(() => {
    const fetchDetail = async () => {
      try {
        setLoading(true);
        // Gọi REST API lấy thông tin phần cứng, IP, OS từ Database
        const data = await getMachineDetailApi(machineId);
        setMachineInfo(data);
      } catch (err) {
        console.error('Lỗi lấy thông tin máy:', err);
        setError('Không thể lấy thông tin chi tiết của máy này!');
      } finally {
        setLoading(false);
      }
    };

    if (machineId) fetchDetail();
  }, [machineId]);

  // =========================================================================
  // ⚡ EVENT-DRIVEN: Lắng nghe phản hồi thời gian thực từ WebSocket (lastMessage)
  // =========================================================================
  useEffect(() => {
    if (!lastMessage) return;

    console.log('📩 Nhận dữ liệu WS mới:', lastMessage);

    /*
      Xử lý dữ liệu trả về dựa theo WSMessage Schema (type):
      - 'process.list.response': Trả về danh sách tiến trình đang chạy
      - 'terminal.output': Trả về kết quả thực thi lệnh Terminal
      - 'system.alert': Trả về thông báo từ Agent
    */
    switch (lastMessage.type) {
      case 'process.list.response':
        // Cập nhật mảng tiến trình thu được từ Agent
        if (lastMessage.payload?.processes) {
          setProcesses(lastMessage.payload.processes);
        }
        break;

      case 'terminal.output':
        // Nối kết quả câu lệnh mới vào khung hiển thị Terminal
        if (lastMessage.payload?.output) {
          setTerminalLogs((prev) => [...prev, lastMessage.payload.output]);
        }
        break;

      case 'system.alert':
        alert(`[CẢNH BÁO TỪ AGENT]: ${lastMessage.payload?.message}`);
        break;

      default:
        break;
    }
  }, [lastMessage]);

  // =========================================================================
  // 🛠️ HÀM TƯƠNG TÁC GỬI LỆNH QUA WEBSOCKET (sendMessage)
  // =========================================================================

  // 1. Yêu cầu Agent gửi danh sách Tiến trình (Process)
  const handleRefreshProcesses = () => {
    if (!isConnected) return alert('Chưa kết nối WebSocket!');
    sendMessage('process.list', {});
  };

  // 2. Yêu cầu Agent diệt 1 Tiến trình theo PID
  const handleKillProcess = (pid) => {
    if (!window.confirm(`Bạn có chắc muốn diệt tiến trình PID: ${pid}?`)) return;
    sendMessage('process.kill', { pid });
    // Sau khi bắn lệnh diệt, yêu cầu gửi lại danh sách mới
    setTimeout(handleRefreshProcesses, 500);
  };

  // 3. Gửi lệnh Shell/CMD sang Agent
  const handleSendTerminalCommand = (e) => {
    e.preventDefault();
    if (!commandInput.trim() || !isConnected) return;

    // Hiển thị ngay lệnh Admin vừa gõ vào khung log
    setTerminalLogs((prev) => [...prev, `> ${commandInput}`]);

    // Gửi lệnh qua WebSocket
    sendMessage('terminal.command', { command: commandInput });

    // Clear ô nhập liệu
    setCommandInput('');
  };

  // 4. Lệnh Hệ thống (Shutdown / Lock / Reboot)
  const handleSystemAction = (actionType) => {
    if (!window.confirm(`XÁC NHẬN: Bạn muốn thực hiện thao tác "${actionType}"?`)) return;
    sendMessage('system.action', { action: actionType });
  };

  if (loading) return <div style={styles.container}>Đang tải thông tin máy...</div>;
  if (error) return <div style={styles.container}>{error}</div>;

  return (
    <div style={styles.container}>
      {/* 1. HEADER & TRẠNG THÁI KẾT NỐI REAL-TIME */}
      <header style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={() => navigate('/dashboard')} style={styles.backBtn}>
            &larr; Quay lại
          </button>
          <h1 style={styles.title}>
            Máy: {machineInfo?.hostname || machineId}
          </h1>
        </div>

        {/* Badge hiển thị trạng thái đường ống WebSocket */}
        <div style={styles.wsStatusBadge}>
          <span
            style={{
              ...styles.statusDot,
              backgroundColor: isConnected ? '#22c55e' : '#ef4444',
            }}
          />
          <span style={{ color: isConnected ? '#22c55e' : '#ef4444', fontWeight: 'bold' }}>
            {isConnected ? 'WEBSOCKET REALTIME: READY' : 'MẤT KẾT NỐI WEBSOCKET'}
          </span>
        </div>
      </header>

      {/* 2. THANH CHỌN TAB NĂNG LỰC ĐIỀU KHIỂN */}
      <div style={styles.tabBar}>
        <button
          style={activeTab === 'info' ? styles.activeTabBtn : styles.tabBtn}
          onClick={() => setActiveTab('info')}
        >
          Thông Tin Máy
        </button>
        <button
          style={activeTab === 'processes' ? styles.activeTabBtn : styles.tabBtn}
          onClick={() => {
            setActiveTab('processes');
            handleRefreshProcesses(); // Mở tab là tự load danh sách tiến trình
          }}
        >
          Quản Lý Tiến Trình (Process)
        </button>
        <button
          style={activeTab === 'terminal' ? styles.activeTabBtn : styles.tabBtn}
          onClick={() => setActiveTab('terminal')}
        >
          Remote Terminal (CMD)
        </button>
        <button
          style={activeTab === 'system' ? styles.activeTabBtn : styles.tabBtn}
          onClick={() => setActiveTab('system')}
        >
          Lệnh Hệ Thống
        </button>
      </div>

      {/* 3. NỘI DUNG TỪNG TAB */}
      <div style={styles.contentArea}>
        {/* TAB 1: THÔNG TIN PHẦN CỨNG & HỆ ĐIỀU HÀNH */}
        {activeTab === 'info' && (
          <div style={styles.card}>
            <h3>Thông tin Tổng quan</h3>
            <p><strong>Machine ID:</strong> {machineInfo?.machine_id}</p>
            <p><strong>Hostname:</strong> {machineInfo?.hostname}</p>
            <p><strong>IP Address:</strong> {machineInfo?.ip_address}</p>
            <p><strong>Mac Address:</strong> {machineInfo?.mac_address || 'N/A'}</p>
            <p><strong>Hệ điều hành:</strong> {machineInfo?.os_info || 'Windows/Linux'}</p>
          </div>
        )}

        {/* TAB 2: QUẢN LÝ TIẾN TRÌNH (PROCESS MANAGER) */}
        {activeTab === 'processes' && (
          <div style={styles.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3>Danh Sách Tiến Trình Đang Chạy</h3>
              <button onClick={handleRefreshProcesses} style={styles.actionBtn}>
                Làm mới (Refresh)
              </button>
            </div>
            <table style={styles.table}>
              <thead>
                <tr style={styles.thRow}>
                  <th style={styles.th}>PID</th>
                  <th style={styles.th}>Tên Tiến Trình</th>
                  <th style={styles.th}>Sử dụng CPU</th>
                  <th style={styles.th}>Sử dụng RAM</th>
                  <th style={styles.th}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {processes.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ ...styles.td, textAlign: 'center' }}>
                      Bấm "Làm mới" hoặc chờ dữ liệu từ Agent gửi về...
                    </td>
                  </tr>
                ) : (
                  processes.map((proc) => (
                    <tr key={proc.pid} style={styles.tr}>
                      <td style={styles.td}>{proc.pid}</td>
                      <td style={styles.td}><strong>{proc.name}</strong></td>
                      <td style={styles.td}>{proc.cpu_usage || 0}%</td>
                      <td style={styles.td}>{proc.memory_usage || 0} MB</td>
                      <td style={styles.td}>
                        <button
                          onClick={() => handleKillProcess(proc.pid)}
                          style={styles.dangerBtn}
                        >
                          Kill Task
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 3: REMOTE TERMINAL / CMD */}
        {activeTab === 'terminal' && (
          <div style={styles.card}>
            <h3>Điều khiển Dòng lệnh Từ xa (Remote Shell)</h3>
            {/* Khung log giống màn hình Console */}
            <div style={styles.terminalConsole}>
              {terminalLogs.map((log, index) => (
                <div key={index} style={styles.terminalLine}>{log}</div>
              ))}
            </div>

            {/* Form gõ lệnh */}
            <form onSubmit={handleSendTerminalCommand} style={styles.terminalForm}>
              <span style={{ color: '#22c55e', fontWeight: 'bold' }}>&gt;</span>
              <input
                type="text"
                placeholder="Nhập lệnh CMD/PowerShell (ví dụ: dir, ipconfig, whoami)..."
                value={commandInput}
                onChange={(e) => setCommandInput(e.target.value)}
                style={styles.terminalInput}
                disabled={!isConnected}
              />
              <button type="submit" style={styles.actionBtn} disabled={!isConnected}>
                Gửi Lệnh
              </button>
            </form>
          </div>
        )}

        {/* TAB 4: LỆNH HỆ THỐNG */}
        {activeTab === 'system' && (
          <div style={styles.card}>
            <h3>Lệnh Điều Khiển Nhanh Hệ Thống</h3>
            <div style={{ display: 'flex', gap: '16px', marginTop: '20px' }}>
              <button onClick={() => handleSystemAction('lock')} style={styles.warnBtn}>
                Khóa Màn Hình Client
              </button>
              <button onClick={() => handleSystemAction('reboot')} style={styles.warnBtn}>
                Khởi Động Lại Máy
              </button>
              <button onClick={() => handleSystemAction('shutdown')} style={styles.dangerBtn}>
                Tắt Máy Ngay Lập Tức
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// =========================================================================
// INLINE STYLES
// =========================================================================
const styles = {
  container: { padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Segoe UI, sans-serif' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  backBtn: { backgroundColor: '#334155', color: '#fff', border: 'none', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer' },
  title: { fontSize: '22px', color: '#38bdf8', margin: 0 },
  wsStatusBadge: { display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#1e293b', padding: '8px 16px', borderRadius: '20px', border: '1px solid #334155' },
  statusDot: { width: '10px', height: '10px', borderRadius: '50%' },
  tabBar: { display: 'flex', gap: '8px', borderBottom: '1px solid #334155', marginBottom: '20px' },
  tabBtn: { padding: '10px 16px', backgroundColor: 'transparent', color: '#94a3b8', border: 'none', cursor: 'pointer', borderBottom: '2px solid transparent' },
  activeTabBtn: { padding: '10px 16px', backgroundColor: 'transparent', color: '#38bdf8', border: 'none', cursor: 'pointer', borderBottom: '2px solid #38bdf8', fontWeight: 'bold' },
  contentArea: { marginTop: '10px' },
  card: { backgroundColor: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left' },
  thRow: { borderBottom: '2px solid #334155' },
  th: { padding: '10px', color: '#94a3b8', fontSize: '14px' },
  tr: { borderBottom: '1px solid #334155' },
  td: { padding: '10px', fontSize: '14px' },
  actionBtn: { backgroundColor: '#0284c7', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '4px', cursor: 'pointer' },
  dangerBtn: { backgroundColor: '#dc2626', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '4px', cursor: 'pointer' },
  warnBtn: { backgroundColor: '#d97706', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '4px', cursor: 'pointer' },
  terminalConsole: { backgroundColor: '#020617', padding: '16px', borderRadius: '6px', height: '300px', overflowY: 'auto', fontFamily: 'Courier New, monospace', fontSize: '14px', border: '1px solid #334155', marginBottom: '12px' },
  terminalLine: { marginBottom: '4px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' },
  terminalForm: { display: 'flex', alignItems: 'center', gap: '8px' },
  terminalInput: { flex: 1, backgroundColor: '#020617', border: '1px solid #334155', color: '#22c55e', padding: '10px', borderRadius: '4px', fontFamily: 'Courier New, monospace', outline: 'none' },
};

export default MachinePage;