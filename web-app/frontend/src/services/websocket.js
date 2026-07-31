import { createWSMessage } from './api';

/**
 * Lớp WebSocketService (Áp dụng thiết kế Singleton Pattern)
 * Quản lý toàn bộ việc truyền nhận dữ liệu thời gian thực qua mạng (TCP/WebSocket).
 * Độc lập hoàn toàn với React (không dùng State hay Hook của React ở đây).
 */
class WebSocketService {
  constructor() {
    this.socket = null;            // Đổi tượng WebSocket gốc của trình duyệt
    this.url = null;               // Lưu URL đường dẫn WebSocket
    this.listeners = new Map();    // Lưu trữ các hàm callback đăng ký lắng nghe theo từng 'type' tin nhắn
    this.stateListeners = [];      // Danh sách callback lắng nghe sự thay đổi trạng thái kết nối
    this.isConnecting = false;     // Cờ đánh dấu đang trong quá trình thực hiện HTTP Handshake
    this.reconnectAttempts = 0;    // Số lần đã thử kết nối lại
    this.maxReconnectAttempts = 5; // Số lần thử kết nối lại tối đa khi rớt mạng
    this.reconnectInterval = 3000; // Khoảng thời gian chờ giữa các lần thử (3000ms = 3 giây)
  }

  // =========================================================================
  // 1. HÀM KẾT NỐI (Connect) - Mở đường ống kết nối TCP
  // =========================================================================
  connect(targetMachineId = null) {
    // Tránh việc mở nhiều kết nối chồng chéo nếu WebSocket đang hoạt động hoặc đang kết nối
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      console.warn('⚠️ [WS Service] Đường ống WebSocket đã hoặc đang được mở!');
      return;
    }

