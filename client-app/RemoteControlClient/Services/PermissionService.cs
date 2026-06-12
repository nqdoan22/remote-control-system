namespace RemoteControlClient.Services
{
    public enum PermissionState { AlwaysAsk, AlwaysAllow, AlwaysDeny }

    public class PermissionService
    {
        // TODO: Lưu trữ permission state cho từng module
        // TODO: Load/Save từ file config

        public PermissionState GetPermission(string moduleName)
        {
            // TODO: Trả về trạng thái quyền của module
            return PermissionState.AlwaysAsk;
        }

        public async Task<bool> RequestPermissionAsync(string moduleName)
        {
            // TODO: Kiểm tra state:
            // - AlwaysAllow -> return true ngay
            // - AlwaysDeny  -> return false ngay
            // - AlwaysAsk   -> hiện PermissionPopupWindow, chờ user chọn
            return false;
        }
    }
}
