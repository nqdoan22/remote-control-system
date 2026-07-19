// web-app/frontend/src/services/websocket.js

export class CentralWebSocketService {
  constructor(endpoint, options = {}) {
    const baseHttpUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const baseWsUrl = baseHttpUrl.replace(/^http/, 'ws');
    
    this.url = `${baseWsUrl}${endpoint}`; 
    this.options = {
      autoReconnect: true,     
      reconnectInterval: 3000, 
      maxReconnectAttempts: 5, 
      ...options
    };

    this.ws = null;
    this.reconnectAttempts = 0;
    this.listeners = {}; // Lưu trữ tập trung các callback xử lý sự kiện
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      console.log(`🔌 Kết nối đường ống dữ liệu thời gian thực: ${this.url}`);
      this.ws = new WebSocket(this.url);

      this.ws.onopen = (event) => this._handleOpen(event);
      this.ws.onmessage = (event) => this._handleMessage(event);
      this.ws.onerror = (event) => this._handleError(event);
      this.ws.onclose = (event) => this._handleClose(event);

    } catch (error) {
      console.error("🚨 Lỗi khởi tạo kết nối WebSocket:", error);
    }
  }

  subscribe(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);
  }

  /**
   * Đã sửa đổi: Gửi dữ liệu từ UI tuân thủ cấu trúc gói tin chuẩn hóa của đồ án
   */
  send(msgType, payload = {}, destination = "gateway") {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const packet = {
        messageId: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2),
        type: msgType, // ví dụ: "screen.live.start"
        timestamp: Math.floor(Date.now() / 1000),
        source: "frontend",
        destination: destination,
        payload: payload
      };
      this.ws.send(JSON.stringify(packet));
    } else {
      console.error("❌ Thất bại: Đường ống WebSocket đang đóng!");
    }
  }

  disconnect() {
    if (this.ws) {
      this.options.autoReconnect = false; 
      this.ws.close();
      this.ws = null;
    }
  }

  _handleOpen(event) {
    console.log("🟢 WebSocket thông suốt.");
    this.reconnectAttempts = 0;
    this._dispatchEvent('open', event);
  }

  /**
   * Đã sửa đổi: Bộ giải mã thông minh bóc tách luồng stream (Hình ảnh màn hình/Webcam)
   */
  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      // Nếu gói tin có trường type rõ ràng (VD: screen.live.frame hoặc machine.status_change)
      // Ta kích hoạt phân phối trực tiếp cho module đó xử lý vẽ UI nhanh hơn
      if (data.type) {
        this._dispatchEvent(data.type, data.payload);
      }
      
      // Giữ nguyên cơ chế đẩy toàn bộ dữ liệu thô về để tương thích các logic cũ
      this._dispatchEvent('message', data);
    } catch (err) {
      // Trường hợp nhận dữ liệu nhị phân thô không phải dạng JSON chuỗi
      this._dispatchEvent('message', event.data);
    }
  }

  _handleError(event) {
    this._dispatchEvent('error', event);
  }

  _handleClose(event) {
    this._dispatchEvent('close', event);

    if (this.options.autoReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), this.options.reconnectInterval);
    }
  }

  _dispatchEvent(eventType, data) {
    if (this.listeners[eventType]) {
      this.listeners[eventType].forEach(callback => {
        try {
          callback(data);
        } catch (err) {
          console.error(`Lỗi hàm callback sự kiện ${eventType}:`, err);
        }
      });
    }
  }
}