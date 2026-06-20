# Đặc tả Hệ thống – Remote Control System

## Mục tiêu

Hệ thống cho phép một người dùng, thông qua giao diện web, điều khiển từ xa một hoặc nhiều máy tính Windows. Người dùng có thể xem trạng thái máy, thao tác với ứng dụng và tiến trình, theo dõi màn hình và webcam theo thời gian thực, ghi lại phím nhấn, tải file về, hoặc ra lệnh tắt/ngủ máy. Mọi hành động trên máy bị điều khiển đều phải được người dùng tại chỗ chấp thuận trước khi thực thi.

---

## Các thành phần

Hệ thống gồm ba thành phần hoạt động độc lập và giao tiếp với nhau qua mạng.

**Giao diện Web** là nơi người dùng đăng nhập và thực hiện toàn bộ thao tác điều khiển. Nó hiển thị danh sách các máy đang kết nối, cho phép chọn máy cần điều khiển, gửi lệnh, và hiển thị kết quả trả về. Người dùng phải đăng nhập bằng tên đăng nhập và mật khẩu trước khi có thể làm bất cứ điều gì; phiên làm việc được duy trì bằng một token xác thực.

**Gateway** là thành phần trung gian nằm giữa giao diện Web và các máy bị điều khiển. Nó không xử lý bất kỳ logic nghiệp vụ nào — nhiệm vụ duy nhất của nó là nhận lệnh từ Web và chuyển đến đúng máy, đồng thời nhận kết quả từ máy và gửi ngược về Web. Gateway cũng theo dõi danh sách các máy đang kết nối và thông báo cho Web khi có máy vào hoặc rời khỏi hệ thống.

**Ứng dụng Client** được cài đặt trên mỗi máy Windows cần điều khiển. Nó chạy ngầm, duy trì kết nối liên tục với Gateway, và tự động kết nối lại nếu mất mạng. Khi nhận được lệnh, nó kiểm tra quyền, thực thi tác vụ, rồi gửi kết quả về. Ứng dụng này cũng cung cấp một giao diện nhỏ để người dùng tại chỗ quản lý cài đặt quyền cho từng chức năng.

---

## Cơ chế cấp quyền

Trước khi thực thi bất kỳ lệnh nào, ứng dụng Client kiểm tra cài đặt quyền của chức năng tương ứng. Mỗi chức năng có thể được đặt ở một trong ba trạng thái: luôn cho phép, luôn từ chối, hoặc hỏi mỗi lần. Ở trạng thái hỏi mỗi lần, một cửa sổ popup xuất hiện trên máy bị điều khiển để người dùng tại chỗ quyết định cho phép hay từ chối lệnh đó; lệnh chỉ được thực thi sau khi có xác nhận. Người dùng tại chỗ có thể thay đổi cài đặt quyền bất kỳ lúc nào thông qua giao diện của ứng dụng Client.

---

## Các chức năng

Hệ thống cung cấp tám chức năng điều khiển.

**Applications** cho phép xem danh sách các ứng dụng đang chạy trên máy, mở một ứng dụng mới theo đường dẫn, hoặc đóng một ứng dụng đang chạy.

**Processes** cho phép xem toàn bộ danh sách tiến trình đang chạy trên máy, kèm theo mức sử dụng CPU và thông tin hàng đợi.

**Screenshot** chụp ảnh toàn bộ màn hình tại thời điểm yêu cầu và trả về một ảnh tĩnh duy nhất.

**Live Screen** truyền hình ảnh màn hình liên tục về giao diện Web theo thời gian thực. Người dùng Web không chỉ xem được mà còn có thể điều khiển chuột và bàn phím trên máy từ xa thông qua tính năng này.

**Key Logger** ghi lại mọi phím được nhấn trên máy bị điều khiển và gửi về giao diện Web ngay lập tức. Dữ liệu chỉ hiển thị trong phiên làm việc, không được lưu trữ lâu dài.

**File Download** cho phép duyệt cây thư mục trên máy bị điều khiển và tải bất kỳ file nào về máy của người dùng. File lớn được truyền theo từng phần để đảm bảo độ tin cậy.

**Webcam** truyền hình ảnh trực tiếp từ camera của máy bị điều khiển về giao diện Web liên tục.

**Power Control** cho phép ra lệnh tắt máy hoặc cho máy vào chế độ ngủ. Chức năng này bắt buộc phải có xác nhận từ người dùng tại chỗ và không thể đặt ở chế độ luôn cho phép mà không hỏi.

---

## Yêu cầu hành vi

Kết nối của ứng dụng Client với hệ thống phải bền vững — nếu mất kết nối vì bất kỳ lý do gì, nó phải tự động thử kết nối lại mà không cần can thiệp thủ công. Giao diện Web phải phản ánh trạng thái online/offline của từng máy ngay khi có thay đổi. Các chức năng truyền dữ liệu liên tục (Live Screen, Key Logger, Webcam) phải hoạt động theo thời gian thực mà không cần giao diện Web chủ động hỏi lại. Mỗi chức năng hoạt động độc lập; sự cố ở một chức năng không được ảnh hưởng đến các chức năng còn lại. Chỉ người dùng đã xác thực mới có thể gửi lệnh, và toàn bộ kết nối giữa các thành phần phải được mã hóa.
