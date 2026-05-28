Bạn là senior product designer kiêm frontend engineer. Hãy redesign màn hình “Create Video” của MoneyPrinterTurbo Studio theo hướng dễ dùng hơn, rõ hierarchy hơn, nhưng vẫn giữ đầy đủ sức mạnh cấu hình cho power user.

Bối cảnh:
Màn hình hiện tại là một form dài để tạo video ngắn. Người dùng nhập brief/script, chọn nguồn video như Pexels/Pixabay/TikTok, chọn voice/audio, cấu hình phụ đề, rồi bấm tạo video. Hiện tại UI có quá nhiều field hiển thị cùng lúc, phân cấp thị giác yếu, cột phải gồm render status/log/CTA nhưng chưa giúp user hiểu rõ tiến trình.

Trước khi sửa code, hãy đọc cấu trúc component hiện tại và đề xuất kế hoạch thay đổi ngắn gọn. Không rewrite toàn bộ app nếu chỉ cần refactor màn hình Create Video.

Mục tiêu redesign:
Tạo trải nghiệm “guided creation flow” thay vì một long technical form. Người dùng mới phải có thể hiểu ngay cần làm gì, còn power user vẫn có thể mở advanced options khi cần.

Yêu cầu chính:
1. Giữ layout 3 vùng: sidebar trái, main form ở giữa, sticky render panel bên phải.
2. Main form phải chia thành các card rõ ràng:
   - Nội dung
   - Nguồn video
   - Giọng đọc & âm thanh
   - Phụ đề & thương hiệu
   - Nâng cao
3. Các cấu hình ít dùng hoặc kỹ thuật phải được đưa vào accordion/collapse, mặc định đóng.
4. Cột phải phải được thiết kế lại thành sticky panel gồm:
   - Tóm tắt video
   - Preview khung video 9:16
   - CTA chính “Tạo video”
   - Progress/status hiện tại
   - Log hệ thống trong accordion, mặc định thu gọn
5. Nút “Tạo video” phải nổi bật, dễ thấy, và không bị chìm giữa log/config.
6. Trạng thái render phải thân thiện với người dùng, không chỉ là raw log. Ví dụ:
   - Đang tìm source
   - Đang tạo script
   - Đang tạo voice
   - Đang ghép video
   - Đang render phụ đề
   - Hoàn tất
7. Raw log vẫn cần giữ lại cho power user/debug, nhưng không được là trạng thái chính.
8. Copywriting cần ngắn, rõ, nhất quán tiếng Việt. Tránh label quá kỹ thuật ở trạng thái mặc định.
9. Thiết kế phải giúp user scan nhanh: section heading rõ, spacing rộng hơn, ít border nặng, visual hierarchy tốt hơn.
10. Không được loại bỏ tính năng hiện có; chỉ tổ chức lại, gom nhóm, hoặc ẩn dưới advanced options.

Wireframe mục tiêu:

