import { useState, useEffect, useRef, useCallback } from 'react';
import { createWSMessage } from '../services/api';

/**
 * Custom Hook quản lý kết nối WebSocket thời gian thực
 * @param {string} targetMachineId - ID của máy Client muốn điều khiển (nếu có)
 * @returns {Object} { isConnected, lastMessage, sendMessage, error }
 */
export const useWebSocket = (targetMachineId = null) => {
  // Trạng thái kết nối (true: Đã kết nối thành công, false: Đã mất kết nối)
  const [isConnected, setIsConnected] = useState(false);

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
  // Sử dụng useCallback để đóng băng hàm này, tránh việc tạo lại hàm mỗi lần Component re-render
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
  // =========================================================================
  useEffect(() => {
    // Lấy Token từ localStorage để gửi xác thực qua WebSocket Connection
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      setError('Không tìm thấy Token xác thực!');
      return;
    }

    // Địa chỉ WebSocket Server (Sử dụng ws:// hoặc wss://)
    const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';
    
    // Tạo Query URL truyền kèm Token và targetMachineId (nếu có)
    let wsUrl = `${WS_BASE_URL}?token=${token}`;
    if (targetMachineId) {
      wsUrl += `&machine_id=${targetMachineId}`;
    }

    console.log(`🔌 Đang kết nối tới WebSocket Gateway: ${wsUrl}`);
    
    // Khởi tạo đối tượng WebSocket
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    // --- SỰ KIỆN 1: KHI KẾT NỐI THÀNH CÔNG ---
    ws.onopen = () => {
      console.log('✅ Đã kết nối WebSocket thành công!');
      setIsConnected(true);
      setError(null);
    };

    // --- SỰ KIỆN 2: KHI NHẬN ĐƯỢC TIN NHẮN TỪ SERVER ---
    ws.onmessage = (event) => {
      try {
        // Giải mã chuỗi JSON từ Server gửi về thành Object
        const parsedData = JSON.parse(event.data);
        // Cập nhật tin nhắn vừa nhận vào State
        setLastMessage(parsedData);
      } catch (err) {
        console.error('❌ Không thể parse dữ liệu JSON từ WebSocket:', err);
      }
    };

    // --- SỰ KIỆN 3: KHI BỊ LỖI KẾT NỐI ---
    ws.onerror = (evt) => {
      console.error('❌ Lỗi kết nối WebSocket:', evt);
      setError('Lỗi kết nối thời gian thực WebSocket!');
    };

    // --- SỰ KIỆN 4: KHI KẾT NỐI BỊ ĐÓNG ---
    ws.onclose = (evt) => {
      console.log(`🔒 WebSocket đã ngắt kết nối. Code: ${evt.code}`);
      setIsConnected(false);
    };

    // --- CLEANUP FUNCTION (HÀM DỌN DẸP) ---
    // Được kích hoạt khi Component unmount (Admin chuyển đổi trang khác)
    return () => {
      if (ws) {
        console.log('🧹 Đang dọn dẹp và đóng kết nối WebSocket...');
        ws.close(); // Ngắt kết nối để giải phóng tài nguyên Server
      }
    };
  }, [targetMachineId]); // Chạy lại Effect nếu targetMachineId thay đổi

  // Trả về các trạng thái & hàm cần thiết cho Component sử dụng
  return {
    isConnected,   // Boolean: true/false
    lastMessage,   // Object: Dữ liệu nhận từ WebSocket
    sendMessage,   // Function: Hàm bắn tin nhắn đi
    error,         // String / null: Thông báo lỗi
  };
};

export default useWebSocket;