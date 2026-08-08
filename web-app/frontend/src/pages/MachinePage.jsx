import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// 1. Import REST API để lấy thông tin tĩnh của máy
import { getMachineDetailApi } from '../services/api';
// 2. Import Custom Hook WebSocket để điều khiển Real-time
import { useWebSocket } from '../hooks/useWebSocket';
// 3. Import định nghĩa chuẩn 8 Module (danh sách Tab theo API Contract)
import { MODULE_TABS } from '../components/shared/ModulePanel';
// 4. Import 8 Component Module chức năng điều khiển máy Client
import Applications from '../components/modules/Applications';
import Processes from '../components/modules/Processes';
import Screenshot from '../components/modules/Screenshot';
import LiveScreen from '../components/modules/LiveScreen';
import InputAuditLog from '../components/modules/InputAuditLog';
import FileTransfer from '../components/modules/FileTransfer';
import Webcam from '../components/modules/Webcam';
import PowerControl from '../components/modules/PowerControl';

// Map 8 tab id -> Component Module tương ứng
const MODULE_COMPONENTS = {
  applications: Applications,
  processes: Processes,
  screenshot: Screenshot,
  livescreen: LiveScreen,
  input_audit: InputAuditLog,
  filemanager: FileTransfer,
  webcam: Webcam,
  power: PowerControl,
};

