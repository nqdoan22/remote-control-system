import React, { useState } from 'react';
import { moduleService } from '../../services/api';

export default function Processes({ machineId }) {
  const [pid, setPid] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  const refreshProcesses = async () => {
    try {
      // Gọi sang router modules của backend: /api/modules/{machine_id}/processes
      await moduleService.sendCommand(machineId, 'processes', '');
      setStatusMsg('Đã gửi yêu cầu lấy danh sách tiến trình.');
    } catch (err) {
      setStatusMsg('Lỗi khi gửi yêu cầu danh sách.');
    }
  };

  const killProcess = async (e) => {
    e.preventDefault();
    try {
      // Gọi sang router modules của backend để thực hiện hành động kill
      await moduleService.sendCommand(machineId, 'processes/kill', '', { pid: parseInt(pid) });
      setStatusMsg(`Đã gửi lệnh kill PID: ${pid}`);
    } catch (err) {
      setStatusMsg('Lỗi khi gửi lệnh kill.');
    }
  };

  return (
    <div style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}>
      <h3>Processes Module</h3>
      <p style={{ fontSize: '13px', color: '#666' }}>Machine ID đang chọn: {machineId}</p>
      
      <button onClick={refreshProcesses} style={{ padding: '6px 12px', cursor: 'pointer' }}>
        Tải danh sách tiến trình
      </button>

      <form onSubmit={killProcess} style={{ marginTop: '15px' }}>
        <input 
          type="number" 
          placeholder="Nhập PID tiến trình" 
          value={pid} 
          onChange={(e) => setPid(e.target.value)}
          required 
          style={{ padding: '5px', width: '150px' }}
        />
        <button type="submit" style={{ marginLeft: '8px', padding: '5px 12px', backgroundColor: '#d9534f', color: '#fff', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
          Kill Process
        </button>
      </form>

      {statusMsg && <p style={{ marginTop: '10px', fontWeight: 'bold', color: '#0275d8' }}>{statusMsg}</p>}
    </div>
  );
}