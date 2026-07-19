// web-app/frontend/src/services/api.js
import axios from 'axios';

// 🌐 1. KHỞI TẠO ĐỊA CHỈ IP GỐC CỦA BACKEND SERVER
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 🏭 2. ĐÚC KHUÔN ĐỐI TƯỢNG AXIOS CLIENT (AXIOS INSTANCE)
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// =========================================================================
// 🔒 3. AXIOS REQUEST INTERCEPTOR: BỘ ĐÁNH CHẶN GÓI TIN ĐI
// =========================================================================
apiClient.interceptors.request.use(
  (config) => {
    // Chỉ cho phép người dùng đã xác thực (Administrator) sử dụng hệ thống[cite: 17].
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// =========================================================================
// 🚨 4. AXIOS RESPONSE INTERCEPTOR: BỘ GIẢI MÃ VÀ SÀN LỌC PHẢN HỒI VỀ
// =========================================================================
apiClient.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        console.warn("⚠️ Cảnh báo: Access Token hết hạn, đang gia hạn...");
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${BASE_URL}/api/auth/refresh`, { refresh_token: refreshToken });
        const newAccessToken = response.data.access_token;
        
        localStorage.setItem('access_token', newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        console.error("🚨 Refresh Token vô hiệu. Hủy quyền truy cập.");
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    const errorMessage = error.response?.data?.detail || "Lỗi đường truyền.";
    return Promise.reject(new Error(errorMessage));
  }
);

// =========================================================================
// 🗃️ 5. KHAI BÁO CÁC DỊCH VỤ DỰA TRÊN YÊU CẦU CHỨC NĂNG (FUNCTIONAL SPECS)
// =========================================================================

export const authService = {
  login: (username, password) => apiClient.post('/api/auth/login', { username, password }),
  logout: () => {
    localStorage.clear();
    window.location.href = '/login';
  }
};

// Theo tài liệu System Spec: Hiển thị danh sách Machine, trạng thái Online/Offline[cite: 13].
export const machineService = {
  getAllMachines: () => apiClient.get('/api/machines/list'),
  getMachineDetail: (machineId) => apiClient.get(`/api/machines/detail/${machineId}`),
};

export const moduleService = {
  // 💾 Quản lý tiến trình (Process Management): Liệt kê toàn bộ tiến trình và Kết thúc tiến trình[cite: 13].
  getProcesses: (machineId) => apiClient.get(`/api/modules/processes/${machineId}`),
  killProcess: (machineId, pid) => apiClient.post(`/api/modules/processes/kill`, { machine_id: machineId, pid }),

  // 🚀 Quản lý ứng dụng (Application Management): Khởi động và Dừng ứng dụng[cite: 13].
  getApplications: (machineId) => apiClient.get(`/api/modules/applications/${machineId}`),
  startApplication: (machineId, appName) => apiClient.post(`/api/modules/applications/start`, { machine_id: machineId, app_name: appName }),
  stopApplication: (machineId, appName) => apiClient.post(`/api/modules/applications/stop`, { machine_id: machineId, app_name: appName }),

  // 📸 Giám sát màn hình (Screen Monitoring): Screenshot không yêu cầu xác nhận của End User[cite: 13].
  takeScreenshot: (machineId) => apiClient.post(`/api/modules/screenshot`, { machine_id: machineId }),

  // 📁 Quản lý File: Chỉ được phép thao tác trong thư mục đã cấu hình (File Sandbox)[cite: 14, 17].
  browseFiles: (machineId, targetPath) => apiClient.post('/api/modules/file/browse', { machine_id: machineId, target_path: targetPath }),
  downloadFile: (machineId, filePath) => apiClient.post('/api/modules/file/download', { machine_id: machineId, file_path: filePath, action: "download" }),

  // ⌨️ Key Logger: Phải được End User xác nhận trước khi sử dụng[cite: 13, 17].
  startKeylogger: (machineId) => apiClient.post('/api/modules/keylogger/start', { machine_id: machineId }),
  stopKeylogger: (machineId) => apiClient.post('/api/modules/keylogger/stop', { machine_id: machineId }),
  getKeyloggerLogs: (machineId) => apiClient.get(`/api/modules/keylogger/${machineId}`),

  // 🔌 Quản lý nguồn (Power Management): Lock Screen, Restart, Shutdown, Sleep yêu cầu xác nhận[cite: 13, 14].
  executePowerCommand: (machineId, action) => apiClient.post(`/api/modules/power`, { machine_id: machineId, action }),
};