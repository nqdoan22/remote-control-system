import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// 1. IMPORT CÁC HÀM API TỪ FILE api.js CỦA BẠN
import { 
  getMachinesApi, 
  getAuditLogsApi, 
  updateMachineApi 
} from '../services/api';

const DashboardPage = () => {
  const navigate = useNavigate();

  // =========================================================================
  // STATE MANAGEMENT (Lưu trữ dữ liệu phản hồi từ API)
  // =========================================================================
  const [machines, setMachines] = useState([]);      // Lưu danh sách Client Machines
  const [totalMachines, setTotalMachines] = useState(0); 
  const [auditLogs, setAuditLogs] = useState([]);    // Lưu nhật ký hệ thống Audit Logs
  
  // Trạng thái bộ lọc & Phân trang (gửi làm Query Parameters cho API)
  const [statusFilter, setStatusFilter] = useState(''); // '', 'online', 'offline'
  
  // Trạng thái giao diện
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // =========================================================================
  // 🚀 HÀM 1: LẤY DANH SÁCH MÁY CLIENT (Sử dụng getMachinesApi)
  // =========================================================================
  const fetchMachines = async () => {
    try {
      /* 
        📌 GỌI API: getMachinesApi(params)
        - Tạo param query: { skip: 0, limit: 50, status: statusFilter }
        - Khớp với MachineListResponse Schema ({ total: int, machines: [...] })
      */
      const params = { skip: 0, limit: 50 };
      if (statusFilter) params.status = statusFilter;

      const data = await getMachinesApi(params);
      
      // Cập nhật State React để vẽ ra bảng danh sách máy
      setMachines(data.machines || []);
      setTotalMachines(data.total || 0);
    } catch (err) {
      console.error('Lỗi lấy danh sách máy:', err);
      setError('Không thể tải danh sách máy client!');
    }
  };

  // =========================================================================
  // 🚀 HÀM 2: LẤY NHẬT KÝ HỆ THỐNG (Sử dụng getAuditLogsApi)
  // =========================================================================
  const fetchAuditLogs = async () => {
    try {
      /* 
        📌 GỌI API: getAuditLogsApi(params)
        - Lấy 10 log mới nhất để hiển thị ở bảng hoạt động gần đây
        - Khớp với AuditLogListResponse Schema ({ total: int, logs: [...] })
      */
      const data = await getAuditLogsApi({ skip: 0, limit: 10 });
      setAuditLogs(data.logs || []);
    } catch (err) {
      console.error('Lỗi lấy audit logs:', err);
    }
  };

  // =========================================================================
  // 🚀 HÀM 3: KHÓA / MỞ KHÓA NHANH MÁY (Sử dụng updateMachineApi)
  // =========================================================================
  const handleToggleLockMachine = async (machineId, currentLockStatus) => {
    try {
      /* 
        📌 GỌI API: updateMachineApi(machineId, updateData)
        - Gửi PATCH request xuống FastAPI với body (MachineUpdate Schema):
          { is_locked: !currentLockStatus }
      */
      await updateMachineApi(machineId, { 
        is_locked: !currentLockStatus 
      });

      // Sau khi Backend cập nhật thành công -> Gọi lại fetchMachines() để làm mới giao diện
      fetchMachines();
      fetchAuditLogs(); // Cập nhật lại cả log hành động
    } catch (err) {
      alert(`Lỗi khi thay đổi trạng thái máy: ${err.detail || err.message}`);
    }
  };

  // =========================================================================
  // 🚪 HÀM ĐĂNG XUẤT (Clear Token)
  // =========================================================================
  const handleLogout = () => {
    // Xóa Token khỏi bộ nhớ trình duyệt
    localStorage.removeItem('access_token');
    // Chuyển hướng ngay về trang Đăng nhập
    navigate('/login');
  };

  // =========================================================================
  // 🔄 LIFECYCLE EFFECT: Tự động chạy khi mở trang hoặc đổi bộ lọc Status
  // =========================================================================
  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      // Gọi song song cả 2 API để tối ưu thời gian tải trang
      await Promise.all([fetchMachines(), fetchAuditLogs()]);
      setLoading(false);
    };

    loadDashboardData();
  }, [statusFilter]); // Re-run khi Admin chọn lọc 'online' / 'offline'

  // =========================================================================
  // JSX INTERFACE (Giao diện hiển thị Dashboard)
  // =========================================================================
  return (
    <div style={styles.container}>
      {/* 1. Header & Thanh công cụ */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>Hệ Thống Quản Trị Remote Control</h1>
          <p style={styles.subtitle}>Tổng số máy quản lý: <strong>{totalMachines}</strong></p>
        </div>
        <button onClick={handleLogout} style={styles.logoutBtn}>
          Đăng xuất
        </button>
      </header>

      {error && <div style={styles.errorAlert}>{error}</div>}

      {/* 2. Thanh lọc dữ liệu (Filter Bar) */}
      <div style={styles.filterBar}>
        <label style={{ color: '#94a3b8' }}>Lọc trạng thái máy: </label>
        <select 
          value={statusFilter} 
          onChange={(e) => setStatusFilter(e.target.value)}
          style={styles.select}
        >
          <option value="">Tất cả trạng thái</option>
          <option value="online">Đang hoạt động (Online)</option>
          <option value="offline">Ngoại tuyến (Offline)</option>
        </select>
      </div>

      {/* 3. Bảng danh sách Máy Client */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Danh Sách Máy Tính Client</h2>
        {loading ? (
          <p style={{ color: '#94a3b8' }}>Đang tải dữ liệu từ Server...</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr style={styles.thRow}>
                <th style={styles.th}>Machine ID</th>
                <th style={styles.th}>Tên máy</th>
                <th style={styles.th}>IP Address</th>
                <th style={styles.th}>Trạng thái</th>
                <th style={styles.th}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {machines.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ ...styles.td, textAlign: 'center' }}>
                    Không tìm thấy máy client nào.
                  </td>
                </tr>
              ) : (
                machines.map((machine) => (
                  <tr key={machine.machine_id} style={styles.tr}>
                    <td style={styles.td}>
                      <strong>{machine.machine_id}</strong>
                    </td>
                    <td style={styles.td}>{machine.hostname || 'N/A'}</td>
                    <td style={styles.td}>{machine.ip_address || 'N/A'}</td>
                    <td style={styles.td}>
                      <span style={{
                        ...styles.badge,
                        backgroundColor: machine.status === 'online' ? '#16a34a' : '#64748b'
                      }}>
                        {machine.status ? machine.status.toUpperCase() : 'UNKNOWN'}
                      </span>
                    </td>
                    <td style={styles.td}>
                      {/* Nút Chuyển sang màn hình Điều khiển Chi tiết (MachinePage) */}
                      <button 
                        onClick={() => navigate(`/machine/${machine.machine_id}`)}
                        style={styles.actionBtn}
                      >
                        Điều khiển
                      </button>

                      {/* Nút Khóa / Mở khóa nhanh (GỌI UPDATE MACHINE API) */}
                      <button 
                        onClick={() => handleToggleLockMachine(machine.machine_id, machine.is_locked)}
                        style={{
                          ...styles.actionBtn,
                          backgroundColor: machine.is_locked ? '#dc2626' : '#d97706',
                          marginLeft: '8px'
                        }}
                      >
                        {machine.is_locked ? 'Mở khóa' : 'Khóa máy'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </section>

      {/* 4. Bảng Nhật ký Hoạt động (Audit Logs) */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Nhật Ký Hoạt Động Gần Đây (Audit Logs)</h2>
        <table style={styles.table}>
          <thead>
            <tr style={styles.thRow}>
              <th style={styles.th}>Thời gian</th>
              <th style={styles.th}>Hành động</th>
              <th style={styles.th}>Máy mục tiêu</th>
              <th style={styles.th}>Chi tiết</th>
            </tr>
          </thead>
          <tbody>
            {auditLogs.map((log) => (
              <tr key={log.id} style={styles.tr}>
                <td style={styles.td}>{new Date(log.created_at).toLocaleString('vi-VN')}</td>
                <td style={styles.td}><strong>{log.action}</strong></td>
                <td style={styles.td}>{log.target_machine_id || 'System'}</td>
                <td style={styles.td}>{JSON.stringify(log.details || {})}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};

// =========================================================================
// INLINE STYLES
// =========================================================================
const styles = {
  container: {
    padding: '24px',
    backgroundColor: '#0f172a',
    minHeight: '100vh',
    color: '#f8fafc',
    fontFamily: 'Segoe UI, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
    borderBottom: '1px solid #334155',
    paddingBottom: '16px',
  },
  title: { fontSize: '24px', color: '#38bdf8', margin: 0 },
  subtitle: { color: '#94a3b8', margin: '4px 0 0 0' },
  logoutBtn: {
    backgroundColor: '#ef4444',
    color: '#fff',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 'bold',
  },
  filterBar: { marginBottom: '20px' },
  select: {
    backgroundColor: '#1e293b',
    color: '#fff',
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #475569',
    marginLeft: '8px',
  },
  section: {
    backgroundColor: '#1e293b',
    padding: '20px',
    borderRadius: '8px',
    marginBottom: '24px',
    border: '1px solid #334155',
  },
  sectionTitle: { color: '#f8fafc', fontSize: '18px', marginTop: 0, marginBottom: '16px' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left' },
  thRow: { borderBottom: '2px solid #334155' },
  th: { padding: '12px', color: '#94a3b8', fontSize: '14px' },
  tr: { borderBottom: '1px solid #334155' },
  td: { padding: '12px', fontSize: '14px' },
  badge: { padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' },
  actionBtn: {
    backgroundColor: '#0284c7',
    color: '#fff',
    border: 'none',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  errorAlert: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    color: '#f87171',
    padding: '12px',
    borderRadius: '6px',
    marginBottom: '20px',
  }
};

export default DashboardPage;