// TODO: WebSocket connection đến Gateway
// Dùng cho: Live Screen, Key Logger, Webcam (real-time streams)

class WebSocketService {
  constructor() {
    this.socket = null
  }

  connect(url) {
    // TODO: Kết nối WebSocket
  }

  disconnect() {
    // TODO: Ngắt kết nối
  }

  send(message) {
    // TODO: Gửi lệnh
  }

  onMessage(callback) {
    // TODO: Nhận dữ liệu real-time
  }
}

export default new WebSocketService()
