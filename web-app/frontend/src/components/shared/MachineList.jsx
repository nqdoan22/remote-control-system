// frontend/src/components/shared/MachineList.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const MachineList = ({ sendCommand, isWsConnected }) => {
    const [machines, setMachines] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    // Hàm gọi lấy danh sách máy tính qua WebSocket
    const fetchMachines = async () => {
        if (!isWsConnected) return;
        
        setIsLoading(true);
        setError('');
        
        try {
            // Theo định dạng API Contract: type là 'machine.list', destination là 'gateway'
            const response = await sendCommand('machine.list', 'gateway', {});
            
            if (response.success && response.data) {
                setMachines(response.data.machines);
            }
        } catch (err) {
            console.error("Lỗi lấy danh sách máy:", err);
            setError('Không thể lấy danh sách thiết bị. Vui lòng thử lại sau.');
        } finally {
            setIsLoading(false);
        }
    };

    // Tự động lấy dữ liệu khi WebSocket kết nối thành công
    useEffect(() => {
        if (isWsConnected) {
            fetchMachines();
        }
    }, [isWsConnected, sendCommand]);

    // Hàm xử lý khi bấm nút "Điều khiển"
    const handleControlClick = (machineId) => {
        navigate(`/machine/${machineId}`);
    };

    // Format thời gian từ Unix Timestamp sang chuẩn dễ đọc
    const formatLastSeen = (timestamp) => {
        if (!timestamp) return 'N/A';
        return new Date(timestamp * 1000).toLocaleString('vi-VN');
    };

    if (!isWsConnected) {
        return <p style={{ color: '#6b7280', fontStyle: 'italic' }}>Đang chờ kết nối tới Gateway...</p>;
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '15px' }}>
                <button 
                    onClick={fetchMachines} 
                    disabled={isLoading}
                    style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: 'white', border: 'none', borderRadius: '4px', cursor: isLoading ? 'wait' : 'pointer' }}
                >
                    {isLoading ? 'Đang làm mới...' : '🔄 Làm mới danh sách'}
                </button>
            </div>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                    <tr style={{ backgroundColor: '#f3f4f6', borderBottom: '2px solid #e5e7eb' }}>
                        <th style={{ padding: '12px' }}>Trạng thái</th>
                        <th style={{ padding: '12px' }}>Tên máy (Hostname)</th>
                        <th style={{ padding: '12px' }}>Địa chỉ IP</th>
                        <th style={{ padding: '12px' }}>Lần cuối Online</th>
                        <th style={{ padding: '12px', textAlign: 'center' }}>Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    {machines.length === 0 ? (
                        <tr>
                            <td colSpan="5" style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
                                Chưa có thiết bị nào kết nối vào hệ thống.
                            </td>
                        </tr>
                    ) : (
                        machines.map((machine) => (
                            <tr key={machine.machineId} style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '12px' }}>
                                    <span style={{ 
                                        display: 'inline-block',
                                        padding: '4px 8px', 
                                        borderRadius: '12px',
                                        fontSize: '12px',
                                        fontWeight: 'bold',
                                        backgroundColor: machine.status === 'online' ? '#dcfce7' : '#f3f4f6',
                                        color: machine.status === 'online' ? '#166534' : '#6b7280'
                                    }}>
                                        {machine.status === 'online' ? 'Online' : 'Offline'}
                                    </span>
                                </td>
                                <td style={{ padding: '12px', fontWeight: 'bold' }}>{machine.hostname}</td>
                                <td style={{ padding: '12px', color: '#4b5563' }}>{machine.ipAddress}</td>
                                <td style={{ padding: '12px', color: '#4b5563', fontSize: '14px' }}>
                                    {formatLastSeen(machine.lastSeen)}
                                </td>
                                <td style={{ padding: '12px', textAlign: 'center' }}>
                                    <button 
                                        onClick={() => handleControlClick(machine.machineId)}
                                        disabled={machine.status !== 'online'}
                                        style={{ 
                                            padding: '6px 12px', 
                                            backgroundColor: machine.status === 'online' ? '#10b981' : '#d1d5db', 
                                            color: 'white', 
                                            border: 'none', 
                                            borderRadius: '4px', 
                                            cursor: machine.status === 'online' ? 'pointer' : 'not-allowed'
                                        }}
                                    >
                                        Điều khiển
                                    </button>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default MachineList;