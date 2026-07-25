// frontend/src/components/modules/Webcam.jsx
import React, { useState, useEffect } from 'react';

const Webcam = ({ machineId, sendCommand, lastMessage }) => {
    const [isStreaming, setIsStreaming] = useState(false);
    const [frameSrc, setFrameSrc] = useState(null);
    const [status, setStatus] = useState('');

    useEffect(() => {
        if (isStreaming && lastMessage && lastMessage.type === 'webcam.frame') {
            if (lastMessage.payload?.imageBase64) {
                setFrameSrc(`data:image/jpeg;base64,${lastMessage.payload.imageBase64}`);
            }
        }
    }, [lastMessage, isStreaming]);

    const startWebcam = async () => {
        setStatus('Đang gửi yêu cầu bật Webcam và chờ người dùng chấp nhận...');
        try {
            const res = await sendCommand('webcam.start', machineId);
            if (res.success) {
                setIsStreaming(true);
                setStatus('🟢 Đang nhận tín hiệu Webcam');
            }
        } catch (err) {
            if (err.code === 'USER_REJECTED') {
                setStatus('❌ Người dùng đã từ chối cho phép bật Webcam.');
            } else if (err.code === 'CONSENT_TIMEOUT') {
                setStatus('⏳ Hết thời gian chờ người dùng xác nhận.');
            } else {
                setStatus(`❌ Lỗi: ${err.message}`);
            }
        }
    };

    const stopWebcam = async () => {
        try {
            await sendCommand('webcam.stop', machineId);
        } catch (err) {
            console.error('Lỗi dừng webcam:', err);
        } finally {
            setIsStreaming(false);
            setFrameSrc(null);
            setStatus('🔴 Đã tắt Webcam');
        }
    };

    useEffect(() => {
        return () => {
            if (isStreaming) {
                sendCommand('webcam.stop', machineId).catch(() => {});
            }
        };
    }, [isStreaming, machineId, sendCommand]);

    return (
        <div style={{ padding: '20px' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>Giám sát Webcam (Webcam Stream)</h3>
            <p style={{ fontSize: '13px', color: '#b45309', backgroundColor: '#fffbeb', padding: '10px', borderRadius: '4px', marginBottom: '15px' }}>
                ⚠️ <strong>Yêu cầu xác nhận:</strong> Cần sự đồng ý của người dùng cuối thông qua Popup hệ thống.
            </p>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                {!isStreaming ? (
                    <button onClick={startWebcam} style={{ padding: '8px 16px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        📷 Bật Webcam
                    </button>
                ) : (
                    <button onClick={stopWebcam} style={{ padding: '8px 16px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        ⏹ Tắt Webcam
                    </button>
                )}
            </div>

            {status && <div style={{ marginBottom: '15px', fontWeight: 'bold' }}>{status}</div>}

            <div style={{ backgroundColor: '#111827', borderRadius: '6px', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '350px' }}>
                {frameSrc ? (
                    <img src={frameSrc} alt="Webcam Feed" style={{ maxWidth: '100%', maxHeight: '500px' }} />
                ) : (
                    <p style={{ color: '#9ca3af' }}>{isStreaming ? 'Đang tải luồng camera...' : 'Webcam đang tắt'}</p>
                )}
            </div>
        </div>
    );
};

export default Webcam;