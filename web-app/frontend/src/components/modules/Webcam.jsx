import React, { useState, useEffect, useRef } from 'react';
import { controlWebcamApi, isWsError, getWsErrorMessage } from '../../services/api';

/**
 * Webcam Module - Stream camera trực tiếp từ máy Client kèm Cảnh báo Đèn đỏ.
 * webcam.start / webcam.stop qua REST (Sensitive Feature List - Gateway tự xin
 * Permission Confirmation). Frame (webcam.frame) nhận qua WebSocket broadcast.
 */
const Webcam = ({ selectedMachine, lastMessage }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);
  const isStreamingRef = useRef(false);

  const stopWebcam = async (silent = false) => {
    setIsStreaming(false);
    isStreamingRef.current = false;
    setLoading(false);
    if (!selectedMachine) return;
    try {
      await controlWebcamApi(selectedMachine.machineId, 'stop');
    } catch (err) {
      if (!silent) alert('Lỗi tắt Webcam: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  // Tự động tắt Webcam khi đổi máy / rời trang để đảm bảo quyền riêng tư
  useEffect(() => {
    return () => {
      if (isStreamingRef.current) stopWebcam(true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMachine]);

  // Lắng nghe frame webcam.frame phát về từ Gateway (broadcast theo machine_id)
  useEffect(() => {
    if (!lastMessage || !isStreaming) return;
    if (lastMessage.type === 'webcam.frame') {
      const { image } = lastMessage.payload || {};
      if (image) setCurrentFrame(`data:image/jpeg;base64,${image}`);
    }
  }, [lastMessage, isStreaming]);

  const startWebcam = async () => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      const res = await controlWebcamApi(selectedMachine.machineId, 'start');
      setLoading(false);
      if (isWsError(res)) {
        alert(getWsErrorMessage(res));
      } else {
        setIsStreaming(true);
        isStreamingRef.current = true;
      }
    } catch (err) {
      setLoading(false);
      alert('Lỗi bật Webcam: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.privacyBanner}>
        📷 <b>QUYỀN RIÊNG TƯ & AN TOÀN TRỰC QUAN:</b>
        <span> Khi Webcam bật, một cửa sổ <b>Đèn Chớp Đỏ (Red Indicator)</b> bắt buộc sẽ hiển thị công khai trên màn hình Client để cảnh báo người dùng.</span>
      </div>

      <div style={styles.topBar}>
        {!isStreaming ? (
          <button onClick={startWebcam} disabled={loading} style={styles.btnStart}>
            {loading ? '⏳ Đang chờ xin phép người dùng Client...' : '📷 Bật Webcam Client'}
          </button>
        ) : (
          <button onClick={() => stopWebcam()} style={styles.btnStop}>
            🛑 Tắt Webcam
          </button>
        )}

        {isStreaming && (
          <div style={styles.recordingBadge}>
            <span style={styles.redDot}></span> WEBCAM IS ACTIVE
          </div>
        )}
      </div>

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
