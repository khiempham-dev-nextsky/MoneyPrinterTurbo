# UI/UX Audit Và Quyết Định Thiết Kế

## Nguồn Chuẩn

Tài liệu `DESIGN.md` là nguồn chuẩn cho lần cải thiện UI này. Các điểm chính được áp dụng:

- Nền chính gần đen tuyệt đối: `#000000`.
- Bảng màu monochrome, chỉ dùng `#c3d9f3` cho link khi cần.
- Bề mặt, card, input và preview dùng góc vuông `0px`; chỉ button dùng dạng pill.
- Type hierarchy ưu tiên chữ uppercase, letter spacing rộng cho heading, nav và button.
- Spacing theo scale 4px: 8, 12, 16, 24, 40px cho UI vận hành; các khoảng 120px trong `DESIGN.md` được xem là rhythm cho marketing/photo band, không áp nguyên xi vào dashboard thao tác dày đặc.

## Mâu Thuẫn Với UI Cũ

- UI cũ là dashboard sáng với xanh/tím accent; `DESIGN.md` yêu cầu dark monochrome.
- Card và preview cũ bo góc 8px; `DESIGN.md` yêu cầu `rounded.none` cho mọi surface ngoài button.
- Native Streamlit navigation không kiểm soát tốt trạng thái sidebar thu gọn, active và hover; yêu cầu hiện tại cần sidebar usable ở cả expanded/collapsed.
- Spacing cũ dựa vào `divider`, `expander` và column gap rời rạc; chưa có nhịp 4px token rõ ràng.

## Quyết Định Triển Khai

Chọn hướng A: custom compact shell.

- Thay native `st.navigation` bằng sidebar riêng trong `webui/studio/navigation.py`.
- Sidebar expanded hiển thị icon chữ + label; collapsed chỉ giữ icon chữ nhưng vẫn có tooltip qua `help`.
- Active state dùng `type="primary"` kết hợp CSS outline trắng, không dùng màu accent.
- Theme mới nằm trong `webui/studio/theme.py`, gom token màu/spacing và CSS override tập trung.
- Flow nghiệp vụ Create, Projects, Assets, Brand, Settings giữ nguyên; chỉ thay shell, visual hierarchy, spacing và sizing.

## Kiểm Chứng

- Smoke test đảm bảo app render được từng page trong custom shell.
- Smoke test đảm bảo collapsed sidebar vẫn còn icon navigation.
- Static test đảm bảo không còn dùng `st.navigation` và theme có token `DESIGN.md` chính.