    // Lấy Token xác thực từ bộ nhớ trình duyệt
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.error('❌ [WS Service] Không tìm thấy Access Token trong localStorage!');
      this._notifyStateChange('ERROR', 'Thiếu Access Token');
      return;
    }

    // Xây dựng đường dẫn WebSocket
    const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';
    let wsUrl = `${WS_BASE_URL}?token=${token}`;
    if (targetMachineId) {
      wsUrl += `&machine_id=${targetMachineId}`;
    }

    this.url = wsUrl;
    this.isConnecting = true;
    this._notifyStateChange('CONNECTING');

    console.log(`🌐 [WS Service] Đang bắt tay kết nối (HTTP Handshake) tới: ${wsUrl}`);
    
    // Khởi tạo đối tượng WebSocket gốc của trình duyệt
    this.socket = new WebSocket(wsUrl);

    // --- SỰ KIỆN 1: Bắt tay thành công (Mở kết nối TCP) ---
    this.socket.onopen = () => {
      console.log('🟢 [WS Service] Kết nối WebSocket/TCP đã sẵn sàng!');
      this.isConnecting = false;
      this.reconnectAttempts = 0; // Reset lại số lần thử kết nối lại
      this._notifyStateChange('CONNECTED');
    };

    // --- SỰ KIỆN 2: Nhận dữ liệu từ Server ---
    this.socket.onmessage = (event) => {
      try {
        // Giải mã dữ liệu JSON nhận được từ đường truyền
        const parsedData = JSON.parse(event.data);
        // Phân phối tin nhắn tới các nơi đã đăng ký lắng nghe
        this._dispatchMessage(parsedData);
      } catch (err) {
        console.error('❌ [WS Service] Lỗi parse dữ liệu JSON từ gói tin nhận về:', err);
      }
    };

    // --- SỰ KIỆN 3: Gặp lỗi đường truyền Mạng ---
    this.socket.onerror = (error) => {
      console.error('🔴 [WS Service] Phát hiện lỗi đường truyền WebSocket:', error);
      this._notifyStateChange('ERROR', error);
    };

    // --- SỰ KIỆN 4: Đóng kết nối ---
    this.socket.onclose = (event) => {
      console.log(`🔒 [WS Service] Ngắt kết nối WebSocket (Mã lỗi: ${event.code})`);
      this.isConnecting = false;
      this._notifyStateChange('DISCONNECTED');

      // Nếu KHÔNG PHẢI chủ động ngắt (Mã 1000 = Normal Closure) -> Kích hoạt cơ chế Tự động kết nối lại
      if (event.code !== 1000) {
        this._tryReconnect(targetMachineId);
      }
    };
  }

  // =========================================================================
  // 2. HÀM GỬI TIN NHẮN (Send) - Đẩy dữ liệu qua đường truyền TCP
  // =========================================================================
  send(type, payload = {}, targetMachineId = null) {
    // Kiểm tra xem kết nối đã mở (Ready State = 1) chưa
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('❌ [WS Service] Gửi thất bại! Đường ống kết nối WebSocket chưa mở.');
      return false;
    }

    /* 
      Sử dụng hàm helper createWSMessage (trong api.js) để bọc gói tin 
      thành định dạng chuẩn WSMessage (Type, Timestamp, Payload...)
    */
    const formattedMsg = createWSMessage({
      type,
      destination: targetMachineId,
      payload,
    });

    // Chuyển Object thành chuỗi JSON và bắn đi qua WebSocket
    this.socket.send(JSON.stringify(formattedMsg));
    console.log(`📤 [WS Service] Đã gửi gói tin [${type}]:`, formattedMsg);
    return true;
  }

  // =========================================================================
  // 3. MÔ HÌNH PUB/SUB (Đăng ký / Hủy đăng ký nghe tin nhắn theo 'type')
  // =========================================================================
  
  /**
   * Đăng ký một hàm Callback để lắng nghe một loại tin nhắn cụ thể
   * @param {string} messageType - Loại tin nhắn (VD: 'process.list.response', 'terminal.output')
   * @param {function} callback - Hàm sẽ được gọi khi có tin nhắn loại này gửi về
   * @returns {function} Hàm hủy đăng ký (Unsubscribe)
   */
  on(messageType, callback) {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, new Set());
    }
    this.listeners.get(messageType).add(callback);

    // Trả về hàm hủy đăng ký tiện lợi
    return () => this.off(messageType, callback);
  }

  /**
   * Hủy đăng ký lắng nghe tin nhắn
   */
  off(messageType, callback) {
    if (this.listeners.has(messageType)) {
      this.listeners.get(messageType).delete(callback);
    }
  }

  /**
   * Đăng ký lắng nghe sự thay đổi TRẠNG THÁI KẾT NỐI (CONNECTING, CONNECTED, DISCONNECTED)
   */
  onStateChange(callback) {
    this.stateListeners.push(callback);
    return () => {
      this.stateListeners = this.stateListeners.filter((cb) => cb !== callback);
    };
  }

  // =========================================================================
  // 4. HÀM ĐÓNG KẾT NỐI CHỦ ĐỘNG (Disconnect)
  // =========================================================================
  disconnect() {
    if (this.socket) {
      console.log('🧹 [WS Service] Chủ động ngắt kết nối WebSocket...');
      // Truyền code 1000 để báo với onclose đây là hành động chủ động (không kích hoạt Auto-reconnect)
      this.socket.close(1000, 'User主动ngắt kết nối');
      this.socket = null;
    }
  }

  // =========================================================================
  // 🛠️ CÁC HÀM NỘI BỘ (PRIVATE HELPER METHODS)
  // =========================================================================

  /**
   * Phân phối tin nhắn nhận được đến đúng các nơi đăng ký qua hàm .on()
   */
  _dispatchMessage(data) {
    const { type } = data;

    // 1. Gửi cho các Callback đăng ký đúng tên `type` này
    if (type && this.listeners.has(type)) {
      this.listeners.get(type).forEach((callback) => callback(data));
    }

    // 2. Gửi cho các Callback đăng ký ký tự đại diện '*' (Lắng nghe TẤT CẢ gói tin)
    if (this.listeners.has('*')) {
      this.listeners.get('*').forEach((callback) => callback(data));
    }
  }

  /**
   * Báo cáo trạng thái kết nối tới tất cả Listener theo dõi State
   */
  _notifyStateChange(state, detail = null) {
    this.stateListeners.forEach((callback) => callback({ state, detail }));
  }

  /**
   * Cơ chế tự động kết nối lại khi bị đứt mạng đột ngột (Auto-reconnect)
   */
  _tryReconnect(targetMachineId) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 [WS Service] Thử kết nối lại lần ${this.reconnectAttempts}/${this.maxReconnectAttempts} sau ${this.reconnectInterval / 1000}s...`);

      setTimeout(() => {
        this.connect(targetMachineId);
      }, this.reconnectInterval);
    } else {
      console.error('❌ [WS Service] Đã vượt quá số lần kết nối lại tối đa. Dừng thử.');
    }
  }
}

// 🚀 EXPORT SINGLETON PATTERN: Khởi tạo 1 Instance duy nhất dùng chung cho toàn bộ ứng dụng
export const websocketService = new WebSocketService();
export default websocketService;