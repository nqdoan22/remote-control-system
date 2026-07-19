// web-app/frontend/src/hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';
import { CentralWebSocketService } from '../services/websocket';

/**
 * 🪝 useWebSocket: Custom Hook điều phối vòng đời kết nối Socket trong môi trường React.
 * ĐÃ ĐỒNG BỘ: Chuyển đổi toàn diện sang mô hình định tuyến gói tin theo cấu trúc "module.action"
 * @param {string} endpoint - Đường dẫn cổng chức năng (Ví dụ: "/webapp")
 * @param {Object} options - Các cấu hình mở rộng (onOpen, onError, onClose...)
 */
export function useWebSocket(endpoint, options = {}) {
  // 1. QUẢN LÝ TRẠNG THÁI GIAO DIỆN (UI STATES)
  const [isConnected, setIsConnected] = useState(false);
  const [latestMessage, setLatestMessage] = useState(null);
  const [error, setError] = useState(null);

  // 2. KỸ THUẬT SỬ DỤNG 'useRef' ĐỂ CHỐNG TRÙNG LẶP KẾT NỐI (ZOMBIE CONNECTIONS)
  // socketServiceRef lưu trữ thực thể Service mạng duy nhất, không bị tạo mới khi React render lại Component.
  const socketServiceRef = useRef(null);

  // Giữ cấu hình tùy chọn ổn định trong Ref để tránh re-run useEffect vô cớ khi Object literal bị đổi tham chiếu
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // =========================================================================
  // 🔄 VÒNG ĐỜI KẾT NỐI CHÍNH (LIFECYCLE CONTROLLER)
  // =========================================================================
  useEffect(() => {
    if (!endpoint) return;

    console.log(`🔌 [Hook] Khởi tạo đường ống mạng LAN mới tới endpoint: ${endpoint}`);
    
    // Đúc một đối tượng dịch vụ mạng từ lớp lớp CentralWebSocketService đã sửa đổi cấu trúc dữ liệu
    const wsService = new CentralWebSocketService(endpoint, optionsRef.current);
    socketServiceRef.current = wsService;

    // A. ĐĂNG KÝ LẮNG NGHE SỰ KIỆN KHAI THÔNG ĐƯỜNG TRUYỀN
    wsService.subscribe('open', (event) => {
      setIsConnected(true);
      setError(null);
      if (optionsRef.current.onOpen) optionsRef.current.onOpen(event);
    });

    // B. ĐĂNG KÝ LẮNG NGHE SỰ KIỆN NHẬN GÓI TIN CHUNG (Tương thích logic cũ)
    wsService.subscribe('message', (rawData) => {
      // Lưu trữ dữ liệu thô hoặc JSON đã phân tích vào state chính để các component cơ bản hiển thị
      setLatestMessage(rawData);
      if (optionsRef.current.onMessage) optionsRef.current.onMessage(rawData);
    });

    // C. ĐĂNG KÝ LẮNG NGHE SỰ KIỆN XẢY RA XUNG ĐỘT ĐƯỜNG TRUYỀN MẠNG
    wsService.subscribe('error', (errEvent) => {
      setError(errEvent);
      if (optionsRef.current.onError) optionsRef.current.onError(errEvent);
    });

    // D. ĐĂNG KÝ LẮNG NGHE SỰ KIỆN ĐÓNG ĐƯỜNG ỐNG DỮ LIỆU
    wsService.subscribe('close', (event) => {
      setIsConnected(false);
      if (optionsRef.current.onClose) optionsRef.current.onClose(event);
    });

    // Phát lệnh thực thi bắt tay (Handshake) kết nối vật lý ra card mạng
    wsService.connect();

    // =========================================================================
    // 🧹 HÀM DỌN DẸP BỘ NHỚ (CLEANUP FUNCTION) - CHỐNG NGHẼN SOCKET NGẦM
    // =========================================================================
    return () => {
      console.log(`🧹 [Hook] Rời trang hoặc hủy Component, tiến hành đóng ống dẫn để tiết kiệm băng thông LAN: ${endpoint}`);
      if (socketServiceRef.current) {
        socketServiceRef.current.disconnect();
        socketServiceRef.current = null;
      }
      // Đưa các trạng thái React về mặc định để an toàn cho đợt gắn kết nối kế tiếp
      setIsConnected(false);
      setLatestMessage(null);
    };
  }, [endpoint]); // Chỉ thực thi lại toàn bộ vòng đời khi endpoint đích danh thay đổi

  // =========================================================================
  // 📯 HÀM ĐĂNG KÝ SỰ KIỆN THEO ĐỊNH DANH CHUYÊN BIỆT (DÀNH CHO LIVE STREAM/WEBCAM)
  // =========================================================================
  // Hàm này giúp các Component (như LiveScreen) đăng ký trực tiếp nhận frame ảnh dựa vào type gói tin
  const subscribeToEvent = useCallback((eventType, callback) => {
    if (socketServiceRef.current) {
      socketServiceRef.current.subscribe(eventType, callback);
    } else {
      console.warn(`⚠️ Chưa thể đăng ký sự kiện [${eventType}] do Socket Service chưa sẵn sàng.`);
    }
  }, []);

  // =========================================================================
  // 🚀 HÀM PHÁT LỆNH ĐIỀU KHIỂN CHUẨN ĐẶC TẢ ĐỒ ÁN (SEND STRUCTURED COMMAND)
  // =========================================================================
  // Thay đổi signature của hàm: Nhận cấu trúc phân cấp thay vì nhận payload hỗn tạp như cũ
  const sendEvent = useCallback((msgType, payload = {}, destination = "gateway") => {
    if (socketServiceRef.current) {
      // Gọi hàm send cải tiến của CentralWebSocketService, tự động bọc chuỗi JSON chuẩn hóa
      socketServiceRef.current.send(msgType, payload, destination);
    } else {
      console.error("❌ Thất bại nghiêm trọng: Đường ống Socket chưa mở, không thể phát lệnh.");
    }
  }, []);

  // Xuất bản các "tay nắm giao tiếp mạng" ra bên ngoài để các file Giao diện (UI) sử dụng dễ dàng
  return {
    isConnected,        // State boolean: Báo tín hiệu mạng Xanh/Đỏ lên màn hình Dashboard
    latestMessage,      // Object JSON: Lưu gói tin chung mới nhất thu được
    error,              // Object Error: Chi tiết sự cố đường truyền mạng LAN nếu có
    sendEvent,          // Hàm mới: Bắn lệnh chuẩn cấu trúc đặc tả xuống thiết bị đích[cite: 5]
    subscribeToEvent    // Hàm mới: Giúp UI "mắc ống nghe" đón đầu luồng dữ liệu luân chuyển tốc độ cao[cite: 6]
  };
}