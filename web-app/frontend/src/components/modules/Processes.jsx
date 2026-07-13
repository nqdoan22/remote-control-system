import React, { useState, useEffect } from 'react';
import { Search, Trash2, RefreshCw, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function ProcessesManager({ machineId }) {
  // --- TRẠNG THÁI DỮ LIỆU ---
  const [processes, setProcesses] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Trạng thái phục vụ cho Hộp thoại xác nhận (Modal) trước khi diệt tiến trình
  const [selectedProcess, setSelectedProcess] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // --- LẤY DANH SÁCH TIẾN TRÌNH TỪ BACKEND ---
  const fetchProcesses = async () => {
    setLoading(true);
    setError(null);
    try {
      // Thực tế sẽ gọi API: fetch(`/api/modules/applications/${machineId}`) kèm Token JWT
      // Ở đây ta mô phỏng dữ liệu thật trả về từ Agent để bạn dễ hình dung giao diện
      setTimeout(() => {
        setProcesses([
          { pid: 4122, name: 'chrome.exe', cpu: '4.2%', memory: '185 MB', user: 'Admin' },
          { pid: 1084, name: 'svchost.exe', cpu: '0.1%', memory: '24 MB', user: 'SYSTEM' },
          { pid: 8540, name: 'vlc.exe', cpu: '12.5%', memory: '92 MB', user: 'Admin' },
          { pid: 3112, name: 'cmd.exe', cpu: '0.0%', memory: '4 MB', user: 'Admin' },
          { pid: 9916, name: 'discord.exe', cpu: '1.8%', memory: '120 MB', user: 'Admin' },
        ]);
        setLoading(false);
      }, 800); // Tạo độ trễ giả lập mạng LAN
    } catch (err) {
      setError('Không thể kết nối tới máy mục tiêu hoặc lỗi quyền truy cập JWT.');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (machineId) fetchProcesses();
  }, [machineId]);

  // --- HÀM GỬI LỆNH DIỆT TIẾN TRÌNH (KILL PROCESS) ---
  const handleKillProcess = async () => {
    if (!selectedProcess) return;
    
    try {
      console.log(`Đang gửi lệnh diệt PID: ${selectedProcess.pid} của máy ${machineId}`);
      
      /* Luồng xử lý API thực tế:
      const token = localStorage.getItem('token');
      await fetch('/api/modules/processes/kill', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          machine_id: machineId,
          pid: selectedProcess.pid,
          process_name: selectedProcess.name
        })
      });
      */

      // Cập nhật nhanh giao diện xóa tiến trình đó ra khỏi bảng (Xử lý UI bọc lót)
      setProcesses(processes.filter(p => p.pid !== selectedProcess.pid));
      setIsModalOpen(false);
      setSelectedProcess(null);
      alert(`Đã hạ lệnh đóng tiến trình thành công!`);
    } catch (err) {
      alert('Lỗi khi gửi lệnh đóng tiến trình.');
    }
  };

  // Lọc tiến trình theo thanh tìm kiếm
  const filteredProcesses = processes.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || p.pid.toString().includes(searchTerm)
  );

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100 max-w-5xl mx-auto">
      
      {/* 💳 TIÊU ĐỀ MODULE & NÚT REFRESH */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <ShieldAlert className="text-indigo-600 w-6 h-6" />
            Quản lý Tiến trình hệ thống (Task Manager)
          </h2>
          <p className="text-sm text-gray-500">Mã thiết bị đang điều khiển: <span className="font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{machineId || "Chưa chọn"}</span></p>
        </div>
        
        <button 
          onClick={fetchProcesses}
          disabled={loading}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Đang quét...' : 'Làm mới bảng'}
        </button>
      </div>

      {/* 🔍 THANH TÌM KIẾM */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Tìm theo tên tiến trình hoặc số PID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
        />
      </div>

      {/* 📊 BẢNG HIỂN THỊ DANH SÁCH TIẾN TRÌNH */}
      {error && <div className="p-4 mb-4 text-sm text-red-700 bg-red-50 rounded-lg">{error}</div>}

      <div className="overflow-x-auto border border-gray-100 rounded-lg">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100 text-gray-600 font-medium">
              <th className="p-3">PID</th>
              <th className="p-3">Tên Tiến Trình</th>
              <th className="p-3">Sử dụng CPU</th>
              <th className="p-3">Bộ nhớ (RAM)</th>
              <th className="p-3">Người chạy</th>
              <th className="p-3 text-center">Hành động</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50 text-gray-700">
            {loading ? (
              <tr>
                <td colSpan="6" className="text-center py-8 text-gray-400 animate-pulse">
                  Đang thu thập dữ liệu tiến trình từ Agent thông qua WebSocket...
                </td>
              </tr>
            ) : filteredProcesses.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-8 text-gray-400">
                  Không tìm thấy tiến trình nào phù hợp.
                </td>
              </tr>
            ) : (
              filteredProcesses.map((proc) => (
                <tr key={proc.pid} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3 font-mono text-gray-500 font-semibold">{proc.pid}</td>
                  <td className="p-3 font-medium text-gray-900">{proc.name}</td>
                  <td className="p-3 text-emerald-600 font-medium">{proc.cpu}</td>
                  <td className="p-3 text-blue-600">{proc.memory}</td>
                  <td className="p-3"><span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 font-mono">{proc.user}</span></td>
                  <td className="p-3 text-center">
                    <button
                      onClick={() => {
                        setSelectedProcess(proc);
                        setIsModalOpen(true);
                      }}
                      className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors inline-flex items-center gap-1 text-xs font-medium border border-transparent hover:border-red-200"
                      title="Kill Process"
                    >
                      <Trash2 className="w-4 h-4" />
                      Buộc dừng
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 🚨 HỘP THOẠI XÁC NHẬN NGUY HIỂM (CONFIRM MODAL) */}
      {isModalOpen && selectedProcess && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white rounded-xl shadow-xl border border-gray-100 max-w-md w-full p-6 animate-scale-up">
            <div className="flex items-center gap-3 text-amber-600 mb-4">
              <AlertTriangle className="w-8 h-8 shrink-0" />
              <h3 className="text-lg font-bold text-gray-900">Xác nhận dừng tiến trình?</h3>
            </div>
            
            <p className="text-sm text-gray-600 mb-4 leading-relaxed">
              Bạn đang yêu cầu ép buộc đóng tiến trình <span className="font-bold text-red-600 font-mono bg-red-50 px-1.5 py-0.5 rounded">{selectedProcess.name}</span> (PID: {selectedProcess.pid}). 
              Việc này có thể làm mất dữ liệu chưa lưu của người dùng trên máy tính đó hoặc gây lỗi hệ thống tạm thời.
            </p>

            <div className="flex justify-end gap-3 text-sm font-medium">
              <button
                onClick={() => { setIsModalOpen(false); setSelectedProcess(null); }}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleKillProcess}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition shadow-sm"
              >
                Vẫn đóng tiến trình
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}