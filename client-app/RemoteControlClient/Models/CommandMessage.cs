namespace RemoteControlClient.Models
{
    public class CommandMessage
    {
        public string Type { get; set; }       // Loại lệnh: "screenshot", "keylogger_start", ...
        public string MachineId { get; set; }  // Máy đích
        public object Payload { get; set; }    // Dữ liệu kèm theo
    }
}
