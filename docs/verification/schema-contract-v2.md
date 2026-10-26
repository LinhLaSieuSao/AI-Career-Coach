# Hợp đồng dữ liệu 2.0: Role × Skill × Level × Evidence

Ngày áp dụng: 26-10-2026. Đây là hợp đồng **cấu trúc và cách diễn giải** cho dữ liệu local. Một trường có mặt nhưng `null`, `unknown` hoặc `pending` không phải bằng chứng đã xác minh. Không chuyển nhãn review chuyên gia hay quyền sử dụng bằng script di trú.

## Rubric hành vi Level 1–3

| Level | Yêu cầu nghề quan sát được | Học liệu có thể hỗ trợ | Câu hỏi và bằng chứng cần thu |
| --- | --- | --- | --- |
| 1 — nền tảng | Giải thích thuật ngữ, làm tác vụ một bước theo hướng dẫn/checklist; biết khi nào cần hỗ trợ. | Bài nhập môn, thao tác có hướng dẫn và ví dụ đơn giản. | Nhận diện khái niệm, giải thích quyết định cơ bản, phát hiện lỗi rõ; có ví dụ đầu vào/đầu ra. |
| 2 — áp dụng độc lập | Hoàn thành tác vụ quen thuộc không cần hướng dẫn từng bước; xử lý lỗi thường gặp, kiểm tra kết quả và phối hợp với người liên quan. | Lab hoặc bài tập theo tình huống có ngoại lệ thường gặp và bước kiểm chứng. | Tình huống có bối cảnh, ràng buộc và sản phẩm bàn giao; hỏi phương án, ngoại lệ, kiểm thử và đánh đổi cơ bản. |
| 3 — phức tạp và dẫn dắt | Thiết kế/điều chỉnh giải pháp cho ca mới hoặc rủi ro cao; phân tích đánh đổi, điều tra nguyên nhân, đặt chuẩn và rà soát cho người khác. | Chương chuyên sâu, case study, thiết kế hệ thống, tài liệu chuẩn hoặc bài thực hành phức tạp với phản hồi. | Tình huống đa ràng buộc; yêu cầu phân tích quyết định, tác động, phục hồi, chứng cứ và giới hạn áp dụng. |

Level mô tả phạm vi nhiệm vụ, không phải số năm kinh nghiệm hoặc chứng chỉ. Level của học liệu nói **nội dung hỗ trợ** mức nào, không xác nhận người dùng đạt mức đó. Với kỹ năng mềm, sản phẩm bàn giao có thể là kịch bản role-play, checklist quan sát, phản hồi của người giám sát và nhật ký cải thiện; không buộc phải có khóa học.

## Schema cấu trúc

Mỗi resource có `scope_granularity` thuộc `lesson`, `module`, `chapter`, `spec`, `course`, `learning_path`, `catalog`, `unknown`; `evidence_locator` là chuỗi cụ thể hoặc `null`. `catalog`/`unknown` được lưu để **phát hiện tồn đọng**, không được coi là bài học đủ Level. Không ép một trang chủ thành `module` để qua gate.

`verification_axes` có sáu khóa: `access_status`, `content_fit`, `level_fit`, `rights_basis`, `practice_type`, `last_live_checked`. Giá trị truy cập `user_attested_manual` chỉ dẫn tới bản ghi 165 URL do chủ dự án báo đã mở; nó không chứng minh nội dung hay quyền. `rights_basis=pending` đến khi có căn cứ thực. `last_live_checked=null` nếu không có bản kiểm tra mạng độc lập cho chính record.

Mỗi câu hỏi có `context_scenario` (chuỗi hoặc `null`), `evaluation_rubric` với `level_1_criteria`, `level_2_criteria`, `level_3_criteria` (chuỗi hoặc `null`), `red_flags` là danh sách chuỗi, và `provenance`. Trường `null` là backlog viết nội dung; không tự suy từ đáp án tham khảo hoặc nâng `quality`.

`provenance` thống nhất bảy trường cho resource, câu hỏi và về sau cho role: `source_url`, `author_origin`, `curated_by`, `review_tier`, `reviewed_at`, `rights_basis`, `license_notes`. URL bài học có thể điền `source_url` cho resource nhưng không nói ai sáng tác mapping. `quality_sources` là nguồn tham khảo câu trả lời, không tự chứng minh tác giả hay quyền của câu hỏi. `rights_basis` và `license_notes` chỉ điền khi có bằng chứng; **MIT của mã nguồn không tự áp cho dữ liệu**.

### Mẫu record với phần chưa xác minh

```json
{
  "scope_granularity": "catalog",
  "evidence_locator": "Danh mục Google Analytics tại trang chủ Skillshop",
  "verification_axes": {
    "access_status": "user_attested_manual",
    "content_fit": "internally_reviewed_partial",
    "level_fit": "internally_bounded",
    "rights_basis": "pending",
    "practice_type": "unknown",
    "last_live_checked": null
  },
  "provenance": {
    "source_url": "https://skillshop.withgoogle.com/",
    "author_origin": null,
    "curated_by": null,
    "review_tier": "internal_partial_unattributed",
    "reviewed_at": "2026-10-26",
    "rights_basis": null,
    "license_notes": null
  }
}
```

## Hai loại gate

`scripts/validate_evidence_schema.py` mặc định kiểm **cấu trúc, enum, khóa ngoại Role–Skill–Level và không tự nâng trục bằng chứng**. PASS của gate này đóng giai đoạn 1 về mặt schema, **không** có nghĩa đã đạt 100% aligned hoặc đủ quyền công bố. Tùy chọn `--require-complete-evidence` là gate nghiệm thu nội dung: `context_scenario`, rubric ở Level câu hỏi, scope đơn vị nhỏ, quyền/provenance và nguồn phù hợp phải có bằng chứng. Nó được kỳ vọng báo PENDING trên dữ liệu hiện tại; CI chạy gate cấu trúc để không cho schema thoái lui. Kết quả pending được ghi trong báo cáo, không đổi thành PASS bằng placeholder.

## Kiểm tra thực tế trước khi chấm điểm

Trong snapshot trước di trú: 1.192 cặp role–skill; 750 có ít nhất một câu hỏi **cùng skill**, 674 có học liệu đúng Level; 442 cặp thiếu câu hỏi theo role–skill. Con số 442 chưa phải số ô Skill × Level toàn catalog. `unsuitable`/`blocked` là trạng thái policy nội dung, không đồng nghĩa 216 URL chết. Một bài học mở được vẫn có thể sai Level hoặc chưa có quyền tái sử dụng. Không quy đổi các số kiểm tra cấu trúc thành điểm giám khảo.
