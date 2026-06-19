import axios from 'axios';

// THAY ĐỔI DÒNG NÀY:
// const API_URL = 'http://localhost:8000';

// THÀNH DÒNG NÀY (Dùng IP số chuẩn xác):
const API_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_URL,
});

// Interceptor: Tự động gắn Token vào Header trước khi gửi request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const authService = {
  login: async (username, password) => {
    // Sử dụng URLSearchParams vì Backend dùng OAuth2PasswordRequestForm (Form Data)
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('token');
  }
};

export const machineService = {
  getMachines: async () => {
    const response = await api.get('/api/machines/');
    return response.data;
  }
};

export const moduleService = {
  sendCommand: async (machineId, module, action, payload = {}) => {
    // Gọi trực tiếp đến router modules của backend
    const response = await api.post(`/api/modules/${machineId}/${module}/${action}`, payload);
    return response.data;
  }
};

export default api;