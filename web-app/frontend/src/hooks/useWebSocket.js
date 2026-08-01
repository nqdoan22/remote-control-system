import { useState, useEffect, useRef, useCallback } from 'react';
import { createWSMessage } from '../services/api';

// =========================================================================
// 🕐 HẰNG SỐ CẤU HÌNH KẾT NỐI & HEARTBEAT (Thêm mới để sửa lỗi mất kết nối)
// =========================================================================
// Chu kỳ gửi tín hiệu Ping (Keep-alive) xuống Backend để giữ đường ống WS luôn "nóng"
const HEARTBEAT_INTERVAL_MS = 20000;   // 20 giây
// Nếu quá 45 giây không nhận được BẤT KỲ tin nhắn nào (kể cả Pong) => coi kết nối đã chết
const STALE_TIMEOUT_MS = 45000;
// Thời gian chờ tối thiểu giữa 2 lần thử kết nối lại (Exponential Backoff: 0.5s -> 1s -> 2s -> ...)
const RECONNECT_BASE_DELAY_MS = 500;
// Giới hạn tối đa thời gian chờ reconnect (tránh spam Backend)
const RECONNECT_MAX_DELAY_MS = 30000;
// Mã đóng 4401 do Backend trả về khi JWT Token không hợp lệ/hết hạn -> KHÔNG tự reconnect
const WS_AUTH_CLOSE_CODE = 4401;

/**
 * Custom Hook quản lý kết nối WebSocket thời gian thực
 * (Đã nâng cấp: Auto-Reconnect + Heartbeat + Phát hiện kết nối chết)
 * @param {string} targetMachineId - ID của máy Client muốn điều khiển (nếu có)
 * @returns {Object} { isConnected, connecting, reconnecting, lastMessage, sendMessage, error }
 */
