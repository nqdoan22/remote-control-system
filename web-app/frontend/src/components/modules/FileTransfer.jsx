import React, { useState, useEffect } from 'react';
import { fileActionApi, uploadFileApi, isWsError, getWsErrorMessage, getWsData } from '../../services/api';

/**
 * FileTransfer Module - Duyệt thư mục Sandbox & Upload/Download tệp.
 * file.list / file.download / file.upload (api_contract.md) - KHÔNG có cơ chế
 * chunk theo giao thức: mỗi file tối đa 50MB, truyền base64 trong 1 request/response.
 */
const FileTransfer = ({ selectedMachine }) => {
  const [currentPath, setCurrentPath] = useState('C:\\RemoteControl\\'); // Sandbox mặc định
  const [fileList, setFileList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [transferStatus, setTransferStatus] = useState('');

  useEffect(() => {
    setCurrentPath('C:\\RemoteControl\\');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMachine]);

  useEffect(() => {
    fetchDirectoryContent(currentPath);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMachine, currentPath]);

  // Lấy danh sách File/Thư mục (file.list)
  const fetchDirectoryContent = async (path) => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      const res = await fileActionApi(selectedMachine.machineId, 'list', path);
      if (isWsError(res)) {
        alert('Không thể mở thư mục: ' + getWsErrorMessage(res));
      } else {
        // payload.data.entries: [{ name, type: 'file'|'directory', sizeBytes, modifiedAt }]
        setFileList(getWsData(res).entries || []);
      }
    } catch (err) {
      alert('Không thể mở thư mục: ' + (err?.detail || 'Không rõ nguyên nhân'));
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (item) => {
    if (item.type === 'directory') {
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

  // 📥 TẢI FILE TỪ CLIENT VỀ ADMIN (file.download - single shot, tối đa 50MB)
  const handleDownloadFile = async (fileName) => {
    if (!selectedMachine) return;
    const fullFilePath = currentPath.endsWith('\\') ? `${currentPath}${fileName}` : `${currentPath}\\${fileName}`;
    setTransferStatus(`Đang tải file "${fileName}" từ Client...`);

    try {
      const res = await fileActionApi(selectedMachine.machineId, 'download', fullFilePath);
      if (isWsError(res)) {
        setTransferStatus('');
        alert('Lỗi tải file: ' + getWsErrorMessage(res));
        return;
      }
      // payload.data: { filename, content (base64), sizeBytes, mimeType }
      const { filename, content, mimeType } = getWsData(res);
      const link = document.createElement('a');
      link.href = `data:${mimeType || 'application/octet-stream'};base64,${content}`;
      link.download = filename || fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTransferStatus('🎉 Tải file hoàn tất!');
      setTimeout(() => setTransferStatus(''), 3000);
    } catch (err) {
      setTransferStatus('');
      alert('Lỗi tải file: ' + (err?.detail || 'File có thể vượt quá 50MB hoặc quá thời gian chờ.'));
    }
  };

  // 📤 TẢI FILE TỪ ADMIN LÊN CLIENT (file.upload - multipart REST, backend tự encode base64)
  const handleFileUploadSelect = async (e) => {
    const file = e.target.files[0];
    e.target.value = ''; // cho phép chọn lại cùng 1 file lần sau
    if (!file || !selectedMachine) return;

    if (file.size > 50 * 1024 * 1024) {
      alert('File vượt quá giới hạn 50MB cho phép (api_contract.md - FILE_TOO_LARGE).');
      return;
    }

    const destinationPath = currentPath.endsWith('\\') ? `${currentPath}${file.name}` : `${currentPath}\\${file.name}`;
    setTransferStatus(`Đang tải file lên Client: ${file.name}...`);

    try {
      const res = await uploadFileApi(selectedMachine.machineId, destinationPath, file);
      if (isWsError(res)) {
        setTransferStatus('');
        alert('Lỗi tải file lên: ' + getWsErrorMessage(res));
        return;
      }
      setTransferStatus('🎉 Tải file lên Client hoàn tất!');
      setTimeout(() => {
        setTransferStatus('');
        fetchDirectoryContent(currentPath);
      }, 1500);
    } catch (err) {
      setTransferStatus('');
      alert('Lỗi tải file lên: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  return (
    <div style={styles.container}>
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

      <div style={styles.sandboxNotice}>
        🔒 Chỉ được thao tác trong thư mục Sandbox đã cấu hình trên Client (mặc định <code>C:\RemoteControl\</code>). Kích thước file tối đa: 50MB.
      </div>

      {transferStatus && (
        <div style={styles.progressContainer}>
          <div style={styles.progressText}>{transferStatus}</div>
        </div>
      )}

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
                    style={{ ...styles.td, cursor: item.type === 'directory' ? 'pointer' : 'default', color: item.type === 'directory' ? '#38bdf8' : '#f8fafc' }}
                    onClick={() => handleItemClick(item)}
                  >
                    {item.type === 'directory' ? '📁 ' : '📄 '} <b>{item.name}</b>
                  </td>
                  <td style={styles.td}>{item.type === 'directory' ? 'Thư mục' : 'Tập tin'}</td>
                  <td style={styles.td}>{item.type === 'directory' ? '--' : `${((item.sizeBytes || 0) / 1024).toFixed(1)} KB`}</td>
                  <td style={styles.td}>
                    {item.type === 'file' && (
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
  sandboxNotice: { fontSize: '0.8rem', color: '#94a3b8' },
  progressContainer: { backgroundColor: '#1e293b', padding: '10px 14px', borderRadius: '6px', border: '1px solid #0284c7' },
  progressText: { fontSize: '0.85rem', color: '#38bdf8' },
  tableWrapper: { flex: 1, overflowY: 'auto', border: '1px solid #334155', borderRadius: '8px', backgroundColor: '#1e293b' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' },
  th: { padding: '12px', backgroundColor: '#0f172a', color: '#38bdf8', borderBottom: '1px solid #334155', position: 'sticky', top: 0 },
  td: { padding: '10px 12px', borderBottom: '1px solid #334155', color: '#f8fafc' },
  tr: {},
  tdCenter: { padding: '24px', textAlign: 'center', color: '#94a3b8' },
  btnDownload: { padding: '4px 10px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }
};

export default FileTransfer;
