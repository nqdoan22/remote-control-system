import React, { useState, useEffect, useRef } from 'react';

/**
 * LiveScreen Module - Stream màn hình máy Client theo thời gian thực (Real-time Screen Stream)
 * 
 * @param {Object} selectedMachine - Thông tin máy Client đang chọn
 * @param {Function} onSendMessage - Hàm gửi WebSocket message đến Gateway
 * @param {Object} lastMessage - Khung hình hoặc phản hồi nhận từ WebSocket
 */
const LiveScreen = ({ selectedMachine, onSendMessage, lastMessage }) => {
  // ===== STATE QUẢN LÝ LUỒNG STREAM =====
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [fps, setFps] = useState(10); // Cấu hình FPS mặc định (5 - 15 FPS)
  const [realtimeFps, setRealtimeFps] = useState(0); // Đo FPS thực tế nhận được

  // Reference để tính toán FPS thực tế
  const frameCountRef = useRef(0);
  const lastFpsCalcTimeRef = useRef(Date.now());

  // Reset luồng Stream khi Admin chuyển đổi sang máy Client khác
  useEffect(() => {
    if (isStreaming) {
      stopStreaming();
    }
    setCurrentFrame(null);
    setIsStreaming(false);
    setLoading(false);
  }, [selectedMachine]);

  // CLEANUP: Tự động ngắt Stream khi Admin chuyển sang Tab Module khác (Chống lãng phí băng thông)
  useEffect(() => {
    return () => {
      if (isStreaming) {
        onSendMessage({
          target_machine_id: selectedMachine?.machineId,
          action: 'stop_live_screen'
        });
      }
    };
  }, [isStreaming, selectedMachine]);

  // ===== LẮNG NGHE KHUNG HÌNH TRẢ VỀ TỪ WEBSOCKET =====
  useEffect(() => {
    if (!lastMessage) return;

    // 1. Phản hồi xác nhận lệnh Bắt đầu/Dừng Stream
    if (lastMessage.action === 'start_live_screen_response') {
      setLoading(false);
      if (lastMessage.status === 'success') {
        setIsStreaming(true);
      } else if (lastMessage.status === 'rejected') {
        alert('❌ Người dùng trên máy Client đã TỪ CHỐI cấp quyền xem Live Screen![cite: 1, 2, 5]');
      } else if (lastMessage.status === 'timeout') {
        alert('⏱️ Yêu cầu xin quyền đã HẾT HẠN (Timeout 15s)![cite: 1, 2, 5, 7]');
      } else {
        alert('Lỗi bắt đầu Live Screen: ' + lastMessage.message);
      }
    }

    // 2. Nhận từng Khung hình Stream (Frame Payload)
    if (lastMessage.action === 'live_screen_frame' && isStreaming) {
      setCurrentFrame(`data:image/jpeg;base64,${lastMessage.data.image_base64}`);
      
      // Tính toán FPS thực tế
      frameCountRef.current += 1;
      const now = Date.now();
      if (now - lastFpsCalcTimeRef.current >= 1000) {
        setRealtimeFps(frameCountRef.current);
        frameCountRef.current = 0;
        lastFpsCalcTimeRef.current = now;
      }
    }
  }, [lastMessage, isStreaming]);

  // Gửi lệnh Bắt đầu Stream
  const startStreaming = () => {
    if (!selectedMachine) return;
    setLoading(true);
    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'start_live_screen',
      payload: { target_fps: fps }
    });
  };

  // Gửi lệnh Dừng Stream
  const stopStreaming = () => {
    setIsStreaming(false);
    setLoading(false);
    setRealtimeFps(0);
    onSendMessage({
      target_machine_id: selectedMachine?.machineId,
      action: 'stop_live_screen'
    });
  };

  return (
    <div style={styles.container}>
      {/* THANH CẤU HÌNH VÀ BẤM BẮT ĐẦU / DỪNG */}
      <div style={styles.topBar}>
        <div style={styles.controlsGroup}>
          {!isStreaming ? (
            <button 
              onClick={startStreaming} 
              disabled={loading}
              style={styles.btnStart}
            >
              {loading ? '⏳ Đang xin phép người dùng Client...' : '▶ Bắt Đầu Stream Live'}
            </button>
          ) : (
            <button onClick={stopStreaming} style={styles.btnStop}>
              ⏹ Dừng Stream
            </button>
          )}

          <div style={styles.fpsSelector}>
            <label style={{ fontSize: '0.85rem' }}>Cấu hình FPS: </label>
            <select 
              value={fps} 
              onChange={(e) => setFps(Number(e.target.value))}
              disabled={isStreaming || loading}
              style={styles.selectInput}
            >
              <option value={5}>5 FPS (Tiết kiệm băng thông)</option>
              <option value={10}>10 FPS (Mặc định - Cân bằng)</option>
              <option value={15}>15 FPS (Mượt mà)</option>
            </select>
          </div>
        </div>

        {/* THÔNG SỐ TRẠNG THÁI STREAM */}
        {isStreaming && (
          <div style={styles.streamStats}>
            <span style={styles.liveIndicator}>🔴 LIVE</span>
            <span>Tốc độ: <b>{realtimeFps} FPS</b></span>
          </div>
        )}
      </div>

      {/* KHU VỰC HIỂN THỊ LUỒNG VIDEO (STREAM SCREEN) */}
      <div style={styles.videoCanvasWrapper}>
        {loading && (
          <div style={styles.statusBox}>
            <div style={{ fontSize: '2.5rem' }}>⏳</div>
            <h4>Đang gửi yêu cầu và chờ người dùng Client đồng ý...</h4>
            <p style={{ color: '#94a3b8' }}>Popup sẽ xuất hiện trên màn hình máy bị điều khiển trong 15s[cite: 1, 2, 5, 7].</p>
          </div>
        )}

        {!loading && !isStreaming && (
          <div style={styles.placeholder}>
            <div style={{ fontSize: '3.5rem', marginBottom: '8px' }}>🖥️</div>
            <p>Nhấn <b>"Bắt Đầu Stream Live"</b> để theo dõi màn hình trực tiếp.</p>
          </div>
        )}

        {isStreaming && currentFrame && (
          <img 
            src={currentFrame} 
            alt="Live Screen Stream" 
            style={styles.streamImage} 
          />
        )}
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#1e293b', padding: '12px 16px', borderRadius: '8px', border: '1px solid #334155' },
  controlsGroup: { display: 'flex', alignItems: 'center', gap: '16px' },
  btnStart: { padding: '8px 16px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  btnStop: { padding: '8px 16px', backgroundColor: '#dc2626', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  fpsSelector: { display: 'flex', alignItems: 'center', gap: '8px' },
  selectInput: { padding: '6px 10px', backgroundColor: '#0f172a', color: '#fff', border: '1px solid #475569', borderRadius: '4px' },
  streamStats: { display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem', color: '#f8fafc' },
  liveIndicator: { backgroundColor: '#b91c1c', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' },
  videoCanvasWrapper: { flex: 1, backgroundColor: '#000', border: '1px solid #334155', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' },
  statusBox: { textAlign: 'center', color: '#f8fafc' },
  placeholder: { textAlign: 'center', color: '#64748b' },
  streamImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }
};

export default LiveScreen;