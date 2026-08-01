import React, { useState, useEffect, useRef } from 'react';
import { controlLiveScreenApi, isWsError, getWsErrorMessage } from '../../services/api';

/**
 * LiveScreen Module - Stream màn hình máy Client theo thời gian thực.
 * screen.live.start / screen.live.stop qua REST (Gateway tự chặn lại để xin
 * Permission Confirmation - Sensitive Feature List). Frame (screen.live.frame)
 * nhận qua kênh WebSocket broadcast (lastMessage), KHÔNG qua REST.
 *
 * @param {Object} selectedMachine - Thông tin máy Client đang chọn
 * @param {Object} lastMessage - Message mới nhất từ WebSocket bridge: { type, payload }
 */
const LiveScreen = ({ selectedMachine, lastMessage }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [fps, setFps] = useState(10);
  const [realtimeFps, setRealtimeFps] = useState(0);

  const frameCountRef = useRef(0);
  const lastFpsCalcTimeRef = useRef(Date.now());
  const isStreamingRef = useRef(false); // đọc được giá trị mới nhất trong cleanup unmount

  const stopStreaming = async (silent = false) => {
    setIsStreaming(false);
    isStreamingRef.current = false;
    setLoading(false);
    setRealtimeFps(0);
    if (!selectedMachine) return;
    try {
      await controlLiveScreenApi(selectedMachine.machineId, 'stop');
    } catch (err) {
      if (!silent) alert('Lỗi dừng Live Screen: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  // Reset luồng Stream khi Admin chuyển đổi sang máy Client khác / rời trang
  useEffect(() => {
    return () => {
      if (isStreamingRef.current) stopStreaming(true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMachine]);

  // Lắng nghe frame phát về từ Gateway (broadcast theo machine_id)
  useEffect(() => {
    if (!lastMessage || !isStreaming) return;

    if (lastMessage.type === 'screen.live.frame') {
      const { image } = lastMessage.payload || {};
      if (image) setCurrentFrame(`data:image/jpeg;base64,${image}`);

      frameCountRef.current += 1;
      const now = Date.now();
      if (now - lastFpsCalcTimeRef.current >= 1000) {
        setRealtimeFps(frameCountRef.current);
        frameCountRef.current = 0;
        lastFpsCalcTimeRef.current = now;
      }
    }
  }, [lastMessage, isStreaming]);

  const startStreaming = async () => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      // Gateway sẽ chặn lại chờ Permission Confirmation (tối đa 30s) trước khi trả response
      const res = await controlLiveScreenApi(selectedMachine.machineId, 'start', fps);
      setLoading(false);
      if (isWsError(res)) {
        alert(getWsErrorMessage(res));
      } else {
        setIsStreaming(true);
        isStreamingRef.current = true;
      }
    } catch (err) {
      setLoading(false);
      alert('Lỗi bắt đầu Live Screen: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  return (
    <div style={styles.container}>
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
            <button onClick={() => stopStreaming()} style={styles.btnStop}>
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

        {isStreaming && (
          <div style={styles.streamStats}>
            <span style={styles.liveIndicator}>🔴 LIVE</span>
            <span>Tốc độ: <b>{realtimeFps} FPS</b></span>
          </div>
        )}
      </div>

      <div style={styles.videoCanvasWrapper}>
        {loading && (
          <div style={styles.statusBox}>
            <div style={{ fontSize: '2.5rem' }}>⏳</div>
            <h4>Đang gửi yêu cầu và chờ người dùng Client đồng ý...</h4>
            <p style={{ color: '#94a3b8' }}>Popup sẽ xuất hiện trên màn hình máy bị điều khiển trong 30s.</p>
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
