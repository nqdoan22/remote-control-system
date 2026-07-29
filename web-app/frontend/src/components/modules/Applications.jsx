// frontend/src/components/modules/Applications.jsx
import React, { useState, useEffect } from 'react';

const Applications = ({ machineId, sendCommand, isConnected }) => {
    const [apps, setApps] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [appPath, setAppPath] = useState('');
    const [message, setMessage] = useState('');

    const fetchApps = async () => {
        setIsLoading(true);
        setMessage('');
        try {
            const res = await sendCommand('application.list', machineId);
            if (res.success) setApps(res.data?.applications || []);
        } catch (err) {
            setMessage(`Lỗi: ${err.message || 'Không thể lấy danh sách ứng dụng'}`);
        } finally {
            setIsLoading(false);
        }
    };

    const startApp = async () => {
        if (!appPath) return;
        try {
            setMessage('Đang gửi lệnh khởi động...');
            await sendCommand('application.start', machineId, { path: appPath });
            setMessage('Khởi động thành công!');
            setAppPath('');
            fetchApps();
        } catch (err) {
            setMessage(`Lỗi: ${err.message}`);
        }
    };

    const stopApp = async (pid) => {
        try {
            await sendCommand('application.stop', machineId, { pid });
            setMessage(`Đã đóng ứng dụng PID: ${pid}`);
            fetchApps();
        } catch (err) {
            setMessage(`Lỗi: ${err.message}`);
        }
    };

    useEffect(() => { if (isConnected) fetchApps(); }, [isConnected]);

    return (
        <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                <h3 style={{ margin: 0 }}>Quản lý Ứng dụng</h3>
                <button onClick={fetchApps} disabled={isLoading} style={{ padding: '6px 12px', cursor: 'pointer' }}>🔄 Làm mới</button>
            </div>
            
            <div style={{ marginBottom: '15px', display: 'flex', gap: '10px' }}>
                <input 
                    type="text" 
                    placeholder="Đường dẫn file .exe (VD: C:\Windows\notepad.exe)" 
                    value={appPath} 
                    onChange={e => setAppPath(e.target.value)}
                    style={{ flex: 1, padding: '8px' }}
                />
                <button onClick={startApp} style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: 'white', border: 'none' }}>Khởi chạy</button>
            </div>

            {message && <div style={{ marginBottom: '15px', color: '#b91c1c' }}>{message}</div>}

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                    <tr style={{ backgroundColor: '#f3f4f6' }}>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Tên Ứng dụng</th>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Tiêu đề Cửa sổ</th>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>PID</th>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>CPU (%)</th>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    {apps.map((app, idx) => (
                        <tr key={idx}>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{app.name}</td>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{app.mainWindowTitle}</td>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{app.pid}</td>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{app.cpuUsage}</td>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>
                                <button onClick={() => stopApp(app.pid)} style={{ backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '4px 8px', borderRadius: '4px' }}>Đóng</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default Applications;