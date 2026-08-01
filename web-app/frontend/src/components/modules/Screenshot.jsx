import React, { useState, useEffect } from 'react';

/**
 * Screenshot Module - Chụp ảnh màn hình máy Client (Có yêu cầu xin phép người dùng)
 * 
 * @param {Object} selectedMachine - Thông tin máy Client được chọn
 * @param {Function} onSendMessage - Hàm gửi WebSocket message đến Gateway
 * @param {Object} lastMessage - Phản hồi nhận từ Gateway
 */
const Screenshot = ({ selectedMachine, onSendMessage, lastMessage }) => {
  // ===== STATE QUẢN LÝ GIAO DIỆN =====
  const [imageData, setImageData] = useState(null); // Chuỗi ảnh Base64 (data:image/jpeg;base64,...)
  const [loading, setLoading] = useState(false);
  const [capturedAt, setCapturedAt] = useState(null); // Thời gian chụp
  const [consentStatus, setConsentStatus] = useState(''); // Trạng thái xin quyền ('waiting', 'rejected', 'timeout', '')

  // Reset dữ liệu ảnh khi Admin đổi sang máy Client khác
  useEffect(() => {
    setImageData(null);
    setCapturedAt(null);
    setConsentStatus('');
    setLoading(false);
  }, [selectedMachine]);

  // ===== LẮNG NGHE PHẢN HỒI TỪ WEBSOCKET =====
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.action === 'take_screenshot_response') {
      setLoading(false);

      if (lastMessage.status === 'success') {
        // Nhận được dữ liệu ảnh thành công
        setImageData(`data:image/jpeg;base64,${lastMessage.data.image_base64}`);
        setCapturedAt(new Date().toLocaleTimeString('vi-VN'));
        setConsentStatus('approved');
      } else if (lastMessage.status === 'rejected') {
        // Người dùng Client bấm từ chối Consent
        setConsentStatus('rejected');
        alert('❌ Người dùng trên máy Client đã TỪ CHỐI cấp quyền chụp màn hình!');
      } else if (lastMessage.status === 'timeout') {
        // Hết 15s timeout người dùng không tương tác -> Tự động từ chối
        setConsentStatus('timeout');
        alert('⏱️ Yêu cầu xin quyền đã HẾT HẠN (Timeout 15s)!');
      } else {
        alert('Lỗi chụp màn hình: ' + (lastMessage.message || 'Không xác định'));
      }
    }
  }, [lastMessage]);

  // Gửi lệnh yêu cầu chụp màn hình
  const handleTakeScreenshot = () => {
    if (!selectedMachine) return;
    setLoading(true);
    setConsentStatus('waiting');
    
    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'take_screenshot'
    });
  };

  // Hàm tải ảnh về máy Admin
  const handleDownloadImage = () => {
    if (!imageData) return;
    const link = document.createElement('a');
    link.href = imageData;
    link.download = `Screenshot_${selectedMachine.hostname}_${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={styles.container}>
      {/* THANH ĐIỀU HƯỚNG BẤM CHỤP & THÔNG TIN */}
      <div style={styles.topBar}>
        <div style={styles.actionGroup}>
          <button 
            onClick={handleTakeScreenshot} 
            disabled={loading}
            style={styles.btnPrimary}
          >
            {loading ? '⏳ Đang chờ người dùng đồng ý...' : '📸 Chụp Màn Hình Ngay'}
          </button>

          {imageData && (
            <button onClick={handleDownloadImage} style={styles.btnSuccess}>
              💾 Tải Ảnh Phân Giải Gốc
            </button>
          )}
        </div>

        {capturedAt && (
          <span style={styles.timeInfo}>
            🕒 Lần chụp cuối: <b>{capturedAt}</b>
          </span>
        )}
      </div>

      {/* BANNER BÁO VỀ CƠ CHẾ XIN QUYỀN (PRIVACY CONSENT) */}
      <div style={styles.consentNotice}>
        ℹ️ <b>Lưu ý An toàn & Bảo mật:</b> Lệnh này sẽ hiển thị Popup xin quyền trên màn hình Client trong <b>15 giây</b>. Ảnh chỉ được gửi về khi End-User đồng ý.
      </div>

      {/* KHU VỰC HIỂN THỊ HÌNH ẢNH (IMAGE CONTAINER) */}
      <div style={styles.imageViewer}>
        {loading && (
          <div style={styles.statusBox}>
            <div style={{ fontSize: '2.5rem' }}>⏳</div>
            <h4>Đang gửi Popup xin phép đến máy {selectedMachine?.hostname}...</h4>
            <p style={{ color: '#94a3b8' }}>Chờ người dùng nhấn "Chấp nhận" trên cửa sổ Client[cite: 1, 2, 5].</p>
          </div>
        )}

        {!loading && !imageData && (
          <div style={styles.placeholder}>
            <div style={{ fontSize: '3rem', marginBottom: '8px' }}>🖼️</div>
            <p>Bấm nút <b>"Chụp Màn Hình Ngay"</b> ở trên để lấy hình ảnh màn hình Client hiện tại.</p>
          </div>
        )}

        {!loading && imageData && (
          <div style={styles.imageWrapper}>
            <img 
              src={imageData} 
              alt="Client Screenshot" 
              style={styles.responsiveImage} 
            />
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  actionGroup: { display: 'flex', gap: '10px' },
  btnPrimary: { padding: '10px 18px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  btnSuccess: { padding: '10px 18px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  timeInfo: { fontSize: '0.9rem', color: '#cbd5e1' },
  consentNotice: { padding: '10px 14px', backgroundColor: '#1e293b', borderLeft: '4px solid #f59e0b', borderRadius: '4px', fontSize: '0.85rem', color: '#fef08a' },
  imageViewer: { flex: 1, backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden', padding: '12px' },
  statusBox: { textAlign: 'center', color: '#f8fafc' },
  placeholder: { textAlign: 'center', color: '#64748b' },
  imageWrapper: { width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' },
  responsiveImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }
};

export default Screenshot;