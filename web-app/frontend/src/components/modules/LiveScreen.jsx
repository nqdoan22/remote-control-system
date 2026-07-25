// frontend/src/components/modules/LiveScreen.jsx
import React, { useState, useEffect } from 'react';

const LiveScreen = ({ machineId, sendCommand, lastMessage }) => {
    const [isStreaming, setIsStreaming] = useState(false);
    const [frameSrc, setFrameSrc] = useState(null);
    const [status, setStatus] = useState('');
    const [fps, setFps] = useState(0);

    // Xử lý luồng hình ảnh thời gian thực gửi về qua WebSocket
    useEffect(() => {
        if (isStreaming && lastMessage && lastMessage.type === 'livescreen.frame') {
            if (lastMessage.payload?.imageBase64) {
                setFrameSrc(`data:image/jpeg;base64,${lastMessage.payload.imageBase64}`);
                if (lastMessage.payload.fps) {
                    setFps(lastMessage.payload.fps);
                }
            }
        }
    }, [lastMessage, isStreaming]);

    const startStream = async () => {
        setStatus('Đang gửi yêu cầu Live Screen và chờ người dùng đồng ý (Timeout 15s)...');
        try {
            const res = await sendCommand('livescreen.start', machineId, { fps: 10 });
            if (res.success) {
                setIsStreaming(true);
                setStatus('🟢 Đang phát trực tiếp màn hình');
            }
        } catch (err) {
            if (err.code === 'USER_REJECTED') {
                setStatus('❌ Người dùng đã từ chối cấp quyền màn hình.');
            } else if (err.code === 'CONSENT_TIMEOUT') {
                setStatus('⏳ Hết thời gian chờ người dùng xác nhận.');
            } else {
                setStatus(`❌ Lỗi: ${err.message}`);
            }
        }
    };

    const stopStream = async () => {
        try {
            await sendCommand('livescreen.stop', machineId);
        } catch (err) {
            console.error('Lỗi khi dừng stream:', err);
        } finally {
            setIsStreaming(false);
            setFrameSrc(null);
            setStatus('🔴 Đã dừng phát màn hình');
        }
    };

    // Tự ngắt stream khi Admin rời trang
    useEffect(() => {
        return () => {
            if (isStreaming) {
                sendCommand('livescreen.stop', machineId).catch(() => {});
            }
        };
    }, [isStreaming, machineId, sendCommand]);

    return (
        <div style={{ padding: '20px' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>Màn hình trực tiếp (Live Screen)</h3>
            <p style={{ fontSize: '13px', color: '#b45309', backgroundColor: '#fffbeb', padding: '10px', borderRadius: '4px', marginBottom: '15px' }}>
                ⚠️ <strong>Yêu cầu xác nhận:</strong> Chức năng này sẽ hiển thị thông báo xin phép trên màn hình máy khách.
            </p>

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '15px' }}>
                {!isStreaming ? (
                    <button onClick={startStream} style={{ padding: '8px 16px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        ▶ Bắt đầu xem Live
                    </button>
                ) : (
                    <button onClick={stopStream} style={{ padding: '8px 16px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        ⏹ Dừng xem Live
                    </button>
                )}
                {isStreaming && <span style={{ fontSize: '13px', color: '#6b7280' }}>Tốc độ: {fps} FPS</span>}
            </div>

            {status && <div style={{ marginBottom: '15px', fontWeight: 'bold' }}>{status}</div>}

            <div style={{ backgroundColor: '#000', borderRadius: '6px', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
                {frameSrc ? (
                    <img src={frameSrc} alt="Live Stream" style={{ maxWidth: '100%', maxHeight: '600px', objectFit: 'contain' }} />
                ) : (
                    <p style={{ color: '#9ca3af' }}>{isStreaming ? 'Đang chờ khung hình đầu tiên...' : 'Chưa bật phát trực tiếp'}</p>
                )}
            </div>
        </div>
    );
};

export default LiveScreen;