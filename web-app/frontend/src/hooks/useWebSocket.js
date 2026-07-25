// frontend/src/hooks/useWebSocket.js
import { useEffect, useState, useCallback } from 'react';
import { wsService } from '../services/websocket';

export const useWebSocket = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);

    useEffect(() => {
        // Lấy token JWT từ Local Storage đã lưu sau khi đăng nhập
        const token = localStorage.getItem('admin_token');
        
        if (!token) {
            console.warn("Không tìm thấy Admin Token, bỏ qua kết nối WebSocket.");
            return;
        }

        // 1. Mở kết nối
        wsService.connect(
            token,
            () => setIsConnected(true),
            () => setIsConnected(false)
        );

        // 2. Đăng ký lắng nghe luồng dữ liệu (Stream/Events)
        const unsubscribe = wsService.subscribe((msg) => {
            setLastMessage(msg);
        });

        // 3. Dọn dẹp khi Component bị hủy (Unmount)
        return () => {
            unsubscribe();
            // Tùy thuộc vào thiết kế, bạn có thể gọi wsService.disconnect() 
            // nếu chỉ muốn kết nối WS khi ở trong Dashboard.
        };
    }, []);

    // Bọc hàm sendCommand bằng useCallback để tránh render lại Component không cần thiết
    const sendCommand = useCallback((type, destination, payload = {}) => {
        return wsService.sendCommand(type, destination, payload);
    }, []);

    return { 
        isConnected, 
        sendCommand, 
        lastMessage 
    };
};