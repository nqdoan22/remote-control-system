// frontend/src/services/websocket.js

class WebSocketService {
    constructor() {
        this.ws = null;
        // Map lưu trữ các Promise (để map Response trả về đúng với Request đã gửi qua messageId)
        this.pendingRequests = new Map(); 
        // Set lưu trữ các callback cho dữ liệu Stream liên tục (Live Screen, Webcam, Keylogger)
        this.streamListeners = new Set();
        // Cổng mặc định của Gateway là 8765
        this.url = import.meta.env.VITE_WS_URL || 'ws://localhost:8765';
    }

    connect(token, onConnect, onDisconnect) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log("🔌 Đã kết nối tới Gateway WebSocket");
            // Gửi gói tin system.auth ngay khi kết nối theo đúng API Contract
            this.send('system.auth', 'gateway', { token });
            if (onConnect) onConnect();
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Xử lý nếu là Response cho một Request cụ thể (có messageId trùng khớp)
            if (data.messageId && this.pendingRequests.has(data.messageId)) {
                const { resolve, reject } = this.pendingRequests.get(data.messageId);
                
                if (data.type === 'error') {
                    reject(data.payload); // Bắn lỗi (VD: USER_REJECTED, CONSENT_TIMEOUT)
                } else {
                    resolve(data.payload); // Thành công
                }
                this.pendingRequests.delete(data.messageId);
            } 
            
            // Broadcast cho tất cả các Listener đang lắng nghe Stream (Event / Frame liên tục)
            this.streamListeners.forEach(callback => callback(data));
        };

        this.ws.onclose = () => {
            console.warn("🔴 Đã ngắt kết nối khỏi Gateway");
            if (onDisconnect) onDisconnect();
            this.ws = null;
            // Tùy chọn: Implement logic Auto-Reconnect ở đây nếu cần
        };

        this.ws.onerror = (err) => {
            console.error("❌ WebSocket Error:", err);
        };
    }

    send(type, destination, payload = {}) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error("WebSocket chưa sẵn sàng.");
            return null;
        }

        // Tạo UUID v4 chuẩn bằng Web API có sẵn của trình duyệt
        const messageId = crypto.randomUUID(); 
        const message = {
            messageId,
            type,
            timestamp: Math.floor(Date.now() / 1000),
            source: 'webapp',       // Định danh cứng của Web App
            destination,            // ID của Client App hoặc 'gateway'
            payload
        };

        this.ws.send(JSON.stringify(message));
        return messageId;
    }

    // Hàm bao bọc việc gửi lệnh thành dạng Promise (có Timeout mặc định 20 giây)
    // Timeout này lớn hơn 15s Timeout của Popup xin quyền một chút
    sendCommand(type, destination, payload = {}, timeoutMs = 20000) {
        return new Promise((resolve, reject) => {
            const messageId = this.send(type, destination, payload);
            if (!messageId) {
                return reject({ code: "WS_OFFLINE", message: "Mất kết nối Gateway" });
            }

            // Cài đặt bộ đếm giờ Timeout
            const timeout = setTimeout(() => {
                this.pendingRequests.delete(messageId);
                reject({ code: "GATEWAY_TIMEOUT", message: "Gateway hoặc Client không phản hồi" });
            }, timeoutMs);

            // Lưu trữ hàm resolve/reject để gọi lại khi onmessage nhận được data
            this.pendingRequests.set(messageId, {
                resolve: (res) => { clearTimeout(timeout); resolve(res); },
                reject: (err) => { clearTimeout(timeout); reject(err); }
            });
        });
    }

    // Đăng ký lắng nghe các gói tin không yêu cầu Response trực tiếp (Stream Frames, Keylogger Events)
    subscribe(callback) {
        this.streamListeners.add(callback);
        return () => this.streamListeners.delete(callback);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Khởi tạo một Singleton Instance dùng chung cho toàn app
export const wsService = new WebSocketService();