import axios from 'axios';

// 1. Cấu hình Axios Instance gốc
// VITE_API_BASE_URL có thể khai báo trong file .env (VD: http://localhost:8000/api)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 25000, // Timeout mặc định: 25s. Các lệnh Module chờ phản hồi tới 15s (COMMAND_TIMEOUT_SECONDS) ở Backend, nên 10s là quá ngắn -> axios tự hủy request -> Frontend báo lỗi sai ('Không rõ nguyên nhân').
});

// 2. Request Interceptor: Tự động "dán" JWT Token vào mỗi Request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 3. Response Interceptor: Bắt lỗi tập trung (VD: Hết hạn Token)
api.interceptors.response.use(
  (response) => response.data, // Trả trực tiếp data từ backend (bỏ qua vỏ axios response)
  (error) => {
    if (error.response && error.response.status === 401) {
      // 401 Unauthorized: Token hết hạn hoặc không hợp lệ -> Xóa token và về trang Login
      localStorage.removeItem('access_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error.response?.data || error.message);
  }
);

/* ============================================================================
   SECTION 1: AUTHENTICATION APIs (Khớp với schemas/auth.py)
   ============================================================================ */

/**
 * Đăng nhập hệ thống Admin
 * @param {Object} credentials - { username, password } (LoginRequest Schema)
 * @returns {Promise<{access_token: string, token_type: string}>} (Token Schema)
 */
export const loginApi = async (credentials) => {
  return await api.post('/auth/login', credentials);
};

/**
 * Lấy thông tin tài khoản Admin đang đăng nhập
 * @returns {Promise<{id: number, username: string, role: string, is_active: boolean}>} (UserResponse Schema)
 */
export const getMeApi = async () => {
  return await api.get('/auth/me');
};

/**
 * Đổi mật khẩu Admin
 * @param {Object} data - { old_password, new_password } (PasswordChangeRequest Schema)
 */
export const changePasswordApi = async (data) => {
  return await api.post('/auth/change-password', data);
};


/* ============================================================================
   SECTION 2: MACHINE MANAGEMENT APIs (Khớp với schemas/machine.py)
   ============================================================================ */

/**
 * Lấy danh sách máy Client (có phân trang)
 * @param {Object} params - { skip: 0, limit: 10, status: 'online' }
 * @returns {Promise<{total: number, machines: Array}>} (MachineListResponse Schema)
 */
export const getMachinesApi = async (params = {}) => {
  return await api.get('/machines', { params });
};

/**
 * Lấy thông tin chi tiết một máy Client theo machine_id
 * @param {string} machineId - ID định danh duy nhất (VD: 'client-app-01')
 * @returns {Promise<MachineResponse>}
 */
export const getMachineDetailApi = async (machineId) => {
  return await api.get(`/machines/${machineId}`);
};

/**
 * Cập nhật thông tin/trạng thái máy tính (Thường dành cho Admin chỉnh sửa tên/IP)
 * @param {string} machineId 
 * @param {Object} updateData - (MachineUpdate Schema)
 */
export const updateMachineApi = async (machineId, updateData) => {
  return await api.patch(`/machines/${machineId}`, updateData);
};


/* ============================================================================
   SECTION 3: AUDIT LOG APIs (Khớp với schemas/audit_log.py)
   ============================================================================ */

/**
 * Lấy danh sách Nhật ký hệ thống Audit Logs (có phân trang & lọc)
 * @param {Object} params - { skip: 0, limit: 20, action: 'lock_machine', target_machine_id: 'client-app-01' }
 * @returns {Promise<{total: number, logs: Array}>} (AuditLogListResponse Schema)
 */
export const getAuditLogsApi = async (params = {}) => {
  return await api.get('/audit-logs', { params });
};


/* ============================================================================
   SECTION 4: MODULE CONTROL APIs (Khớp với routers/modules.py + api_contract.md)
   Backend trả về nguyên vẹn WSMessage envelope { type, payload: {success, data} }
   nhận từ Gateway/Client App. Dùng isWsError()/getWsData() bên dưới để đọc.
   ============================================================================ */

export const controlApplicationsApi = (machineId, action, extra = {}) =>
  api.post('/modules/applications', { machine_id: machineId, action, ...extra });

export const controlProcessesApi = (machineId, action, extra = {}) =>
  api.post('/modules/processes', { machine_id: machineId, action, ...extra });

export const takeScreenshotApi = (machineId) =>
  api.post(
    '/modules/screenshot',
    { machine_id: machineId },
    { timeout: SENSITIVE_COMMAND_TIMEOUT_MS }
  );

// Lệnh thuộc Sensitive Feature List (screen.live.start, webcam.start, keylogger.start,
// power.*) có thể mất tới ~35s phía Backend (chờ Permission Confirmation ở Gateway,
// tối đa 30s theo api_contract.md) -> phải nới timeout HTTP client, nếu không axios
// sẽ tự hủy request trước khi Backend kịp trả lời.
const SENSITIVE_COMMAND_TIMEOUT_MS = 40000;

export const controlLiveScreenApi = (machineId, action, fps = 10, selfView = false, options = {}) =>
  api.post(
    '/modules/live-screen',
    {
      machine_id: machineId,
      action,
      fps,
      self_view: selfView,
      // options.videoRect: { x, y, w, h } (CSS px, tương đối cửa sổ trình duyệt)
      // options.dpr: devicePixelRatio — giúp Client che đúng vùng khung xem
      // Live Screen khi self-view thay vì che toàn bộ cửa sổ trình duyệt.
      video_rect: options.videoRect || null,
      dpr: options.dpr || 1,
    },
    { timeout: SENSITIVE_COMMAND_TIMEOUT_MS }
  );

export const controlKeyloggerApi = (machineId, action) =>
  api.post(
    '/modules/keylogger',
    { machine_id: machineId, action },
    { timeout: SENSITIVE_COMMAND_TIMEOUT_MS }
  );

// File tối đa 50MB (api_contract.md) không chunk -> cần timeout dài hơn mặc định 10s.
const FILE_TRANSFER_TIMEOUT_MS = 60000;

export const fileActionApi = (machineId, action, path) =>
  api.post(
    '/modules/file/action',
    { machine_id: machineId, action, path },
    { timeout: FILE_TRANSFER_TIMEOUT_MS }
  );

export const uploadFileApi = (machineId, destinationPath, file) => {
  const form = new FormData();
  form.append('machine_id', machineId);
  form.append('destination_path', destinationPath);
  form.append('file', file);
  return api.post('/modules/file/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: FILE_TRANSFER_TIMEOUT_MS,
  });
};

export const controlWebcamApi = (machineId, action, fps = 10) =>
  api.post(
    '/modules/webcam',
    { machine_id: machineId, action, fps },
    { timeout: SENSITIVE_COMMAND_TIMEOUT_MS }
  );

export const controlPowerApi = (machineId, action, delaySeconds = 0) =>
  api.post(
    '/modules/power',
    { machine_id: machineId, action, delay_seconds: delaySeconds },
    { timeout: SENSITIVE_COMMAND_TIMEOUT_MS }
  );

/**
 * Response thành công từ REST module APIs LUÔN có dạng WSMessage envelope
 * { type: 'response' | 'error', payload: {...} } - kể cả khi Gateway trả về
 * lỗi nghiệp vụ (VD: PERMISSION_DENIED, PERMISSION_TIMEOUT) vì đó vẫn là
 * HTTP 200 OK (chỉ lỗi hạ tầng như MACHINE Offline mới raise HTTPException).
 */
export const isWsError = (res) => !res || res.type === 'error';

export const getWsErrorMessage = (res) => {
  if (!res) return 'Không nhận được phản hồi.';
  if (res.type === 'error') {
    const code = res.payload?.code;
    if (code === 'PERMISSION_DENIED') return 'Người dùng trên máy Client đã TỪ CHỐI cấp quyền.';
    if (code === 'PERMISSION_TIMEOUT') return 'Hết thời gian chờ xác nhận từ người dùng Client (Timeout).';
    return res.payload?.message || `Lỗi: ${code || 'UNKNOWN'}`;
  }
  return '';
};

export const getWsData = (res) => res?.payload?.data ?? {};

/* ============================================================================
   SECTION 5: WEBSOCKET PROTOCOL HELPER (Khớp với schemas/protocol.py)
   ============================================================================ */

/**
 * Helper hàm tạo cấu trúc WebSocket Envelope (WSMessage Schema) chuẩn hóa
 * Giúp tạo khung JSON đồng nhất trước khi bắn qua WebSocket Gateway
 */
export const createWSMessage = ({
  type,
  source = 'webapp',
  destination,
  payload = {},
  messageId = undefined
}) => {
  return {
    messageId: messageId || crypto.randomUUID(), // Tạo UUID v4 chuẩn
    type,
    timestamp: Math.floor(Date.now() / 1000), // Unix Epoch Time
    source,
    destination,
    payload,
  };
};

export default api;