Bạn là senior product designer kiêm frontend engineer. Hãy redesign màn hình “Projects” của MoneyPrinterTurbo Studio theo hướng dễ scan hơn, quản lý task rõ hơn, và preview video tiện hơn, nhưng vẫn giữ đầy đủ thông tin kỹ thuật cho power user.

Bối cảnh:
Màn hình Projects hiện tại dùng để review các render task gần đây, xem preview video, xem script/keyword/log, reuse task trong Create, continue task trong Create, và mở project folder. UI hiện tại gồm bảng task ở trên, dropdown preview task, path dài, accordion script/log, các nút action, và video preview lớn ở dưới.

Vấn đề hiện tại:
1. Bảng task quá kỹ thuật, nhiều ID/path dài, làm user khó scan nhanh.
2. Các task chưa có hierarchy rõ: task nào mới, task nào đang render, task nào lỗi, task nào hoàn tất.
3. Cột path chiếm nhiều không gian nhưng ít hữu ích ở trạng thái mặc định.
4. Preview task nằm dưới bảng nhưng chưa đủ kết nối trực quan với row đang chọn.
5. Video preview quá lớn và đẩy các thông tin/action quan trọng ra xa.
6. Các action “Reuse in Create”, “Continue in Create”, “Open Project Folder” đang nằm ngang nhưng chưa rõ action chính/phụ.
7. Render log và script/keywords đang bị giấu trong accordion, nhưng không có summary ngắn phía ngoài.
8. Page thiếu filter/search/sort rõ ràng cho một danh sách task có thể tăng dần theo thời gian.
9. Empty/loading/error states chưa rõ.
10. Copy và label còn thiên về kỹ thuật, cần thân thiện hơn với người dùng phổ thông.

Mục tiêu redesign:
Biến Projects page thành một “project/task dashboard” gồm danh sách task dễ lọc ở bên trái hoặc phía trên, và panel chi tiết/preview rõ ràng ở bên phải hoặc bên dưới. User phải có thể nhanh chóng trả lời:
- Task nào vừa tạo?
- Task nào render xong?
- Task nào lỗi?
- Task này tạo từ source nào?
- Video output trông như thế nào?
- Tôi có thể tiếp tục/reuse/mở folder ở đâu?

Yêu cầu chính:
1. Giữ layout tổng thể có sidebar trái và content chính.
2. Redesign phần Projects thành 2 vùng chính:
   - Task list / task table
   - Task detail / video preview panel
3. Bảng task phải dễ scan hơn:
   - Hiển thị subject/title nổi bật hơn ID.
   - ID task chỉ hiện dạng rút gọn hoặc trong detail.
   - Path dài không hiển thị trực tiếp trong table, chỉ đưa vào detail/copy button.
   - Dùng badge cho source: TikTok, Pexels, Pixabay.
   - Dùng badge/status rõ ràng: Done, Rendering, Failed, Draft, Empty.
   - Dùng progress bar hoặc % gọn.
4. Thêm toolbar phía trên task list:
   - Search task theo subject/source/id.
   - Filter theo source.
   - Filter theo status.
   - Sort theo newest/progress/status.
5. Khi chọn một task, detail panel phải hiển thị:
   - Subject/title.
   - Status.
   - Source.
   - Number of videos.
   - Progress.
   - Created/updated time nếu có dữ liệu.
   - Short path với nút copy/open folder.
   - Script & keywords summary.
   - Render log summary.
   - Video preview.
6. Video preview không nên chiếm toàn bộ chiều ngang ngay lập tức. Nên nằm trong card preview có max width hợp lý, giữ tỷ lệ 9:16 hoặc responsive.
7. Action hierarchy cần rõ:
   - Primary action: Continue in Create hoặc Open Video tùy state.
   - Secondary actions: Reuse in Create, Open Project Folder.
   - Utility actions: Copy path, View log.
8. Script/keywords và render log vẫn có thể dùng accordion, nhưng bên ngoài cần có summary ngắn:
   - “Script: 520 words, 8 keywords”
   - “Log: completed, no errors”
9. Nếu task chưa có video hoặc videos = 0, preview card phải có empty state rõ: “Chưa có video output”.
10. Nếu task lỗi, hiển thị error summary dễ hiểu và cho phép mở log chi tiết.
11. Không loại bỏ thông tin kỹ thuật; chỉ chuyển thông tin kỹ thuật xuống detail hoặc advanced/debug sections.
12. Giữ logic nghiệp vụ hiện có, không rewrite toàn bộ app nếu không cần.

