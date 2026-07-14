// web-app/frontend/src/services/api.js
import axios from 'axios';

// 🌐 1. KHỞI TẠO ĐỊA CHỈ IP GỐC CỦA BACKEND SERVER
// Hệ thống sẽ ưu tiên đọc cấu hình từ file môi trường .env (VITE_API_URL).
// Nếu đang chạy thử nghiệm trong mạng LAN nội bộ không cấu hình biến môi trường,
// hệ thống sẽ tự động fallback về địa chỉ localhost trên cổng mặc định 8000.
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 🏭 2. ĐÚC KHUÔN ĐỐI TƯỢNG AXIOS CLIENT (AXIOS INSTANCE)
// Việc tạo Instance giúp ta cố định cấu hình mạng, tránh xung đột cấu hình 
// với các thư viện bên thứ ba khác cùng sử dụng Axios trong ứng dụng.
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000, // Cơ chế Timeout: Nếu sau 10 giây Backend không phản hồi, tự động hủy để giải phóng RAM.
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// =========================================================================
// 🔒 3. AXIOS REQUEST INTERCEPTOR: BỘ ĐÁNH CHẶN GÓI TIN ĐI (GẮN Ổ KHÓA JWT)
// =========================================================================
// Trước khi bất kỳ một yêu cầu HTTP nào được truyền đi qua card mạng, 
// hàm interceptor này sẽ chặn gói tin lại trên RAM, lục soát xem có Access Token 
// lưu trong bộ nhớ trình duyệt hay không để tự động dán vào Header Authorization.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      // Tuân thủ nghiêm ngặt tiêu chuẩn OAuth 2.0 và cơ chế mã hóa JWT (JSON Web Token)
      // Định dạng cấu trúc chuỗi gửi lên Server bắt buộc phải là: Bearer <chuỗi_token>
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config; // Trả về cấu hình đã được bổ sung Token để tiếp tục hành trình mạng
  },
  (error) => {
    // Xử lý lỗi xảy ra ngay tại Frontend trong quá trình đóng gói dữ liệu cấu hình
    return Promise.reject(error);
  }
);

// =========================================================================
// 🚨 4. AXIOS RESPONSE INTERCEPTOR: BỘ GIẢI MÃ VÀ SÀN LỌC PHẢN HỒI VỀ
// =========================================================================
// Khi nhận được phản hồi từ Backend, trước khi phân phối dữ liệu về cho các module UI,
// bộ đánh chặn này sẽ kiểm tra xem mã trạng thái HTTP (HTTP Status Code) có an toàn không.
apiClient.interceptors.response.use(
  (response) => {
    // Nếu HTTP Status Code nằm trong khoảng 2xx (Thành công)
    // Ta bóc tách và chỉ trả về phần thuộc tính 'data' do Server phản hồi cho tinh gọn code bên ngoài.
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config;

    // Kịch bản đặc biệt: Mã lỗi 401 (Unauthorized) - Token hết hạn hoặc không hợp lệ
    // và gói tin này chưa từng thực hiện cơ chế thử lại (tính năng phòng chống vòng lặp vô hạn _retry)
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        console.warn("⚠️ Cảnh báo hệ thống: Access Token hết hạn, đang kích hoạt luồng gia hạn...");
        
        // Gọi API Refresh Token để lấy Access Token mới mà không bắt người dùng đăng nhập lại
        const refreshToken = localStorage.getItem('refresh_token');
        
        // Thực hiện một request HTTP thô không qua instance chung để tránh vòng lặp interceptor
        const response = await axios.post(`${BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken
        });

        const newAccessToken = response.data.access_token;
        
        // Cập nhật lại "ổ khóa" mới vào bộ nhớ cứng vật lý của trình duyệt
        localStorage.setItem('access_token', newAccessToken);
        
        // Cập nhật lại Header của gói tin cũ bị lỗi bằng Token mới tinh vừa xin được
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        
        // Bắn lại gói tin cũ ra mạng một lần nữa, người dùng hoàn toàn không hề nhận ra sự gián đoạn này
        return axios(originalRequest);
      } catch (refreshError) {
        // Nếu ngay cả Refresh Token cũng hết hạn gắt gao -> Cưỡng chế đăng xuất, xóa toàn bộ bộ nhớ tạm
        console.error("🚨 Lỗi nghiêm trọng: Refresh Token vô hiệu. Hủy quyền truy cập hệ thống.");
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Phân tích và chuẩn hóa các mã lỗi hệ thống khác để UI hiển thị thông báo tường minh
    const errorMessage = error.response?.data?.detail || "Lỗi đường truyền hoặc máy chủ mất kết nối.";
    return Promise.reject(new Error(errorMessage));
  }
);

// =========================================================================
// 🗃️ 5. KHAI BÁO CÁC DỊCH VỤ ĐẦU CUỐI PHÂN CHIA THEO TIỂU MODULE MẠNG
// =========================================================================

// Chức năng A: Xác thực danh tính hệ thống
export const authService = {
  login: (username, password) => apiClient.post('/api/auth/login', { username, password }),
  logout: () => {
    localStorage.clear();
    window.location.href = '/login';
  }
};

// Chức năng B: Quản lý tổng quan danh sách Agent trong mạng LAN
export const machineService = {
  getAllMachines: () => apiClient.get('/api/machines/list'),
  getMachineDetail: (machineId) => apiClient.get(`/api/machines/detail/${machineId}`),
};

// Chức năng C: Thao tác nghiệp vụ sâu vào lõi hệ điều hành của máy đích
export const moduleService = {
  // 💾 Phân hệ tiến trình (Task Manager)
  getProcesses: (machineId) => apiClient.get(`/api/modules/processes/${machineId}`),
  killProcess: (machineId, pid) => apiClient.post(`/api/modules/processes/kill`, { machine_id: machineId, pid }),

  // 🚀 Phân hệ ứng dụng phần mềm (Applications)
  getApplications: (machineId) => apiClient.get(`/api/modules/applications/${machineId}`),
  startApplication: (machineId, appName) => apiClient.post(`/api/modules/applications/start`, { machine_id: machineId, app_name: appName }),
  stopApplication: (machineId, appName) => apiClient.post(`/api/modules/applications/stop`, { machine_id: machineId, app_name: appName }),

  // 📸 Phân hệ chụp ảnh đóng gói (HTTP Screenshot)
  takeScreenshot: (machineId) => apiClient.post(`/api/modules/screenshot`, { machine_id: machineId }),

  // 📁 Phân hệ quản lý tệp tin cục bộ từ xa
  browseFiles: (machineId, targetPath) => apiClient.post('/api/modules/file/browse', { machine_id: machineId, target_path: targetPath }),
  downloadFile: (machineId, filePath) => apiClient.post('/api/modules/file/download', { machine_id: machineId, file_path: filePath, action: "download" }),

  // ⌨️ Phân hệ thu thập tín hiệu bàn phím (Keylogger)
  startKeylogger: (machineId) => apiClient.post('/api/modules/keylogger/start', { machine_id: machineId }),
  stopKeylogger: (machineId) => apiClient.post('/api/modules/keylogger/stop', { machine_id: machineId }),
  getKeyloggerLogs: (machineId) => apiClient.get(`/api/modules/keylogger/${machineId}`),

  // 🔌 Phân hệ điều khiển nguồn điện phần cứng
  executePowerCommand: (machineId, action) => apiClient.post(`/api/modules/power`, { machine_id: machineId, action }),
};