export const useWebSocket = (targetMachineId = null) => {
  // Trạng thái kết nối (true: Đã kết nối thành công, false: Đã mất kết nối)
  const [isConnected, setIsConnected] = useState(false);

  // 🔧 THÊM MỚI: Trạng thái đang "kết nối lần đầu" (dùng để hiển thị badge "ĐANG KẾT NỐI...")
  const [connecting, setConnecting] = useState(false);

  // 🔧 THÊM MỚI: Trạng thái đang "thử kết nối lại sau khi rớt" (dùng để hiển thị badge reconnect)
  const [reconnecting, setReconnecting] = useState(false);

  // Lưu trữ tin nhắn mới nhất vừa nhận được từ WebSocket Server
  const [lastMessage, setLastMessage] = useState(null);

  // Lưu thông báo lỗi nếu xảy ra sự cố kết nối
  const [error, setError] = useState(null);

  // Sử dụng useRef để lưu trữ đối tượng WebSocket instance gốc.
  // useRef giúp giữ nguyên giá trị qua các lần Re-render của React mà không làm kích hoạt Render lại.
  const socketRef = useRef(null);

  // =========================================================================
  // 1. HÀM GỬI TIN NHẮN (sendMessage)
  // =========================================================================
  const sendMessage = useCallback((type, payload = {}) => {
    // Kiểm tra xem Socket có tồn tại và đang ở trạng thái OPEN (1) hay không
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      /* 
        🚀 Chuẩn hóa gói tin chuẩn Envelope bằng hàm createWSMessage trong api.js:
        { messageId, type, timestamp, source: 'webapp', destination, payload }
      */
      const formattedMessage = createWSMessage({
        type,
        destination: targetMachineId,
        payload,
      });

      // Chuyển Object JavaScript thành chuỗi JSON string trước khi bắn qua Socket
      socketRef.current.send(JSON.stringify(formattedMessage));
    } else {
      console.warn('⚠️ WebSocket chưa sẵn sàng hoặc đã bị ngắt kết nối!');
    }
  }, [targetMachineId]);

  // =========================================================================
  // 2. VÒNG ĐỜI KẾT NỐI WEBSOCKET (EFFECT)
  //    🔧 ĐÃ VIẾT LẠI: Bổ sung Auto-Reconnect + Heartbeat + Stale Detection
  // =========================================================================
  useEffect(() => {
    // Cờ đánh dấu Component đã unmount -> dừng mọi thao tác/đóng socket tương ứng
    let disposed = false;

    // Các biến nội bộ giữ trạng thái của lần kết nối hiện tại (KHÔNG dùng State để tránh re-render)
    let socket = null;
    let reconnectTimer = null;   // Timer lên lịch thử kết nối lại
    let heartbeatTimer = null;   // Timer gửi Ping định kỳ
    let staleTimer = null;       // Timer phát hiện kết nối "chết im lặng"
    let reconnectAttempts = 0;   // Số lần reconnect liên tiếp (để tăng thời gian chờ Backoff)

    // ---------- HÀM TIỆN ÍCH NỘI BỘ ----------

    // Xóa toàn bộ Timer đang chạy (dọn dẹp trước khi tạo kết nối mới hoặc unmount)
    const clearTimers = () => {
      if (heartbeatTimer) clearInterval(heartbeatTimer);
      if (staleTimer) clearTimeout(staleTimer);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      heartbeatTimer = staleTimer = reconnectTimer = null;
    };

    // 🔧 THÊM MỚI: Cài lại Timer "hết hạn im lặng".
    // Mỗi khi nhận được 1 tin nhắn (kể cả Pong) => đếm ngược lại từ đầu.
    // Nếu hết thời gian mà không có tin nào => chủ động đóng socket để kích hoạt Reconnect.
    const armStaleTimer = () => {
      if (staleTimer) clearTimeout(staleTimer);
      staleTimer = setTimeout(() => {
        if (disposed) return;
        console.warn('⚠️ [useWebSocket] Không nhận được tin nhắn nào trong thời gian dài -> ép đóng kết nối để reconnect.');
        try {
          if (socket) socket.close();
        } catch (err) {
          /* bỏ qua lỗi khi đóng */
        }
      }, STALE_TIMEOUT_MS);
    };

    // 🔧 THÊM MỚI: Lên lịch thử kết nối lại với Exponential Backoff (0.5s -> 1s -> 2s -> ... tối đa 30s)
    const scheduleReconnect = () => {
      if (disposed) return;
      setReconnecting(true); // Báo cho giao diện biết đang ở trạng thái "đang thử kết nối lại"
      const delay = Math.min(
        RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempts,
        RECONNECT_MAX_DELAY_MS
      );
      reconnectAttempts += 1;
      clearTimers();
      reconnectTimer = setTimeout(() => {
        if (disposed) return;
        clearTimers();
        connect();
      }, delay);
    };

    // 🔧 THÊM MỚI: Khởi chạy Heartbeat (gửi Ping định kỳ) + cài Timer phát hiện kết nối chết.
    // Được gọi ngay sau khi WebSocket mở thành công.
    const startHeartbeat = () => {
      heartbeatTimer = setInterval(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          try {
            const ping = createWSMessage({ type: 'system.ping', destination: 'webapp', payload: {} });
            socket.send(JSON.stringify(ping));
          } catch (err) {
            console.error('❌ [useWebSocket] Lỗi gửi heartbeat:', err);
          }
        }
      }, HEARTBEAT_INTERVAL_MS);
      armStaleTimer();
    };

    // ---------- HÀM KẾT NỐI CHÍNH ----------

    // Tạo một WebSocket mới và gắn toàn bộ sự kiện (được gọi ở lần đầu & mỗi lần reconnect)
    const connect = () => {
      // Lấy Token từ localStorage để gửi xác thực qua WebSocket Connection
      const token = localStorage.getItem('access_token');

      if (!token) {
        setError('Không tìm thấy Token xác thực!');
        setIsConnected(false);
        return;
      }

      // Địa chỉ WebSocket Server (Sử dụng ws:// hoặc wss://)
      const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';

      // Tạo Query URL truyền kèm Token và targetMachineId (nếu có)
      let wsUrl = `${WS_BASE_URL}?token=${token}`;
      if (targetMachineId) {
        wsUrl += `&machine_id=${targetMachineId}`;
      }

      // Khởi tạo đối tượng WebSocket
      // 🔧 THÊM MỚI: Bọc try/catch để nếu URL sai hoặc trình duyệt chặn kết nối
      // (VD: kết nối tới cổng không cho phép) thì lên lịch reconnect thay vì crash.
      try {
        socket = new WebSocket(wsUrl);
      } catch (err) {
        console.error('❌ Không thể khởi tạo WebSocket:', err);
        scheduleReconnect();
        return;
      }
      socketRef.current = socket;

      // --- SỰ KIỆN 1: KHI KẾT NỐI THÀNH CÔNG ---
      socket.onopen = () => {
        if (disposed) return;
        reconnectAttempts = 0;   // Reset số lần reconnect (kết nối đã thành công)
        setIsConnected(true);
        setConnecting(false);
        setReconnecting(false);
        setError(null);
        clearTimers();
        startHeartbeat();       // Bắt đầu duy trì kết nối "nóng"
      };

      // --- SỰ KIỆN 2: KHI NHẬN ĐƯỢC TIN NHẮN TỪ SERVER ---
      socket.onmessage = (event) => {
        if (disposed) return;
        try {
          // Giải mã chuỗi JSON từ Server gửi về thành Object
          const parsedData = JSON.parse(event.data);
          // Cập nhật tin nhắn vừa nhận vào State
          setLastMessage(parsedData);
          // 🔧 THÊM MỚI: Có tin nhắn tới => kết nối còn sống => đếm ngược lại Timer hết hạn
          armStaleTimer();
        } catch (err) {
          console.error('❌ Không thể parse dữ liệu JSON từ WebSocket:', err);
        }
      };

      // --- SỰ KIỆN 3: KHI BỊ LỖI KẾT NỐI ---
      socket.onerror = (evt) => {
        console.error('❌ Lỗi kết nối WebSocket:', evt);
        setError('Lỗi kết nối thời gian thực WebSocket!');
      };

      // --- SỰ KIỆN 4: KHI KẾT NỐI BỊ ĐÓNG ---
      socket.onclose = (evt) => {
        if (disposed) return;
        clearTimers();
        setIsConnected(false);
        // Chỉ null hóa ref nếu socket đóng vẫn là socket hiện tại (tránh làm mất socket mới sau reconnect)
        if (socketRef.current === socket) socketRef.current = null;

        // 🔧 THÊM MỚI: Nếu Backend đóng kết nối với mã 4401 (Token không hợp lệ/hết hạn)
        // thì KHÔNG tự reconnect (sẽ lặp lại lỗi vô ích) -> báo lỗi để Admin đăng nhập lại.
        if (evt.code === WS_AUTH_CLOSE_CODE) {
          setError('Phiên đăng nhập hết hạn hoặc không hợp lệ! Vui lòng đăng nhập lại.');
          return;
        }

        console.log(`🔒 WebSocket đã ngắt kết nối. Code: ${evt.code}`);
        // 🔧 THÊM MỚI: Mọi trường hợp đóng kết nối khác => tự động thử kết nối lại
        scheduleReconnect();
      };
    };

    // Bắt đầu kết nối lần đầu
    setConnecting(true);
    connect();

    // --- CLEANUP FUNCTION (HÀM DỌN DẸP) ---
    // Được kích hoạt khi Component unmount (Admin chuyển đổi trang khác)
    // hoặc khi targetMachineId thay đổi.
    return () => {
      disposed = true;        // Đánh dấu không được thao tác State/Timer nữa
      clearTimers();          // Dọn toàn bộ Timer Heartbeat/Reconnect
      if (socket) {
        try {
          socket.close();     // Ngắt kết nối để giải phóng tài nguyên Server
        } catch (err) {
          /* bỏ qua lỗi khi đóng */
        }
        if (socketRef.current === socket) socketRef.current = null;
      }
    };
  }, [targetMachineId]); // Chạy lại Effect nếu targetMachineId thay đổi

  // Trả về các trạng thái & hàm cần thiết cho Component sử dụng
  return {
    isConnected,    // Boolean: true/false
    connecting,     // Boolean (THÊM MỚI): đang mở kết nối lần đầu
    reconnecting,   // Boolean (THÊM MỚI): đang thử kết nối lại sau khi rớt
    lastMessage,    // Object: Dữ liệu nhận từ WebSocket
    sendMessage,    // Function: Hàm bắn tin nhắn đi
    error,          // String / null: Thông báo lỗi
  };
};

export default useWebSocket;