Wireframe mục tiêu:

┌──────────────────────────────────────────────────────────────────────────────┐
│ Projects                                                                     │
│ Quản lý render task, xem lại video và tiếp tục chỉnh sửa.                    │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Search tasks...        Source: All       Status: All       Sort: Newest  │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌──────────────────────────────────────┬───────────────────────────────────┐ │
│ │ TASK LIST                            │ TASK DETAIL                       │ │
│ │                                      │                                   │ │
│ │ ┌──────────────────────────────────┐ │ ┌───────────────────────────────┐ │ │
│ │ │ Hoạt hình không chỉ...           │ │ │ Hoạt hình không chỉ...        │ │ │
│ │ │ TikTok  •  Done  •  1 video      │ │ │ TikTok  Done  100%            │ │ │
│ │ │ Progress: 100%                   │ │ │ Task ID: d3a67136...          │ │ │
│ │ └──────────────────────────────────┘ │ │ Path: /storage/tasks/...       │ │ │
│ │                                      │ │ [Copy path] [Open folder]      │ │ │
│ │ ┌──────────────────────────────────┐ │ └───────────────────────────────┘ │ │
│ │ │ 5 thói quen giúp ngủ ngon hơn    │ │                                   │ │
│ │ │ TikTok  •  Done  •  1 video      │ │ ┌───────────────────────────────┐ │ │
│ │ │ Progress: 100%                   │ │ │ Video Preview                 │ │ │
│ │ └──────────────────────────────────┘ │ │ │                               │ │ │
│ │                                      │ │ │       9:16 video frame        │ │ │
│ │ ┌──────────────────────────────────┐ │ │ │                               │ │ │
│ │ │ Thi cấp 3                        │ │ │ │ [video player]                │ │ │
│ │ │ Pexels • Draft • 0 video         │ │ │ │                               │ │ │
│ │ │ Progress: 0%                     │ │ │ └───────────────────────────────┘ │ │
│ │ └──────────────────────────────────┘ │ │                                   │ │
│ │                                      │ │ ┌───────────────────────────────┐ │ │
│ │                                      │ │ │ Actions                       │ │ │
│ │                                      │ │ │ [Continue in Create]          │ │ │
│ │                                      │ │ │ [Reuse] [Open Project Folder] │ │ │
│ │                                      │ │ └───────────────────────────────┘ │ │
│ │                                      │ │                                   │ │
│ │                                      │ │ ┌───────────────────────────────┐ │ │
│ │                                      │ │ │ Script & Keywords             │ │ │
│ │                                      │ │ │ Summary line                  │ │ │
│ │                                      │ │ │ [Accordion detail]            │ │ │
│ │                                      │ │ └───────────────────────────────┘ │ │
│ │                                      │ │                                   │ │
│ │                                      │ │ ┌───────────────────────────────┐ │ │
│ │                                      │ │ │ Render Log                    │ │ │
│ │                                      │ │ │ Completed, no errors          │ │ │
│ │                                      │ │ │ [View full log]               │ │ │
│ │                                      │ │ └───────────────────────────────┘ │ │
│ └──────────────────────────────────────┴───────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘

Nếu muốn giữ table thay vì card list, dùng wireframe này:

┌──────────────────────────────────────────────────────────────────────────────┐
│ Projects                                                                     │
│ Quản lý render task, xem lại video và tiếp tục chỉnh sửa.                    │
│                                                                              │
│ [Search] [Source filter] [Status filter] [Sort]                              │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Subject              Source    Videos   Progress    Status     Updated   │ │
│ │ Hoạt hình...         TikTok    1        █████ 100%   Done       Today     │ │
│ │ 5 thói quen...       TikTok    1        █████ 100%   Done       Today     │ │
│ │ Thi cấp 3            Pexels    1        ░░░░░ 0%     Draft      Today     │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Selected task detail                                                     │ │
│ │ Subject, metadata, actions, preview, script/log accordion                 │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘

Khuyến nghị:
Nếu số lượng task thường ít, dùng card list + detail panel sẽ dễ dùng hơn.
Nếu số lượng task nhiều, giữ table nhưng cần thêm toolbar filter/search và detail panel rõ hơn.
Ưu tiên của tôi: card list + detail panel, vì page này thiên về review video hơn là quản lý dữ liệu dạng spreadsheet.

