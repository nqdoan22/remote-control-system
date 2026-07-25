// frontend/src/components/modules/Processes.jsx
import React, { useState, useEffect } from 'react';

const Processes = ({ machineId, sendCommand, isConnected }) => {
    const [processes, setProcesses] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [search, setSearch] = useState('');
    const [message, setMessage] = useState('');

    const fetchProcesses = async () => {
        setIsLoading(true);
        setMessage('');
        try {
            const res = await sendCommand('process.list', machineId);
            if (res.success) setProcesses(res.data.processes);
        } catch (err) {
            setMessage(`Lỗi: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const killProcess = async (pid) => {
        if (!window.confirm(`Bạn có chắc muốn tắt tiến trình PID ${pid}?`)) return;
        try {
            await sendCommand('process.kill', machineId, { pid });
            setMessage(`Đã diệt tiến trình PID: ${pid}`);
            fetchProcesses();
        } catch (err) {
            setMessage(`Lỗi: ${err.message}`);
        }
    };

    useEffect(() => { if (isConnected) fetchProcesses(); }, [isConnected]);

    const filteredProcesses = processes.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));

    return (
        <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                <h3 style={{ margin: 0 }}>Quản lý Tiến trình (Processes)</h3>
                <button onClick={fetchProcesses} disabled={isLoading} style={{ padding: '6px 12px', cursor: 'pointer' }}>🔄 Làm mới</button>
            </div>

            <input 
                type="text" 
                placeholder="Tìm kiếm tiến trình..." 
                value={search} 
                onChange={e => setSearch(e.target.value)}
                style={{ width: '100%', padding: '8px', marginBottom: '15px', boxSizing: 'border-box' }}
            />

            {message && <div style={{ marginBottom: '15px', color: '#b91c1c' }}>{message}</div>}

            <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ position: 'sticky', top: 0, backgroundColor: '#f3f4f6' }}>
                        <tr>
                            <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>PID</th>
                            <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Tên Tiến trình</th>
                            <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>CPU (%)</th>
                            <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>RAM (MB)</th>
                            <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredProcesses.map((proc, idx) => (
                            <tr key={idx}>
                                <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{proc.pid}</td>
                                <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{proc.name}</td>
                                <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{proc.cpuUsage}</td>
                                <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{proc.memoryMB}</td>
                                <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>
                                    <button onClick={() => killProcess(proc.pid)} style={{ backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '4px 8px', borderRadius: '4px' }}>Kill</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Processes;