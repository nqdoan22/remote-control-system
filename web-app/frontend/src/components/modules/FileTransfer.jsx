import React, { useState, useEffect, useRef } from 'react';
import { fileActionApi, uploadFileApi, isWsError, getWsErrorMessage, getWsData } from '../../services/api';

/**
 * FileTransfer Module - Duyệt thư mục Sandbox & Upload/Download tệp.
 * file.list / file.download / file.upload (api_contract.md) - KHÔNG có cơ chế
 * chunk theo giao thức: mỗi file tối đa 50MB, truyền base64 trong 1 request/response.
 *
 * Gốc Sandbox mặc định trùng cấu hình Client (client-app/config.py + .env:
 * SANDBOX_DIR=C:/AgentSandbox). Sau lần file.list đầu tiên, Client trả về
 * rootPath (gốc thật của máy) -> Frontend tự khớp lại nếu máy dùng sandbox khác.
 */
const DEFAULT_SANDBOX_ROOT = 'C:\\AgentSandbox\\';

// Chuẩn hóa đường dẫn dùng ổ định cho các phép so sánh (đổi '/' thành '\', bỏ '\' cuối)
const norm = (p) => String(p || '').replace(/[\\/]+$/, '').replace(/\//g, '\\').toLowerCase();

// Lấy đường dẫn cha ('C:\AgentSandbox\sub' -> 'C:\AgentSandbox\')
const parentOf = (p) => {
  const parts = String(p || '').replace(/[\\/]+$/, '').split(/[\\/]/).filter(Boolean);
  parts.pop();
  return parts.join('\\') + '\\';
};

const FileTransfer = ({ selectedMachine }) => {
  const [currentPath, setCurrentPath] = useState(DEFAULT_SANDBOX_ROOT); // Sandbox mặc định
  const [fileList, setFileList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [transferStatus, setTransferStatus] = useState('');
  const sandboxRootRef = useRef(DEFAULT_SANDBOX_ROOT); // gốc Sandbox thật của máy hiện tại
  const currentPathRef = useRef(DEFAULT_SANDBOX_ROOT); // luôn giữ đường dẫn MỚI NHẤT để batch upload dùng (tránh stale closure)
  const folderInputRef = useRef(null);                 // input chọn thư mục (webkitdirectory)

  // Đồng bộ ref mỗi khi currentPath đổi -> upload folder luôn lấy đúng thư mục đang mở.
  useEffect(() => {
    currentPathRef.current = currentPath;
  }, [currentPath]);

  // Đảm bảo thuộc tính webkitdirectory tồn tại trên DOM (cho phép chọn CẢ THƯ MỤC).
  // Set qua ref để tránh trường hợp React bỏ qua attribute lạ trong một số phiên bản
  // khiến nút "Tải Thư Mục" chỉ mở được trình chọn file chứ không phải chọn folder.
  useEffect(() => {
    if (folderInputRef.current) {
      folderInputRef.current.setAttribute('webkitdirectory', '');
      folderInputRef.current.setAttribute('directory', '');
    }
  }, []);

  // Chỉ reset/tải lại khi ĐỔI MÁY (machineId), tránh gửi lệnh 'file.list' lặp
  // khi selectedMachine bị tạo lại do isConnected (WS) thay đổi.
  const machineId = selectedMachine?.machineId;
  useEffect(() => {
    sandboxRootRef.current = DEFAULT_SANDBOX_ROOT;
    setCurrentPath(DEFAULT_SANDBOX_ROOT);
    // Xóa danh sách cũ của máy trước đó NGAY LẬP TỨC: nếu không, khi chuyển máy
    // mà file.list của máy mới chưa kịp trả về, Admin vẫn thấy thư mục CỦA MÁY
    // CŨ và bấm tải -> path gửi xuống máy mới không tồn tại -> lỗi FILE_NOT_FOUND.
    setFileList([]);
    fetchDirectoryContent(DEFAULT_SANDBOX_ROOT);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [machineId]);

  // Điều hướng có kiểm soát: chặn đường dẫn ngoài Sandbox (không gửi lệnh)
  // và quay về gốc Sandbox nếu bị Client từ chối vì lý do INVALID_PATH.
  const navigateTo = (path) => {
    const root = norm(sandboxRootRef.current);
    const target = norm(path);
    const insideSandbox = target === root || target.startsWith(root + '\\');
    if (!insideSandbox) {
      alert('Đường dẫn nằm ngoài phạm vi Sandbox. Đã quay lại gốc Sandbox.');
      setCurrentPath(sandboxRootRef.current);
      fetchDirectoryContent(sandboxRootRef.current);
      return;
    }
    setCurrentPath(path);
    fetchDirectoryContent(path);
  };

  // Lấy danh sách File/Thư mục (file.list)
  const fetchDirectoryContent = async (path) => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      const res = await fileActionApi(selectedMachine.machineId, 'list', path);
      if (isWsError(res)) {
        const code = res.payload?.code;
        const msg = getWsErrorMessage(res);
        // Client từ chối (đường dẫn ngoài Sandbox / không hợp lệ) -> quay về gốc
        if (code === 'INVALID_PATH') {
          alert(msg + ' Đã quay lại gốc Sandbox.');
          navigateTo(sandboxRootRef.current);
          return;
        }
        alert('Không thể mở thư mục: ' + msg);
      } else {
        // payload.data: { rootPath, entries: [{ name, type, sizeBytes, modifiedAt }] }
        const data = getWsData(res);
        const root = data.rootPath;
        if (root) {
          // Ghi nhận gốc Sandbox thật để chặn "Thư Mục Cha" đi quá root
          sandboxRootRef.current = String(root).replace(/[\\/]+$/, '') + '\\';
          // Tự sửa đường dẫn mặc định nếu máy này đang dùng sandbox khác
          if (path === DEFAULT_SANDBOX_ROOT && norm(root) !== norm(DEFAULT_SANDBOX_ROOT)) {
            const actualRoot = String(root).replace(/[\\/]+$/, '') + '\\';
            setCurrentPath(actualRoot);
            return fetchDirectoryContent(actualRoot);
          }
        }
        setFileList(data.entries || []);
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
      navigateTo(newPath);
    }
  };

  const handleNavigateUp = () => {
    const root = norm(sandboxRootRef.current);
    const parent = norm(parentOf(currentPath));
    // Không cho đi lên quá gốc Sandbox
    if (parent === root || !parent.startsWith(root + '\\')) {
      navigateTo(sandboxRootRef.current);
      return;
    }
    navigateTo(parentOf(currentPath));
  };

  // 📥 TẢI FILE/THƯ MỤC TỪ CLIENT VỀ ADMIN (file.download - single shot, tối đa 50MB).
  // Thư mục được Client nén thành <tên>.zip nên handler này dùng chung cho cả 2 loại.
  const handleDownloadFile = async (fileName, isDirectory = false) => {
    if (!selectedMachine) return;
    const dir = currentPathRef.current;
    const fullFilePath = dir.endsWith('\\') ? `${dir}${fileName}` : `${dir}\\${fileName}`;
    setTransferStatus(`Đang tải "${fileName}" từ Client...`);

    try {
      const res = await fileActionApi(selectedMachine.machineId, 'download', fullFilePath);
      if (isWsError(res)) {
        setTransferStatus('');
        const code = res?.payload?.code;
        // FILE_NOT_FOUND với THƯ MỤC thường do 1 trong 2 nguyên nhân:
        //   1. Thư mục không tồn tại trên máy Client đang chọn (danh sách cũ).
        //   2. Client đang chạy PHIÊN BẢN CŨ: dispatcher cũ chỉ gọi download_file
        //      (tải file đơn), không hỗ trợ nén thư mục thành .zip nên trả đúng
        //      thông báo này. -> Đưa gợi ý rõ ràng để Admin biết phải cập nhật.
        if (code === 'FILE_NOT_FOUND' && isDirectory) {
          alert('Lỗi tải: ' + getWsErrorMessage(res) + ' — Thư mục không tồn tại trên máy Client đang chọn, hoặc Client đang chạy phiên bản cũ chưa hỗ trợ tải thư mục (nén .zip). Hãy cập nhật Client lên phiên bản mới nhất.');
          return;
        }
        alert('Lỗi tải: ' + getWsErrorMessage(res));
        return;
      }
      // payload.data: { filename, content (base64), sizeBytes, mimeType }
      const { filename, content, mimeType } = getWsData(res);
      const mime = mimeType || 'application/octet-stream';

      // KHÔNG dùng data: URL để tải vì Chrome/Edge giới hạn data URL tải xuống
      // ~2MB -> file/folder (zip) lớn hơn sẽ bị fail âm thầm dù file nhỏ vẫn tải
      // được. Giải mã base64 thành Blob rồi dùng URL.createObjectURL (không giới
      // hạn kích thước, giới hạn còn lại chỉ là 50MB của giao thức).
      const binary = atob(content);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const blobUrl = URL.createObjectURL(new Blob([bytes], { type: mime }));

      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename || fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      setTransferStatus('🎉 Tải về hoàn tất!');
      setTimeout(() => setTransferStatus(''), 3000);
    } catch (err) {
      setTransferStatus('');
      alert('Lỗi tải: ' + (err?.detail || 'Nội dung có thể vượt quá 50MB hoặc quá thời gian chờ.'));
    }
  };

  // 📤 TẢI FILE / THƯ MỤC TỪ ADMIN LÊN CLIENT (file.upload - multipart REST,
  // backend tự encode base64). Hỗ trợ chọn NHIỀU file một lúc + cả folder
  // (input webkitdirectory -> file.webkitRelativePath giữ cây thư mục).
  const MAX_UPLOAD_SIZE = 50 * 1024 * 1024; // 50MB/file (api_contract.md)

  const handleUploadSelect = (e) => {
    const files = Array.from(e.target.files || []);
    e.target.value = ''; // cho phép chọn lại cùng 1 file/folder lần sau
    if (!files.length || !selectedMachine) return;
    handleMultiUpload(files);
  };

  const handleMultiUpload = async (files) => {
    const total = files.length;
    let processed = 0;
    let failed = 0;
    let skipped = 0;
    let stopped = false;

    // Lấy đường dẫn đích MỘT LẦN từ ref (bản mới nhất tại thời điểm bắt đầu),
    // tránh dùng currentPath cũ trong closure khi React chưa kịp render lại.
    const targetDir = currentPathRef.current;
    const joinPath = (rel) =>
      targetDir.endsWith('\\') ? `${targetDir}${rel}` : `${targetDir}\\${rel}`;

    for (const file of files) {
      processed += 1;
      if (file.size > MAX_UPLOAD_SIZE) {
        skipped += 1;
        alert(`File "${file.webkitRelativePath || file.name}" vượt quá giới hạn 50MB, đã bỏ qua (FILE_TOO_LARGE).`);
        continue;
      }

      // Thư mục: webkitRelativePath = 'FolderCon/File.txt'; file thường: chỉ có name
      const relativePath = file.webkitRelativePath || file.name;
      // Chuẩn hóa dấu phân cách: webkitRelativePath dùng '/', sandbox dùng '\'
      const normalizedRel = relativePath.replace(/\//g, '\\');
      const destinationPath = joinPath(normalizedRel);
      setTransferStatus(`Đang tải (${processed}/${total}): ${relativePath}...`);

      try {
        const res = await uploadFileApi(selectedMachine.machineId, destinationPath, file);
        if (isWsError(res)) {
          const code = res?.payload?.code;
          // End User TỪ CHỐI hoặc HẾT GIỜ xác nhận quyền -> các file còn lại
          // sẽ lại mở popup xin quyền nên dừng hẳn batch (không spam popup nữa).
          if (code === 'PERMISSION_DENIED' || code === 'PERMISSION_TIMEOUT') {
            failed += 1;
            stopped = true;
            alert(`Lỗi tải "${relativePath}": ${getWsErrorMessage(res)}. Đã dừng ${total - processed} mục còn lại.`);
            break;
          }
          failed += 1;
          alert(`Lỗi tải "${relativePath}": ${getWsErrorMessage(res)}`);
        }
      } catch (err) {
        failed += 1;
        alert(`Lỗi tải "${relativePath}": ${err?.detail || 'Không rõ nguyên nhân'}`);
      }
    }

    const uploaded = processed - skipped - failed;
    const summary = stopped
      ? `⚠️ Đã dừng tải: ${uploaded}/${total} mục thành công (${failed} lỗi).`
      : failed
      ? `⚠️ Đã tải ${uploaded}/${total} mục thành công${skipped ? ` (${skipped} quá 50MB)` : ''}${failed ? ` (${failed} lỗi)` : ''}.`
      : `🎉 Đã tải ${uploaded} file/thư mục lên Client thành công!`;
    setTransferStatus(summary);
    setTimeout(() => {
      setTransferStatus('');
      fetchDirectoryContent(targetDir);
    }, 1500);
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
          onKeyDown={(e) => e.key === 'Enter' && navigateTo(currentPath)}
          style={styles.pathInput}
        />

        <label style={styles.btnUpload}>
          📤 Tải File Lên Client
          <input type="file" multiple onChange={handleUploadSelect} style={{ display: 'none' }} />
        </label>

        <label style={styles.btnUploadFolder}>
          📂 Tải Thư Mục Lên Client
          <input type="file" ref={folderInputRef} webkitdirectory="" directory="" onChange={handleUploadSelect} style={{ display: 'none' }} />
        </label>
      </div>

      <div style={styles.sandboxNotice}>
        🔒 Chỉ được thao tác trong thư mục Sandbox đã cấu hình trên Client (mặc định <code>C:\AgentSandbox\</code>). Kích thước mỗi file tối đa: 50MB. Có thể chọn nhiều file cùng lúc hoặc cả thư mục. Khi tải thư mục về, Client sẽ nén thành file <code>.zip</code> (giới hạn 50MB cho file nén).
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
                    {(item.type === 'file' || item.type === 'directory') && (
                      <button onClick={() => handleDownloadFile(item.name, item.type === 'directory')} style={styles.btnDownload}>
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
  btnUploadFolder: { padding: '8px 16px', backgroundColor: '#7c3aed', color: '#fff', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' },
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
