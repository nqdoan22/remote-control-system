import React, { useState, useEffect } from 'react';
import { takeScreenshotApi, isWsError, getWsErrorMessage, getWsData } from '../../services/api';

/**
 * Screenshot Module - Chụp ảnh màn hình máy Client.
 * screen.screenshot KHÔNG nằm trong Sensitive Feature List (api_contract.md),
 * nên không cần Popup xin quyền / không có PERMISSION_TIMEOUT.
 *
 * @param {Object} selectedMachine - Thông tin máy Client được chọn
 */
const Screenshot = ({ selectedMachine }) => {
  const [imageData, setImageData] = useState(null); // Chuỗi ảnh Base64 (data:image/jpeg;base64,...)
  const [loading, setLoading] = useState(false);
  const [capturedAt, setCapturedAt] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Reset dữ liệu ảnh khi Admin đổi sang máy Client khác
  useEffect(() => {
    setImageData(null);
    setCapturedAt(null);
    setErrorMsg('');
    setLoading(false);
  }, [selectedMachine]);

  const handleTakeScreenshot = async () => {
    if (!selectedMachine) return;
    setLoading(true);
    setErrorMsg('');

    try {
      // REST -> Backend -> Gateway (screen.screenshot) -> Client App
      const res = await takeScreenshotApi(selectedMachine.machineId);

      if (isWsError(res)) {
        setErrorMsg(getWsErrorMessage(res));
      } else {
        const data = getWsData(res); // { image, width, height, timestamp } theo api_contract.md
        setImageData(`data:image/jpeg;base64,${data.image}`);
        setCapturedAt(new Date().toLocaleTimeString('vi-VN'));
      }
    } catch (err) {
      // Lỗi hạ tầng (machine offline, gateway lỗi...) -> HTTPException từ backend
      setErrorMsg(err?.detail || 'Không thể chụp màn hình. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadImage = () => {
    if (!imageData) return;
    const link = document.createElement('a');
    link.href = imageData;
    link.download = `Screenshot_${selectedMachine.hostname}_${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={styles.container}>
      <div style={styles.topBar}>
        <div style={styles.actionGroup}>
          <button
            onClick={handleTakeScreenshot}
            disabled={loading}
            style={styles.btnPrimary}
          >
            {loading ? '⏳ Đang chụp...' : '📸 Chụp Màn Hình Ngay'}
          </button>

          {imageData && (
            <button onClick={handleDownloadImage} style={styles.btnSuccess}>
              💾 Tải Ảnh Phân Giải Gốc
            </button>
          )}
        </div>

        {capturedAt && (
          <span style={styles.timeInfo}>
            🕒 Lần chụp cuối: <b>{capturedAt}</b>
          </span>
        )}
      </div>

      {errorMsg && <div style={styles.errorBanner}>⚠️ {errorMsg}</div>}

      <div style={styles.imageViewer}>
        {loading && (
          <div style={styles.statusBox}>
            <div style={{ fontSize: '2.5rem' }}>⏳</div>
            <h4>Đang chụp màn hình {selectedMachine?.hostname}...</h4>
          </div>
        )}

        {!loading && !imageData && (
          <div style={styles.placeholder}>
            <div style={{ fontSize: '3rem', marginBottom: '8px' }}>🖼️</div>
            <p>Bấm nút <b>"Chụp Màn Hình Ngay"</b> ở trên để lấy hình ảnh màn hình Client hiện tại.</p>
          </div>
        )}

        {!loading && imageData && (
          <div style={styles.imageWrapper}>
            <img
              src={imageData}
              alt="Client Screenshot"
              style={styles.responsiveImage}
            />
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  actionGroup: { display: 'flex', gap: '10px' },
  btnPrimary: { padding: '10px 18px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  btnSuccess: { padding: '10px 18px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' },
  timeInfo: { fontSize: '0.9rem', color: '#cbd5e1' },
  errorBanner: { padding: '10px 14px', backgroundColor: '#1e293b', borderLeft: '4px solid #ef4444', borderRadius: '4px', fontSize: '0.85rem', color: '#fca5a5' },
  imageViewer: { flex: 1, backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden', padding: '12px' },
  statusBox: { textAlign: 'center', color: '#f8fafc' },
  placeholder: { textAlign: 'center', color: '#64748b' },
  imageWrapper: { width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' },
  responsiveImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }
};

export default Screenshot;
