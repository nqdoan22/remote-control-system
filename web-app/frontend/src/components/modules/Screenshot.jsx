// web-app/frontend/src/components/modules/Screenshot.jsx
import React, { useState } from 'react';
import ModulePanel from '../shared/ModulePanel';

function Screenshot({ machineId }) {
  const [status, setStatus] = useState('idle'); 
  const [screenshotUrl, setScreenshotUrl] = useState(null);
  const [capturedAt, setCapturedAt] = useState('');

  const triggerCaptureRequest = () => {
    setStatus('requesting');
    setScreenshotUrl(null); 
    setTimeout(() => {
      setStatus('waiting_confirm');
      setTimeout(() => {
        const mockBase64Image = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450' viewBox='0 0 800 450'><rect width='100%' height='100%' fill='%231e293b'/><text x='50%' y='50%' font-family='sans-serif' font-weight='bold' font-size='24' fill='%2364748b' text-anchor='middle'>MÔ PHỎNG MÀN HÌNH</text></svg>";
        setScreenshotUrl(mockBase64Image);
        setCapturedAt(new Date().toLocaleTimeString()); 
        setStatus('success');
      }, 2500);
    }, 1000);
  };

  const actionBtns = (
    <button 
      onClick={triggerCaptureRequest}
      disabled={status === 'requesting' || status === 'waiting_confirm'}
      style={{
        ...styles.captureBtn,
        backgroundColor: (status === 'requesting' || status === 'waiting_confirm') ? '#94a3b8' : '#2563eb',
        cursor: (status === 'requesting' || status === 'waiting_confirm') ? 'not-allowed' : 'pointer'
      }}
    >
      {status === 'idle' && '🚀 Gửi Lệnh Chụp'}
      {status === 'requesting' && '📡 Đang Kết Nối...'}
      {status === 'waiting_confirm' && '⏳ Chờ Duyệt...'}
      {(status === 'success' || status === 'denied') && '📸 Chụp Tấm Khác'}
    </button>
  );

  return (
    <ModulePanel 
      title="📸 Chụp Màn Hình Từ Xa" 
      description="Gửi yêu cầu lệnh chụp màn hình thời gian thực."
      actionButtons={actionBtns}
    >
      <div style={styles.statusBannerContainer}>
        {status === 'waiting_confirm' && (
          <div style={{...styles.banner, backgroundColor: '#fef3c7', color: '#d97706', border: '1px solid #fcd34d'}}>
            <strong>🛡️ ĐẢM BẢO QUYỀN RIÊNG TƯ:</strong> Đang chờ xác nhận từ người dùng.
          </div>
        )}
        {status === 'success' && (
          <div style={{...styles.banner, backgroundColor: '#ecfdf5', color: '#059669', border: '1px solid #a7f3d0'}}>
            <strong>✅ THÀNH CÔNG:</strong> Đã nhận dữ liệu lúc <strong>{capturedAt}</strong>.
          </div>
        )}
      </div>

      <div style={styles.viewportContainer}>
        {status === 'idle' && (
          <div style={styles.emptyState}>
            <span style={{fontSize: '3.5rem'}}>🖥️</span>
            <p>Nhấn nút "Gửi Lệnh Chụp" để lấy màn hình hiện tại.</p>
          </div>
        )}
        {(status === 'requesting' || status === 'waiting_confirm') && (
          <div style={styles.loadingState}>
            <div style={styles.spinner}></div>
            <p>Đang xử lý...</p>
          </div>
        )}
        {screenshotUrl && (
          <div style={styles.imageWrapper}>
            <img src={screenshotUrl} alt="Screenshot" style={styles.screenshotImage} />
          </div>
        )}
      </div>
    </ModulePanel>
  );
}

const styles = {
  captureBtn: { color: 'white', border: 'none', padding: '0.65rem 1.3rem', borderRadius: '6px', fontWeight: 'bold', transition: 'all 0.2s ease' },
  statusBannerContainer: { marginBottom: '1.5rem' },
  banner: { padding: '1rem', borderRadius: '8px', fontSize: '0.875rem' },
  viewportContainer: { width: '100%', minHeight: '450px', backgroundColor: '#f1f5f9', borderRadius: '12px', border: '2px dashed #cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' },
  emptyState: { textAlign: 'center', color: '#64748b' },
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center' },
  spinner: { width: '40px', height: '40px', border: '4px solid #cbd5e1', borderTopColor: '#2563eb', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  imageWrapper: { width: '100%', maxWidth: '800px', backgroundColor: 'white', borderRadius: '8px', padding: '0.5rem', border: '1px solid #e2e8f0' },
  screenshotImage: { width: '100%', height: 'auto', borderRadius: '6px', display: 'block' }
};

export default Screenshot;