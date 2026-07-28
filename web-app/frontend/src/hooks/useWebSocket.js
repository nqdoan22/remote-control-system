import { useEffect, useState, useCallback } from 'react';
import { wsService } from '../services/websocket';

export const useWebSocket = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('admin_token');

        if (!token) {
            console.warn("Không tìm thấy Admin Token, bỏ qua kết nối WebSocket.");
            return;
        }

        wsService.connect(
            token,
            () => setIsConnected(true),
            () => setIsConnected(false)
        );

        const unsubscribe = wsService.subscribe((msg) => {
            setLastMessage(msg);
        });

        return () => {
            unsubscribe();
            wsService.disconnect();
        };
    }, []);

    const sendCommand = useCallback((type, destination, payload = {}) => {
        return wsService.sendCommand(type, destination, payload);
    }, []);

    return {
        isConnected,
        sendCommand,
        lastMessage
    };
};