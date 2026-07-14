// web-app/frontend/src/components/modules/Screenshot.jsx
import React, { useState } from 'react';

function Screenshot({ machineId }) {
  // --- 🧠 1. QUẢN LÝ TRẠNG THÁI (STATE MANAGEMENT) ---
  
  // Trạng thái tiến trình: 'idle' (rảnh), 'requesting' (đang gửi yêu cầu), 'waiting_confirm' (chờ user xác nhận), 'success' (thành công), 'denied' (bị từ chối)
  const [status, setStatus] = useState('idle'); 
  
  // Lưu trữ chuỗi ảnh Base64 nhận được từ Agent để hiển thị lên thẻ <img>
  const [screenshotUrl, setScreenshotUrl] = useState(null);
  
  // Ghi nhận mốc thời gian chụp để người dùng quản trị biết ảnh này cũ hay mới
  const [capturedAt, setCapturedAt] = useState('');

  // --- 🔄 2. LOGIC MÔ PHỎNG LUỒNG XỬ LÝ (MOCK WORKFLOW) ---
  // Hàm này mô phỏng chính xác luồng đi của dữ liệu từ WebApp -> Gateway -> Agent -> Chờ xác nhận -> Phản hồi ảnh
  const triggerCaptureRequest = () => {
    // Bước A: Chuyển trạng thái sang "Đang gửi yêu cầu hạ tầng"
    setStatus('requesting');
    setScreenshotUrl(null); // Xóa ảnh cũ nếu có

    setTimeout(() => {
      // Bước B: Thể hiện tư duy An toàn & Bảo mật theo yêu cầu đồ án.
      // Hệ thống chuyển sang trạng thái treo máy, chờ User ngồi trước máy Agent bấm "Đồng ý" (Allow)
      setStatus('waiting_confirm');

      // Mô phỏng độ trễ 2.5 giây khi user suy nghĩ và bấm chấp thuận trên Popup của Agent Windows
      setTimeout(() => {
        // Giả lập tình huống User nhấn "ĐỒNG Ý"
        const userApproved = true; 

        if (userApproved) {
          // Chuỗi Base64 giả lập của 1 tấm ảnh chụp màn hình Windows Desktop thực tế
          const mockBase64Image = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450' viewBox='0 0 800 450'><rect width='100%' height='100%' fill='%231e293b'/><circle cx='400' cy='225' r='80' fill='%233b82f6' opacity='0.3'/><text x='50%' y='45%' font-family='Segoe UI, sans-serif' font-weight='bold' font-size='24' fill='%2364748b' text-anchor='middle'>WINDOWS DESKTOP AGENT SIMULATION</text><text x='50%' y='55%' font-family='monospace' font-size='16' fill='%2310b981' text-anchor='middle'>[Connection: Secure WebSocket LAN]</text></svg>";
          
          setScreenshotUrl(mockBase64Image);
          setCapturedAt(new Date().toLocaleTimeString()); // Ghi lại khung giờ chụp thành công
          setStatus('success');
        } else {
          // Trường hợp User từ chối (bấm Deny) trên màn hình máy Agent
          setStatus('denied');
        }
      }, 2500);

    }, 1000);
  };

  // --- 🖨️ 3. GIAO DIỆN HIỂN THỊ (RENDERING) ---
  return (
    <div style={styles.container}>
      {/* TIÊU ĐỀ MODULE */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>📸 Chụp Màn Hình Từ Xa (Remote Screenshot)</h2>
          <p style={styles.subtitle}>Gửi yêu cầu lệnh chụp màn hình thời gian thực dưới dạng chuỗi dữ liệu ảnh Base64.</p>
        </div>
        
        {/* NÚT BẤM KÍCH HOẠT LỆNH - Bị vô hiệu hóa khi hệ thống đang xử lý luồng ngầm */}
        <button 
          onClick={triggerCaptureRequest}
          disabled={status === 'requesting' || status === 'waiting_confirm'}
          style={{
            ...styles.captureBtn,
            backgroundColor: (status === 'requesting' || status === 'waiting_confirm') ? '#94a3b8' : '#2563eb',
            cursor: (status === 'requesting' || status === 'waiting_confirm') ? 'not-allowed' : 'pointer'
          }}
        >
          {status === 'idle' && '🚀 Gửi Lệnh Chụp'}
          {status === 'requesting' && '📡 Đang Kết Nối...'}
          {status === 'waiting_confirm' && '⏳ Chờ Máy Đích Phê Duyệt...'}
          {(status === 'success' || status === 'denied') && '📸 Chụp Tấm Khác'}
        </button>
      </div>

      {/* ⚠️ KHU VỰC HIỂN THỊ TRẠNG THÁI TƯ DUY BẢO MẬT & RỦI RO */}
      <div style={styles.statusBannerContainer}>
        {status === 'waiting_confirm' && (
          <div style={{...styles.banner, backgroundColor: '#fef3c7', color: '#d97706', border: '1px solid #fcd34d'}}>
            <strong>🛡️ ĐẢM BẢO QUYỀN RIÊNG TƯ:</strong> Một thông báo xác nhận yêu cầu cấp quyền truy cập màn hình (UAC Prompt) đang hiển thị tại máy trạm <strong>{machineId}</strong>. Tiến trình bị đóng băng cho đến khi người dùng đồng ý.
          </div>
        )}
        
        {status === 'denied' && (
          <div style={{...styles.banner, backgroundColor: '#fee2e2', color: '#dc2626', border: '1px solid #fca5a5'}}>
            <strong>❌ TRUY CẬP BỊ TỪ CHỐI:</strong> Người dùng tại máy trạm <strong>{machineId}</strong> đã chủ động nhấn từ chối hoặc yêu cầu xác nhận đã hết hạn (Timeout). Không thể bóc tách dữ liệu màn hình!
          </div>
        )}

        {status === 'success' && (
          <div style={{...styles.banner, backgroundColor: '#ecfdf5', color: '#059669', border: '1px solid #a7f3d0'}}>
            <strong>✅ THÀNH CÔNG:</strong> Đã nhận gói tin chứa chuỗi Base64 từ Agent lúc <strong>{capturedAt}</strong>. Mã hóa hình ảnh an toàn.
          </div>
        )}
      </div>

      {/* 🖼️ KHU VỰC CANVAS / KHUNG HIỂN THỊ HÌNH ẢNH SCREENSHOT */}
      <div style={styles.viewportContainer}>
        {status === 'idle' && (
          <div style={styles.emptyState}>
            <span style={{fontSize: '3.5rem'}}>🖥️</span>
            <p style={{margin: '1rem 0 0 0', fontWeight: '500'}}>Chưa có dữ liệu hình ảnh</p>
            <p style={{margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#94a3b8'}}>Nhấn nút "Gửi Lệnh Chụp" phía trên để yêu cầu Agent trích xuất màn hình desktop.</p>
          </div>
        )}

        {(status === 'requesting' || status === 'waiting_confirm') && (
          <div style={styles.loadingState}>
            <div style={styles.spinner}></div>
            <p style={{marginTop: '1rem', fontWeight: '500', color: '#475569'}}>
              {status === 'requesting' ? 'Đang đóng gói cấu trúc TCP/WebSocket...' : 'Đang đợi người dùng bấm [Cho Phép] trên OS Windows...'}
            </p>
          </div>
        )}

        {screenshotUrl && (
          <div style={styles.imageWrapper}>
            <img src={screenshotUrl} alt="Remote Desktop Screenshot" style={styles.screenshotImage} />
          </div>
        )}
      </div>
    </div>
  );
}

// --- 🖌️ CSS INLINE MƯỢT MÀ, ĐỒNG BỘ DESIGN SYSTEM THANH LỊCH ---
const styles = {
  container: { padding: '1rem' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' },
  title: { fontSize: '1.5rem', fontWeight: 'bold', color: '#1e293b', margin: '0 0 0.25rem 0' },
  subtitle: { fontSize: '0.95rem', color: '#64748b', margin: 0 },
  captureBtn: { color: 'white', border: 'none', padding: '0.65rem 1.3rem', borderRadius: '6px', fontWeight: 'bold', fontSize: '0.9rem', transition: 'all 0.2s ease', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' },
  
  statusBannerContainer: { marginBottom: '1.5rem' },
  banner: { padding: '1rem', borderRadius: '8px', fontSize: '0.875rem', lineHeight: '1.5' },
  
  viewportContainer: { width: '100%', minHeight: '450px', backgroundColor: '#f1f5f9', borderRadius: '12px', border: '2px dashed #cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', boxSizing: 'border-box' },
  emptyState: { textAlign: 'center', color: '#64748b', padding: '2rem' },
  
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center' },
  spinner: { width: '40px', height: '40px', border: '4px solid #cbd5e1', borderTopColor: '#2563eb', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  
  imageWrapper: { width: '100%', maxWidth: '800px', backgroundColor: 'white', borderRadius: '8px', padding: '0.5rem', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0' },
  screenshotImage: { width: '100%', height: 'auto', borderRadius: '6px', display: 'block' }
};

// Khởi tạo hiệu ứng xoay tròn cho Spinner thông qua CSS chèn trực tiếp vào Document Head (Để tránh phải xài file CSS ngoài)
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement("style");
  styleSheet.innerText = `@keyframes spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(styleSheet);
}

export default Screenshot;