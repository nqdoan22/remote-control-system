// web-app/frontend/src/components/shared/MachineList.jsx
import React from 'react';

/**
 * 🖥️ MachineList: Thành phần hiển thị danh sách máy tính đang chịu sự điều khiển
 * @param {Array} machines - Mảng chứa danh sách các máy tính gửi từ Backend về
 * @param {function} onMachineClick - Hàm callback kích hoạt khi Admin bấm chọn 1 máy cụ thể
 */
function MachineList({ machines, onMachineClick }) {
  
  // 🔍 Trường hợp đặc biệt: Nếu hệ thống chưa quét được máy nào qua mạng LAN
  if (!machines || machines.length === 0) {
    return (
      <div style={styles.emptyState}>
        📡 Đang quét mạng LAN... Chưa tìm thấy máy Agent nào trực tuyến.
      </div>
    );
  }

  return (
    <div style={styles.gridContainer}>
      {/* 🔄 VÒNG LẶP MAP: Duyệt qua từng máy tính trong mảng để dựng thành thẻ giao diện */}
      {machines.map((machine) => {
        // Kiểm tra trạng thái mạng của Agent
        const isOnline = machine.status === 'online';

        return (
          <div 
            key={machine.id} 
            onClick={() => onMachineClick(machine.id)} // Kích hoạt lệnh chuyển hướng trang
            style={styles.machineCard}
            title={`Bấm để điều khiển máy: ${machine.id}`}
          >
            {/* 🔴 Đèn Led báo trạng thái mạng vật lý */}
            <div style={styles.cardHeader}>
              <span style={{
                ...styles.statusDot,
                backgroundColor: isOnline ? '#10b981' : '#94a3b8' // Xanh = Online, Xám = Offline
              }} />
              <strong style={styles.machineId}>{machine.id}</strong>
            </div>

            {/* Đục lỗ thông tin hệ điều hành và địa chỉ IP thu thập từ Agent */}
            <div style={styles.cardBody}>
              <p style={styles.infoLine}>🖥️ <strong>HĐH:</strong> {machine.os || 'Windows 11 Pro'}</p>
              <p style={styles.infoLine}>🌐 <strong>IP Mạng LAN:</strong> {machine.ip_address || '192.168.1.15'}</p>
              <p style={styles.infoLine}>⏱️ <strong>Cập nhật cuối:</strong> {machine.last_seen || 'Vừa xong'}</p>
            </div>

            <div style={{
              ...styles.cardFooter,
              backgroundColor: isOnline ? '#eff6ff' : '#f8fafc',
              color: isOnline ? '#2563eb' : '#64748b'
            }}>
              {isOnline ? '⚡ SẴN SÀNG ĐIỀU KHIỂN' : '💤 MẤT KẾT NỐI'}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// 🎨 STYLE HỆ THỐNG GRID ĐỂ CÁC THẺ TỰ ĐỘNG XẾP HÀNG NGANG MƯỢT MÀ
const styles = {
  gridContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', // Tự động co giãn theo độ rộng màn hình
    gap: '1.5rem',
    padding: '1rem 0'
  },
  machineCard: {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    overflow: 'hidden',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    display: 'flex',
    flexDirection: 'column'
  },
  cardHeader: {
    padding: '1rem',
    borderBottom: '1px solid #f1f5f9',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    backgroundColor: '#f8fafc'
  },
  statusDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    display: 'inline-block'
  },
  machineId: {
    color: '#0f172a',
    fontSize: '1rem',
    fontFamily: 'monospace'
  },
  cardBody: {
    padding: '1rem',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  infoLine: {
    margin: 0,
    fontSize: '0.85rem',
    color: '#334155'
  },
  cardFooter: {
    padding: '0.75rem 1rem',
    fontSize: '0.75rem',
    fontWeight: 'bold',
    textAlign: 'center',
    borderTop: '1px solid #f1f5f9'
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem',
    color: '#64748b',
    backgroundColor: '#f8fafc',
    borderRadius: '8px',
    border: '1px dashed #cbd5e1'
  }
};

export default MachineList;