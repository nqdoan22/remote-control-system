// web-app/frontend/src/components/modules/LiveScreen.jsx
import React, { useState, useEffect, useRef } from 'react';

function LiveScreen({ machineId }) {
  const [status, setStatus] = useState('disconnected'); 
  const [imageSrc, setImageSrc] = useState(null); 
  const wsRef = useRef(null); 

  const startStream = () => {
    setStatus('connecting');

    try {
      const wsUrl = `ws://localhost:8000/api/ws/livestream/${machineId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('streaming');
        // Đồng bộ hóa gửi tin nhắn kích hoạt Command lên Gateway
        const startMessage = {
          messageId: crypto.randomUUID(),
          type: "screen.live.start",
          timestamp: Math.floor(Date.now() / 1000),
          source: "web-app",
          destination: machineId,
          payload: {}
        };
        ws.send(JSON.stringify(startMessage));
      };

      // Xử lý thông điệp JSON gói tin từ dữ liệu phân tuyến của Gateway
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          // Kiểm tra đúng loại tin nhắn đồng bộ theo quy ước đặt tên: module.action
          if (message.type === 'screen.live.frame' && message.payload?.frame) {
            const frameData = `data:image/jpeg;base64,${message.payload.frame}`;
            setImageSrc(frameData); 
          }
        } catch (err) {
          console.error("Gói tin không khớp định dạng thiết kế JSON tổng quát:", err);
        }
      };

      ws.onerror = (error) => {
        console.error("Lỗi luồng WebSocket:", error);
        setStatus('error');
      };

      ws.onclose = () => {
        setStatus('disconnected');
      };

    } catch (error) {
      alert("Không thể khởi tạo luồng mạng: " + error.message);
      setStatus('error');
    }
  };

  const stopStream = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Gửi lệnh đóng stream có cấu trúc trước khi ngắt socket vật lý
      const stopMessage = {
        messageId: crypto.randomUUID(),
        type: "screen.live.stop",
        timestamp: Math.floor(Date.now() / 1000),
        source: "web-app",
        destination: machineId,
        payload: {}
      };
      wsRef.current.send(JSON.stringify(stopMessage));
      wsRef.current.close(); 
      wsRef.current = null;
    }
    setStatus('disconnected');
    setImageSrc(null); 
  };

  useEffect(() => {
    return () => { stopStream(); };
  }, []);

  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2>📺 Luồng Giám Sát Màn Hình (Real-time Stream)</h2>
      
      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {status === 'disconnected' || status === 'error' ? (
          <button onClick={startStream} style={styles.btnStart}>
            ▶️ Bắt Đầu Xem Trực Tiếp
          </button>
        ) : (
          <button onClick={stopStream} style={styles.btnStop}>
            ⏹️ Dừng Giám Sát
          </button>
        )}

        <span style={{ fontWeight: 'bold', color: status === 'streaming' ? '#10b981' : (status === 'connecting' ? '#f59e0b' : '#ef4444') }}>
          {status === 'streaming' ? '🟢 KẾT NỐI ỔN ĐỊNH' : status === 'connecting' ? '🟡 ĐANG XÁC THỰC QUYỀN TRUY CẬP...' : '🔴 ĐÃ NGẮT KẾT NỐI'}
        </span>
      </div>

      <div style={styles.screenContainer}>
        {imageSrc ? (
          <img src={imageSrc} alt="Live Screen" style={styles.screenImage} />
        ) : (
          <div style={styles.placeholder}>
            {status === 'connecting' ? 'Đang chờ khung hình xác nhận từ End User...' : 'Màn hình đang tắt. Bấm bắt đầu để xem.'}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  btnStart: { backgroundColor: '#2563eb', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' },
  btnStop: { backgroundColor: '#ef4444', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' },
  screenContainer: { flex: 1, backgroundColor: '#0f172a', borderRadius: '8px', border: '2px solid #334155', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px', marginTop: '1rem' },
  screenImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' },
  placeholder: { color: '#64748b', fontSize: '1.2rem', fontFamily: 'monospace' }
};

export default LiveScreen;