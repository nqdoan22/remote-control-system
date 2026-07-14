// web-app/frontend/src/hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';
import { CentralWebSocketService } from '../services/websocket';

/**
 * 🪝 useWebSocket: Custom Hook điều phối vòng đời kết nối Socket trong môi trường React
 * @param {string} endpoint - Đường dẫn cổng chức năng (Ví dụ: "/api/ws/live-screen/agent_01")
 * @param {Object} options - Các cấu hình mở rộng (Tự động kết nối lại, khoảng thời gian chờ...)
 */
export function useWebSocket(endpoint, options = {}) {
  // 1. QUẢN LÝ TRẠNG THÁI GIAO DIỆN (UI STATES)
  const [isConnected, setIsConnected] = useState(false);
  const [latestMessage, setLatestMessage] = useState(null);
  const [error, setError] = useState(null);

  // 2. KỸ THUẬT SỬ DỤNG 'useRef' ĐỂ CHỐNG TRÙNG LẶP KẾT NỐI (ZOMBIE CONNECTIONS)
  // useRef giúp lưu trữ thực thể Service duy nhất trên RAM xuyên suốt các lần Component bị render lại.
  const socketServiceRef = useRef(null);

  // Gói các cấu hình tùy chọn vào Ref để tránh kích hoạt lại useEffect khi Object options bị thay đổi địa chỉ vùng nhớ
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // =========================================================================
  // 🔄 VÒNG ĐỜI KẾT NỐI CHÍNH (LIFECYCLE CONTROLLER)
  // =========================================================================
  useEffect(() => {
    // Nếu không có endpoint truyền vào, lập tức hủy tiến trình
    if (!endpoint) return;

    console.log(`🔌 [Hook] Khởi tạo vòng đời kết nối mới cho Endpoint: ${endpoint}`);
    
    // Đúc một đối tượng dịch vụ mạng từ lớp CentralWebSocketService đã viết ở tầng Service
    const wsService = new CentralWebSocketService(endpoint, optionsRef.current);
    socketServiceRef.current = wsService;

    // A. Đăng ký lắng nghe sự kiện KHAI THÔNG đường ống
    wsService.subscribe('open', () => {
      setIsConnected(true);
      setError(null);
      if (optionsRef.current.onOpen) optionsRef.current.onOpen();
    });

    // B. Đăng ký lắng nghe sự kiện NHẬN DỮ LIỆU THỜI GIAN THỰC (Ví dụ: Luồng ảnh Base64 từ Webcam)
    wsService.subscribe('message', (rawData) => {
      try {
        // Thử giải mã dữ liệu chuỗi thô từ mạng thành Object JSON nếu có thể
        const parsedData = JSON.parse(rawData);
        setLatestMessage(parsedData);
        if (optionsRef.current.onMessage) optionsRef.current.onMessage(parsedData);
      } catch (e) {
        // Nếu Backend chỉ ném về chuỗi String thô (không phải JSON), ta giữ nguyên dạng String
        setLatestMessage(rawData);
        if (optionsRef.current.onMessage) optionsRef.current.onMessage(rawData);
      }
    });

    // C. Đăng ký lắng nghe sự kiện XẢY RA XUNG ĐỘT ĐƯỜNG TRUYỀN
    wsService.subscribe('error', (errEvent) => {
      setError(errEvent);
      if (optionsRef.current.onError) optionsRef.current.onError(errEvent);
    });

    // D. Đăng ký lắng nghe sự kiện ĐÓNG ĐƯỜNG ỐNG
    wsService.subscribe('close', () => {
      setIsConnected(false);
      if (optionsRef.current.onClose) optionsRef.current.onClose();
    });

    // Kích hoạt lệnh phóng gói tin kết nối ra Card mạng vật lý
    wsService.connect();

    // =========================================================================
    // 🧹 HÀM DỌN DẸP BỘ NHỚ (CLEANUP FUNCTION) - VŨ KHÍ TỐI THƯỢNG CỦA HOOK
    // =========================================================================
    // Khi Admin chuyển đổi sang Tab chức năng khác hoặc rời khỏi trang MachinePage,
    // Component sẽ bị "Unmount" (Xóa khỏi RAM trình duyệt). Hàm return này sẽ tự động 
    // kích hoạt để bóp chết kết nối Socket đang chạy ngầm, tránh rò rỉ RAM và nghẽn CPU.
    return () => {
      console.log(`🧹 [Hook] Thu hồi tài nguyên và đóng ống dẫn: ${endpoint}`);
      if (socketServiceRef.current) {
        socketServiceRef.current.disconnect();
        socketServiceRef.current = null;
      }
      // Khôi phục các trạng thái về mặc định để chuẩn bị cho lần mở sau
      setIsConnected(false);
      setLatestMessage(null);
    };
  }, [endpoint]); // Hàm useEffect này chỉ chạy lại DUY NHẤT khi biến số endpoint thay đổi

  // =========================================================================
  // 📯 HÀM PHÁT LỆNH NGƯỢC LÊN SERVER (SEND COMMAND)
  // =========================================================================
  // Sử dụng useCallback để đóng băng hàm send, giúp Component con không bị render thừa thãi
  const sendMessage = useCallback((payload) => {
    if (socketServiceRef.current) {
      socketServiceRef.current.send(payload);
    } else {
      console.error("❌ Thất bại: Đường ống Socket chưa được thiết lập để truyền lệnh.");
    }
  }, []);

  // Xuất bản các "tay nắm điều khiển" ra bên ngoài cho các file Module sử dụng
  return {
    isConnected,     // Đúng/Sai: Báo cho UI biết để vẽ đèn LED tín hiệu Xanh/Đỏ
    latestMessage,   // Dữ liệu mới nhất gửi về (Màn hình máy mục tiêu, logs keylogger...)
    error,           // Chi tiết mã lỗi nếu đường truyền gặp sự cố
    sendMessage      // Hàm giúp UI bấm nút một cái là bắn lệnh điều khiển xuống Agent ngay tức thì
  };
}