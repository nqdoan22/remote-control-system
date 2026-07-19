// web-app/frontend/src/hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';
import { CentralWebSocketService } from '../services/websocket';

/**
 * 🪝 useWebSocket: Điều phối kết nối Socket.
 * ĐÃ ĐỒNG BỘ: Chuyển đổi định tuyến theo cấu trúc "module.action" chuẩn giao thức[cite: 18].
 */
export function useWebSocket(endpoint, options = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [latestMessage, setLatestMessage] = useState(null);
  const [error, setError] = useState(null);

  const socketServiceRef = useRef(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  useEffect(() => {
    if (!endpoint) return;

    // Giao tiếp thời gian thực bằng WebSocket được sử dụng cho Heartbeat, Live Screen, Webcam Streaming[cite: 14, 16].
    const wsService = new CentralWebSocketService(endpoint, optionsRef.current);
    socketServiceRef.current = wsService;

    wsService.subscribe('open', (event) => {
      setIsConnected(true);
      setError(null);
      if (optionsRef.current.onOpen) optionsRef.current.onOpen(event);
    });

    // Mọi kết quả/thông điệp từ hệ thống sẽ nhận qua đây (Event/Response)[cite: 18].
    wsService.subscribe('message', (rawData) => {
      setLatestMessage(rawData);
      if (optionsRef.current.onMessage) optionsRef.current.onMessage(rawData);
    });

    wsService.subscribe('error', (errEvent) => {
      setError(errEvent);
      if (optionsRef.current.onError) optionsRef.current.onError(errEvent);
    });

    wsService.subscribe('close', (event) => {
      setIsConnected(false);
      if (optionsRef.current.onClose) optionsRef.current.onClose(event);
    });

    wsService.connect();

    return () => {
      if (socketServiceRef.current) {
        socketServiceRef.current.disconnect();
        socketServiceRef.current = null;
      }
      setIsConnected(false);
      setLatestMessage(null);
    };
  }, [endpoint]);

  // Đăng ký nhận luồng Streaming (Streaming được dùng cho Live Screen và Webcam)[cite: 18].
  const subscribeToEvent = useCallback((eventType, callback) => {
    if (socketServiceRef.current) {
      socketServiceRef.current.subscribe(eventType, callback);
    }
  }, []);

  // Phát lệnh gửi đi: Bắt buộc cấu trúc phân cấp module.action (VD: "process.list")[cite: 18].
  const sendEvent = useCallback((msgType, payload = {}, destination = "gateway") => {
    if (socketServiceRef.current) {
      socketServiceRef.current.send(msgType, payload, destination);
    }
  }, []);

  return { isConnected, latestMessage, error, sendEvent, subscribeToEvent };
}