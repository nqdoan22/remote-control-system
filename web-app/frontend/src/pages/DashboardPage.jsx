// frontend/src/pages/DashboardPage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import MachineList from '../components/shared/MachineList';

const DashboardPage = () => {
    // Gọi hook để khởi tạo WebSocket và lấy trạng thái kết nối
    const { isConnected, sendCommand } = useWebSocket();
    const navigate = useNavigate();

    const handleLogout = () => {
        // Xóa token và quay về trang đăng nhập
        localStorage.removeItem('admin_token');
        navigate('/login');
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', fontFamily: 'Arial, sans-serif' }}>
            {/* Header / Navbar */}
            <header style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                backgroundColor: '#ffffff',
                padding: '15px 30px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: '20px', color: '#111827' }}>Quản Trị Hệ Thống Từ Xa</h1>
                    <p style={{ margin: '5px 0 0 0', fontSize: '13px', color: '#6b7280' }}>Dashboard Giám Sát</p>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    {/* Hiển thị trạng thái kết nối với Gateway */}
                    <div style={{ 
                        padding: '6px 12px', 
                        borderRadius: '20px', 
                        fontSize: '14px',
                        fontWeight: 'bold',
                        backgroundColor: isConnected ? '#dcfce7' : '#fee2e2',
                        color: isConnected ? '#166534' : '#991b1b'
                    }}>
                        {isConnected ? '🟢 Gateway: Online' : '🔴 Gateway: Offline'}
                    </div>
                    
                    <button 
                        onClick={handleLogout}
                        style={{ padding: '8px 16px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                        Đăng xuất
                    </button>
                </div>
            </header>

            {/* Nội dung chính */}
            <main style={{ padding: '30px' }}>
                <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                    <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#374151' }}>Danh sách thiết bị (Clients)</h2>
                    
                    {/* Render Component Danh sách máy tính */}
                    <MachineList sendCommand={sendCommand} isWsConnected={isConnected} />
                </div>
            </main>
        </div>
    );
};

export default DashboardPage;