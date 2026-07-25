// frontend/src/components/modules/Screenshot.jsx
import React, { useState } from 'react';

const Screenshot = ({ machineId, sendCommand }) => {
    const [imageSrc, setImageSrc] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const captureScreenshot = async () => {
        setIsLoading(true);
        setError('');
        try {
            const res = await sendCommand('screenshot.capture', machineId);
            if (res.success && res.data?.imageBase64) {
                setImageSrc(`data:image/png;base64,${res.data.imageBase64}`);
            }
        } catch (err) {
            setError(err.message || 'Không thể chụp ảnh màn hình');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0 }}>Chụp ảnh màn hình (Static Screenshot)</h3>
                <button 
                    onClick={captureScreenshot} 
                    disabled={isLoading}
                    style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: 'white', border: 'none', borderRadius: '4px', cursor: isLoading ? 'wait' : 'pointer' }}
                >
                    {isLoading ? 'Đang chụp...' : '📸 Chụp màn hình'}
                </button>
            </div>

            {error && <div style={{ color: '#ef4444', marginBottom: '15px' }}>{error}</div>}

            {imageSrc ? (
                <div style={{ textAlign: 'center' }}>
                    <img src={imageSrc} alt="Screenshot" style={{ maxWidth: '100%', maxHeight: '500px', border: '1px solid #ccc', borderRadius: '4px' }} />
                    <div style={{ marginTop: '10px' }}>
                        <a href={imageSrc} download={`screenshot_${machineId}.png`} style={{ color: '#2563eb', textDecoration: 'underline' }}>
                            ⬇ Tải ảnh về
                        </a>
                    </div>
                </div>
            ) : (
                <p style={{ color: '#6b7280', fontStyle: 'italic' }}>Bấm "Chụp màn hình" để lấy hình ảnh hiện tại từ máy khách.</p>
            )}
        </div>
    );
};

export default Screenshot;