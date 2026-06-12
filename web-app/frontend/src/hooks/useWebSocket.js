import { useEffect, useRef, useCallback } from "react";

/**
 * Custom hook for WebSocket connection to Gateway.
 * @param {string} url - WebSocket URL
 * @param {function} onMessage - Callback when message received
 */
export function useWebSocket(url, onMessage) {
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(url);
    ws.current.onmessage = (event) => onMessage(JSON.parse(event.data));
    ws.current.onclose   = () => console.log("WebSocket closed");
    ws.current.onerror   = (e) => console.error("WebSocket error", e);
    return () => ws.current?.close();
  }, [url]);

  const send = useCallback((data) => {
    ws.current?.send(JSON.stringify(data));
  }, []);

  return { send };
}
