import React from 'react';

function PowerControl({ machineId }) {
  // --- CSS ĐỂ CÁC NÚT TỰ XUỐNG DÒNG, KHÔNG DÍNH CHỮ ---
  const powerStyles = {
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1.5rem',
      marginTop: '1.5rem'
    },
    button: {
      backgroundColor: 'white',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '1.5rem',
      cursor: 'pointer',
      display: 'flex',
      flexDirection: 'column', // Ép chữ xuống dòng
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.75rem',
      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
      transition: 'all 0.2s ease',
    },
    btnIcon: { fontSize: '2rem', color: '#3b82f6' },
    btnTitle: { fontWeight: 'bold', fontSize: '1rem', color: '#1e293b', margin: 0 },
    btnDesc: { fontSize: '0.8rem', color: '#64748b', margin: 0, textAlign: 'center' }
  };

  return (
    <div style={{ padding: '1rem' }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', margin: '0 0 0.5rem 0' }}>
        🔌 Điều khiển Nguồn hệ thống (Power Control)
      </h2>
      <p style={{ fontSize: '0.95rem', color: '#475569', marginBottom: '1.5rem' }}>
        Mã thiết bị nhận lệnh: <strong style={{ color: '#2563eb', fontFamily: 'monospace' }}>{machineId || 'Chưa chọn'}</strong>
      </p>

      {/* VÙNG CHỨA CÁC NÚT */}
      <div style={powerStyles.grid}>
        <button style={powerStyles.button} onClick={() => alert('Gửi lệnh Tắt máy')}>
          <span style={powerStyles.btnIcon}>🛑</span>
          <h4 style={powerStyles.btnTitle}>Tắt máy từ xa</h4>
          <p style={powerStyles.btnDesc}>Click để kích hoạt lệnh</p>
        </button>

        <button style={powerStyles.button} onClick={() => alert('Gửi lệnh Khởi động lại')}>
          <span style={powerStyles.btnIcon}>🔄</span>
          <h4 style={powerStyles.btnTitle}>Khởi động lại</h4>
          <p style={powerStyles.btnDesc}>Click để kích hoạt lệnh</p>
        </button>

        <button style={powerStyles.button} onClick={() => alert('Gửi lệnh Khóa màn hình')}>
          <span style={powerStyles.btnIcon}>🔒</span>
          <h4 style={powerStyles.btnTitle}>Khóa màn hình</h4>
          <p style={powerStyles.btnDesc}>Click để kích hoạt lệnh</p>
        </button>

        <button style={powerStyles.button} onClick={() => alert('Gửi lệnh Sleep')}>
          <span style={powerStyles.btnIcon}>🌙</span>
          <h4 style={powerStyles.btnTitle}>Chế độ ngủ (Sleep)</h4>
          <p style={powerStyles.btnDesc}>Click để kích hoạt lệnh</p>
        </button>
      </div>
    </div>
  );
}

export default PowerControl;