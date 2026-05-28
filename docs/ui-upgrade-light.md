Hãy sửa UI/UX của app theo hướng ổn định, light mode only và bám sát DESIGN.md. Lưu ý: lần tối ưu trước làm giao diện lỗi hơn, nên lần này KHÔNG được redesign tự do toàn bộ app. Hãy sửa theo hướng có kiểm soát, ưu tiên ổn định layout, sidebar, spacing và component consistency.

Bắt buộc:
1. Đọc kỹ DESIGN.md trước khi sửa.
2. Không dùng dark mode. Không thêm theme switcher. Không để global background màu đen/tối.
3. Nếu code hiện tại có dark theme, class dark, CSS variable dark, hoặc style nền đen đang áp lên toàn app, hãy loại bỏ/vô hiệu hóa để app luôn là light mode.
4. Không thay đổi business logic, route, data flow, API call, render flow hoặc chức năng hiện có.
5. Không sửa lan man từng chỗ nếu có thể sửa ở layout/component foundation.
6. Sau mỗi nhóm thay đổi, kiểm tra lại visual bằng cách chạy app và xem các page: Create, Projects, Assets, Brand.

Mục tiêu UI:
- App dùng light theme: background tổng thể neutral light, surface/card trắng, border nhẹ, text tối dễ đọc.
- Sidebar gọn, usable và nhất quán ở cả expanded/collapsed state.
- Content layout có container/padding/max-width hợp lý, không bị kéo quá rộng hoặc lệch nhịp.
- Spacing giữa section/card/input/button/table đồng đều theo scale rõ ràng.
- Component sizing nhất quán: input/select/button/table row/card padding/radius/border.
- Table không phá layout khi có path dài; cần truncate, wrap hợp lý hoặc horizontal scroll trong container.
- Preview/video không chiếm quá nhiều chiều rộng/chiều cao gây mất cân bằng.
- Typography có hierarchy rõ: page title, section title, label, helper text, table text.

Các vấn đề cần sửa cụ thể theo screenshot hiện tại:

1. Global theme
- Chuyển toàn bộ app sang light mode only.
- Body/app background không dùng black.
- Text không dùng màu trắng mặc định trên nền tối nữa; dùng text color phù hợp light theme.
- Card/table/form/input/select/accordion dùng cùng hệ surface/border.
- Loại bỏ visual conflict kiểu table trắng nằm trong app nền đen.

2. Sidebar
- Expanded sidebar width khoảng 220–240px nếu desktop, nhưng nav item không được quá to.
- Collapsed sidebar width khoảng 64–72px.
- Collapsed state vẫn phải hiển thị icon/logo compact/active state, không được trống.
- Thay các chữ cái “P/A/B” nếu có thể bằng icon rõ nghĩa hoặc ít nhất giữ label/tooltip hợp lý.
- Nav item height/padding/spacing phải nhất quán.
- Active state rõ nhưng không quá gắt; dùng background nhẹ + text/icon primary.
- Sidebar phải bám cùng light theme, không dùng nền đen.

3. App shell và content
- Tạo layout shell rõ: sidebar bên trái, main content bên phải.
- Main content nên có padding đồng nhất, ví dụ 32px desktop, 20–24px tablet/mobile.
- Header/top bar và page title cần align theo cùng grid.
- Content max-width nên hợp lý. Form page có thể max-width khoảng 960–1120px; table page có thể rộng hơn nhưng nằm trong container có overflow xử lý.
- Không để mỗi page có margin/padding khác nhau tùy tiện.

4. Create page
- Chia thành các section/card rõ: Brief & Script, Source & Materials, Voice & Audio, Subtitles & Brand, Render & Monitor.
- Section spacing đồng đều.
- Input/select/textarea width và height nhất quán.
- Textarea lớn vừa đủ, không tạo khoảng trống quá nặng.
- Render & Monitor sidebar/card bên phải cần align tốt với form chính; nếu màn hình hẹp thì stack xuống dưới.
- Warning/status card dùng màu light semantic nhẹ, không dùng nền quá tối.
- Button chính “Tạo Video” nổi bật nhưng vẫn trong design system.

5. Projects page
- Table cần nằm trong card/surface nhất quán, không bị chói hoặc tách khỏi theme.
- Các cột path dài phải truncate bằng ellipsis hoặc cho scroll ngang trong table container, không làm vỡ layout.
- Row height, header style, border table đồng đều.
- Preview video hiện quá lớn; đặt trong preview card có max-width hợp lý, ví dụ 480–720px tùy layout, hoặc chia layout 2 cột nếu phù hợp.
- Các button “Reuse”, “Continue”, “Open Project Folder” cần cùng height/spacing và disabled state rõ ràng.

6. Assets page
- Source diagnostics và TikTok cache table cần cùng style với Projects table.
- Path dài phải truncate/scroll trong container.
- Empty state “No assets found” nên là light info card, không phải block nền tối.
- Page quá rộng; cần container và table overflow hợp lý.

7. Brand page
- Preview “Clean Vietnamese Shorts” hiện quá lớn và áp đảo page. Giảm preview height/font-size, biến nó thành preview card gọn hơn.
- Form tạo preset cần chia nhóm rõ, spacing đều.
- Slider, color picker, select, number input, button phải cùng style light theme.
- Button disabled cần nhìn disabled rõ nhưng không chói.
- Tránh dùng accent đỏ quá mạnh nếu DESIGN.md không quy định.

Quy trình thực hiện:
1. Tìm file định nghĩa theme/global CSS/layout/sidebar/component primitives.
2. Sửa light theme foundation trước.
3. Sửa AppShell/Sidebar/MainLayout.
4. Sửa component styles dùng chung: Button, Input, Select, Textarea, Table, Card, Accordion.
5. Sau đó mới tinh chỉnh từng page Create, Projects, Assets, Brand.
6. Chạy app và kiểm tra screenshot/visual regression thủ công.
7. Báo cáo lại: đã sửa file nào, thay đổi chính là gì, còn rủi ro gì cần kiểm tra.

Tiêu chí hoàn thành:
- Không còn dark mode.
- Create/Projects/Assets/Brand đều dùng cùng light visual system.
- Sidebar expanded/collapsed đều usable.
- Spacing và sizing đồng đều hơn rõ rệt.
- Table/path dài không phá layout.
- Video/preview không làm page mất cân bằng.
- Không làm hỏng chức năng hiện tại.\