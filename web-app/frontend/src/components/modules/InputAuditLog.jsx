import React, { useState, useEffect, useRef } from 'react';
import { controlInputAuditApi, isWsError, getWsErrorMessage } from '../../services/api';

/**
 * Input Audit Log Module - Theo dõi phím bấm từ máy Client theo thời gian thực.
 * input_audit.start / input_audit.stop qua REST (Sensitive Feature List). Dữ liệu
 * phím (input_audit.data) nhận qua WebSocket broadcast, payload = { entries: [{key,
 * timestamp}], windowTitle } theo api_contract.md.
 */
const InputAuditLog = ({ selectedMachine, lastMessage }) => {
  const [isLogging, setIsLogging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [keystrokes, setKeystrokes] = useState([]); // [{ key, timestamp, windowTitle }]
  const [filterText, setFilterText] = useState('');

  const logContainerRef = useRef(null);
  const isLoggingRef = useRef(false);

  const stopInputAudit = async (silent = false) => {
    setIsLogging(false);
    isLoggingRef.current = false;
    setLoading(false);
    if (!selectedMachine) return;
    try {
      await controlInputAuditApi(selectedMachine.machineId, 'stop');
    } catch (err) {
      if (!silent) alert('Lỗi dừng Input Audit Log: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  // Reset khi đổi máy / rời trang -> tự động dừng input audit log
  useEffect(() => {
    setKeystrokes([]);
    return () => {
      if (isLoggingRef.current) stopInputAudit(true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMachine?.machineId]);

  // Tự động cuộn xuống cuối khung Log
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [keystrokes]);

  // Nhận dữ liệu phím bấm đẩy về từ Client (input_audit.data - event định kỳ)
  useEffect(() => {
    if (!lastMessage || !isLogging) return;
    if (lastMessage.type === 'input_audit.data') {
      const { entries = [], windowTitle } = lastMessage.payload || {};
      const tagged = entries.map((e) => ({ ...e, windowTitle }));
      setKeystrokes((prev) => [...prev, ...tagged]);
    }
  }, [lastMessage, isLogging]);

  const startInputAudit = async () => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      const res = await controlInputAuditApi(selectedMachine.machineId, 'start');
      setLoading(false);
      if (isWsError(res)) {
        alert(getWsErrorMessage(res));
      } else {
        setIsLogging(true);
        isLoggingRef.current = true;
      }
    } catch (err) {
      setLoading(false);
      alert('Lỗi khởi động Input Audit Log: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  // Tải file Log phím bấm về máy Admin (.txt)
  const handleDownloadLog = () => {
    const rawContent = keystrokes.map(k => `[${k.timestamp}] (${k.windowTitle || 'N/A'}): ${k.key}`).join('\n');
    const blob = new Blob([rawContent], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `InputAuditLog_${selectedMachine?.hostname}_${Date.now()}.txt`;
    link.click();
  };

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
        title={`Cửa sổ: ${keyObj.windowTitle || 'Không rõ'} | Thời gian: ${keyObj.timestamp}`}
      >
        {keyObj.key}
      </span>
    );
  };

  return (
    <div style={styles.container}>
      <div style={styles.privacyNotice}>
        🛡️ <b>CẢNH BÁO BẢO MẬT VÀ QUYỀN RIÊNG TƯ:</b> Tính năng Input Audit Log yêu cầu sự đồng ý trực tiếp (Explicit Consent) từ người dùng Client.
      </div>

      <div style={styles.topBar}>
        <div style={styles.actionGroup}>
          {!isLogging ? (
            <button onClick={startInputAudit} disabled={loading} style={styles.btnStart}>
              {loading ? '⏳ Đang xin phép người dùng Client...' : '⌨️ Bắt Đầu Theo Dõi Phím'}
            </button>
          ) : (
            <button onClick={() => stopInputAudit()} style={styles.btnStop}>
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

      <div style={styles.searchBar}>
        <input
          type="text"
          placeholder="🔍 Tìm kiếm từ khóa/ký tự trong nhật ký phím..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          style={styles.searchInput}
        />
      </div>

      <div style={styles.logTerminal} ref={logContainerRef}>
        {keystrokes.length === 0 ? (
          <div style={styles.emptyState}>
            {loading ? 'Đang gửi thông báo xin quyền đến Client...' : 'Chưa có dữ liệu phím nào được ghi nhận.'}
          </div>
        ) : (
          <div style={styles.keysWrapper}>
            {keystrokes
              .filter(k => k.key.toLowerCase().includes(filterText.toLowerCase()) || (k.windowTitle && k.windowTitle.toLowerCase().includes(filterText.toLowerCase())))
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

export default InputAuditLog;
