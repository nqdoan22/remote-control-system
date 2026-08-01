import React, { useState, useMemo } from 'react';

/**
 * MachineList Component - Hiển thị danh sách các máy tính Client trong mạng LAN
 * 
 * @param {Array} machines - Danh sách các máy tính nhận từ API/WebSocket
 * @param {Object} selectedMachine - Máy tính hiện đang được Admin chọn
 * @param {Function} onSelectMachine - Hàm Callback khi bấm chọn 1 máy tính
 * @param {Boolean} loading - Trạng thái đang tải dữ liệu danh sách máy
 * @param {Function} onRefresh - Hàm Callback để gọi làm mới danh sách máy
 */
const MachineList = ({ 
  machines = [], 
  selectedMachine = null, 
  onSelectMachine, 
  loading = false,
  onRefresh 
}) => {
  // ===== STATE NỘI BỘ (Local State) =====
  // Từ khóa tìm kiếm (theo Hostname hoặc IP)
  const [searchTerm, setSearchTerm] = useState('');
  
  // Bộ lọc trạng thái: 'all' (Tất cả), 'online' (Đang kết nối), 'offline' (Mất kết nối)
  const [statusFilter, setStatusFilter] = useState('all');

  // ===== KỸ THUẬT LỌC DỮ LIỆU TỐI ƯU (Memoized Filtering) =====
  // useMemo giúp chỉ tính toán lại danh sách hiển thị khi `machines`, `searchTerm` hoặc `statusFilter` thay đổi
  const filteredMachines = useMemo(() => {
    return machines.filter((machine) => {
      // 1. Kiểm tra từ khóa tìm kiếm (so sánh chuỗi không phân biệt hoa/thường)
      const matchesSearch = 
        (machine.hostname && machine.hostname.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (machine.ipAddress && machine.ipAddress.includes(searchTerm));

      // 2. Kiểm tra trạng thái Online/Offline
      const matchesStatus = 
        statusFilter === 'all' || 
        machine.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [machines, searchTerm, statusFilter]);

  // ===== HÀM BỔ TRỢ HỖ TRỢ XỬ LÝ THỜI GIAN =====
  const formatLastSeen = (timestamp) => {
    if (!timestamp) return 'Chưa ghi nhận';
    const date = new Date(timestamp * 1000); // Đổi Unix epoch sang JS Date
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="machine-list-container" style={styles.container}>
      {/* --- HEADER DANH SÁCH --- */}
      <div style={styles.header}>
        <h3 style={styles.title}>Danh Sách Máy Client</h3>
        <button 
          onClick={onRefresh} 
          disabled={loading}
          style={styles.refreshBtn}
          title="Làm mới danh sách"
        >
          {loading ? '🔄 ...' : '🔄 Làm mới'}
        </button>
      </div>

      {/* --- THANH TÌM KIẾM CẢI TIẾN --- */}
      <div style={styles.searchBox}>
        <input
          type="text"
          placeholder="🔍 Tìm theo Hostname hoặc IP..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.searchInput}
        />
      </div>

      {/* --- BỘ LỌC TRẠNG THÁI (Tabs nhỏ) --- */}
      <div style={styles.filterGroup}>
        <button 
          style={statusFilter === 'all' ? styles.activeFilterBtn : styles.filterBtn}
          onClick={() => setStatusFilter('all')}
        >
          Tất cả ({machines.length})
        </button>
        <button 
          style={statusFilter === 'online' ? styles.activeFilterBtn : styles.filterBtn}
          onClick={() => setStatusFilter('online')}
        >
          🟢 Online ({machines.filter(m => m.status === 'online').length})
        </button>
        <button 
          style={statusFilter === 'offline' ? styles.activeFilterBtn : styles.filterBtn}
          onClick={() => setStatusFilter('offline')}
        >
          🔴 Offline ({machines.filter(m => m.status === 'offline').length})
        </button>
      </div>

      {/* --- DANH SÁCH CÁC MÁY TÍNH (Scrollable List) --- */}
      <div style={styles.listWrapper}>
        {loading && <p style={styles.statusText}>Đang tải danh sách máy...</p>}

        {!loading && filteredMachines.length === 0 && (
          <p style={styles.statusText}>Không tìm thấy máy tính nào phù hợp.</p>
        )}

        {!loading && filteredMachines.map((machine) => {
          // Kiểm tra xem máy này có đang được Admin chọn hay không
          const isSelected = selectedMachine && selectedMachine.machineId === machine.machineId;
          const isOnline = machine.status === 'online';

          return (
            <div
              key={machine.machineId}
              onClick={() => onSelectMachine(machine)}
              style={{
                ...styles.machineCard,
                ...(isSelected ? styles.selectedCard : {}),
                opacity: isOnline ? 1 : 0.65 // Làm mờ các máy Offline
              }}
            >
              {/* Cột trái: Đèn trạng thái & Tên máy */}
              <div style={styles.cardHeader}>
                <span 
                  style={{
                    ...styles.statusDot,
                    backgroundColor: isOnline ? '#22c55e' : '#ef4444' // Xanh lá = Online, Đỏ = Offline
                  }} 
                />
                <strong style={styles.hostname}>{machine.hostname || 'Unknown PC'}</strong>
              </div>

              {/* Cột phải / Thông tin phụ: IP & Lần cuối thấy */}
              <div style={styles.cardDetails}>
                <span>IP: <code>{machine.ipAddress || '127.0.0.1'}</code></span>
                <small style={styles.lastSeen}>
                  {isOnline ? 'Đang hoạt động' : `Thấy cuối: ${formatLastSeen(machine.lastSeen)}`}
                </small>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ===== CSS-IN-JS STYLES (Đảm bảo chạy ngay không cần cấu hình CSS ngoài) =====
const styles = {
  container: {
    width: '320px',
    height: '100%',
    backgroundColor: '#1e293b',
    color: '#f8fafc',
    display: 'flex',
    flexDirection: 'column',
    borderRight: '1px solid #334155',
    padding: '16px',
    boxSizing: 'border-box'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px'
  },
  title: { margin: 0, fontSize: '1.1rem', color: '#38bdf8' },
  refreshBtn: {
    backgroundColor: '#334155',
    color: '#f8fafc',
    border: 'none',
    padding: '6px 10px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem'
  },
  searchBox: { marginBottom: '10px' },
  searchInput: {
    width: '100%',
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #475569',
    backgroundColor: '#0f172a',
    color: '#fff',
    boxSizing: 'border-box'
  },
  filterGroup: { display: 'flex', gap: '4px', marginBottom: '12px' },
  filterBtn: {
    flex: 1,
    padding: '4px 2px',
    fontSize: '0.75rem',
    backgroundColor: '#0f172a',
    color: '#94a3b8',
    border: '1px solid #334155',
    borderRadius: '4px',
    cursor: 'pointer'
  },
  activeFilterBtn: {
    flex: 1,
    padding: '4px 2px',
    fontSize: '0.75rem',
    backgroundColor: '#0284c7',
    color: '#ffffff',
    border: '1px solid #0284c7',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold'
  },
  listWrapper: { flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' },
  statusText: { textAlignment: 'center', color: '#94a3b8', fontSize: '0.9rem', marginTop: '20px' },
  machineCard: {
    padding: '12px',
    borderRadius: '8px',
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    cursor: 'pointer',
    transition: 'all 0.2s ease-in-out'
  },
  selectedCard: {
    borderColor: '#38bdf8',
    backgroundColor: '#1e3a8a',
    boxShadow: '0 0 8px rgba(56, 189, 248, 0.4)'
  },
  cardHeader: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' },
  statusDot: { width: '10px', height: '10px', borderRadius: '50%', display: 'inline-block' },
  hostname: { fontSize: '0.95rem', color: '#f1f5f9' },
  cardDetails: { display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8' },
  lastSeen: { fontSize: '0.75rem', color: '#64748b' }
};

export default MachineList;