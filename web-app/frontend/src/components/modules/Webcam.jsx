// web-app/frontend/src/components/modules/WebcamMonitor.jsx
import React, { useState, useEffect, useRef } from 'react';

function WebcamMonitor({ machineId }) {
  // --- 🧠 1. KHỞI TẠO BỘ NHỚ TRẠNG THÁI (STATE) ---
  
  // Quản lý trạng thái kết nối mạng: disconnected, connecting, streaming, error
  const [status, setStatus] = useState('disconnected'); 
  
  // Chứa chuỗi Base64 của khung hình (Frame) camera mới nhất
  const [imageSrc, setImageSrc] = useState(null); 
  
  // useRef: Đóng vai trò là "chiếc mỏ neo" giữ chặt đối tượng WebSocket
  // Giúp đường truyền không bị đứt đoạn mỗi khi giao diện React cập nhật
  const wsRef = useRef(null); 

  // --- 🔄 2. HÀM KÍCH HOẠT CAMERA VÀ MỞ LUỒNG TRUYỀN (WEBSOCKET) ---
  const startWebcam = () => {
    // ⚠️ BẢO MẬT: Hiển thị cảnh báo vì việc bật webcam là hành động cực kỳ nhạy cảm
    const confirmAction = window.confirm(
      "CẢNH BÁO: Bạn đang yêu cầu kích hoạt phần cứng Webcam của máy đích.\n" +
      "Hành động này có thể xâm phạm nghiêm trọng quyền riêng tư. Bạn có chắc chắn?"
    );
    if (!confirmAction) return;

    setStatus('connecting');

    try {
      // Thiết lập đường ống WebSocket trỏ tới cổng xử lý Webcam trên Backend
      // Lưu ý: Endpoint này khác với LiveScreen (/api/ws/webcam/...)
      const wsUrl = `ws://localhost:8000/api/ws/webcam/${machineId}`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // KỊCH BẢN A: Khi kết nối mạng thành công
      ws.onopen = () => {
        setStatus('streaming');
        // Backend sẽ ra lệnh cho Agent: "Mở thiết bị cv2.VideoCapture(0) ngay!"
      };

      // KỊCH BẢN B: Khi Frontend nhận được 1 khung hình từ Agent gửi lên
      ws.onmessage = (event) => {
        // Biến chuỗi văn bản Base64 thành định dạng Data URI để hiển thị thành ảnh động
        const frameData = `data:image/jpeg;base64,${event.data}`;
        setImageSrc(frameData); 
      };

      // KỊCH BẢN C: Khi có lỗi mạng (đứt cáp, Agent sập nguồn...)
      ws.onerror = (error) => {
        console.error("Lỗi đường truyền Webcam:", error);
        setStatus('error');
      };

      // KỊCH BẢN D: Khi luồng bị đóng lại an toàn
      ws.onclose = () => {
        setStatus('disconnected');
      };

    } catch (error) {
      alert("Không thể khởi tạo đường truyền Webcam: " + error.message);
      setStatus('error');
    }
  };

  // --- 🛑 3. HÀM TẮT CAMERA VÀ ĐÓNG KẾT NỐI ---
  const stopWebcam = () => {
    // Nếu kết nối đang mở -> Gửi tín hiệu ngắt mạng
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close(); 
      wsRef.current = null;
    }
    setStatus('disconnected');
    setImageSrc(null); // Xóa trắng màn hình hiển thị để đảm bảo riêng tư
  };

  // --- 🧹 4. HÀM BẢO VỆ TÀI NGUYÊN (CLEANUP) ---
  // Tự động tắt luồng Webcam nếu quản trị viên vô tình chuyển sang tab khác 
  // (Ví dụ: Đang xem webcam mà bấm sang tab File, mạng sẽ tự ngắt để tránh lãng phí RAM)
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  // --- 🖼️ GIAO DIỆN NGƯỜI DÙNG ---
  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2>📷 Giám Sát Phần Cứng Camera (Webcam Stream)</h2>
      
      {/* 🎮 THANH CÔNG CỤ ĐIỀU KHIỂN */}
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
          {status === 'streaming' ? '🟢 ĐANG TRUYỀN DỮ LIỆU' : status === 'connecting' ? '🟡 ĐANG KÍCH HOẠT PHẦN CỨNG...' : '🔴 CAMERA ĐANG TẮT'}
        </span>
      </div>

      {/* 🖥️ KHU VỰC HIỂN THỊ CAMERA */}
      <div style={styles.cameraContainer}>
        {imageSrc ? (
          // Khung hình được vẽ lại liên tục tạo thành Video
          <img src={imageSrc} alt="Webcam Stream" style={styles.cameraImage} />
        ) : (
          <div style={styles.placeholder}>
            {status === 'connecting' ? 'Đang khởi động ống kính...' : 'Webcam đã tắt. Bấm kích hoạt để bắt đầu.'}
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

export default WebcamMonitor;