┌──────────────────────────────────────────────────────────────────────────────┐
│ Create Video                                                                │
│ Tạo video ngắn từ brief hoặc kịch bản có sẵn                                │
│                                                                              │
│ [1 Nội dung] ─── [2 Nguồn video] ─── [3 Giọng đọc] ─── [4 Phụ đề & Xuất]    │
├───────────────────────────────────────┬──────────────────────────────────────┤
│                                       │                                      │
│  CARD 1: Nội dung                     │  PANEL STICKY                        │
│  ┌───────────────────────────────┐    │  ┌────────────────────────────────┐  │
│  │ Brief / ý tưởng               │    │  │ Tóm tắt video                  │  │
│  │ [ textarea ]                  │    │  │ Source: TikTok                 │  │
│  │ [ Gợi ý AI ] [ Tạo lại từ khóa]│   │  │ Ratio: 9:16                    │  │
│  └───────────────────────────────┘    │  │ Voice: Nam miền Nam            │  │
│                                       │  │ Subtitle: Clean Shorts         │  │
│  ┌───────────────────────────────┐    │  └────────────────────────────────┘  │
│  │ Kịch bản video                │    │                                      │
│  │ [ textarea lớn ]              │    │  ┌────────────────────────────────┐  │
│  └───────────────────────────────┘    │  │ Preview 9:16                   │  │
│                                       │  │ Mock video frame                │  │
│  ┌───────────────────────────────┐    │  └────────────────────────────────┘  │
│  │ Từ khóa video                 │    │                                      │
│  │ [ input / tags ]              │    │  ┌────────────────────────────────┐  │
│  └───────────────────────────────┘    │  │ [ Tạo video ]                  │  │
│                                       │  │ [ Lưu preset ]                 │  │
│  CARD 2: Nguồn video                  │  └────────────────────────────────┘  │
│  ┌───────────────────────────────┐    │                                      │
│  │ Nguồn: TikTok / Pexels / ...  │    │  ┌────────────────────────────────┐  │
│  │ Các field cơ bản              │    │  │ Tiến trình                     │  │
│  │ Tùy chọn nâng cao collapsed   │    │  │ Step hiện tại + progress bar   │  │
│  └───────────────────────────────┘    │  └────────────────────────────────┘  │
│                                       │                                      │
│  CARD 3: Giọng đọc & âm thanh         │  ┌────────────────────────────────┐  │
│  ┌───────────────────────────────┐    │  │ Nhật ký hệ thống               │  │
│  │ Engine, voice, speed, music   │    │  │ Accordion collapsed            │  │
│  └───────────────────────────────┘    │  └────────────────────────────────┘  │
│                                       │                                      │
│  CARD 4: Phụ đề & thương hiệu         │                                      │
│  ┌───────────────────────────────┐    │                                      │
│  │ Preset, font, vị trí, preview │    │                                      │
│  └───────────────────────────────┘    │                                      │
│                                       │                                      │
│  CARD 5: Nâng cao                     │                                      │
│  ┌───────────────────────────────┐    │                                      │
│  │ Aspect ratio, duration,       │    │                                      │
│  │ threads, cookie, debug config │    │                                      │
│  │ Mặc định thu gọn              │    │                                      │
│  └───────────────────────────────┘    │                                      │
└───────────────────────────────────────┴──────────────────────────────────────┘

Component cần có:
- SectionCard: card chứa từng nhóm cấu hình.
- AdvancedAccordion: dùng cho option kỹ thuật/ít dùng.
- VideoSummaryPanel: hiển thị tóm tắt output.
- VideoPreviewFrame: preview 9:16.
- RenderProgressPanel: hiển thị trạng thái render thân thiện.
- SystemLogPanel: log raw, collapse mặc định.
- PrimaryCTAGroup: nút Tạo video và Lưu preset.

Các trạng thái cần thiết kế:
1. Empty state: chưa nhập brief/script.
2. Ready state: đủ thông tin để tạo video.
3. Rendering state: đang tạo video, có progress.
4. Success state: render hoàn tất, hiển thị output/action mở thư mục.
5. Error state: lỗi render, hiển thị lỗi dễ hiểu và log chi tiết nếu cần.

Nguyên tắc UI:
- Ưu tiên readability và scanability.
- Mỗi section chỉ phục vụ một mục tiêu.
- Mặc định chỉ hiện cấu hình phổ biến.
- Advanced options không biến mất, chỉ được giấu hợp lý.
- Progress phải thân thiện với user phổ thông.
- Log là lớp phụ cho debug, không phải UI chính.
- Giữ style hiện tại nếu cần, nhưng cải thiện spacing, hierarchy và grouping.

Deliverable mong muốn:
- Cập nhật UI theo wireframe trên.
- Giữ nguyên logic nghiệp vụ hiện có.
- Không làm mất config hiện có.
- Nếu có thể, refactor component để form dễ bảo trì hơn.
- Sau khi hoàn thành, mô tả ngắn những thay đổi đã thực hiện và những phần nào vẫn giữ nguyên.