// frontend/src/components/modules/FileTransfer.jsx
import React, { useState, useEffect, useRef } from 'react';

const FileTransfer = ({ machineId, sendCommand, isConnected }) => {
    const [files, setFiles] = useState([]);
    const [currentPath, setCurrentPath] = useState('C:\\AgentSandbox\\');
    const [status, setStatus] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const fileInputRef = useRef(null);

    const fetchFiles = async (path) => {
        setIsLoading(true);
        setStatus('');
        try {
            const res = await sendCommand('file.list', machineId, { path });
            if (res.success) {
                setFiles(res.data.entries);
                setCurrentPath(path);
            }
        } catch (err) {
            setStatus(`Lỗi: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { if (isConnected) fetchFiles(currentPath); }, [isConnected]);

    const handleDownload = async (filename) => {
        setStatus(`Đang tải xuống ${filename}...`);
        try {
            const res = await sendCommand('file.download', machineId, { path: `${currentPath}${filename}` });
            if (res.success) {
                const link = document.createElement('a');
                link.href = `data:${res.data.mimeType};base64,${res.data.content}`;
                link.download = res.data.filename;
                link.click();
                setStatus(`Đã tải xong: ${res.data.filename}`);
            }
        } catch (err) {
            setStatus(`Lỗi Download: ${err.message}`);
        }
    };

    const handleUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Giới hạn 50MB theo API Contract
        if (file.size > 50 * 1024 * 1024) {
            setStatus('File quá lớn. Tối đa 50MB.');
            return;
        }

        setStatus(`Đang tải lên ${file.name}...`);
        const reader = new FileReader();
        reader.onload = async () => {
            const base64Content = reader.result.split(',')[1];
            try {
                const res = await sendCommand('file.upload', machineId, {
                    destinationPath: `${currentPath}${file.name}`,
                    filename: file.name,
                    content: base64Content,
                    sizeBytes: file.size
                });
                if (res.success) {
                    setStatus(`Upload thành công: ${file.name}`);
                    fetchFiles(currentPath);
                }
            } catch (err) {
                setStatus(`Lỗi Upload: ${err.message}`);
            }
        };
        reader.readAsDataURL(file);
    };

    return (
        <div style={{ padding: '20px' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>Quản lý Tệp tin (Sandbox)</h3>
            <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '20px' }}>
                Thư mục hiện tại: <strong>{currentPath}</strong>
            </p>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <button onClick={() => fetchFiles(currentPath)} disabled={isLoading} style={{ padding: '8px 16px', cursor: 'pointer' }}>🔄 Làm mới</button>
                
                <input type="file" ref={fileInputRef} onChange={handleUpload} style={{ display: 'none' }} />
                <button onClick={() => fileInputRef.current.click()} style={{ padding: '8px 16px', backgroundColor: '#10b981', color: 'white', border: 'none', cursor: 'pointer' }}>
                    ⬆️ Tải file lên
                </button>
            </div>

            {status && <div style={{ padding: '10px', backgroundColor: '#f3f4f6', marginBottom: '15px' }}>{status}</div>}

            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead style={{ backgroundColor: '#f3f4f6' }}>
                    <tr>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Tên Tệp/Thư mục</th>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Loại</th>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Kích thước</th>
                        <th style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    {files.map((file, idx) => (
                        <tr key={idx}>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{file.name}</td>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{file.type === 'directory' ? '📁 Folder' : '📄 File'}</td>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>{file.sizeBytes ? `${(file.sizeBytes / 1024).toFixed(1)} KB` : '-'}</td>
                            <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>
                                {file.type === 'file' && (
                                    <button onClick={() => handleDownload(file.name)} style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '4px 8px', borderRadius: '4px' }}>⬇️ Tải về</button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default FileTransfer;