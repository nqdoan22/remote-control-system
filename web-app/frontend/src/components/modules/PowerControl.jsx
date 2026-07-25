// frontend/src/components/modules/PowerControl.jsx
import React, { useState } from 'react';

const PowerControl = ({ machineId, sendCommand }) => {
    const [status, setStatus] = useState('');
    const [isRequesting, setIsRequesting] = useState(false);

    const handlePowerAction = async (actionStr) => {
        setIsRequesting(true);
        setStatus(`Đang gửi yêu cầu [${actionStr}] và chờ người dùng xác nhận (Timeout 15s)...`);
        
        try {
            // Lệnh power.lock, power.restart, power.shutdown, power.sleep
            const res = await sendCommand(`power.${actionStr}`, machineId);
            if (res.success) {
                setStatus(`✅ Thành công! Đã thực thi lệnh ${actionStr}.`);
            }
        } catch (err) {
            if (err.code === 'USER_REJECTED') {
                setStatus('❌ Thất bại: Người dùng đã từ chối yêu cầu.');
            } else if (err.code === 'CONSENT_TIMEOUT') {
                setStatus('⏳ Thất bại: Quá 15 giây không có phản hồi từ người dùng (Timeout).');
            } else {
                setStatus(`❌ Lỗi: ${err.message}`);
            }
        } finally {
            setIsRequesting(false);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <h3 style={{ margin: '0 0 20px 0' }}>Điều khiển Nguồn (Power Management)</h3>
            
            <div style={{ padding: '15px', backgroundColor: '#fffbeb', color: '#b45309', borderLeft: '4px solid #f59e0b', marginBottom: '20px' }}>
                <strong>Lưu ý Bảo mật:</strong> Mọi thao tác tại đây đều yêu cầu người dùng cuối (End User) bấm xác nhận trên Popup.
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', maxWidth: '400px' }}>
                <button onClick={() => handlePowerAction('lock')} disabled={isRequesting} style={{ padding: '15px', cursor: 'pointer', backgroundColor: '#e5e7eb', border: 'none', borderRadius: '4px' }}>🔒 Khóa màn hình (Lock)</button>
                <button onClick={() => handlePowerAction('sleep')} disabled={isRequesting} style={{ padding: '15px', cursor: 'pointer', backgroundColor: '#e5e7eb', border: 'none', borderRadius: '4px' }}>🌙 Chế độ ngủ (Sleep)</button>
                <button onClick={() => handlePowerAction('restart')} disabled={isRequesting} style={{ padding: '15px', cursor: 'pointer', backgroundColor: '#fca5a5', border: 'none', borderRadius: '4px' }}>🔄 Khởi động lại (Restart)</button>
                <button onClick={() => handlePowerAction('shutdown')} disabled={isRequesting} style={{ padding: '15px', cursor: 'pointer', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px' }}>⛔ Tắt máy (Shutdown)</button>
            </div>

            {status && (
                <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f3f4f6', borderRadius: '4px', fontWeight: 'bold' }}>
                    {status}
                </div>
            )}
        </div>
    );
};

export default PowerControl;