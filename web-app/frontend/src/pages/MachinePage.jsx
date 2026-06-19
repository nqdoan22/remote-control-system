import React, { useState } from 'react';
import Processes from '../components/modules/Processes';

export default function MachinePage() {
  const [activeTab, setActiveTab] = useState('processes');

  // Lấy danh sách ID máy từ URL (Do cơ chế State-based Routing trong App.jsx cấu hình)
  const currentPath = window.location.pathname;
  const machineId = currentPath.replace('/machine/', '') || 'UNKNOWN-DEVICE';

  const goBack = () => {
    window.location.href = '/dashboard';
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <button onClick={goBack} style={{ marginBottom: '15px', padding: '6px 12px', cursor: 'pointer' }}>
        ← Quay lại Dashboard
      </button>

      <div style={{ backgroundColor: '#f1f1f1', padding: '15px', borderRadius: '6px', marginBottom: '20px' }}>
        <h2 style={{ margin: 0 }}>Giao diện điều khiển máy</h2>
        <p style={{ margin: '5px 0 0 0', color: '#555' }}>
          <strong>Đang điều khiển:</strong> <span style={{ color: '#0275d8', fontWeight: 'bold' }}>{decodeURIComponent(machineId)}</span>
        </p>
      </div>

      {/* Tabs cho 8 module (Hiện tại hiển thị trước 5 tab cơ bản để test cấu trúc) */}
      <div style={{ display: 'flex', gap: '5px', borderBottom: '2px solid #ccc', paddingBottom: '10px', marginBottom: '20px', overflowX: 'auto' }}>
        <button onClick={() => setActiveTab('processes')} style={{ padding: '10px', cursor: 'pointer', backgroundColor: activeTab === 'processes' ? '#0275d8' : '#fff', color: activeTab === 'processes' ? '#fff' : '#000', border: '1px solid #ccc', borderRadius: '4px' }}>
          Tiến trình (Processes)
        </button>
        <button onClick={() => setActiveTab('applications')} style={{ padding: '10px', cursor: 'pointer', backgroundColor: activeTab === 'applications' ? '#0275d8' : '#fff', color: activeTab === 'applications' ? '#fff' : '#000', border: '1px solid #ccc', borderRadius: '4px' }}>
          Ứng dụng (Apps)
        </button>
        <button onClick={() => setActiveTab('screenshot')} style={{ padding: '10px', cursor: 'pointer', backgroundColor: activeTab === 'screenshot' ? '#0275d8' : '#fff', color: activeTab === 'screenshot' ? '#fff' : '#000', border: '1px solid #ccc', borderRadius: '4px' }}>
          Chụp màn hình
        </button>
        <button onClick={() => setActiveTab('files')} style={{ padding: '10px', cursor: 'pointer', backgroundColor: activeTab === 'files' ? '#0275d8' : '#fff', color: activeTab === 'files' ? '#fff' : '#000', border: '1px solid #ccc', borderRadius: '4px' }}>
          Quản lý File
        </button>
        <button onClick={() => setActiveTab('power')} style={{ padding: '10px', cursor: 'pointer', backgroundColor: activeTab === 'power' ? '#0275d8' : '#fff', color: activeTab === 'power' ? '#fff' : '#000', border: '1px solid #ccc', borderRadius: '4px' }}>
          Nguồn (Power)
        </button>
      </div>

      {/* Khung nội dung hiển thị Module tương ứng */}
      <div style={{ marginTop: '15px' }}>
        {activeTab === 'processes' && <Processes machineId={machineId} />}
        
        {activeTab === 'applications' && (
          <div style={{ padding: '15px', border: '1px solid #ccc', borderRadius: '4px' }}>Applications Module (Coming Soon)</div>
        )}
        {activeTab === 'screenshot' && (
          <div style={{ padding: '15px', border: '1px solid #ccc', borderRadius: '4px' }}>Screenshot Module (Coming Soon)</div>
        )}
        {activeTab === 'files' && (
          <div style={{ padding: '15px', border: '1px solid #ccc', borderRadius: '4px' }}>Files Module (Coming Soon)</div>
        )}
        {activeTab === 'power' && (
          <div style={{ padding: '15px', border: '1px solid #ccc', borderRadius: '4px' }}>Power Control Module (Coming Soon)</div>
        )}
      </div>
    </div>
  );
}