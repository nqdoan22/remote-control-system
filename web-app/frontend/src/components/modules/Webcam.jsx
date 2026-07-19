// web-app/frontend/src/components/modules/Webcam.jsx
import React, { useState, useEffect, useRef } from 'react';

function Webcam({ machineId }) {
  const [status, setStatus] = useState('disconnected'); 
  const [imageSrc, setImageSrc] = useState(null); 
  const wsRef = useRef(null); 

  const startWebcam = () => {
    const confirmAction = window.confirm(
      "CẢNH BÁO RIÊNG TƯ: Yêu cầu kích hoạt phần cứng Camera trên máy trạm Windows.\nHành động này cần sự đồng ý của người dùng đích."
    );
    if (!confirmAction) return;

    setStatus('connecting');

    try {
      const wsUrl = `ws://localhost:8000/api/ws/webcam/${machineId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('streaming');
        // Gửi thông tin thông điệp khởi động phần cứng theo chuẩn cấu trúc JSON
        const startMessage = {
          messageId: crypto.randomUUID(),
          type: "webcam.start",
          timestamp: Math.floor(Date.now() / 1000),
          source: "web-app",
          destination: machineId,
          payload: {}
        };
        ws.send(JSON.stringify(startMessage));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'webcam.frame' && message.payload?.frame) {
            const frameData = `data:image/jpeg;base64,${message.payload.frame}`;
            setImageSrc(frameData); 
          }
        } catch (err) {
          console.error("Lỗi xử lý luồng dữ liệu hình ảnh nhận được:", err);
        }
      };

      ws.onerror = (error) => {
        console.error("Lỗi đường truyền Webcam:", error);
        setStatus('error');
      };

      ws.onclose = () => {
        setStatus('disconnected');
      };

    } catch (error) {
      alert("Không thể khởi tạo đường truyền Webcam: " + error.message);
      setStatus('error');
    }
  };

  const stopWebcam = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const stopMessage = {
        messageId: crypto.randomUUID(),
        type: "webcam.stop",
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
    return () => { stopWebcam(); };
  }, []);

  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2>📷 Giám Sát Phần Cứng Camera (Webcam Stream)</h2>
      
      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {status === 'disconnected' || status === 'error' ? (
          <button onClick={startWebcam} style={styles.btnStart}>
            ▶️ Kích Hoạt Webcam
          </button>
        ) : (
          <button onClick={stopWebcam} style={styles.btnStop}>
            ⏹️ Tắt Webcam
          </button>
        )}

        <span style={{ fontWeight: 'bold', color: status === 'streaming' ? '#10b981' : (status === 'connecting' ? '#f59e0b' : '#ef4444') }}>
          {status === 'streaming' ? '🟢 ĐANG TRUYỀN DỮ LIỆU (ĐÈN CHỈ BÁO TRÊN MÁY ĐÍCH SÁNG)' : status === 'connecting' ? '🟡 ĐANG CHỜ PHẢN HỒI XÁC NHẬN...' : '🔴 CAMERA ĐANG TẮT'}
        </span>
      </div>

      <div style={styles.cameraContainer}>
        {imageSrc ? (
          <img src={imageSrc} alt="Webcam Stream" style={styles.cameraImage} />
        ) : (
          <div style={styles.placeholder}>
            {status === 'connecting' ? 'Đang kích hoạt ống kính đính kèm phần cứng máy trạm...' : 'Webcam đã tắt. Bấm kích hoạt để bắt đầu.'}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  btnStart: { backgroundColor: '#2563eb', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' },
  btnStop: { backgroundColor: '#ef4444', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' },
  cameraContainer: { flex: 1, backgroundColor: '#000', borderRadius: '12px', border: '4px solid #334155', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px', marginTop: '1rem', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' },
  cameraImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'cover' },
  placeholder: { color: '#64748b', fontSize: '1.2rem', fontFamily: 'monospace' }
};

export default Webcam;