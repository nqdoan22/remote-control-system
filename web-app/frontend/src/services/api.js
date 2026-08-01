import axios from 'axios';

// 1. Cấu hình Axios Instance gốc
// VITE_API_BASE_URL có thể khai báo trong file .env (VD: http://localhost:8000/api)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // Timeout sau 10s nếu backend không hồi đáp
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
   SECTION 4: WEBSOCKET PROTOCOL HELPER (Khớp với schemas/protocol.py)
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