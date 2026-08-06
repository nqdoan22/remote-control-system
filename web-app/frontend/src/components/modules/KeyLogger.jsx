import React, { useState, useEffect, useRef } from 'react';
import { controlKeyloggerApi, isWsError, getWsErrorMessage } from '../../services/api';

/**
 * Keylogger Module - Theo dõi phím bấm từ máy Client theo thời gian thực.
 * keylogger.start / keylogger.stop qua REST (Sensitive Feature List). Dữ liệu
 * phím (keylogger.data) nhận qua WebSocket broadcast, payload = { entries: [{key,
 * timestamp}], windowTitle } theo api_contract.md.
 *
 * Hiển thị dạng "Transcript liên tục": phím thường gõ liền thành dòng văn bản,
 * phím đặc biệt (SPACE/ENTER/TAB/BACKSPACE) hiện dưới dạng marker/badge dễ đọc.
 */
const Keylogger = ({ selectedMachine, lastMessage }) => {
  const [isLogging, setIsLogging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [keystrokes, setKeystrokes] = useState([]); // [{ key, timestamp, windowTitle }]
  const [filterText, setFilterText] = useState('');

  const logContainerRef = useRef(null);
  const isLoggingRef = useRef(false);

  const stopKeylogger = async (silent = false) => {
    setIsLogging(false);
    isLoggingRef.current = false;
    setLoading(false);
    if (!selectedMachine) return;
    try {
      await controlKeyloggerApi(selectedMachine.machineId, 'stop');
    } catch (err) {
      if (!silent) alert('Lỗi dừng Keylogger: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  // Reset khi đổi máy / rời trang -> tự động dừng keylogger
  useEffect(() => {
    setKeystrokes([]);
    return () => {
      if (isLoggingRef.current) stopKeylogger(true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMachine?.machineId]);

  // Tự động cuộn xuống cuối khung Log
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [keystrokes]);

  // Nhận dữ liệu phím bấm đẩy về từ Client (keylogger.data - event định kỳ)
  useEffect(() => {
    if (!lastMessage || !isLogging) return;
    if (lastMessage.type === 'keylogger.data') {
      const { entries = [], windowTitle } = lastMessage.payload || {};
      const tagged = entries.map((e) => ({ ...e, windowTitle }));
      setKeystrokes((prev) => [...prev, ...tagged]);
    }
  }, [lastMessage, isLogging]);

  const startKeylogger = async () => {
    if (!selectedMachine) return;
    setLoading(true);
    try {
      const res = await controlKeyloggerApi(selectedMachine.machineId, 'start');
      setLoading(false);
      if (isWsError(res)) {
        alert(getWsErrorMessage(res));
      } else {
        setIsLogging(true);
        isLoggingRef.current = true;
      }
    } catch (err) {
      setLoading(false);
      alert('Lỗi khởi động Keylogger: ' + (err?.detail || 'Không rõ nguyên nhân'));
    }
  };

  // Gom các phím liên tiếp trong cùng cửa sổ & gần nhau về thời gian thành từng
  // cụm để hiển thị thành những khối "phiên gõ" liên tục, dễ đọc hơn.
  const buildGroups = (items) => {
    // Khoảng dừng gõ vượt ngưỡng này -> coi là cụm gõ mới (dòng/câu mới).
    const TIME_GROUP_GAP_SECONDS = 3;
    const groups = [];
    let current = null;

    const flush = () => {
      if (current && current.keys.length) groups.push(current);
      current = null;
    };

    for (const k of items) {
      const windowTitle = k.windowTitle || 'N/A';
      if (
        !current
        || current.windowTitle !== windowTitle
        || (current.lastTs && k.timestamp - current.lastTs > TIME_GROUP_GAP_SECONDS)
      ) {
        flush();
        current = {
          id: `g${groups.length}-${k.timestamp}-${windowTitle}`,
          timestamp: k.timestamp,
          windowTitle,
          keys: [],
          lastTs: k.timestamp,
        };
      }
      current.keys.push(k);
      current.lastTs = k.timestamp;
    }
    flush();
    return groups;
  };

  const formatTime = (ts) => {
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Gom các phím liên tiếp trong cùng cửa sổ & gần nhau về thời gian thành từ/câu
  // (dùng cho file log .txt khi tải về).
  const buildKeylogTranscript = (keystrokes) => {
    const TIME_GROUP_GAP_SECONDS = 2;
    const groups = [];
    let current = null;

    const pushGroup = () => {
      if (current && current.text) groups.push(current);
      current = null;
    };

    for (const k of keystrokes) {
      const key = k.key || '';
      const windowTitle = k.windowTitle || 'N/A';

      if (
        !current
        || current.windowTitle !== windowTitle
        || (current.lastTs !== null && k.timestamp - current.lastTs > TIME_GROUP_GAP_SECONDS)
      ) {
        pushGroup();
        current = { timestamp: k.timestamp, windowTitle, text: '', lastTs: k.timestamp };
      }

      switch (key) {
        case 'BACKSPACE': {
          const trimmed = current.text.replace(/\s+$/, '');
          current.text = trimmed.length ? trimmed.slice(0, -1) : '';
          break;
        }
        case 'ENTER':
          current.text += '\n';
          break;
        case 'TAB':
          current.text += '\t';
          break;
        case 'SPACE':
          current.text += ' ';
          break;
        default:
          current.text += key;
      }
      current.lastTs = k.timestamp;
    }
    pushGroup();

    return groups
      .map((g) => `[${g.timestamp}] (${g.windowTitle}):\n${g.text}`)
      .join('\n\n');
  };

  // Tải file Log phím bấm về máy Admin (.txt)
  const handleDownloadLog = () => {
    const rawContent = buildKeylogTranscript(keystrokes);
    const blob = new Blob([rawContent], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `Keylog_${selectedMachine?.hostname}_${Date.now()}.txt`;
    link.click();
  };

  // Render một phím trong dòng transcript liên tục
  const renderKey = (k, i) => {
    const key = k.key || '';
    const title = `Cửa sổ: ${k.windowTitle || 'Không rõ'} | Thời gian: ${k.timestamp}`;

    switch (key) {
      case 'SPACE':
        // Khoảng trắng thật (giống gõ trên bàn phím), không dùng ký hiệu ␣
        return <span key={i} title={title}>{' '}</span>;
      case 'ENTER':
        // Xuống dòng + marker xuống dòng
        return <span key={i} style={styles.mkEnter} title={title}>↵</span>;
      case 'TAB':
        return <span key={i} style={styles.mkTabs} title={title}>⇥</span>;
      case 'BACKSPACE':
        return <span key={i} style={styles.mkBksp} title={title}>⌫</span>;
      default:
        if (key.startsWith('[') && key.endsWith(']')) {
          return <span key={i} style={styles.mkSpecial} title={title}>{key}</span>;
        }
        return <span key={i} style={styles.mkChar} title={title}>{key}</span>;
    }
  };

  // Lọc theo từ khóa (bỏ qua chuỗi rỗng / chỉ toàn khoảng trắng)
  const filteredKeystrokes = keystrokes.filter((k) => {
    const q = filterText.trim().toLowerCase();
    if (!q) return true;
    return (
      (k.key && k.key.toLowerCase().includes(q))
      || (k.windowTitle && k.windowTitle.toLowerCase().includes(q))
    );
  });

  const groups = buildGroups(filteredKeystrokes);

  return (
    <div style={styles.container}>
      <div style={styles.privacyNotice}>
        <LockIcon />
        <span>
          <b>CẢNH BÁO BẢO MẬT:</b> Tính năng Keylogger yêu cầu sự đồng ý trực tiếp
          (Explicit Consent) từ người dùng Client.
        </span>
      </div>

      <div style={styles.topBar}>
        <div style={styles.actionGroup}>
          {!isLogging ? (
            <button
              onClick={startKeylogger}
              disabled={loading}
              style={{ ...styles.btn, ...styles.btnStart }}
              className="kl-btn"
            >
              <PlayIcon />
              {loading ? 'Đang xin phép...' : 'Bắt Đầu Theo Dõi'}
            </button>
          ) : (
            <button
              onClick={() => stopKeylogger()}
              style={{ ...styles.btn, ...styles.btnStop }}
              className="kl-btn"
            >
              <StopIcon />
              Dừng Ghi Phím
            </button>
          )}

          <button
            onClick={() => setKeystrokes([])}
            style={{ ...styles.btn, ...styles.btnSecondary }}
            className="kl-btn"
          >
            <TrashIcon />
            Xóa Nhật Ký
          </button>

          {keystrokes.length > 0 && (
            <button
              onClick={handleDownloadLog}
              style={{ ...styles.btn, ...styles.btnSuccess }}
              className="kl-btn"
            >
              <DownloadIcon />
              Tải Log (.txt)
            </button>
          )}
        </div>

        <div style={styles.statusArea}>
          {isLogging ? (
            <div style={styles.activeStatus}>
              <span className="kl-dot" style={styles.greenDot}></span>
              Đang ghi nhận thao tác phím...
            </div>
          ) : (
            <div style={styles.inactiveStatus}>
              <span style={styles.grayDot}></span>
              Đang dừng
            </div>
          )}
        </div>
      </div>

      <div style={styles.searchBar}>
        <div style={styles.searchInputWrap}>
          <SearchIcon />
          <input
            type="text"
            placeholder="Tìm kiếm từ khóa / ký tự trong nhật ký phím..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={styles.searchInput}
          />
        </div>
      </div>

      <div style={styles.logTerminal} ref={logContainerRef}>
        {keystrokes.length === 0 ? (
          <div style={styles.emptyState}>
            {loading
              ? 'Đang gửi thông báo xin quyền đến Client...'
              : 'Chưa có dữ liệu phím nào được ghi nhận.'}
          </div>
        ) : groups.length === 0 ? (
          <div style={styles.emptyState}>
            Không tìm thấy kết quả phù hợp với từ khóa "{filterText}".
          </div>
        ) : (
          <div>
            {groups.map((g) => (
              <div key={g.id} style={styles.group}>
                <div style={styles.groupHeader}>
                  <span style={styles.groupWindow}>{g.windowTitle}</span>
                  <span style={styles.groupTime}>{formatTime(g.timestamp)}</span>
                </div>
                <div style={styles.groupBody}>
                  {g.keys.map((k, i) => renderKey(k, i))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        .kl-btn { transition: filter 0.15s ease, transform 0.1s ease; }
        .kl-btn:hover { filter: brightness(1.15); }
        .kl-btn:active { transform: translateY(1px); }
        .kl-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .kl-dot { animation: kl-blink 1.2s ease-in-out infinite; }
        @keyframes kl-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
};

// ===== SVG ICONS (gọn gàng, không rối mắt như emoji) =====
const PlayIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
);
const StopIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
);
const TrashIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /></svg>
);
const DownloadIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>
);
const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
);
const LockIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
);

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' },
  privacyNotice: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '10px 14px', backgroundColor: '#1e1b4b',
    border: '1px solid #4c1d95', borderRadius: '8px',
    color: '#c4b5fd', fontSize: '0.82rem',
  },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' },
  actionGroup: { display: 'flex', gap: '8px', flexWrap: 'wrap' },
  btn: {
    display: 'inline-flex', alignItems: 'center', gap: '6px',
    padding: '8px 14px', border: 'none', borderRadius: '6px',
    cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem',
    color: '#fff',
  },
  btnStart: { backgroundColor: '#0284c7' },
  btnStop: { backgroundColor: '#dc2626' },
  btnSecondary: { backgroundColor: '#334155' },
  btnSuccess: { backgroundColor: '#16a34a' },
  statusArea: { display: 'flex', alignItems: 'center' },
  activeStatus: { display: 'flex', alignItems: 'center', gap: '7px', color: '#22c55e', fontSize: '0.82rem', fontWeight: '600' },
  inactiveStatus: { display: 'flex', alignItems: 'center', gap: '7px', color: '#94a3b8', fontSize: '0.82rem' },
  greenDot: { width: '9px', height: '9px', backgroundColor: '#22c55e', borderRadius: '50%', display: 'inline-block', boxShadow: '0 0 6px #22c55e' },
  grayDot: { width: '9px', height: '9px', backgroundColor: '#64748b', borderRadius: '50%', display: 'inline-block' },
  searchBar: { display: 'flex' },
  searchInputWrap: {
    display: 'flex', alignItems: 'center', gap: '8px', flex: 1,
    backgroundColor: '#1e293b', border: '1px solid #334155',
    borderRadius: '8px', padding: '0 12px', color: '#94a3b8',
  },
  searchInput: {
    flex: 1, padding: '9px 0', backgroundColor: 'transparent',
    border: 'none', outline: 'none', color: '#f8fafc', fontSize: '0.88rem',
  },
  logTerminal: {
    flex: 1, backgroundColor: '#0b1120', border: '1px solid #1e293b',
    borderRadius: '10px', padding: '14px 16px', overflowY: 'auto',
    fontFamily: "'JetBrains Mono', 'Consolas', 'Courier New', monospace",
    minHeight: 0,
  },
  emptyState: { textAlign: 'center', color: '#64748b', marginTop: '48px', fontSize: '0.9rem' },

  // Transcript groups
  group: { marginBottom: '14px', paddingBottom: '10px', borderBottom: '1px dashed #1e293b' },
  groupHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', marginBottom: '5px' },
  groupWindow: { fontSize: '0.72rem', color: '#38bdf8', backgroundColor: '#0c4a6e', padding: '2px 8px', borderRadius: '10px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '70%' },
  groupTime: { fontSize: '0.7rem', color: '#475569', flexShrink: 0 },
  groupBody: { fontSize: '0.95rem', lineHeight: '1.75', color: '#e2e8f0', wordBreak: 'break-word', minHeight: '1.5em' },

  // Key markers
  mkChar: { color: '#e2e8f0' },
  mkEnter: { display: 'block', color: '#818cf8', backgroundColor: '#312e81', borderRadius: '3px', padding: '0 4px', margin: '1px 0', fontSize: '0.75rem', width: 'fit-content' },
  mkTabs: { color: '#f59e0b', backgroundColor: '#451a03', borderRadius: '3px', padding: '0 4px', margin: '0 1px', fontSize: '0.8rem' },
  mkBksp: { color: '#fb7185', backgroundColor: '#4c0519', borderRadius: '3px', padding: '0 4px', margin: '0 1px', fontSize: '0.8rem' },
  mkSpecial: { color: '#c4b5fd', backgroundColor: '#2e1065', borderRadius: '3px', padding: '0 4px', margin: '0 1px', fontSize: '0.8rem' },
};

export default Keylogger;
