import React, { useState } from 'react';
import { controlPowerApi, isWsError, getWsErrorMessage } from '../../services/api';

/**
 * PowerControl Module - Điều khiển nguồn máy tính Client (Lock, Sleep, Restart, Shutdown).
 * power.lock / power.restart / power.shutdown / power.sleep qua REST.
 * Toàn bộ nằm trong Sensitive Feature List -> Gateway tự xin Permission Confirmation.
 */
const PowerControl = ({ selectedMachine }) => {
  const [loading, setLoading] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null); // { type, label }
  const [statusLog, setStatusLog] = useState('');

  const initiatePowerAction = (actionType, label) => {
    setSelectedAction({ type: actionType, label });
  };

  const confirmAndExecute = async () => {
    if (!selectedAction || !selectedMachine) return;
    const { type, label } = selectedAction;

    setLoading(true);
    setStatusLog(`⏳ Đang gửi lệnh "${label}" đến Client (có thể chờ người dùng Client xác nhận)...`);
    setSelectedAction(null);

    try {
      const res = await controlPowerApi(selectedMachine.machineId, type);
      if (isWsError(res)) {
        setStatusLog(`⚠️ ${getWsErrorMessage(res)}`);
      } else {
        setStatusLog(`✅ Đã gửi lệnh thành công: ${label}`);
      }
    } catch (err) {
      setStatusLog(`⚠️ Lỗi thực thi: ${err?.detail || 'Không rõ nguyên nhân'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.warningBanner}>
        ⚠️ <b>CẢNH BÁO AN TOÀN NGUỒN ĐIỆN:</b>
        <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem' }}>
          Các thao tác Khởi động lại hoặc Tắt máy có thể làm gián đoạn công việc và gây mất dữ liệu chưa lưu trên máy tính Client.
        </p>
      </div>

      <div style={styles.gridContainer}>
        <div style={styles.powerCard}>
          <div style={{ fontSize: '2.5rem' }}>🔒</div>
          <h3>Khóa Màn Hình</h3>
          <p style={styles.cardDesc}>Khóa phiên làm việc hiện tại. Yêu cầu nhập mật khẩu để mở lại.</p>
          <button
            onClick={() => initiatePowerAction('lock', 'Khóa màn hình')}
            disabled={loading}
            style={{ ...styles.actionBtn, backgroundColor: '#0284c7' }}
          >
            Khóa Màn Hình
          </button>
        </div>

        <div style={styles.powerCard}>
          <div style={{ fontSize: '2.5rem' }}>🌙</div>
          <h3>Chế Độ Ngủ (Sleep)</h3>
          <p style={styles.cardDesc}>Đưa máy tính vào trạng thái tiết kiệm điện năng thấp mà không đóng ứng dụng.</p>
          <button
            onClick={() => initiatePowerAction('sleep', 'Đưa vào chế độ Sleep')}
            disabled={loading}
            style={{ ...styles.actionBtn, backgroundColor: '#d97706' }}
          >
            Chuyển Sang Sleep
          </button>
        </div>

        <div style={styles.powerCard}>
          <div style={{ fontSize: '2.5rem' }}>🔄</div>
          <h3>Khởi Động Lại</h3>
          <p style={styles.cardDesc}>Đóng tất cả ứng dụng và khởi động lại hệ điều hành Windows.</p>
          <button
            onClick={() => initiatePowerAction('restart', 'Khởi động lại máy')}
            disabled={loading}
            style={{ ...styles.actionBtn, backgroundColor: '#ea580c' }}
          >
            Khởi Động Lại
          </button>
        </div>

        <div style={styles.powerCard}>
          <div style={{ fontSize: '2.5rem' }}>🔌</div>
          <h3>Tắt Máy Tính</h3>
          <p style={styles.cardDesc}>Tắt hoàn toàn nguồn điện của máy Client.</p>
          <button
            onClick={() => initiatePowerAction('shutdown', 'Tắt máy tính')}
            disabled={loading}
            style={{ ...styles.actionBtn, backgroundColor: '#dc2626' }}
          >
            Tắt Máy Tính
          </button>
        </div>
      </div>

      {statusLog && (
        <div style={styles.statusBox}>
          <b>Nhật ký phản hồi:</b> {statusLog}
        </div>
      )}

      {selectedAction && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <h3 style={{ color: '#ef4444', marginTop: 0 }}>🚨 Xác Nhận Thao Tác Bắt Buộc</h3>
            <p>
              Bạn có chắc chắn muốn gửi lệnh: <b>"{selectedAction.label}"</b> đến máy tính <b>{selectedMachine?.hostname}</b> không?
            </p>
            <div style={styles.modalActions}>
              <button onClick={() => setSelectedAction(null)} style={styles.cancelBtn}>
                Hủy Bỏ
              </button>
              <button onClick={confirmAndExecute} style={styles.confirmBtn}>
                Đồng Ý Thực Thi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' },
  warningBanner: { padding: '12px 16px', backgroundColor: '#451a1a', border: '1px solid #991b1b', borderRadius: '8px', color: '#fca5a5' },
  gridContainer: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' },
  powerCard: { backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' },
  cardDesc: { fontSize: '0.8rem', color: '#94a3b8', minHeight: '40px', margin: '8px 0 16px 0' },
  actionBtn: { width: '100%', padding: '10px', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' },
  statusBox: { padding: '12px', backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', fontSize: '0.9rem' },
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 },
  modalContent: { backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px', padding: '24px', maxWidth: '400px', width: '90%', color: '#fff' },
  modalActions: { display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' },
  cancelBtn: { padding: '8px 16px', backgroundColor: '#475569', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' },
  confirmBtn: { padding: '8px 16px', backgroundColor: '#dc2626', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }
};

export default PowerControl;
