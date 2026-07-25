// frontend/src/pages/MachinePage.jsx
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import ModulePanel from '../components/shared/ModulePanel';

// Placeholder cho các modules (Chúng ta sẽ code chi tiết sau)
const PlaceholderModule = ({ title }) => (
    <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
        <h3>Module: {title}</h3>
        <p>Đang chờ triển khai giao diện...</p>
    </div>
);

const MachinePage = () => {
    const { machineId } = useParams();
    const navigate = useNavigate();
    const { isConnected, sendCommand, lastMessage } = useWebSocket();
    
    // State lưu trữ module đang được chọn (Mặc định là xem Tiến trình)
    const [activeModule, setActiveModule] = useState('processes');

    // Hàm render nội dung động dựa vào activeModule
    const renderActiveModule = () => {
        // Truyền các props cần thiết xuống cho từng module con
        const moduleProps = { machineId, sendCommand, lastMessage, isConnected };

        switch (activeModule) {
            case 'processes': return <PlaceholderModule title="Quản lý Tiến trình (Processes)" {...moduleProps} />;
            case 'applications': return <PlaceholderModule title="Quản lý Ứng dụng (Applications)" {...moduleProps} />;
            case 'screenshot': return <PlaceholderModule title="Chụp ảnh màn hình (Screenshot)" {...moduleProps} />;
            case 'livescreen': return <PlaceholderModule title="Live Screen (Yêu cầu cấp quyền)" {...moduleProps} />;
            case 'keylogger': return <PlaceholderModule title="Keylogger (Yêu cầu cấp quyền)" {...moduleProps} />;
            case 'webcam': return <PlaceholderModule title="Webcam (Yêu cầu cấp quyền)" {...moduleProps} />;
            case 'filetransfer': return <PlaceholderModule title="Truyền tệp - Sandbox (Yêu cầu cấp quyền)" {...moduleProps} />;
            case 'power': return <PlaceholderModule title="Nguồn (Yêu cầu cấp quyền)" {...moduleProps} />;
            default: return <div>Vui lòng chọn một chức năng</div>;
        }
    };

    return (
        <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f9fafb' }}>
            {/* Cột trái: Sidebar Menu */}
            <ModulePanel 
                activeModule={activeModule} 
                setActiveModule={setActiveModule} 
                onBack={() => navigate('/')}
            />

            {/* Cột phải: Không gian thao tác chính */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                {/* Header của Machine */}
                <header style={{ 
                    padding: '15px 20px', 
                    backgroundColor: 'white', 
                    borderBottom: '1px solid #e5e7eb',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <div>
                        <h2 style={{ margin: 0, fontSize: '18px' }}>Đang điều khiển: <span style={{ color: '#2563eb' }}>{machineId}</span></h2>
                    </div>
                    <div style={{ 
                        padding: '4px 10px', 
                        borderRadius: '12px', 
                        fontSize: '13px',
                        backgroundColor: isConnected ? '#dcfce7' : '#fee2e2',
                        color: isConnected ? '#166534' : '#991b1b'
                    }}>
                        {isConnected ? '🟢 Đã kết nối' : '🔴 Mất kết nối'}
                    </div>
                </header>

                {/* Khu vực render Module */}
                <main style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
                    <div style={{ backgroundColor: 'white', borderRadius: '8px', minHeight: '100%', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                        {renderActiveModule()}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default MachinePage;