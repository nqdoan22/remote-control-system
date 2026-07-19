// web-app/frontend/src/components/modules/FileDownload.jsx
import React, { useState, useEffect } from 'react';

function FileDownload({ machineId }) {
  const [currentPath, setCurrentPath] = useState(''); 
  const [fileList, setFileList] = useState([]); 
  const [isLoading, setIsLoading] = useState(false); 
  const [errorMessage, setErrorMessage] = useState('');
  
  const [selectedUploadFile, setSelectedUploadFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // --- 🔄 DUYỆT THƯ MỤC TRONG PHÂN VÙNG SANDBOX ---
  const loadDirectory = async (path) => {
    setIsLoading(true);
    setErrorMessage('');
    
    // Giả định kiểm tra chuỗi bảo mật an toàn phân vùng Sandbox
    if (path && !path.startsWith("C:\\RemoteSandbox") && path !== "C:") {
      setErrorMessage("Mã lỗi: INVALID_PATH. Yêu cầu truy cập thư mục nằm ngoài Sandbox bị từ chối.");
      setIsLoading(false);
      return;
    }

    try {
      setTimeout(() => {
        const mockCurrentPath = path || "C:\\RemoteSandbox";
        const mockFiles = [
          { name: "..", isDir: true, size: 0, lastModified: "-" }, 
          { name: "Documents", isDir: true, size: 0, lastModified: "2026-07-10 14:20" },
          { name: "Photos", isDir: true, size: 0, lastModified: "2026-07-12 09:05" },
          { name: "bao_cao_do_an.docx", isDir: false, size: 2457600, lastModified: "2026-07-13 18:00" }, 
          { name: "passwords.txt", isDir: false, size: 1024, lastModified: "2026-07-01 23:11" } 
        ];
        
        setCurrentPath(mockCurrentPath);
        setFileList(mockFiles);
        setIsLoading(false);
      }, 800);
    } catch (error) {
      setErrorMessage("Không thể kết nối truy cập hệ thống thư mục đĩa từ xa.");
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDirectory('');
  }, [machineId]);

  const handleItemClick = (item) => {
    if (item.isDir) {
      let newPath = "";
      if (item.name === "..") {
        const parts = currentPath.split('\\');
        parts.pop();
        newPath = parts.join('\\');
      } else {
        newPath = `${currentPath}\\${item.name}`;
      }
      loadDirectory(newPath);
    } else {
      handleDownloadFile(item.name);
    }
  };

  // --- 📥 TẢI FILE VỀ (HÀNH ĐỘNG: file.download) ---
  const handleDownloadFile = async (fileName) => {
    const fullFilePath = `${currentPath}\\${fileName}`;
    const confirmDownload = window.confirm(`Xác nhận tải tập tin đĩa hệ thống:\n${fullFilePath}?`);
    if (!confirmDownload) return;

    alert(`Đang khởi tạo gói tin trích xuất dữ liệu (file.download) cho file: ${fileName}`);
    try {
      const mockBase64 = "SGVsbG8gV29ybGQgLSBEYXRhIHR1IG1heSB0aW5oIGRpY2gh"; 
      const byteCharacters = atob(mockBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "application/octet-stream" });
      const fileBlobUrl = window.URL.createObjectURL(blob);
      
      const hiddenAnchor = document.createElement('a');
      hiddenAnchor.href = fileBlobUrl;
      hiddenAnchor.download = fileName; 
      document.body.appendChild(hiddenAnchor);
      hiddenAnchor.click(); 
      
      document.body.removeChild(hiddenAnchor);
      window.URL.revokeObjectURL(fileBlobUrl);
    } catch (error) {
      alert("Lỗi tải tệp tin hệ thống: " + error.message);
    }
  };

  // --- 📤 ĐẨY FILE LÊN (HÀNH ĐỘNG: file.upload) ---
  const handleUploadFile = () => {
    if (!selectedUploadFile) return;
    
    setIsUploading(true);
    
    const reader = new FileReader();
    reader.readAsDataURL(selectedUploadFile);
    reader.onload = () => {
      const base64Data = reader.result.split(',')[1];
      
      // Đồng bộ thiết kế cấu trúc phong cách truyền thông JSON định nghĩa trong tài liệu
      const uploadEnvelope = {
        messageId: crypto.randomUUID(),
        type: "file.upload",
        timestamp: Math.floor(Date.now() / 1000),
        source: "web-app",
        destination: machineId,
        payload: {
          targetPath: `${currentPath}\\${selectedUploadFile.name}`,
          fileBase64: base64Data
        }
      };
      
      console.log("Đã phát lệnh tải lên qua WebSocket Gateway:", uploadEnvelope);

      setTimeout(() => {
        alert(`🎉 Upload thành công file [${selectedUploadFile.name}] vào phân vùng Sandbox đích!`);
        setIsUploading(false);
        setSelectedUploadFile(null);
        loadDirectory(currentPath); 
      }, 1200);
    };
  };

  return (
    <div style={{ padding: '1rem' }}>
      <h2>📁 Hệ Thống Tải / Quản Lý Tập Tin (File Sandbox)</h2>
      <p>Thư mục Sandbox hiện tại: <strong style={{color: '#2563eb'}}>{currentPath || "Đang kết nối..."}</strong></p>

      {/* GIAO DIỆN UPLOAD ĐỒNG BỘ THEO MÔ HÌNH TRUYỀN TẢI TỆP TIN */}
      <div style={styles.uploadContainer}>
        <h4 style={{margin: '0 0 0.5rem 0', color: '#1e293b'}}>📤 Upload file vật lý vào thư mục máy đích này:</h4>
        <div style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
          <input 
            type="file" 
            onChange={(e) => setSelectedUploadFile(e.target.files[0])}
            style={styles.fileInput}
          />
          <button 
            onClick={handleUploadFile} 
            disabled={isUploading || !selectedUploadFile}
            style={{...styles.uploadBtn, opacity: (!selectedUploadFile || isUploading) ? 0.6 : 1}}
          >
            {isUploading ? '⏳ Đang truyền dữ liệu mạng LAN...' : 'Gửi tập tin (file.upload) 🚀'}
          </button>
        </div>
      </div>

      {errorMessage && <div style={{ color: '#ef4444', backgroundColor: '#fef2f2', padding: '0.75rem', borderRadius: '6px', margin: '1rem 0', border: '1px solid #fee2e2', fontWeight: '500' }}>⚠️ {errorMessage}</div>}
      
      {isLoading ? (
        <div style={{padding: '2rem 0'}}>🔄 Đang truy xuất luồng lưu trữ đĩa cục bộ qua cấu trúc mạng...</div>
      ) : (
        <table border="1" cellPadding="10" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem', borderColor: '#e2e8f0' }}>
          <thead>
            <tr style={{ backgroundColor: '#f1f5f9' }}>
              <th align="left">Tên File / Thư mục</th>
              <th align="left">Loại</th>
              <th align="right">Dung lượng (Bytes)</th>
              <th align="left">Ngày cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {fileList.map((item, index) => (
              <tr key={index} style={{ cursor: 'pointer', borderBottom: '1px solid #e2e8f0' }} onClick={() => handleItemClick(item)}>
                <td>{item.isDir ? `📁 ${item.name}` : `📄 ${item.name}`}</td>
                <td>{item.isDir ? "Thư mục" : "Tập tin"}</td>
                <td align="right">{item.isDir ? "-" : item.size.toLocaleString()}</td>
                <td>{item.lastModified}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const styles = {
  uploadContainer: { backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px dashed #cbd5e1', marginBottom: '1.5rem' },
  fileInput: { padding: '0.4rem', border: '1px solid #cbd5e1', borderRadius: '4px', backgroundColor: 'white' },
  uploadBtn: { backgroundColor: '#2563eb', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }
};

export default FileDownload;