// frontend/src/components/shared/ModulePanel.jsx
import React from 'react';

const ModulePanel = ({ activeModule, setActiveModule, onBack }) => {
    // Danh sách menu định nghĩa sẵn
    const menuGroups = [
        {
            title: "CHỨC NĂNG TIÊU CHUẨN",
            items: [
                { id: 'processes', label: 'Quản lý Tiến trình' },
                { id: 'applications', label: 'Quản lý Ứng dụng' },
                { id: 'screenshot', label: 'Chụp ảnh màn hình tĩnh' },
            ]
        },
        {
            title: "CHỨC NĂNG NHẠY CẢM (CẦN XIN QUYỀN)",
            items: [
                { id: 'livescreen', label: 'Màn hình trực tiếp (Live)' },
                { id: 'webcam', label: 'Giám sát Webcam' },
                { id: 'keylogger', label: 'Ghi phím (Keylogger)' },
                { id: 'filetransfer', label: 'Quản lý Tệp (Sandbox)' },
                { id: 'power', label: 'Điều khiển Nguồn' },
            ]
        }
    ];

    return (
        <div style={{ 
            width: '260px', 
            backgroundColor: '#1f2937', 
            color: 'white', 
            display: 'flex', 
            flexDirection: 'column' 
        }}>
            {/* Nút quay lại Dashboard */}
            <div style={{ padding: '20px', borderBottom: '1px solid #374151' }}>
                <button 
                    onClick={onBack}
                    style={{ 
                        width: '100%', padding: '10px', backgroundColor: '#374151', 
                        color: 'white', border: 'none', borderRadius: '4px', 
                        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
                    }}
                >
                    ⬅ Quay lại Dashboard
                </button>
            </div>

            {/* Render Menu */}
            <div style={{ padding: '10px 0', flex: 1, overflowY: 'auto' }}>
                {menuGroups.map((group, gIndex) => (
                    <div key={gIndex} style={{ marginBottom: '20px' }}>
                        <div style={{ 
                            padding: '0 20px', fontSize: '11px', fontWeight: 'bold', 
                            color: '#9ca3af', marginBottom: '8px', letterSpacing: '1px' 
                        }}>
                            {group.title}
                        </div>
                        {group.items.map(item => (
                            <button
                                key={item.id}
                                onClick={() => setActiveModule(item.id)}
                                style={{
                                    width: '100%',
                                    padding: '12px 20px',
                                    textAlign: 'left',
                                    backgroundColor: activeModule === item.id ? '#374151' : 'transparent',
                                    color: activeModule === item.id ? '#60a5fa' : '#d1d5db',
                                    border: 'none',
                                    borderLeft: activeModule === item.id ? '4px solid #3b82f6' : '4px solid transparent',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    transition: 'all 0.2s'
                                }}
                            >
                                {item.label}
                            </button>
                        ))}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ModulePanel;