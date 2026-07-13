// web-app/frontend/src/components/modules/Processes.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Processes({ machineId }) {
  const [processes, setProcesses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState('');

  // 🔄 Tự động lấy danh sách tiến trình giả lập ban đầu
  useEffect(() => {
    // Để đơn giản, ta nạp danh sách tiến trình ban đầu tại đây
    setProcesses([
      { pid: 4122, name: 'chrome.exe', cpu: '4.2%', ram: '180 MB' },
      { pid: 1024, name: 'svchost.exe', cpu: '0.1%', ram: '24 MB' },
      { pid: 8840, name: 'python.exe (Agent)', cpu: '1.5%', ram: '45 MB' },
      { pid: 5632, name: 'explorer.exe', cpu: '0.8%', ram: '90 MB' }
    ]);
    setIsLoading(false);
  }, [machineId]);

  // ⚡ Hàm xử lý khi bấm nút Tắt tiến trình (Gọi API thật xuống Backend)
  const handleKill = async (pid, name) => {
    try {
      // 🔗 Gọi API thật đến ô cửa /api/modules/kill-process
      const response = await axios.post('http://127.0.0.1:8000/api/modules/kill-process', {
        machine_id: machineId,
        pid: pid,
        process_name: name
      });

      if (response.data.status === 'success') {
        // Hiện thông báo từ Backend trả về
        setMessage(response.data.message);
        // Xóa tiến trình đó khỏi giao diện ngay lập tức
        setProcesses(processes.filter(p => p.pid !== pid));
        
        // Tự động xóa dòng thông báo sau 4 giây cho đỡ rối mắt
        setTimeout(() => setMessage(''), 4000);
      }
    } catch (err) {
      console.error(err);
      alert('Không thể gửi lệnh tắt tiến trình đến Backend!');
    }
  };

  if (isLoading) return <div>🔄 Đang tải danh sách tiến trình...</div>;

  return (
    <div>
      <h3>⚙️ Quản Lý Tiến Trình Đang Chạy Ngầm (Task Manager)</h3>
      
      {/* Hiển thị thông báo phản hồi từ Backend nếu có */}
      {message && <div style={{ padding: '0.75rem', backgroundColor: '#d1fae5', color: '#065f46', borderRadius: '6px', marginBottom: '1rem', fontWeight: '500', fontSize: '0.9rem' }}>{message}</div>}

      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ backgroundColor: '#f1f5f9' }}>
            <th style={styles.th}>PID</th>
            <th style={styles.th}>Tên Tiến Trình</th>
            <th style={styles.th}>CPU</th>
            <th style={styles.th}>RAM</th>
            <th style={styles.th}>Hành Động</th>
          </tr>
        </thead>
        <tbody>
          {processes.map(p => (
            <tr key={p.pid} style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={styles.td}>{p.pid}</td>
              <td style={{ ...styles.td, fontWeight: 'bold' }}>{p.name}</td>
              <td style={styles.td}>{p.cpu}</td>
              <td style={styles.td}>{p.ram}</td>
              <td style={styles.td}>
                <button onClick={() => handleKill(p.pid, p.name)} style={styles.killBtn}>
                  Kill Process (Tắt)
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const styles = {
  th: { padding: '0.75rem 1rem', borderBottom: '2px solid #cbd5e1', color: '#334155', fontSize: '0.9rem' },
  td: { padding: '0.75rem 1rem', fontSize: '0.9rem', color: '#334155' },
  killBtn: { backgroundColor: '#fee2e2', color: '#ef4444', border: '1px solid #fca5a5', padding: '0.4rem 0.8rem', borderRadius: '4px', cursor: 'pointer', fontWeight: '600', fontSize: '0.8rem' }
};

export default Processes;