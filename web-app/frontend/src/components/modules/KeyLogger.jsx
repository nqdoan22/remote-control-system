import React, { useState, useEffect, useRef } from 'react';

/**
 * Keylogger Module - Theo dõi phím bấm từ máy Client theo thời gian thực
 * 
 * @param {Object} selectedMachine - Máy Client đang chọn
 * @param {Function} onSendMessage - Hàm gửi WebSocket message
 * @param {Object} lastMessage - Dữ liệu nhận từ WebSocket
 */
const Keylogger = ({ selectedMachine, onSendMessage, lastMessage }) => {
  // ===== STATE QUẢN LÝ GIAO DIỆN =====
  const [isLogging, setIsLogging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [keystrokes, setKeystrokes] = useState([]); // Danh sách các phím đã nhận
  const [filterText, setFilterText] = useState('');
  
  // Ref tự động cuộn khung văn bản xuống dưới cùng khi có phím mới
  const logContainerRef = useRef(null);

  // Reset khi chuyển máy
  useEffect(() => {
    if (isLogging) {
      stopKeylogger();
    }
    setKeystrokes([]);
    setIsLogging(false);
    setLoading(false);
  }, [selectedMachine]);

  // Cleanup: Ngắt Keylogger khi Admin thoát tab
  useEffect(() => {
    return () => {
      if (isLogging) {
        onSendMessage({
          target_machine_id: selectedMachine?.machineId,
          action: 'stop_keylogger'
        });
      }
    };
  }, [isLogging, selectedMachine]);

  // Tự động cuộn xuống cuối khung Log
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [keystrokes]);

  // ===== LẮNG NGHE LỖI VÀ DỮ LIỆU PHÍM BẤM PHÁT BẤM VỀ =====
  useEffect(() => {
    if (!lastMessage) return;

    // Phản hồi lệnh Bắt đầu / Dừng
    if (lastMessage.action === 'start_keylogger_response') {
      setLoading(false);
      if (lastMessage.status === 'success') {
        setIsLogging(true);
      } else if (lastMessage.status === 'rejected') {
        alert('❌ Người dùng trên máy Client đã TỪ CHỐI cho phép bật Keylogger![cite: 1, 2, 5]');
      } else if (lastMessage.status === 'timeout') {
        alert('⏱️ Yêu cầu xin quyền đã HẾT HẠN (Timeout 15s)![cite: 1, 2, 5, 7]');
      } else {
        alert('Lỗi khởi động Keylogger: ' + lastMessage.message);
      }
    }

    // Nhận dữ liệu phím bấm đẩy về từ Client[cite: 1, 5, 6, 8]
    if (lastMessage.action === 'keylogger_data' && isLogging) {
      const newKeys = lastMessage.data.keys || [];
      setKeystrokes(prev => [...prev, ...newKeys]);
    }
  }, [lastMessage, isLogging]);

  const startKeylogger = () => {
    if (!selectedMachine) return;
    setLoading(true);
    onSendMessage({
      target_machine_id: selectedMachine.machineId,
      action: 'start_keylogger'
    });
  };

  const stopKeylogger = () => {
    setIsLogging(false);
    setLoading(false);
    onSendMessage({
      target_machine_id: selectedMachine?.machineId,
      action: 'stop_keylogger'
    });
  };

  // Tải file Log phím bấm về máy Admin (.txt)
  const handleDownloadLog = () => {
    const rawContent = keystrokes.map(k => `[${k.timestamp}] (${k.window_title || 'N/A'}): ${k.key}`).join('\n');
    const blob = new Blob([rawContent], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `Keylog_${selectedMachine?.hostname}_${Date.now()}.txt`;
    link.click();
  };

  // Định dạng lại các phím đặc biệt (VD: [ENTER], [BACKSPACE]) để làm nổi bật trên UI
  const renderKeyItem = (keyObj, index) => {
    const isSpecial = keyObj.key.startsWith('[') && keyObj.key.endsWith(']');
    return (
      <span 
        key={index} 
        style={{
          ...styles.keyTag,
          backgroundColor: isSpecial ? '#9333ea' : '#334155',
          color: isSpecial ? '#f3e8ff' : '#f8fafc'
        }}
        title={`Cửa sổ: ${keyObj.window_title || 'Khấu hiểu'} | Thời gian: ${keyObj.timestamp}`}
      >
        {keyObj.key}
      </span>
    );
  };

  return (
    <div style={styles.container}>
      {/* BANNER NGUYÊN TẮC BẢO MẬT & XIN QUYỀN */}
      <div style={styles.privacyNotice}>
        🛡️ <b>CẢNH BÁO BẢO MẬT VÀ QUYỀN RIÊNG TƯ:</b> Tính năng Keylogger yêu cầu sự đồng ý trực tiếp (Explicit Consent) từ người dùng Client[cite: 1, 2, 5, 7].
      </div>

      {/* THANH ĐIỀU HƯỚNG BẤM TẮT/MỞ VÀ TẢI LOG */}
      <div style={styles.topBar}>
        <div style={styles.actionGroup}>
          {!isLogging ? (
            <button onClick={startKeylogger} disabled={loading} style={styles.btnStart}>
              {loading ? '⏳ Đang xin phép người dùng Client...' : '⌨️ Bắt Đầu Theo Dõi Phím'}
            </button>
          ) : (
            <button onClick={stopKeylogger} style={styles.btnStop}>
              ⏹ Dừng Ghi Phím
            </button>
          )}

          <button onClick={() => setKeystrokes([])} style={styles.btnSecondary}>
            🗑️ Xóa Nhật Ký Màn Hình
          </button>

          {keystrokes.length > 0 && (
            <button onClick={handleDownloadLog} style={styles.btnSuccess}>
              💾 Tải File Log (.txt)
            </button>
          )}
        </div>

        {isLogging && (
          <div style={styles.activeStatus}>
            <span style={styles.greenDot}></span> Đang ghi nhận thao tác phím...
          </div>
        )}
      </div>

      {/* KHU VỰC TÌM KIẾM TỪ KHÓA TRONG NỘI DUNG PHÍM */}
      <div style={styles.searchBar}>
        <input
          type="text"
          placeholder="🔍 Tìm kiếm từ khóa/ký tự trong nhật ký phím..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          style={styles.searchInput}
        />
      </div>

      {/* KHUNG BẢNG HIỂN THỊ NHẬT KÝ PHÍM (KEYLOG TERMINAL) */}
      <div style={styles.logTerminal} ref={logContainerRef}>
        {keystrokes.length === 0 ? (
          <div style={styles.emptyState}>
            {loading ? 'Đang gửi thông báo xin quyền đến Client...' : 'Chưa có dữ liệu phím nào được ghi nhận.'}
          </div>
        ) : (
          <div style={styles.keysWrapper}>
            {keystrokes
              .filter(k => k.key.toLowerCase().includes(filterText.toLowerCase()) || (k.window_title && k.window_title.toLowerCase().includes(filterText.toLowerCase())))
              .map((k, idx) => renderKeyItem(k, idx))}
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' },
  privacyNotice: { padding: '10px 14px', backgroundColor: '#3b0764', border: '1px solid #7e22ce', borderRadius: '6px', color: '#e9d5ff', fontSize: '0.85rem' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  actionGroup: { display: 'flex', gap: '8px' },
  btnStart: { padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  btnStop: { padding: '8px 16px', backgroundColor: '#dc2626', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  btnSecondary: { padding: '8px 16px', backgroundColor: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  btnSuccess: { padding: '8px 16px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  activeStatus: { display: 'flex', alignItems: 'center', gap: '8px', color: '#22c55e', fontSize: '0.85rem', fontWeight: 'bold' },
  greenDot: { width: '8px', height: '8px', backgroundColor: '#22c55e', borderRadius: '50%', display: 'inline-block' },
  searchBar: { display: 'flex' },
  searchInput: { width: '100%', padding: '8px 12px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#fff' },
  logTerminal: { flex: 1, backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px', padding: '16px', overflowY: 'auto', fontFamily: 'monospace' },
  emptyState: { textAlign: 'center', color: '#64748b', marginTop: '40px' },
  keysWrapper: { display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' },
  keyTag: { padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem', display: 'inline-block', border: '1px solid rgba(255,255,255,0.1)' }
};

export default Keylogger;