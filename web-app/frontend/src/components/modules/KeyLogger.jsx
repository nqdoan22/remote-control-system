// web-app/frontend/src/components/modules/KeyLogger.jsx
import React, { useState, useEffect } from 'react';
// import { moduleService } from '../../services/api'; // Gỡ comment khi kết nối API thật

function KeyLogger({ machineId }) {
  // --- 🧠 1. QUẢN LÝ TRẠNG THÁI (STATE MANAGEMENT) ---
  
  // Trạng thái hoạt động: "disabled" (Tắt), "pending" (Chờ user duyệt), "active" (Đang ghi phím)
  const [status, setStatus] = useState('disabled'); 
  
  // Mảng chứa danh sách các dòng nhật ký phím gõ được từ máy đích
  const [logs, setLogs] = useState([]); 
  
  // Trạng thái đợi mạng tải dữ liệu (Hiệu ứng loading)
  const [isLoading, setIsLoading] = useState(false); 
  
  // Từ khóa dùng để tìm kiếm/lọc nội dung nhạy cảm trong nhật ký phím
  const [filterText, setFilterText] = useState(''); 

  // --- 🔄 2. HÀM LẤY NHẬT KÝ PHÍM (FETCH LOGS) ---
  const fetchKeyLogs = async () => {
    // Nếu tính năng chưa được bật thì không cho phép lấy dữ liệu để bảo mật
    if (status !== 'active') return;
    
    setIsLoading(true);
    try {
      // TRONG THỰC TẾ: Gọi API lấy dữ liệu thật từ Backend Python
      // const response = await moduleService.getKeyloggerLogs(machineId);
      // setLogs(response.data.logs); // Giả sử backend trả về mảng Object
      
      // MOCK DATA: Giả lập dữ liệu có cấu trúc cao để kiểm thử
      setTimeout(() => {
        const mockLogs = [
          { timestamp: "19:45:12", window: "Google Chrome (Facebook)", content: "nguyenvanan@gmail.com[TAB]MatKhau123[ENTER]" },
          { timestamp: "19:46:05", window: "Notepad (BaoCao.txt)", content: "Dang viet do an mang may tinh phan keylogger..." },
          { timestamp: "19:47:40", window: "Windows Run Command", content: "cmd.exe[ENTER]ipconfig /all[ENTER]" }
        ];
        setLogs(mockLogs);
        setIsLoading(false);
      }, 600);
      
    } catch (error) {
      alert("Không thể lấy nhật ký phím: " + error.message);
      setIsLoading(false);
    }
  };

  // Cơ chế tự động làm mới nhật ký phím sau mỗi 5 giây (Polling) nếu đang trong trạng thái Active
  useEffect(() => {
    let intervalId;
    if (status === 'active') {
      fetchKeyLogs(); // Lấy dữ liệu lần đầu ngay lập tức
      intervalId = setInterval(fetchKeyLogs, 5000); // Kích hoạt vòng lặp chạy ngầm sau mỗi 5s
    }
    // Hàm dọn dẹp (Cleanup) của React: Tự động hủy vòng lặp nếu user chuyển sang tab khác hoặc tắt tính năng
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [status, machineId]);

  // --- 🔓 3. LOGIC KÍCH HOẠT HỆ THỐNG GHI PHÍM ---
  const handleStartLogging = async () => {
    // Bước A: Hiện cảnh báo an toàn trên Web App (Tư duy quản trị rủi ro)
    const confirmAction = window.confirm(
      "⚠️ CẢNH BÁO AN TOÀN & QUYỀN RIÊNG TƯ:\n\n" +
      "Tính năng Keylogger sẽ ghi lại mọi thao tác phím (bao gồm cả mật khẩu, tài khoản ngân hàng).\n" +
      "Yêu cầu này cần được sự CHẤP THUẬN bằng Pop-up trực tiếp của người dùng ngồi trước máy đích.\n\n" +
      "Bạn có muốn phát lệnh xin quyền không?"
    );
    
    if (!confirmAction) return;

    // Chuyển trạng thái sang Chờ phê duyệt (Pending) trên giao diện Web App
    setStatus('pending');
    
    try {
      // TRONG THỰC TẾ: Bắn lệnh xuống backend qua đường dẫn API
      // await moduleService.startKeylogger(machineId);
      
      // GIẢ LẬP: Sau 3 giây người dùng ngồi máy Agent bấm nút "ĐỒNG Ý" trên Pop-up Windows
      setTimeout(() => {
        alert("🎉 Thông báo từ Hệ thống: Người dùng máy đích ĐÃ BẤM CHẤP THUẬN cho phép giám sát!");
        setStatus('active');
      }, 3000);

    } catch (error) {
      alert("Lỗi phát lệnh kích hoạt: " + error.message);
      setStatus('disabled');
    }
  };

  // --- 🔒 4. LOGIC HỦY BỎ / TẮT HỆ THỐNG GHI PHÍM ---
  const handleStopLogging = async () => {
    const confirmStop = window.confirm("Bạn có chắc chắn muốn TẮT tính năng Ghi phím từ xa?");
    if (!confirmStop) return;

    try {
      // TRONG THỰC TẾ: Gọi API thông báo Agent gỡ bỏ hook bàn phím
      // await moduleService.stopKeylogger(machineId);
      
      setStatus('disabled');
      setLogs([]); // Xóa sạch dữ liệu hiển thị trên RAM trình duyệt để bảo mật thông tin
      alert("🛑 Đã tắt Keylogger thành công. Agent đã ngừng theo dõi phím gõ.");
    } catch (error) {
      alert("Lỗi khi tắt Keylogger: " + error.message);
    }
  };

  // --- 🔍 5. THUẬT TOÁN LỌC TÌM KIẾM NHẬT KÝ ---
  // Hỗ trợ người quản trị lọc nhanh các dòng log liên quan đến ứng dụng hoặc nội dung cụ thể
  const filteredLogs = logs.filter(item => 
    item.window.toLowerCase().includes(filterText.toLowerCase()) ||
    item.content.toLowerCase().includes(filterText.toLowerCase())
  );

  // --- 🖼️ GIAO DIỆN HIỂN THỊ (RÚT GỌN CSS) ---
  return (
    <div style={{ padding: '1rem' }}>
      <h2>⌨️ Hệ Thống Giám Sát Bàn Phím (Keylogger Auditing)</h2>
      <p>Trạng thái phân hệ: 
        <strong style={{
          marginLeft: '0.5rem',
          color: status === 'active' ? '#10b981' : status === 'pending' ? '#f59e0b' : '#ef4444'
        }}>
          {status === 'active' ? '🟢 ĐANG HOẠT ĐỘNG (REAL-TIME)' : status === 'pending' ? '🟡 ĐANG CHỜ USER DUYỆT CỬA SỔ POP-UP...' : '🔴 ĐÃ TẮT AN TOÀN'}
        </strong>
      </p>

      {/* 🎮 KHU VỰC CÁC NÚT ĐIỀU KHIỂN HÀNH ĐỘNG AN TOÀN */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem' }}>
        {status === 'disabled' && (
          <button onClick={handleStartLogging} style={{ backgroundColor: '#2563eb', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            🚀 Kích Hoạt Theo Dõi (Xin Quyền User)
          </button>
        )}
        {(status === 'active' || status === 'pending') && (
          <button onClick={handleStopLogging} style={{ backgroundColor: '#ef4444', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            🛑 Hủy Bỏ Giám Sát & Xóa Log Tạm
          </button>
        )}
        {status === 'active' && (
          <button onClick={fetchKeyLogs} disabled={isLoading} style={{ backgroundColor: '#10b981', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            {isLoading ? '⏳ Đang đồng bộ...' : '🔄 Làm mới bộ đệm (Refresh)'}
          </button>
        )}
      </div>

      {/* 📊 BẢNG HIỂN THỊ NHẬT KÝ PHÍM (CHỈ HIỆN KHI TRẠNG THÁI LÀ ACTIVE) */}
      {status === 'active' && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <input 
              type="text" 
              placeholder="🔍 Tìm nhanh theo Tên ứng dụng hoặc nội dung đã gõ..." 
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              style={{ width: '100%', maxWidth: '400px', padding: '0.5rem' }}
            />
          </div>

          <table border="1" cellPadding="10" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc' }}>
                <th style={{ width: '15%' }}>Thời Gian</th>
                <th style={{ width: '30%' }}>Ứng Dụng Đang Truy Cập (Active Window)</th>
                <th style={{ width: '55%' }}>Nội Dung Ký Tự Đã Gõ</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length > 0 ? (
                filteredLogs.map((item, idx) => (
                  <tr key={idx}>
                    <td><code>{item.timestamp}</code></td>
                    <td style={{ color: '#0369a1', fontWeight: '500' }}>{item.window}</td>
                    <td style={{ backgroundColor: '#f1f5f9', fontFamily: 'monospace', wordBreak: 'break-all' }}>{item.content}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan="3" style={{ textAlign: 'center', color: '#64748b' }}>Chưa có dữ liệu bàn phím mới được ghi nhận trong bộ đệm.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default KeyLogger;