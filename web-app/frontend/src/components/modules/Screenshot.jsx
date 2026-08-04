import React, { useState, useEffect } from 'react';
import { takeScreenshotApi, isWsError, getWsErrorMessage, getWsData } from '../../services/api';

/**
 * Screenshot Module - Chụp ảnh màn hình máy Client (Có yêu cầu xin phép người dùng).
 *
 * screen.screenshot thuộc Sensitive Feature List (api_contract.md). Gateway sẽ chặn
 * lệnh, gửi permission.request xuống Client App -> hiện CỬA SỔ CẢNH BÁO (Popup xin
 * quyền) trên màn hình máy bị điều khiển. Ảnh chỉ được gửi về Web khi End User đồng ý.
 * Nếu từ chối/timeout -> Backend trả envelope error với code PERMISSION_DENIED /
 * PERMISSION_TIMEOUT.
 *
 * UX theo template LiveScreen: khi đang chờ consent hiển thị khối "Đang gửi yêu cầu
 * và chờ người dùng Client đồng ý..." kèm dòng nhắc Popup xuất hiện trên máy Client.
 *
 * @param {Object} selectedMachine - Thông tin máy Client được chọn
 */
const Screenshot = ({ selectedMachine }) => {
  const [imageData, setImageData] = useState(null); // Chuỗi ảnh Base64 (data:image/jpeg;base64,...)
  const [loading, setLoading] = useState(false);
  const [capturedAt, setCapturedAt] = useState(null);
  // Trạng thái Consent: '' | 'waiting' | 'approved' | 'rejected' | 'timeout'
  const [consentStatus, setConsentStatus] = useState('');

  // Reset dữ liệu ảnh chỉ khi Admin đổi sang máy Client KHÁC.
  // KHÔNG dùng toàn bộ object selectedMachine làm dependency vì nó được tạo lại
  // mỗi khi isConnected (WebSocket) thay đổi -> sẽ reset ảnh ngay sau lần chụp đầu
  // khi kết nối realtime vừa xong (bug "ảnh biến mất").
  const machineId = selectedMachine?.machineId;
  useEffect(() => {
    setImageData(null);
    setCapturedAt(null);
    setConsentStatus('');
    setLoading(false);
  }, [machineId]);

  const takeScreenshot = async () => {
    if (!selectedMachine) return;
    setLoading(true);
    setConsentStatus('waiting');

    try {
      // REST -> Backend -> Gateway -> (chờ End User Consent) -> Client App
      const res = await takeScreenshotApi(selectedMachine.machineId);

      if (isWsError(res)) {
        const code = res.payload?.code;
        const errMsg = getWsErrorMessage(res);

        if (code === 'PERMISSION_DENIED') {
          setConsentStatus('rejected');
          alert('❌ Người dùng trên máy Client đã TỪ CHỐI cấp quyền chụp màn hình!');
        } else if (code === 'PERMISSION_TIMEOUT') {
          setConsentStatus('timeout');
          alert('⏱️ Yêu cầu xin quyền đã HẾT HẠN (Timeout) — người dùng Client không phản hồi.');
        } else {
          setConsentStatus('');
          alert('Lỗi chụp màn hình: ' + errMsg);
        }
      } else {
        const data = getWsData(res); // { image, width, height, timestamp } theo api_contract.md
        const image = data?.image;

        // Kiểm tra dữ liệu ảnh trước khi tạo data URL. Nếu rỗng/thiếu -> báo lỗi rõ
        // ràng thay vì img src hỏng ('...base64,undefined') khiến trình duyệt chỉ hiện
        // đúng chữ alt "Client Screenshot" (bug "chỉ cho coi text").
        if (!image || typeof image !== 'string' || image.length === 0) {
          setConsentStatus('');
          alert('Lỗi chụp màn hình: Phản hồi không chứa dữ liệu ảnh (image rỗng).');
        } else {
          setConsentStatus('approved');
          setImageData(`data:image/jpeg;base64,${image}`);
          setCapturedAt(new Date().toLocaleTimeString('vi-VN'));
        }
      }
    } catch (err) {
      // Lỗi hạ tầng (machine offline, gateway lỗi...) -> HTTPException từ backend
      setConsentStatus('');
      alert('Lỗi chụp màn hình: ' + (err?.detail || 'Không rõ nguyên nhân'));
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadImage = () => {
    if (!imageData) return;
    const link = document.createElement('a');
    link.href = imageData;
    link.download = `Screenshot_${selectedMachine?.hostname || selectedMachine?.machineId || 'client'}_${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Banner phản hồi kết quả Consent
  const renderConsentBanner = () => {
    if (consentStatus === 'rejected') {
      return (
        <div style={styles.consentBannerRejected}>
          ❌ Người dùng Client đã TỪ CHỐI cấp quyền chụp màn hình. Không chụp được ảnh.
        </div>
      );
    }
    if (consentStatus === 'timeout') {
      return (
        <div style={styles.consentBannerTimeout}>
          ⏱️ Yêu cầu xin quyền đã HẾT HẠN (Timeout). Người dùng Client không phản hồi.
        </div>
      );
    }
    if (consentStatus === 'approved') {
      return (
        <div style={styles.consentBannerApproved}>
          ✅ Người dùng Client đã đồng ý. Ảnh chụp được hiển thị bên dưới.
        </div>
      );
    }
    return null;
  };

  return (
    <div style={styles.container}>
      {/* Thanh điều khiển: nút chụp + tải ảnh + thông tin lần chụp */}
      <div style={styles.topBar}>
        <div style={styles.actionGroup}>
          <button
            onClick={takeScreenshot}
            disabled={loading}
            style={styles.btnPrimary}
          >
            {loading
              ? '⏳ Đang chờ người dùng Client đồng ý...'
              : '📸 Chụp Màn Hình Ngay'}
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

      {/* Banner kết quả Consent */}
      {renderConsentBanner()}

      {/* Khu vực hiển thị ảnh */}
      <div style={styles.imageViewer}>
        {loading && (
          <div style={styles.statusBox}>
            <div style={{ fontSize: '2.5rem' }}>⏳</div>
            <h4>Đang gửi yêu cầu và chờ người dùng Client đồng ý...</h4>
            <p style={{ color: '#94a3b8' }}>
              Cửa sổ cảnh báo (Popup xin quyền) sẽ xuất hiện trên màn hình máy bị điều khiển trong 15s.
            </p>
          </div>
        )}

        {!loading && !imageData && (
          <div style={styles.placeholder}>
            <div style={{ fontSize: '3.5rem', marginBottom: '8px' }}>🖼️</div>
            <p>
              Nhấn <b>"Chụp Màn Hình Ngay"</b> để lấy ảnh màn hình Client.
              <br />
              <span style={{ color: '#94a3b8' }}>
                Yêu cầu cần sự đồng ý của người dùng Client (hiện Popup xin quyền).
              </span>
            </p>
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
  consentBannerApproved: { padding: '10px 14px', backgroundColor: '#14532d', borderLeft: '4px solid #16a34a', borderRadius: '4px', fontSize: '0.85rem', color: '#bbf7d0' },
  consentBannerRejected: { padding: '10px 14px', backgroundColor: '#451a1a', borderLeft: '4px solid #ef4444', borderRadius: '4px', fontSize: '0.85rem', color: '#fecaca' },
  consentBannerTimeout: { padding: '10px 14px', backgroundColor: '#451a1a', borderLeft: '4px solid #f59e0b', borderRadius: '4px', fontSize: '0.85rem', color: '#fde68a' },
  imageViewer: { flex: 1, backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden', padding: '12px' },
  statusBox: { textAlign: 'center', color: '#f8fafc' },
  placeholder: { textAlign: 'center', color: '#64748b' },
  imageWrapper: { width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' },
  responsiveImage: { maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }
};

export default Screenshot;