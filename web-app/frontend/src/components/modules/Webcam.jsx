import React, { useState, useEffect } from 'react';

/**
 * Webcam Module - Stream camera trực tiếp từ máy Client kèm Cảnh báo Đèn đỏ (Red Indicator)
 */
const Webcam = ({ selectedMachine, onSendMessage, lastMessage }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);

  // Reset khi đổi máy
  useEffect(() => {
    if (isStreaming) {
      stopWebcam();
    }
    setCurrentFrame(null);
    setIsStreaming(false);
    setLoading(false);
  }, [selectedMachine]);

  // CLEANUP: Tự động tắt Webcam khi Admin thoát khỏi Tab để đảm bảo quyền riêng tư
  useEffect(() => {
    return () => {
      if (isStreaming) {
        onSendMessage({
          target_machine_id: selectedMachine?.machineId,
          action: 'stop_webcam'
        });
      }
    };
  }, [isStreaming, selectedMachine]);

  // LẮNG NGHE LỖI VÀ KHUNG HÌNH TỪ WEBSOCKET
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.action === 'start_webcam_response') {
      setLoading(false);
      if (lastMessage.status === 'success') {
        setIsStreaming(true);
      } else if (lastMessage.status === 'rejected') {
        alert('❌ Người dùng Client TỪ CHỐI mở Webcam![cite: 1, 2, 5]');
      } else if (lastMessage.status === 'timeout') {
        alert('⏱️ Yêu cầu mở Webcam đã HẾT HẠN (Timeout 15s)![cite: 1, 2, 5, 7]');
      } else {
        alert('Lỗi Webcam: ' + lastMessage.message);
      }
    }

    if (lastMessage.action === 'webcam_frame' && isStreaming) {
      setCurrentFrame(`data:image/jpeg;base64,${lastMessage.data.image_base64}`);
    }
  }, [lastMessage, isStreaming]);

  const startWebcam = () => {
    if (!selectedMachine) return;
    setLoading(true);
    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'start_webcam'
    });
  };

  const stopWebcam = () => {
    setIsStreaming(false);
    setLoading(false);
    onSendMessage({
      target_machine_id: selectedMachine?.machineId,
      action: 'stop_webcam'
    });
  };

  return (
    <div style={styles.container}>
      {/* CẢNH BÁO MINH BẠCH BẢO MẬT (RED INDICATOR NOTICE) */}
      <div style={styles.privacyBanner}>
        📷 <b>QUYỀN RIÊNG TƯ & AN TOÀN TRỰC QUAN:</b> 
        <span> Khi Webcam bật, một cửa sổ <b>Đèn Chớp Đỏ (Red Indicator)</b> bắt buộc sẽ hiển thị công khai trên màn hình Client để cảnh báo người dùng[cite: 1, 2, 3, 6].</span>
      </div>

      {/* THANH THAO TÁC */}
      <div style={styles.topBar}>
        {!isStreaming ? (
          <button onClick={startWebcam} disabled={loading} style={styles.btnStart}>
            {loading ? '⏳ Đang chờ xin phép người dùng Client...' : '📷 Bật Webcam Client'}
          </button>
        ) : (
          <button onClick={stopWebcam} style={styles.btnStop}>
            🛑 Tắt Webcam
          </button>
        )}

        {isStreaming && (
          <div style={styles.recordingBadge}>
            <span style={styles.redDot}></span> WEBCAM IS ACTIVE
          </div>
        )}
      </div>

      {/* MÀN HÌNH HIỂN THỊ CAMERA */}
      <div style={styles.cameraViewer}>
        {loading && (
          <div style={styles.statusBox}>
            <div style={{ fontSize: '2.5rem' }}>⏳</div>
            <h4>Đang hiển thị Popup xin quyền mở Camera trên Client...</h4>
          </div>
        )}

        {!loading && !isStreaming && (
          <div style={styles.placeholder}>
            <div style={{ fontSize: '3.5rem', marginBottom: '8px' }}>📸</div>
            <p>Nhấn <b>"Bật Webcam Client"</b> để xem luồng Video trực tiếp từ Camera.</p>
          </div>
        )}

        {isStreaming && currentFrame && (
          <div style={styles.frameContainer}>
            <img src={currentFrame} alt="Webcam Stream" style={styles.webcamImage} />
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' },
  privacyBanner: { padding: '10px 14px', backgroundColor: '#451a1a', border: '1px solid #991b1b', borderRadius: '6px', color: '#fca5a5', fontSize: '0.85rem' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  btnStart: { padding: '10px 18px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  btnStop: { padding: '10px 18px', backgroundColor: '#dc2626', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  recordingBadge: { display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', fontWeight: 'bold', fontSize: '0.85rem' },
  redDot: { width: '10px', height: '10px', backgroundColor: '#ef4444', borderRadius: '50%', display: 'inline-block' },
  cameraViewer: { flex: 1, backgroundColor: '#000', border: '1px solid #334155', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' },
  statusBox: { textAlign: 'center', color: '#f8fafc' },
  placeholder: { textAlign: 'center', color: '#64748b' },
  frameContainer: { width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' },
  webcamImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', borderRadius: '4px' }
};

export default Webcam;