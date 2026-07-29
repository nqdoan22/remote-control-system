// frontend/src/pages/MachinePage.jsx
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import ModulePanel from '../components/shared/ModulePanel';
import Processes from '../components/modules/Processes';
import Applications from '../components/modules/Applications';
import Screenshot from '../components/modules/Screenshot';
import LiveScreen from '../components/modules/LiveScreen';
import Keylogger from '../components/modules/KeyLogger';
import FileTransfer from '../components/modules/FileTransfer';
import Webcam from '../components/modules/Webcam';
import PowerControl from '../components/modules/PowerControl';

const MachinePage = () => {
    const { machineId } = useParams();
    const navigate = useNavigate();
    const { isConnected, sendCommand, lastMessage } = useWebSocket();
    
    const [activeModule, setActiveModule] = useState('processes');
    const moduleProps = { machineId, sendCommand, lastMessage, isConnected };

    const renderActiveModule = () => {
        switch (activeModule) {
            case 'processes': return <Processes {...moduleProps} />;
            case 'applications': return <Applications {...moduleProps} />;
            case 'screenshot': return <Screenshot {...moduleProps} />;
            case 'livescreen': return <LiveScreen {...moduleProps} />;
            case 'keylogger': return <Keylogger {...moduleProps} />;
            case 'webcam': return <Webcam {...moduleProps} />;
            case 'filetransfer': return <FileTransfer {...moduleProps} />;
            case 'power': return <PowerControl {...moduleProps} />;
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