const MachinePage = () => {
  // Lấy machineId từ URL (ví dụ: /machine/client-app-01 -> machineId = 'client-app-01')
  const { machineId } = useParams();
  const navigate = useNavigate();

  // =========================================================================
  // STATE MANAGEMENT (Quản lý trạng thái giao diện)
  // =========================================================================
  const [machineInfo, setMachineInfo] = useState(null); // Thông tin chi tiết máy
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Tab Module đang mở (Mặc định mở Module 'applications' - Module đầu tiên trong 8 Module)
  const [activeTab, setActiveTab] = useState('applications');

  // =========================================================================
  // 🔌 KHỞI TẠO WEBSOCKET CONNECTION TỚI MÁY CLIENT
  // =========================================================================
  const { isConnected, connecting, reconnecting, lastMessage } = useWebSocket(machineId);

  // =========================================================================
  // 🚀 REST API: Lấy thông tin cơ bản của máy khi mới mở trang
  // =========================================================================
  useEffect(() => {
    const fetchDetail = async () => {
      try {
        setLoading(true);
        // Gọi REST API lấy thông tin phần cứng, IP, OS từ Database
        const data = await getMachineDetailApi(machineId);
        setMachineInfo(data);
      } catch (err) {
        console.error('Lỗi lấy thông tin máy:', err);
        setError('Không thể lấy thông tin chi tiết của máy này!');
      } finally {
        setLoading(false);
      }
    };

    if (machineId) fetchDetail();
  }, [machineId]);

  // =========================================================================
  // ⚡ XỬ LÝ CẢNH BÁO TOÀN CỤC TỪ AGENT (không thuộc riêng Module nào)
  // =========================================================================
  useEffect(() => {
    if (lastMessage?.type === 'system.alert') {
      alert(`[CẢNH BÁO TỪ AGENT]: ${lastMessage.payload?.message}`);
    }
  }, [lastMessage]);

  // =========================================================================
  // Các Module Component giờ điều khiển qua REST API (services/api.js) - đúng
  // theo docs/api_contract.md - và chỉ dùng `lastMessage` (shape {type, payload}
  // nguyên vẹn từ Gateway/Client App) để nhận dữ liệu streaming: screen.live.frame,
  // webcam.frame, input_audit.data. Không còn cần adapter action/status/data nữa.
  // =========================================================================
  // 🖥️ CHUẨN HÓA selectedMachine: Các Module Component yêu cầu object có
  // { machineId, hostname, ipAddress, status } từ REST MachineResponse.
  // =========================================================================
  const selectedMachine = useMemo(() => {
    if (!machineInfo) return null;
    return {
      machineId: machineInfo.machine_id || machineId,
      hostname: machineInfo.hostname,
      ipAddress: machineInfo.ip_address,
      status: isConnected ? 'online' : 'offline',
    };
  }, [machineInfo, isConnected, machineId]);

  // Component Module đang được chọn theo Tab
  const ActiveModuleComponent = MODULE_COMPONENTS[activeTab];

  if (loading) return <div style={styles.container}>Đang tải thông tin máy...</div>;
  if (error) return <div style={styles.container}>{error}</div>;

  return (
    <div style={styles.container}>
      {/* 1. HEADER & TRẠNG THÁI KẾT NỐI REAL-TIME + THÔNG TIN MÁY */}
      <header style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <button onClick={() => navigate('/dashboard')} style={styles.backBtn}>
            &larr; Quay lại
          </button>
          <h1 style={styles.title}>
            Máy: {machineInfo?.hostname || machineId}
          </h1>
          <span style={styles.infoChip}>IP: {machineInfo?.ip_address || 'N/A'}</span>
          <span style={styles.infoChip}>OS: {machineInfo?.os_info || 'N/A'}</span>
          <span style={styles.infoChip}>MAC: {machineInfo?.mac_address || 'N/A'}</span>
        </div>

        {/* Badge hiển thị trạng thái đường ống WebSocket */}
        {/* 🔧 ĐÃ CẬP NHẬT: Phân biệt 3 trạng thái 'READY' / 'ĐANG KẾT NỐI' / 'MẤT KẾT NỐI' để
            Admin không bị hiểu lầm khi hook đang tự động reconnect. */}
        <div style={styles.wsStatusBadge}>
          <span
            style={{
              ...styles.statusDot,
              backgroundColor: isConnected
                ? '#22c55e'
                : connecting || reconnecting
                  ? '#f59e0b'
                  : '#ef4444',
            }}
          />
          <span
            style={{
              color: isConnected ? '#22c55e' : connecting || reconnecting ? '#f59e0b' : '#ef4444',
              fontWeight: 'bold',
            }}
          >
            {isConnected
              ? 'WEBSOCKET REALTIME: READY'
              : reconnecting
                ? 'MẤT KẾT NỐI - ĐANG KẾT NỐI LẠI...'
                : connecting
                  ? 'ĐANG KẾT NỐI WEBSOCKET...'
                  : 'MẤT KẾT NỐI WEBSOCKET'}
          </span>
        </div>
      </header>

      {/* 2. THANH CHỌN TAB THEO ĐÚNG 8 MODULE CHỨC NĂNG */}
      <div style={styles.tabBar}>
        {MODULE_TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              style={isActive ? styles.activeTabBtn : styles.tabBtn}
              onClick={() => setActiveTab(tab.id)}
            >
              <span style={{ marginRight: '6px' }}>{tab.icon}</span>
              {tab.label}

              {/* Badge chỉ báo các chức năng nhạy cảm phải xin quyền người dùng Client */}
              {tab.sensitive && (
                <span
                  title="Chức năng nhạy cảm - Bắt buộc xin phép người dùng Client"
                  style={styles.sensitiveBadge}
                >
                  🔒 Consent
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* 3. NỘI DUNG MODULE ĐANG ĐƯỢC CHỌN */}
      <div style={styles.contentArea}>
        {ActiveModuleComponent && selectedMachine ? (
          <ActiveModuleComponent
            selectedMachine={selectedMachine}
            lastMessage={lastMessage}
          />
        ) : (
          <div style={styles.card}>
            <h3>Chưa có thông tin máy</h3>
            <p>Không thể hiển thị các Module điều khiển. Vui lòng thử lại.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// =========================================================================
// INLINE STYLES
// =========================================================================
const styles = {
  container: { padding: '24px', backgroundColor: '#0f172a', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Segoe UI, sans-serif' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' },
  backBtn: { backgroundColor: '#334155', color: '#fff', border: 'none', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer' },
  title: { fontSize: '22px', color: '#38bdf8', margin: 0 },
  infoChip: { backgroundColor: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '4px 10px', borderRadius: '14px', fontSize: '0.8rem' },
  wsStatusBadge: { display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#1e293b', padding: '8px 16px', borderRadius: '20px', border: '1px solid #334155' },
  statusDot: { width: '10px', height: '10px', borderRadius: '50%' },
  tabBar: { display: 'flex', gap: '8px', borderBottom: '1px solid #334155', marginBottom: '20px', overflowX: 'auto', flexWrap: 'nowrap' },
  tabBtn: { padding: '10px 16px', backgroundColor: 'transparent', color: '#94a3b8', border: 'none', cursor: 'pointer', borderBottom: '2px solid transparent', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center' },
  activeTabBtn: { padding: '10px 16px', backgroundColor: 'transparent', color: '#38bdf8', border: 'none', cursor: 'pointer', borderBottom: '2px solid #38bdf8', fontWeight: 'bold', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center' },
  sensitiveBadge: { fontSize: '0.65rem', backgroundColor: '#334155', color: '#fbbf24', padding: '2px 4px', borderRadius: '3px', marginLeft: '6px', border: '1px solid #d97706' },
  contentArea: { marginTop: '10px' },
  card: { backgroundColor: '#1e293b', padding: '20px', borderRadius: '8px', border: '1px solid #334155' },
};

export default MachinePage;
