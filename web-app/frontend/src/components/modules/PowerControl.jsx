// web-app/frontend/src/components/modules/PowerControl.jsx
import React from 'react';
import ModulePanel from '../shared/ModulePanel';

function PowerControl({ machineId }) {
  return (
    <ModulePanel 
      title="🔌 Điều khiển Nguồn hệ thống (Power Control)"
      description={`Mã thiết bị nhận lệnh: ${machineId || 'Chưa chọn'}`}
    >
      <div style={styles.grid}>
        <button style={styles.button} onClick={() => alert('Gửi lệnh Tắt máy')}>
          <span style={styles.btnIcon}>🛑</span>
          <h4 style={styles.btnTitle}>Tắt máy từ xa</h4>
          <p style={styles.btnDesc}>Click để kích hoạt lệnh shutdown</p>
        </button>

        <button style={styles.button} onClick={() => alert('Gửi lệnh Khởi động lại')}>
          <span style={styles.btnIcon}>🔄</span>
          <h4 style={styles.btnTitle}>Khởi động lại</h4>
          <p style={styles.btnDesc}>Click để kích hoạt lệnh restart</p>
        </button>

        <button style={styles.button} onClick={() => alert('Gửi lệnh Khóa màn hình')}>
          <span style={styles.btnIcon}>🔒</span>
          <h4 style={styles.btnTitle}>Khóa màn hình</h4>
          <p style={styles.btnDesc}>Click để kích hoạt lệnh lock</p>
        </button>

        <button style={styles.button} onClick={() => alert('Gửi lệnh Sleep')}>
          <span style={styles.btnIcon}>🌙</span>
          <h4 style={styles.btnTitle}>Chế độ ngủ (Sleep)</h4>
          <p style={styles.btnDesc}>Click để kích hoạt lệnh sleep</p>
        </button>
      </div>
    </ModulePanel>
  );
}

const styles = {
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' },
  button: {
    backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.5rem',
    cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', gap: '0.75rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
    transition: 'all 0.2s ease',
  },
  btnIcon: { fontSize: '2.5rem', color: '#3b82f6' },
  btnTitle: { fontWeight: 'bold', fontSize: '1.1rem', color: '#1e293b', margin: 0 },
  btnDesc: { fontSize: '0.85rem', color: '#64748b', margin: 0, textAlign: 'center' }
};

export default PowerControl;