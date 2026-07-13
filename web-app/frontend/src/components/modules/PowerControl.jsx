import React, { useState } from 'react';
import { Power, RotateCcw, Lock, Moon, AlertTriangle } from 'lucide-react';

export default function PowerControl({ machineId }) {
  const [loading, setLoading] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null); // Lưu hành động đang chọn để hiện Modal
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Danh sách 4 nút nguồn "quyền lực"
  const actionsConfig = {
    shutdown: { label: 'Tắt máy từ xa', icon: Power, color: 'bg-red-500 hover:bg-red-600 border-red-200 text-red-600', text: 'Hệ thống sẽ thực hiện tắt nguồn máy tính đích ngay lập tức.' },
    restart: { label: 'Khởi động lại', icon: RotateCcw, color: 'bg-amber-500 hover:bg-amber-600 border-amber-200 text-amber-600', text: 'Hệ thống sẽ khởi động lại hệ điều hành của máy đích.' },
    lock: { label: 'Khóa màn hình', icon: Lock, color: 'bg-blue-500 hover:bg-blue-600 border-blue-200 text-blue-600', text: 'Máy tính đích sẽ bị đẩy ra màn hình khóa (Lock Screen).' },
    sleep: { label: 'Chế độ ngủ (Sleep)', icon: Moon, color: 'bg-purple-500 hover:bg-purple-600 border-purple-200 text-purple-600', text: 'Máy tính đích sẽ chuyển sang trạng thái tiết kiệm điện năng.' }
  };

  // --- HÀM GỬI LỆNH ĐIỀU KHIỂN NGUỒN ---
  const handlePowerControl = async () => {
    if (!selectedAction || !machineId) return;
    
    setLoading(true);
    try {
      console.log(`Đang gửi lệnh [${selectedAction.toUpperCase()}] tới máy: ${machineId}`);
      
      /* Luồng xử lý gọi API thực tế của chúng ta:
      const token = localStorage.getItem('token');
      const response = await fetch('/api/modules/power/control', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          machine_id: machineId,
          action: selectedAction
        })
      });
      const resData = await response.json();
      */

      // Giả lập xử lý thành công
      setTimeout(() => {
        alert(`Đã phát lệnh [${actionsConfig[selectedAction].label}] thành công tới Agent!`);
        setLoading(false);
        setIsModalOpen(false);
      }, 1000);

    } catch (error) {
      alert('Có lỗi xảy ra khi truyền lệnh qua mạng LAN.');
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100 max-w-4xl mx-auto">
      
      {/* 🏷️ TIÊU ĐỀ MODULE */}
      <div className="mb-8 border-b border-gray-50 pb-4">
        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Power className="text-red-500 w-6 h-6 animate-pulse" />
          Điều khiển Nguồn hệ thống (Power Control)
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Mã thiết bị nhận lệnh: <span className="font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{machineId || "Chưa chọn"}</span>
        </p>
      </div>

      {/* 🎛️ BỘ NÚT BẤM ĐIỀU KHIỂN (GRID LAYOUT) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {Object.entries(actionsConfig).map(([key, item]) => {
          const IconComponent = item.icon;
          return (
            <button
              key={key}
              disabled={!machineId || loading}
              onClick={() => {
                setSelectedAction(key);
                setIsModalOpen(true);
              }}
              className="flex flex-col items-center justify-center p-6 bg-white border border-gray-100 rounded-xl hover:shadow-md hover:border-gray-200 transition group disabled:opacity-40 disabled:hover:shadow-none disabled:hover:border-gray-100"
            >
              {/* Vòng tròn chứa Icon bên trong */}
              <div className={`p-4 rounded-full mb-4 bg-gray-50 text-gray-500 transition-colors duration-300 group-hover:${item.color.split(' ')[0]} group-hover:text-white`}>
                <IconComponent className="w-6 h-6" />
              </div>
              <span className="font-semibold text-gray-700 text-sm">{item.label}</span>
              <span className="text-xs text-gray-400 text-center mt-2 px-2 leading-tight">Click để kích hoạt lệnh</span>
            </button>
          );
        })}
      </div>

      {/* 🚨 HỘP THOẠI XÁC NHẬN NGUY HIỂM (CONFIRM MODAL) */}
      {isModalOpen && selectedAction && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-gray-100">
            <div className="flex items-center gap-3 text-red-500 mb-4">
              <AlertTriangle className="w-8 h-8 shrink-0" />
              <h3 className="text-lg font-bold text-gray-900">Yêu cầu xác nhận hành động</h3>
            </div>
            
            <p className="text-sm text-gray-600 mb-2">
              Bạn đang chuẩn bị thực hiện: <span className="font-bold text-gray-900">{actionsConfig[selectedAction].label}</span> trên thiết bị mục tiêu.
            </p>
            <p className="text-xs text-red-500 font-medium bg-red-50 p-3 rounded-lg border border-red-100 leading-relaxed mb-6">
              ⚠️ {actionsConfig[selectedAction].text} Hành động này không thể hoàn tác, vui lòng đảm bảo bạn có quyền hoặc máy đích không có tác vụ quan trọng đang chạy.
            </p>

            <div className="flex justify-end gap-3 text-sm font-medium">
              <button
                disabled={loading}
                onClick={() => { setIsModalOpen(false); setSelectedAction(null); }}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition disabled:opacity-50"
              >
                Hủy lệnh
              </button>
              <button
                disabled={loading}
                onClick={handlePowerControl}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition shadow-sm disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? 'Đang truyền lệnh...' : 'Xác nhận kích hoạt'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}