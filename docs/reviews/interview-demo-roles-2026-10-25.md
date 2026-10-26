# Rà soát nội dung nhóm role demo — 2026-10-25

## Phạm vi

Catalog hiện không có ID chung `frontend_developer` hoặc `software_engineer`. Lượt rà soát dùng ba role tồn tại và có ngân hàng câu hỏi: `data_analyst` (6 câu), `frontend_developer_react` (7 câu) và `backend_developer_java` (7 câu), tổng 20 câu.

Trong 20 câu, 4 câu đã mang metadata review nội bộ trước lượt này (`data_analyst_q01`, `data_analyst_q02`, `backend_developer_java_q02`, `backend_developer_java_q03`). 16 câu còn lại đã được biên tập đáp án và các ý tự phản tư, sau đó gắn `quality=ai_reviewed_internal`, reviewer, ngày, ghi chú giới hạn và nguồn kỹ thuật.

## Phương pháp và giới hạn

- Rà theo bốn câu hỏi: nội dung có gắn với role không; câu trả lời có đủ cụ thể và có điều kiện/edge cases không; các ý tự phản tư có thể quan sát được không; nguồn kỹ thuật có liên quan trực tiếp không.
- Câu hỏi hành vi/tình huống giữ trọng tâm vào tình huống thật, trách nhiệm cá nhân, hành động, bằng chứng kết quả và bài học; không khuyến khích bịa số liệu.
- Các nguồn chính thức được lưu trực tiếp trong `quality_sources` của từng câu. Chúng hỗ trợ kiểm tra chủ đề kỹ thuật, không xác minh ứng viên, không chứng minh câu hỏi đã được kiểm định psychometric.
- Trạng thái `ai_reviewed_internal` chỉ có nghĩa AI hỗ trợ biên tập/rà soát cấu trúc. Nó không được gộp với 6 bản ghi có review nội bộ hiện hữu, không phải review chuyên gia độc lập và cần owner/chuyên gia xác nhận trước khi dùng trong tuyển dụng thật.
- Phần này là hướng dẫn tự phản tư; ứng dụng không chấm điểm câu trả lời.

## Nguồn chính thức dùng làm căn cứ kỹ thuật

- [React: Rendering Lists](https://react.dev/learn/rendering-lists)
- [MDN: HTML accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML)
- [MDN: CSS media queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries)
- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [Redux Toolkit: Usage Guide](https://redux-toolkit.js.org/usage/usage-guide/)
- [Spring Boot: Dependency Injection](https://docs.spring.io/spring-boot/reference/using/spring-beans-and-dependency-injection.html)
- [Spring Boot: Testing](https://docs.spring.io/spring-boot/reference/testing/)
- [PostgreSQL: Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- [PostgreSQL: Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [Git: gittutorial](https://git-scm.com/docs/gittutorial/2.46.1)
- [U.S. OPM: Structured Interview Guide](https://www.opm.gov/policy-data-oversight/assessment-and-selection/structured-interviews/guide/)

## Bằng chứng kiểm tra

- `scripts/validate_question_bank.py` kiểm tra số lượng, role/skill tham chiếu, trùng lặp, độ dài, hướng dẫn trả lời và provenance review.
- `tests/test_question_bank_integrity.py` giữ kỳ vọng 752 câu/131 role và kiểm tra từ chối AI review thiếu nguồn/giới hạn.
- `tests/test_interview_assessment.py` xác nhận ba role demo có 20/20 câu với hướng dẫn và status AI được trình bày riêng.
