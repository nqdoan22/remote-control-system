import React, { useState, useEffect, useRef, useMemo } from 'react';
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

  // ⚠️ Phát hiện Admin đang xem chính máy Client. Trường hợp này frame chụp lại
  // bao gồm chính cửa sổ trình duyệt đang hiển thị stream → hiệu ứng gương lặp
  // vô hạn (feedback loop / "đệ quy"). Client sẽ được báo selfView để che toàn bộ
  // cửa sổ trình duyệt trong stream (kể cả khi đang mở trang web khác).
  // localhost/127.0.0.1 cũng coi là self-view (khi Admin chạy toàn bộ hệ thống
  // trên chính máy này để tự kiểm tra).
  const isSelfView = useMemo(() => {
    if (!selectedMachine) return false;
    const host = window.location.hostname;
    if (!host) return false;
    return host === selectedMachine.ipAddress || host === 'localhost' || host === '127.0.0.1';
  }, [selectedMachine]);

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
  }, [selectedMachine?.machineId]);

  // Lắng nghe frame phát về từ Gateway (broadcast theo machine_id)
  useEffect(() => {
    if (!lastMessage || !isStreaming) return;

    if (lastMessage.type === 'screen.live.frame') {
      const { image_base64 } = lastMessage.payload || {};
      if (image_base64) setCurrentFrame(`data:image/jpeg;base64,${image_base64}`);

      frameCountRef.current += 1;
      const now = Date.now();
      if (now - lastFpsCalcTimeRef.current >= 1000) {
        setRealtimeFps(frameCountRef.current);
        frameCountRef.current = 0;
        lastFpsCalcTimeRef.current = now;
      }
    }
  }, [lastMessage, isStreaming]);

  const startStreaming = async (retry = true) => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      // Gateway sẽ chặn lại chờ Permission Confirmation (tối đa 30s) trước khi trả response
      const res = await controlLiveScreenApi(selectedMachine.machineId, 'start', fps, isSelfView);
      setLoading(false);
      if (isWsError(res)) {
        const code = res.payload?.code;
        if (retry && code === 'ALREADY_RUNNING') {
          // Client vẫn còn stream cũ (VD: lần trước rời trang đột ngột, lệnh stop
          // chưa kịp về). Tự động tắt stream cũ rồi bật lại ngay cho Admin.
          try {
            await controlLiveScreenApi(selectedMachine.machineId, 'stop');
          } catch (err) {
            /* bỏ qua — start lại lần 2 vẫn xử lý tiếp */
          }
          return startStreaming(false);
        }
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
      {isSelfView && (
        <div style={styles.selfViewWarning}>
          <span style={{ fontSize: '1.2rem', marginRight: '8px' }}>🪞</span>
          <div>
            <b>Bạn đang xem chính máy này</b> (trình duyệt đang truy cập qua IP{' '}
            {selectedMachine?.ipAddress}). Client sẽ <b>che toàn bộ cửa sổ trình duyệt</b>{' '}
            trong stream (kể cả khi bạn mở tab/trang web khác) để tránh hiệu ứng gương
            lặp vô hạn (feedback loop) — vùng đó hiển thị màu đen.
          </div>
        </div>
      )}

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
  selfViewWarning: { display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: '#451a03', border: '1px solid #f59e0b', color: '#fde68a', padding: '10px 14px', borderRadius: '8px', fontSize: '0.9rem', lineHeight: 1.5 },
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
