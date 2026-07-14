// web-app/frontend/src/components/modules/FileDownload.jsx
import React, { useState, useEffect } from 'react';
// import { moduleService } from '../../services/api'; // Gỡ comment khi chạy thực tế

function FileDownload({ machineId }) {
  // --- 🧠 1. KHỞI TẠO CÁC STATE QUẢN LÝ DỮ LIỆU ---
  const [currentPath, setCurrentPath] = useState(''); // Lưu đường dẫn hiện tại đang đứng (Chuỗi String)
  const [fileList, setFileList] = useState([]);       // Lưu danh sách file/thư mục con (Mảng Array)
  const [isLoading, setIsLoading] = useState(false);   // Trạng thái chờ đợi phản hồi từ mạng (Boolean)
  const [errorMessage, setErrorMessage] = useState(''); // Lưu thông điệp lỗi nếu có (String)

  // --- 🔄 2. HÀM GỌI API DUYỆT THƯ MỤC ---
  const loadDirectory = async (path) => {
    setIsLoading(true);
    setErrorMessage('');
    
    try {
      // TRONG THỰC TẾ: Gọi lên backend qua API Axios
      // const response = await moduleService.browseFiles(machineId, path);
      // const { current_path, files } = response.data;
      
      // GIẢ LẬP: Dữ liệu mẫu (Mock Data) chuẩn định dạng để bạn test giao diện
      setTimeout(() => {
        const mockCurrentPath = path || "C:\\RemoteSandbox";
        const mockFiles = [
          { name: "..", is_dir: true, size: 0, last_modified: "-" }, // Nút quay lại thư mục cha
          { name: "Documents", is_dir: true, size: 0, last_modified: "2026-07-10 14:20" },
          { name: "Photos", is_dir: true, size: 0, last_modified: "2026-07-12 09:05" },
          { name: "bao_cao_do_an.docx", is_dir: false, size: 2457600, last_modified: "2026-07-13 18:00" }, // 2.4 MB
          { name: "passwords.txt", is_dir: false, size: 1024, last_modified: "2026-07-01 23:11" } // 1 KB
        ];
        
        // Cập nhật dữ liệu mới vào State để React vẽ lại màn hình
        setCurrentPath(mockCurrentPath);
        setFileList(mockFiles);
        setIsLoading(false);
      }, 800);

    } catch (error) {
      setErrorMessage(error.response?.data?.detail || "Không thể kết nối tới thư mục này.");
      setIsLoading(false);
    }
  };

  // Tự động kích hoạt quét thư mục gốc ngay khi user click mở Tab Quản lý File
  useEffect(() => {
    loadDirectory('');
  }, [machineId]);

  // --- 📂 3. LOGIC XỬ LÝ KHI USER CLICK VÀO MỘT DÒNG ---
  const handleItemClick = (item) => {
    // Nếu click vào một thư mục -> Tiến hành đi sâu vào bên trong thư mục đó
    if (item.is_dir) {
      let newPath = "";
      if (item.name === "..") {
        // Thuật toán cắt chuỗi để lùi lại 1 cấp thư mục (Quay lại thư mục cha)
        const parts = currentPath.split('\\');
        parts.pop();
        newPath = parts.join('\\');
      } else {
        // Nối thêm tên thư mục con vào đường dẫn hiện tại
        newPath = `${currentPath}\\${item.name}`;
      }
      loadDirectory(newPath);
    } else {
      // Nếu click vào một File tập tin -> Kích hoạt lệnh Tải xuống
      handleDownloadFile(item.name);
    }
  };

  // --- 📥 4. THUẬT TOÁN TẢI FILE VÀ CHUYỂN ĐỔI CHUỖI MẠNG THÀNH FILE VẬT LÝ ---
  const handleDownloadFile = async (fileName) => {
    const fullFilePath = `${currentPath}\\${fileName}`;
    
    // Thể hiện tư duy an toàn: Cảnh báo người dùng trước khi tải file từ xa
    const confirmDownload = window.confirm(`Bạn có chắc chắn muốn tải file từ xa:\n${fullFilePath}?`);
    if (!confirmDownload) return;

    alert(`Đang gửi yêu cầu trích xuất dữ liệu file: ${fileName}`);

    try {
      // TRONG THỰC TẾ: Gọi API lấy chuỗi mã hóa Base64 của file về
      // const response = await moduleService.downloadFile(machineId, fullFilePath);
      // const { file_base64 } = response.data;
      
      // GIẢ LẬP: Chuỗi Base64 mẫu của một file text chứa chữ "Hello World"
      const mockBase64 = "SGVsbG8gV29ybGQgLSBEYXRhIHR1IG1heSB0aW5oIGRpY2gh"; 

      // 🛠️ KỸ THUẬT JAVASCRIPT ĐỂ ÉP TRÌNH DUYỆT TỰ ĐỘNG TẢI FILE:
      // Bước A: Chuyển chuỗi Text mã hóa Base64 ngược trở lại thành các mảng byte nhị phân dữ liệu thô
      const byteCharacters = atob(mockBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      
      // Bước B: Đóng gói mảng byte thô thành một đối tượng Blob (Binary Large Object) của trình duyệt
      const blob = new Blob([byteArray], { type: "application/octet-stream" });
      
      // Bước C: Tạo ra một đường link ảo nội bộ (URL Object) trỏ tới Blob dữ liệu đó
      const fileBlobUrl = window.URL.createObjectURL(blob);
      
      // Bước D: Giả lập một chiếc thẻ <a> ẩn, tự động nhấn click để kích hoạt hộp thoại lưu file của Windows
      const hiddenAnchor = document.createElement('a');
      hiddenAnchor.href = fileBlobUrl;
      hiddenAnchor.download = fileName; // Đặt tên file khi tải về máy quản trị
      document.body.appendChild(hiddenAnchor);
      hiddenAnchor.click(); // Click chuột ảo
      
      // Dọn dẹp bộ nhớ RAM sau khi đã tải xong file ảo
      document.body.removeChild(hiddenAnchor);
      window.URL.revokeObjectURL(fileBlobUrl);

    } catch (error) {
      alert("Lỗi tải file: " + (error.response?.data?.detail || error.message));
    }
  };

  // --- 🖼️ GIAO DIỆN HIỂN THỊ (ĐÃ RÚT GỌN TỐI ĐA PHẦN THẨM MỸ CỦA CSS) ---
  return (
    <div style={{ padding: '1rem' }}>
      <h2>📁 Hệ Thống Quản Lý Tập Tin An Toàn</h2>
      <p>Thư mục hiện tại: <strong style={{color: '#2563eb'}}>{currentPath || "Đang tải thư mục gốc..."}</strong></p>

      {errorMessage && <div style={{ color: 'red', margin: '1rem 0' }}>⚠️ Lỗi: {errorMessage}</div>}
      
      {isLoading ? (
        <div>🔄 Đang truy xuất luồng dữ liệu đĩa từ xa...</div>
      ) : (
        <table border="1" cellPadding="10" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
          <thead>
            <tr style={{ backgroundColor: '#f1f5f9' }}>
              <th>Tên File / Thư mục</th>
              <th>Loại</th>
              <th>Dung lượng (Bytes)</th>
              <th>Ngày cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {fileList.map((item, index) => (
              <tr key={index} style={{ cursor: 'pointer' }} onClick={() => handleItemClick(item)}>
                {/* Tên hiển thị kèm biểu tượng trực quan để phân biệt */}
                <td>{item.is_dir ? `📁 ${item.name}` : `📄 ${item.name}`}</td>
                <td>{item.is_dir ? "Thư mục" : "Tập tin"}</td>
                <td>{item.is_dir ? "-" : item.size.toLocaleString()}</td>
                <td>{item.last_modified}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default FileDownload;