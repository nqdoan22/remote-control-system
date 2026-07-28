// frontend/src/services/websocket.js

class WebSocketService {
    constructor() {
        this.ws = null;
        this.pendingRequests = new Map();
        this.streamListeners = new Set();
        this.url = import.meta.env.VITE_WS_URL || 'ws://localhost:8765';
    }

    connect(token, onConnect, onDisconnect) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

        // Xóa handler cũ để tránh race condition khi StrictMode unmount/remount
        const oldWs = this.ws;
        if (oldWs) {
            oldWs.onopen = null;
            oldWs.onclose = null;
            oldWs.onerror = null;
            if (oldWs.readyState === WebSocket.OPEN || oldWs.readyState === WebSocket.CONNECTING) {
                oldWs.close();
            }
        }

        this.ws = new WebSocket(this.url);
        const ws = this.ws;

        ws.onopen = () => {
            if (this.ws !== ws) return;
            console.log("Da ket noi toi Gateway WebSocket");
            this.send('system.auth', 'gateway', { token });
            if (onConnect) onConnect();
        };

        ws.onmessage = (event) => {
            if (this.ws !== ws) return;
            const data = JSON.parse(event.data);

            if (data.messageId && this.pendingRequests.has(data.messageId)) {
                const { resolve, reject } = this.pendingRequests.get(data.messageId);

                if (data.type === 'error') {
                    reject(data.payload);
                } else {
                    resolve(data.payload);
                }
                this.pendingRequests.delete(data.messageId);
            }

            this.streamListeners.forEach(callback => callback(data));
        };

        ws.onclose = () => {
            if (this.ws !== ws) return;
            console.warn("Da ngat ket noi khoi Gateway");
            if (onDisconnect) onDisconnect();
            this.ws = null;
        };

        ws.onerror = (err) => {
            if (this.ws !== ws) return;
            console.error("WebSocket Error:", err);
        };
    }

    send(type, destination, payload = {}) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error("WebSocket chua san sang.");
            return null;
        }

        const messageId = crypto.randomUUID();
        const message = {
            messageId,
            type,
            timestamp: Math.floor(Date.now() / 1000),
            source: 'webapp',
            destination,
            payload
        };

        this.ws.send(JSON.stringify(message));
        return messageId;
    }

    sendCommand(type, destination, payload = {}, timeoutMs = 20000) {
        return new Promise((resolve, reject) => {
            const messageId = this.send(type, destination, payload);
            if (!messageId) {
                return reject({ code: "WS_OFFLINE", message: "Mat ket noi Gateway" });
            }

            const timeout = setTimeout(() => {
                this.pendingRequests.delete(messageId);
                reject({ code: "GATEWAY_TIMEOUT", message: "Gateway hoac Client khong phan hoi" });
            }, timeoutMs);

            this.pendingRequests.set(messageId, {
                resolve: (res) => { clearTimeout(timeout); resolve(res); },
                reject: (err) => { clearTimeout(timeout); reject(err); }
            });
        });
    }

    subscribe(callback) {
        this.streamListeners.add(callback);
        return () => this.streamListeners.delete(callback);
    }

    disconnect() {
        if (this.ws) {
            this.ws.onopen = null;
            this.ws.onclose = null;
            this.ws.onerror = null;
            this.ws.close();
            this.ws = null;
        }
    }
}

export const wsService = new WebSocketService();