using System.Threading.Tasks;

namespace RemoteControlClient.Services
{
    public class GatewayService
    {
        private readonly string _gatewayUrl;

        public GatewayService(string gatewayUrl)
        {
            _gatewayUrl = gatewayUrl;
        }

        public async Task ConnectAsync()
        {
            // TODO: Kết nối WebSocket đến Gateway
        }

        public async Task DisconnectAsync()
        {
            // TODO: Ngắt kết nối
        }

        public async Task SendAsync(object message)
        {
            // TODO: Gửi message dạng JSON đến Gateway
        }

        public void OnMessageReceived(string message)
        {
            // TODO: Xử lý lệnh nhận từ Gateway, điều phối đến đúng module
        }
    }
}