Component cần có:
- ProjectsToolbar: search, source filter, status filter, sort.
- TaskList: danh sách task dạng card hoặc table.
- TaskListItem hoặc TaskTableRow: hiển thị subject, source badge, status badge, videos, progress.
- StatusBadge: Done, Rendering, Failed, Draft, Empty.
- SourceBadge: TikTok, Pexels, Pixabay.
- ProgressIndicator: % và progress bar nhỏ.
- TaskDetailPanel: metadata của task đang chọn.
- VideoPreviewCard: video player hoặc empty state.
- TaskActionGroup: Continue, Reuse, Open folder, Copy path.
- ScriptKeywordsPanel: summary + accordion detail.
- RenderLogPanel: summary + accordion/debug detail.
- EmptyProjectsState: khi chưa có project nào.
- TaskErrorState: khi task lỗi hoặc thiếu output video.

Các trạng thái cần thiết kế:
1. Loading state:
   - Skeleton cho task list.
   - Skeleton cho detail panel.
2. Empty state:
   - “Chưa có project nào”
   - CTA “Tạo video đầu tiên”
3. No selected task:
   - “Chọn một task để xem chi tiết”
4. Ready/done state:
   - Có video preview.
   - Action chính rõ.
5. Rendering state:
   - Progress bar.
   - Status text thân thiện.
   - Disable hoặc thay đổi action phù hợp.
6. Failed state:
   - Error summary.
   - CTA “Xem log” hoặc “Thử lại trong Create”.
7. Missing video state:
   - Hiển thị placeholder thay vì để khu vực trắng hoặc player lỗi.

Quy tắc hiển thị dữ liệu:
- Subject là thông tin chính trong list.
- Task ID chỉ hiển thị rút gọn, ví dụ d3a67136..., và full ID chỉ trong detail/copy.
- Path không hiển thị nguyên dòng dài trong table.
- Source dùng badge màu nhẹ.
- Status dùng badge màu rõ:
  - Done: xanh
  - Rendering: xanh dương hoặc tím
  - Failed: đỏ
  - Draft/Empty: xám
- Progress dùng cả % và progress bar nhỏ.
- Nếu videos = 0, hiển thị “No video” hoặc “Chưa có video”.
- Nếu progress = 100 và state done, ưu tiên action “Open video” hoặc “Open folder”.
- Nếu progress < 100 hoặc state rendering, ưu tiên hiển thị progress/status.
- Nếu state failed, ưu tiên hiển thị error summary.

Microcopy đề xuất:
- “Projects” → giữ nguyên nếu app đang dùng tiếng Anh, hoặc đổi thành “Dự án” nếu đang ở tiếng Việt.
- Subtitle: “Review recent render tasks and open final videos without leaving the studio.”
  Có thể đổi thành: “Xem lại video đã render, kiểm tra log và tiếp tục chỉnh sửa.”
- “Preview task” → “Task đang chọn”
- “Script and keywords” → “Kịch bản & từ khóa”
- “Render log” → “Nhật ký render”
- “Reuse in Create” → “Dùng lại cấu hình”
- “Continue in Create” → “Tiếp tục chỉnh sửa”
- “Open Project Folder” → “Mở thư mục dự án”

Implementation guidance:
1. Trước khi sửa code, hãy đọc cấu trúc component hiện tại của Projects page.
2. Xác định data model hiện tại của task: id, subject, source, videos, progress, state, path, script, keywords, logs, output video.
3. Không thay đổi backend/data model nếu không cần.
4. Refactor UI bằng cách tạo component nhỏ, không dồn tất cả logic vào một file lớn.
5. Giữ nguyên các action hiện có: reuse, continue, open folder, preview video, view script/log.
6. Nếu chưa có dữ liệu cho created/updated time, không tự thêm giả; chỉ thiết kế slot để hỗ trợ sau.
7. Nếu task state đang là None hoặc rỗng, map sang Draft/Unknown bằng helper rõ ràng.
8. Nếu path quá dài, truncate ở giữa và thêm copy button.
9. Nếu video không tồn tại, hiển thị empty preview state.
10. Sau khi hoàn thành, mô tả ngắn các thay đổi UI và xác nhận các action cũ vẫn hoạt động.

Deliverable mong muốn:
- Projects page mới có task list dễ scan.
- Có search/filter/sort nếu data hiện tại cho phép.
- Có detail panel rõ cho task đang chọn.
- Có video preview card gọn, không phá layout.
- Có status/progress thân thiện.
- Có log/script detail nhưng không làm rối UI mặc định.
- Không làm mất bất kỳ tính năng hiện có nào.