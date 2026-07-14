// web-app/frontend/src/components/modules/LiveScreen.jsx
import React, { useState, useEffect, useRef } from 'react';

function LiveScreen({ machineId }) {
  // --- 🧠 1. QUẢN LÝ TRẠNG THÁI VÀ BỘ NHỚ TẠM ---
  
  // Trạng thái hệ thống: Đang kết nối, Đã kết nối (Đang stream), hoặc Bị lỗi
  const [status, setStatus] = useState('disconnected'); 
  
  // Nơi chứa dữ liệu ảnh Base64 mới nhất để hiển thị lên màn hình
  const [imageSrc, setImageSrc] = useState(null); 
  
  // useRef: Đóng vai trò như một "cái neo" giữ kết nối WebSocket không bị mất 
  // khi React vẽ lại giao diện. Nó không làm màn hình chớp giật như useState.
  const wsRef = useRef(null); 

  // --- 🔄 2. HÀM KHỞI TẠO LUỒNG KẾT NỐI (WEBSOCKET CLIENT) ---
  const startStream = () => {
    setStatus('connecting');

    try {
      // ⚠️ LƯU Ý MẠNG: Khác với http://, WebSocket bắt đầu bằng ws:// (hoặc wss:// nếu có mã hóa SSL)
      // Địa chỉ này trỏ thẳng tới cổng WebSocket mở riêng trên Backend FastAPI của bạn
      const wsUrl = `ws://localhost:8000/api/ws/livestream/${machineId}`;
      
      // Tạo một đường ống mạng nối thẳng từ Trình duyệt (Frontend) đến Backend
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // SỰ KIỆN A: Khi đường ống được kết nối thành công
      ws.onopen = () => {
        setStatus('streaming');
        // Lúc này, Backend sẽ tự hiểu và ra lệnh cho Agent: "Bắt đầu chụp ảnh liên tục đi!"
      };

      // SỰ KIỆN B: Khi đường ống nhận được "hàng" (Gói tin từ Backend gửi tới)
      ws.onmessage = (event) => {
        // event.data chính là chuỗi mã hóa Base64 của 1 khung hình (1 tấm ảnh)
        // Ta nối thêm tiền tố "data:image/jpeg;base64," để Trình duyệt hiểu đây là một bức ảnh
        const frameData = `data:image/jpeg;base64,${event.data}`;
        setImageSrc(frameData); // Cập nhật hình ảnh lên UI ngay lập tức
      };

      // SỰ KIỆN C: Khi đường ống bị đứt ngầm hoặc lỗi mạng LAN
      ws.onerror = (error) => {
        console.error("Lỗi luồng WebSocket:", error);
        setStatus('error');
      };

      // SỰ KIỆN D: Khi kết nối bị đóng lại (do người dùng tắt hoặc Agent sập nguồn)
      ws.onclose = () => {
        setStatus('disconnected');
      };

    } catch (error) {
      alert("Không thể khởi tạo luồng mạng: " + error.message);
      setStatus('error');
    }
  };

  // --- 🛑 3. HÀM ĐÓNG LUỒNG KẾT NỐI ---
  const stopStream = () => {
    // Nếu đường ống đang tồn tại và đang mở, ta tiến hành bóp nghẹt (đóng) nó lại
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close(); // Gửi tín hiệu đóng lên Backend
      wsRef.current = null;
    }
    setStatus('disconnected');
    setImageSrc(null); // Xóa khung hình cuối cùng còn lưu trên màn hình
  };

  // --- 🧹 4. DỌN DẸP BỘ NHỚ KHI CHUYỂN TAB ---
  // Rất quan trọng: Nếu người dùng đang xem stream mà bấm sang tab "Quản lý File",
  // ta phải tự động cắt đứt luồng stream, nếu không máy Agent sẽ bị vắt kiệt CPU.
  useEffect(() => {
    return () => {
      stopStream(); // Hàm chạy khi Component bị tháo gỡ (Unmount)
    };
  }, []);

  // --- 🖼️ GIAO DIỆN HIỂN THỊ (RÚT GỌN CSS) ---
  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2>📺 Luồng Giám Sát Màn Hình (Real-time Stream)</h2>
      
      {/* 🎮 KHU VỰC ĐIỀU KHIỂN */}
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

        {/* Đèn tín hiệu mạng */}
        <span style={{ fontWeight: 'bold', color: status === 'streaming' ? '#10b981' : (status === 'connecting' ? '#f59e0b' : '#ef4444') }}>
          {status === 'streaming' ? '🟢 KẾT NỐI ỔN ĐỊNH' : status === 'connecting' ? '🟡 ĐANG THIẾT LẬP ĐƯỜNG TRUYỀN...' : '🔴 ĐÃ NGẮT KẾT NỐI'}
        </span>
      </div>

      {/* 🖥️ KHU VỰC MÀN HÌNH HIỂN THỊ */}
      <div style={styles.screenContainer}>
        {imageSrc ? (
          // Kỹ thuật Data URI: Nhét thẳng chuỗi Base64 vào thuộc tính src của thẻ img
          <img src={imageSrc} alt="Live Screen" style={styles.screenImage} />
        ) : (
          <div style={styles.placeholder}>
            {status === 'connecting' ? 'Đang chờ khung hình đầu tiên...' : 'Màn hình đang tắt. Bấm bắt đầu để xem.'}
          </div>
        )}
      </div>
    </div>
  );
}

// CSS tối giản để màn hình trông giống một chiếc TV
const styles = {
  btnStart: { backgroundColor: '#2563eb', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' },
  btnStop: { backgroundColor: '#ef4444', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' },
  screenContainer: { flex: 1, backgroundColor: '#0f172a', borderRadius: '8px', border: '2px solid #334155', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px', marginTop: '1rem' },
  screenImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' },
  placeholder: { color: '#64748b', fontSize: '1.2rem', fontFamily: 'monospace' }
};

export default LiveScreen;