// frontend/src/components/modules/Keylogger.jsx
import React, { useState, useEffect } from 'react';

const Keylogger = ({ machineId, sendCommand, lastMessage }) => {
    const [isLogging, setIsLogging] = useState(false);
    const [logs, setLogs] = useState('');
    const [status, setStatus] = useState('');

    // Lắng nghe sự kiện bàn phím thời gian thực từ WebSocket
    useEffect(() => {
        if (isLogging && lastMessage && lastMessage.type === 'keylogger.event') {
            if (lastMessage.payload?.key) {
                setLogs(prev => prev + lastMessage.payload.key);
            }
        }
    }, [lastMessage, isLogging]);

    const startLogging = async () => {
        setStatus('Đang xin phép người dùng để bật ghi phím...');
        try {
            const res = await sendCommand('keylogger.start', machineId);
            if (res.success) {
                setIsLogging(true);
                setStatus('🟢 Đang ghi phím thời gian thực');
            }
        } catch (err) {
            if (err.code === 'USER_REJECTED') {
                setStatus('❌ Người dùng đã từ chối cấp quyền Ghi phím.');
            } else if (err.code === 'CONSENT_TIMEOUT') {
                setStatus('⏳ Hết thời gian chờ người dùng xác nhận.');
            } else {
                setStatus(`❌ Lỗi: ${err.message}`);
            }
        }
    };

    const stopLogging = async () => {
        try {
            await sendCommand('keylogger.stop', machineId);
        } catch (err) {
            console.error('Lỗi khi dừng keylogger:', err);
        } finally {
            setIsLogging(false);
            setStatus('🔴 Đã dừng ghi phím');
        }
    };

    const clearLogs = () => setLogs('');

    useEffect(() => {
        return () => {
            if (isLogging) {
                sendCommand('keylogger.stop', machineId).catch(() => {});
            }
        };
    }, [isLogging, machineId, sendCommand]);

    return (
        <div style={{ padding: '20px' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>Ghi Bàn Phím (Keylogger)</h3>
            <p style={{ fontSize: '13px', color: '#b45309', backgroundColor: '#fffbeb', padding: '10px', borderRadius: '4px', marginBottom: '15px' }}>
                ⚠️ <strong>Yêu cầu xác nhận:</strong> Tính năng theo dõi thao tác phím cần người dùng bấm chấp nhận trên Popup.
            </p>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                {!isLogging ? (
                    <button onClick={startLogging} style={{ padding: '8px 16px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        ⌨️ Bắt đầu Ghi phím
                    </button>
                ) : (
                    <button onClick={stopLogging} style={{ padding: '8px 16px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        ⏹ Dừng Ghi phím
                    </button>
                )}
                <button onClick={clearLogs} style={{ padding: '8px 16px', backgroundColor: '#6b7280', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                    🗑️ Xóa màn hình
                </button>
            </div>

            {status && <div style={{ marginBottom: '15px', fontWeight: 'bold' }}>{status}</div>}

            <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '14px' }}>Nhật ký phím gõ (Key Logs):</label>
                <textarea 
                    value={logs} 
                    readOnly 
                    placeholder="Dữ liệu bàn phím sẽ hiển thị ở đây khi có thao tác trên máy khách..."
                    style={{ 
                        width: '100%', 
                        height: '300px', 
                        backgroundColor: '#1e293b', 
                        color: '#38bdf8', 
                        fontFamily: 'monospace', 
                        padding: '12px', 
                        borderRadius: '6px',
                        boxSizing: 'border-box',
                        resize: 'vertical'
                    }}
                />
            </div>
        </div>
    );
};

export default Keylogger;