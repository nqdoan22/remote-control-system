// web-app/frontend/src/services/websocket.js

/**
 * 🏭 Lớp quản lý WebSocket nâng cao tích hợp cơ chế tự phục hồi mạng
 */
export class CentralWebSocketService {
  constructor(endpoint, options = {}) {
    // Cấu hình URL cơ sở bằng cách chuyển đổi giao thức http:// sang ws://
    const baseHttpUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const baseWsUrl = baseHttpUrl.replace(/^http/, 'ws');
    
    this.url = `${baseWsUrl}${endpoint}`; // Ghép nối endpoint để tạo URL WS hoàn chỉnh
    this.options = {
      autoReconnect: true,     // Tự động kết nối lại khi rớt mạng vật lý
      reconnectInterval: 3000, // Khoảng thời gian chờ (ms) trước khi thử lại lần tiếp theo
      maxReconnectAttempts: 5, // Giới hạn số lần thử lại tối đa trước khi buông xuôi báo lỗi
      ...options
    };

    this.ws = null;
    this.reconnectAttempts = 0;
    this.listeners = {}; // Lưu trữ tập trung các hàm callback xử lý sự kiện
  }

  /**
   * 🔌 Hàm thiết lập đường ống TCP Socket vật lý
   */
  connect() {
    // Nếu đường ống đang mở sẵn, không cần tạo thêm để tránh lãng phí tài nguyên mạng
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      console.log(`🔌 Đang thiết lập đường ống dẫn dữ liệu thời gian thực tới: ${this.url}`);
      this.ws = new WebSocket(this.url);

      // Đồng bộ hóa các cổng sự kiện gốc của trình duyệt vào hệ thống xử lý nội bộ
      this.ws.onopen = (event) => this._handleOpen(event);
      this.ws.onmessage = (event) => this._handleMessage(event);
      this.ws.onerror = (event) => this._handleError(event);
      this.ws.onclose = (event) => this._handleClose(event);

    } catch (error) {
      console.error("🚨 Lỗi nghiêm trọng khi khởi tạo Socket cấu trúc:", error);
    }
  }

  /**
   * 📡 Hàm đăng ký lắng nghe sự kiện từ giao diện UI (Event Subscription)
   */
  subscribe(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);
  }

  /**
   * 📯 Hàm gửi dữ liệu từ Frontend ngược lên Backend thông qua ống dẫn đang mở
   */
  send(payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Ép kiểu toàn bộ dữ liệu Object phức tạp về chuỗi JSON thô trước khi ném vào mạng
      this.ws.send(JSON.stringify(payload));
    } else {
      console.error("❌ Thất bại: Không thể truyền gói tin do đường ống WebSocket đang đóng!");
    }
  }

  /**
   * 🛑 Hàm chủ động bóp nghẹt và đóng kết nối (Hủy giải phóng RAM)
   */
  disconnect() {
    if (this.ws) {
      console.log("🛑 Chủ động đóng kết nối WebSocket theo yêu cầu hệ thống.");
      this.options.autoReconnect = false; // Tắt tự động kết nối lại vì đây là hành động chủ động của Admin
      this.ws.close();
      this.ws = null;
    }
  }

  // =========================================================================
  // 🔒 CÁC HÀM XỬ LÝ NỘI BỘ (PRIVATE PHƯƠNG THỨC - ĐÁNH DẤU BẰNG TIỀN TỐ '_')
  // =========================================================================
  
  _handleOpen(event) {
    console.log("🟢 Đường ống WebSocket đã thông suốt. Kết nối TCP thiết lập thành công.");
    this.reconnectAttempts = 0; // Reset số lần đếm thử lại về 0
    this._dispatchEvent('open', event);
  }

  _handleMessage(event) {
    // Chuyển tiếp luồng dữ liệu thô nhận được từ card mạng về cho các hàm UI xử lý tiếp
    this._dispatchEvent('message', event.data);
  }

  _handleError(event) {
    console.error("💥 Xảy ra lỗi xung đột xung thần số mạng trên đường truyền WebSocket.");
    this._dispatchEvent('error', event);
  }

  _handleClose(event) {
    console.warn("⚠️ Hệ thống mạng báo động: Đường ống WebSocket đã bị khép lại.");
    this._dispatchEvent('close', event);

    // Kích hoạt thuật toán tự phục hồi mạng nếu quyền tự động kết nối lại được bật
    if (this.options.autoReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Thử kết nối lại lần thứ [${this.reconnectAttempts}/${this.options.maxReconnectAttempts}] sau ${this.options.reconnectInterval}ms...`);
      setTimeout(() => this.connect(), this.options.reconnectInterval);
    }
  }

  /**
   * 🔀 Bộ phân phối sự kiện (Event Dispatcher)
   */
  _dispatchEvent(eventType, data) {
    if (this.listeners[eventType]) {
      this.listeners[eventType].forEach(callback => {
        try {
          callback(data);
        } catch (err) {
          console.error(`Lỗi thực thi hàm callback trong sự kiện ${eventType}:`, err);
        }
      });
    }
  }
}