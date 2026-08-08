import React from 'react';

// Danh sách định nghĩa 8 Module chức năng theo chuẩn thiết kế API Contract
export const MODULE_TABS = [
  { id: 'applications', label: 'Applications', icon: '📱', sensitive: false },
  { id: 'processes', label: 'Processes', icon: '⚙️', sensitive: false },
  { id: 'screenshot', label: 'Screenshot', icon: '📸', sensitive: true },
  { id: 'livescreen', label: 'Live Screen', icon: '🖥️', sensitive: true },
  { id: 'input_audit', label: 'Input Audit Log', icon: '⌨️', sensitive: true },
  { id: 'filemanager', label: 'File Transfer', icon: '📁', sensitive: true },
  { id: 'webcam', label: 'Webcam', icon: '📷', sensitive: true },
  { id: 'power', label: 'Power Control', icon: '⚡', sensitive: true },
];

/**
 * ModulePanel Component - Khung giao diện bao bọc 8 Module chức năng điều khiển
 * 
 * @param {Object} selectedMachine - Thông tin máy Client được chọn từ MachineList
 * @param {String} activeTab - ID của Tab chức năng hiện tại đang active
 * @param {Function} onTabChange - Hàm Callback khi Admin chuyển tab
 * @param {React.ReactNode} children - Component Module thực tế tương ứng với activeTab
 */
const ModulePanel = ({ 
  selectedMachine = null, 
  activeTab = 'applications', 
  onTabChange, 
  children 
}) => {
  // Kiểm tra xem máy được chọn có đang Online không
  const isMachineOnline = selectedMachine && selectedMachine.status === 'online';

  return (
    <div style={styles.container}>
      {/* --- HEADER KHU VỰC ĐIỀU KHIỂN --- */}
      <div style={styles.header}>
        {selectedMachine ? (
          <div style={styles.machineInfo}>
            <h2 style={styles.machineTitle}>
              Đang điều khiển: <span style={{ color: '#38bdf8' }}>{selectedMachine.hostname}</span>
            </h2>
            <span style={styles.ipBadge}>IP: {selectedMachine.ipAddress}</span>
            <span 
              style={{
                ...styles.statusTag,
                backgroundColor: isMachineOnline ? '#166534' : '#991b1b',
                color: isMachineOnline ? '#4ade80' : '#fca5a5'
              }}
            >
              {isMachineOnline ? '● CONNECTED' : '● DISCONNECTED'}
            </span>
          </div>
        ) : (
          <h2 style={{ ...styles.machineTitle, color: '#94a3b8' }}>
            ⚠️ Chưa chọn máy tính nào để điều khiển
          </h2>
        )}
      </div>

      {/* --- THANH TABS NỔI CHỌN 8 MODULE --- */}
      <div style={styles.tabBar}>
        {MODULE_TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              disabled={!selectedMachine} // Vô hiệu hóa nút nếu chưa chọn máy
              onClick={() => onTabChange(tab.id)}
              style={{
                ...styles.tabButton,
                ...(isActive ? styles.activeTabButton : {}),
                opacity: !selectedMachine ? 0.4 : 1
              }}
            >
              <span style={{ marginRight: '6px' }}>{tab.icon}</span>
              {tab.label}
              
              {/* Badge chỉ báo các chức năng nhạy cảm phải xin quyền người dùng */}
              {tab.sensitive && (
                <span 
                  title="Chức năng nhạy cảm - Bắt buộc xin phép người dùng Client"
                  style={styles.sensitiveBadge}
                >
                  🔒 Consent
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* --- KHU VỰC HIỂN THỊ NỘI DUNG MODULE (CONTENT AREA) --- */}
      <div style={styles.contentArea}>
        {/* Trường hợp 1: Chưa chọn máy */}
        {!selectedMachine && (
          <div style={styles.placeholderContainer}>
            <div style={{ fontSize: '3rem', marginBottom: '10px' }}>🖥️ 👈</div>
            <h3>Vui lòng chọn một máy tính từ danh sách bên trái</h3>
            <p style={{ color: '#94a3b8' }}>
              Bạn cần chọn một máy tính Client đang Online để bắt đầu giám sát hoặc điều khiển.
            </p>
          </div>
        )}

        {/* Trường hợp 2: Máy được chọn nhưng đang Offline[cite: 1, 6, 7] */}
        {selectedMachine && !isMachineOnline && (
          <div style={styles.offlineWarningBox}>
            <div style={{ fontSize: '2.5rem' }}>⚠️</div>
            <h3 style={{ color: '#ef4444', margin: '8px 0' }}>Máy tính hiện đang Offline</h3>
            <p style={{ color: '#cbd5e1' }}>
              Không thể gửi lệnh điều khiển. Vui lòng chờ Agent trên máy <b>{selectedMachine.hostname}</b> kết nối lại vào Gateway.
            </p>
          </div>
        )}

        {/* Trường hợp 3: Máy chọn đang Online -> Render Module thực tế (children) */}
        {selectedMachine && isMachineOnline && (
          <div style={styles.activeModuleWrapper}>
            {children}
          </div>
        )}
      </div>
    </div>
  );
};

// ===== CSS-IN-JS STYLES =====
const styles = {
  container: {
    flex: 1,
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#0f172a',
    color: '#f8fafc',
    overflow: 'hidden'
  },
  header: {
    padding: '16px 24px',
    backgroundColor: '#1e293b',
    borderBottom: '1px solid #334155',
    display: 'flex',
    alignItems: 'center'
  },
  machineInfo: { display: 'flex', alignItems: 'center', gap: '12px' },
  machineTitle: { margin: 0, fontSize: '1.2rem', fontWeight: '600' },
  ipBadge: {
    backgroundColor: '#334155',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '0.85rem',
    fontFamily: 'monospace',
    color: '#cbd5e1'
  },
  statusTag: {
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: 'bold'
  },
  tabBar: {
    display: 'flex',
    backgroundColor: '#1e293b',
    borderBottom: '2px solid #334155',
    overflowX: 'auto',
    padding: '0 16px'
  },
  tabButton: {
    padding: '12px 16px',
    backgroundColor: 'transparent',
    color: '#94a3b8',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '500',
    whiteSpace: 'nowrap',
    display: 'flex',
    alignItems: 'center',
    transition: 'all 0.2s'
  },
  activeTabButton: {
    color: '#38bdf8',
    borderBottomColor: '#38bdf8',
    backgroundColor: '#0f172a',
    fontWeight: 'bold'
  },
  sensitiveBadge: {
    fontSize: '0.65rem',
    backgroundColor: '#334155',
    color: '#fbbf24',
    padding: '2px 4px',
    borderRadius: '3px',
    marginLeft: '6px',
    border: '1px solid #d97706'
  },
  contentArea: {
    flex: 1,
    padding: '20px',
    overflowY: 'auto',
    position: 'relative'
  },
  placeholderContainer: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#64748b',
    textAlign: 'center'
  },
  offlineWarningBox: {
    margin: '40px auto',
    maxWidth: '500px',
    padding: '24px',
    backgroundColor: '#451a1a',
    border: '1px solid #991b1b',
    borderRadius: '8px',
    textAlign: 'center'
  },
  activeModuleWrapper: {
    height: '100%',
    width: '100%'
  }
};

export default ModulePanel;