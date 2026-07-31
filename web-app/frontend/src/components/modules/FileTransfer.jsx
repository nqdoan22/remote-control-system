import React, { useState, useEffect } from 'react';

/**
 * FileTransfer Module - Quản lý Cây Thư Mục & Chuyển File Cắt Mảnh (Chunking File Transfer)
 */
const FileTransfer = ({ selectedMachine, onSendMessage, lastMessage }) => {
  // ===== STATE QUẢN LÝ ĐIỀU HƯỚNG CÂY THƯ MỤC =====
  const [currentPath, setCurrentPath] = useState('C:\\'); // Thư mục mặc định
  const [fileList, setFileList] = useState([]);
  const [loading, setLoading] = useState(false);

  // ===== STATE QUẢN LÝ TIẾN TRÌNH TRUYỀN FILE (CHUNKING) =====
  const [transferProgress, setTransferProgress] = useState(0); // 0% -> 100%
  const [transferStatus, setTransferStatus] = useState(''); // Thông báo trạng thái

  // Lấy danh sách File/Thư mục khi đổi đường dẫn hoặc chọn máy mới
  useEffect(() => {
    fetchDirectoryContent(currentPath);
  }, [selectedMachine, currentPath]);

  // LẮNG NGHE PHẢN HỒI DỮ LIỆU FILE VÀ TIẾN TRÌNH TỪ WEBSOCKET
  useEffect(() => {
    if (!lastMessage) return;

    // 1. Phản hồi Lấy danh sách file trong thư mục[cite: 1, 6, 7]
    if (lastMessage.action === 'list_directory_response') {
      setLoading(false);
      if (lastMessage.status === 'success') {
        setFileList(lastMessage.data.items || []);
      } else {
        alert('Không thể mở thư mục: ' + lastMessage.message);
      }
    }

    // 2. Nhận từng mảnh Chunk File Tải từ Client về Admin (Download)
    if (lastMessage.action === 'download_file_chunk') {
      const { chunk_index, total_chunks, data_base64, file_name } = lastMessage.payload;
      const progress = Math.round(((chunk_index + 1) / total_chunks) * 100);
      setTransferProgress(progress);
      setTransferStatus(`Đang tải file "${file_name}": ${progress}% (${chunk_index + 1}/${total_chunks} chunks)`);

      // Khi đã nhận đủ 100% các mảnh
      if (chunk_index + 1 === total_chunks) {
        setTransferStatus('🎉 Tải file hoàn tất!');
        setTimeout(() => setTransferProgress(0), 3000);
      }
    }
  }, [lastMessage]);

  // Gửi lệnh lấy danh sách File/Thư mục
  const fetchDirectoryContent = (path) => {
    if (!selectedMachine) return;
    setLoading(true);
    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'list_directory',
      payload: { path: path }
    });
  };

  // Điều hướng chuyển thư mục con hoặc quay lại thư mục cha
  const handleItemClick = (item) => {
    if (item.is_directory) {
      const newPath = currentPath.endsWith('\\') 
        ? `${currentPath}${item.name}` 
        : `${currentPath}\\${item.name}`;
      setCurrentPath(newPath);
    }
  };

  const handleNavigateUp = () => {
    const parts = currentPath.split('\\').filter(Boolean);
    if (parts.length > 1) {
      parts.pop();
      setCurrentPath(parts.join('\\') + '\\');
    }
  };

  // 📥 TẢI FILE TỪ CLIENT VỀ ADMIN (DOWNLOAD WITH CHUNKING)
  const handleDownloadFile = (fileName) => {
    const fullFilePath = currentPath.endsWith('\\') ? `${currentPath}${fileName}` : `${currentPath}\\${fileName}`;
    setTransferProgress(1);
    setTransferStatus(`Khởi tạo tiến trình tải file: ${fileName}...`);

    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'request_download_file',
      payload: { file_path: fullFilePath, chunk_size: 64 * 1024 } // Mảnh 64KB
    });
  };

  // 📤 TẢI FILE TỪ ADMIN LÊN CLIENT (UPLOAD WITH CHUNKING)
  const handleFileUploadSelect = (e) => {
    const file = e.target.files[0];
    if (!file || !selectedMachine) return;

    const CHUNK_SIZE = 64 * 1024; // Cắt thành từng mảnh 64KB
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    const reader = new FileReader();

    let currentChunkIndex = 0;

    reader.onload = (event) => {
      const base64Data = btoa(event.target.result);

      // Gửi từng mảnh Chunk qua WebSocket[cite: 1, 4, 8]
      onSendMessage({
        target_machine_id: selectedMachine.machineId,
        action: 'upload_file_chunk',
        payload: {
          destination_path: currentPath,
          file_name: file.name,
          chunk_index: currentChunkIndex,
          total_chunks: totalChunks,
          data_base64: base64Data
        }
      });

      currentChunkIndex++;
      const progress = Math.round((currentChunkIndex / totalChunks) * 100);
      setTransferProgress(progress);
      setTransferStatus(`Đang tải file lên Client: ${progress}%`);

      if (currentChunkIndex < totalChunks) {
        readNextChunk();
      } else {
        setTransferStatus('🎉 Tải file lên Client hoàn tất!');
        setTimeout(() => {
          setTransferProgress(0);
          fetchDirectoryContent(currentPath); // Làm mới danh sách file
        }, 2000);
      }
    };

    const readNextChunk = () => {
      const start = currentChunkIndex * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file.size);
      const slice = file.slice(start, end);
      reader.readAsBinaryString(slice);
    };

    readNextChunk(); // Khởi chạy vòng lặp cắt mảnh
  };

  return (
    <div style={styles.container}>
      {/* THANH ĐIỀU HƯỚNG ĐƯỜNG DẪN (PATH BAR) */}
      <div style={styles.topBar}>
        <button onClick={handleNavigateUp} style={styles.btnSecondary}>
          ⬆️ Thư Mục Cha
        </button>

        <input
          type="text"
          value={currentPath}
          onChange={(e) => setCurrentPath(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && fetchDirectoryContent(currentPath)}
          style={styles.pathInput}
        />

        <label style={styles.btnUpload}>
          📤 Tải File Lên Client
          <input type="file" onChange={handleFileUploadSelect} style={{ display: 'none' }} />
        </label>
      </div>

      {/* THANH TIẾN TRÌNH CHUYỂN FILE (PROGRESS BAR) */}
      {transferProgress > 0 && (
        <div style={styles.progressContainer}>
          <div style={styles.progressText}>{transferStatus}</div>
          <div style={styles.progressBarTrack}>
            <div style={{ ...styles.progressBarFill, width: `${transferProgress}%` }}></div>
          </div>
        </div>
      )}

      {/* BẢNG BÀN GIAO FILE & THƯ MỤC */}
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Tên File / Thư Mục</th>
              <th style={styles.th}>Loại</th>
              <th style={styles.th}>Kích Thước</th>
              <th style={styles.th}>Thao Tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="4" style={styles.tdCenter}>Đang quét thư mục trên Client...</td></tr>
            ) : fileList.length === 0 ? (
              <tr><td colSpan="4" style={styles.tdCenter}>Thư mục rỗng.</td></tr>
            ) : (
              fileList.map((item, index) => (
                <tr key={index} style={styles.tr}>
                  <td 
                    style={{ ...styles.td, cursor: item.is_directory ? 'pointer' : 'default', color: item.is_directory ? '#38bdf8' : '#f8fafc' }}
                    onClick={() => handleItemClick(item)}
                  >
                    {item.is_directory ? '📁 ' : '📄 '} <b>{item.name}</b>
                  </td>
                  <td style={styles.td}>{item.is_directory ? 'Thư mục' : 'Tập tin'}</td>
                  <td style={styles.td}>{item.is_directory ? '--' : `${(item.size_bytes / 1024).toFixed(1)} KB`}</td>
                  <td style={styles.td}>
                    {!item.is_directory && (
                      <button onClick={() => handleDownloadFile(item.name)} style={styles.btnDownload}>
                        📥 Tải Về Admin
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' },
  topBar: { display: 'flex', gap: '8px', alignItems: 'center' },
  btnSecondary: { padding: '8px 12px', backgroundColor: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  pathInput: { flex: 1, padding: '8px 12px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#fff', fontFamily: 'monospace' },
  btnUpload: { padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' },
  progressContainer: { backgroundColor: '#1e293b', padding: '10px 14px', borderRadius: '6px', border: '1px solid #0284c7' },
  progressText: { fontSize: '0.85rem', color: '#38bdf8', marginBottom: '6px' },
  progressBarTrack: { height: '8px', backgroundColor: '#0f172a', borderRadius: '4px', overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: '#0284c7', transition: 'width 0.2s ease' },
  tableWrapper: { flex: 1, overflowY: 'auto', border: '1px solid #334155', borderRadius: '8px', backgroundColor: '#1e293b' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' },
  th: { padding: '12px', backgroundColor: '#0f172a', color: '#38bdf8', borderBottom: '1px solid #334155', position: 'sticky', top: 0 },
  td: { padding: '10px 12px', borderBottom: '1px solid #334155', color: '#f8fafc' },
  tdCenter: { padding: '24px', textAlign: 'center', color: '#94a3b8' },
  btnDownload: { padding: '4px 10px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }
};

export default FileTransfer;