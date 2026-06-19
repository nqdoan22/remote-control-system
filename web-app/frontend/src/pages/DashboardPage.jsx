import React, { useState, useEffect } from 'react';
import { machineService } from '../services/api';

export default function DashboardPage() {
  const [machines, setMachines] = useState([]);
  const [selectedMachineIds, setSelectedMachineIds] = useState([]);
  const [statusMsg, setStatusMsg] = useState('');

  // Tải danh sách máy từ Backend
  const loadMachines = async () => {
    try {
      const data = await machineService.getMachines();
      setMachines(data);
    } catch (err) {
      setStatusMsg('Lỗi kết nối API danh sách máy.');
    }
  };

  useEffect(() => {
    loadMachines();
  }, []);

  // Xử lý khi tick chọn/bỏ chọn từng máy
  const handleSelectMachine = (machineId) => {
    if (selectedMachineIds.includes(machineId)) {
      setSelectedMachineIds(selectedMachineIds.filter(id => id !== machineId));
    } else {
      setSelectedMachineIds([...selectedMachineIds, machineId]);
    }
  };

  // Xử lý khi nhấn nút điều khiển các máy đã chọn
  const handleControlSelected = () => {
    if (selectedMachineIds.length === 0) {
      alert('Vui lòng chọn ít nhất một máy để điều khiển!');
      return;
    }
    // Chuyển sang trang điều khiển với danh sách ID máy (truyền qua URL query hoặc state)
    window.location.href = `/machine/${selectedMachineIds.join(',')}`;
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>Dashboard - Danh sách máy</h2>
      
      {statusMsg && <p style={{ color: 'red' }}>{statusMsg}</p>}

      <div style={{ marginBottom: '15px' }}>
        <button onClick={handleControlSelected} style={{ padding: '8px 16px', backgroundColor: '#5cb85c', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Điều khiển các máy đã chọn ({selectedMachineIds.length})
        </button>
        <button onClick={loadMachines} style={{ marginLeft: '10px', padding: '8px 16px', cursor: 'pointer' }}>
          Làm mới ↻
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {machines.map((machine) => (
          <div 
            key={machine.machine_id} 
            style={{ 
              border: '1px solid #ccc', 
              padding: '12px', 
              borderRadius: '6px', 
              display: 'flex', 
              alignItems: 'center',
              backgroundColor: selectedMachineIds.includes(machine.machine_id) ? '#e6f7ff' : '#fff'
            }}
          >
            {/* Checkbox để chọn nhiều máy */}
            <input 
              type="checkbox" 
              checked={selectedMachineIds.includes(machine.machine_id)} 
              onChange={() => handleSelectMachine(machine.machine_id)}
              style={{ width: '18px', height: '18px', marginRight: '15px', cursor: 'pointer' }}
            />
            
            <div style={{ flexGrow: 1 }}>
              <strong style={{ fontSize: '16px' }}>{machine.machine_id}</strong>
              <span style={{ marginLeft: '15px', color: '#666' }}>IP: {machine.ip}</span>
              <span style={{ marginLeft: '15px', color: '#666' }}>OS: {machine.os}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%', 
                backgroundColor: machine.status === 'online' ? '#5cb85c' : '#d9534f',
                marginRight: '6px'
              }}></span>
              <span style={{ color: machine.status === 'online' ? '#5cb85c' : '#d9534f', fontWeight: 'bold', fontSize: '14px' }}>
                {machine.status.toUpperCase()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}