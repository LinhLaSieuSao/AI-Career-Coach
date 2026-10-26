"""Curate four demo question sets without claiming human review.

Default is a read-only dry run. --apply backs up every changed part file,
refuses unexpected editorial changes, and is idempotent. This is an AI draft.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.migrate_evidence_schema_v2 import _format_json

BANK_DIR = ROOT / "Data/interview_question"
BACKUP_DIR = ROOT / "dist/data-backups/step3-demo-questions"
ROLES = ("sales_executive", "frontend_developer_react", "data_analyst", "backend_developer_java")

# These are fictional interview exercises, not observed recruitment cases.
CONTEXTS = {
    "sales_executive_q01": "SME đang chọn gói CRM cho 20 nhân viên. Người liên hệ muốn triển khai trong 4 tuần nhưng chưa xác nhận ngân sách hoặc người ký; bạn chuẩn bị cuộc khám phá nhu cầu đầu tiên.",
    "sales_executive_q03": "Pipeline CRM cho SME có 60 liên hệ mới nhưng chỉ 6 cơ hội đủ điều kiện trong hai tuần; nguồn lead từ hai kênh và CRM có bản ghi trùng.",
    "frontend_developer_react_q01": "Trang React liệt kê 500 sản phẩm, có ảnh thiếu, dữ liệu rỗng và người dùng điều hướng bằng bàn phím; bạn chịu trách nhiệm cấu trúc HTML.",
    "frontend_developer_react_q02": "Danh sách sản phẩm phải dùng được từ màn hình 320 px đến desktop; tên sản phẩm dài, ảnh không đồng nhất và trạng thái focus phải nhìn thấy.",
    "frontend_developer_react_q03": "Người dùng đổi bộ lọc hai lần liên tiếp; API trả lời lần đầu sau lần thứ hai, đôi lúc trả HTTP 500 hoặc dữ liệu thiếu trường giá.",
    "frontend_developer_react_q04": "Danh sách 500 sản phẩm có lọc và sắp xếp; một sản phẩm thay đổi vị trí sau cập nhật và giao diện phải giữ đúng state của từng thẻ.",
    "frontend_developer_react_q05": "Bộ lọc sản phẩm được dùng ở danh sách và thanh điều hướng; nhóm đang cân nhắc Redux Toolkit so với state cục bộ khi API có trạng thái tải và lỗi.",
    "frontend_developer_react_q06": "Frontend, thiết kế và backend cùng sửa trang sản phẩm trong một sprint; response API đổi tên trường khi pull request giao diện đang chờ review.",
    "frontend_developer_react_q07": "Thiết kế yêu cầu thẻ sản phẩm bấm được, QA báo điều hướng bàn phím không hoạt động; bạn cần thống nhất lại tiêu chí chấp nhận với designer và QA.",
    "data_analyst_q01": "Bảng orders có một dòng mỗi đơn, campaign_events có nhiều dòng mỗi đơn; sau join, doanh thu chiến dịch tăng gấp đôi so với nguồn.",
    "data_analyst_q02": "Dashboard chiến dịch đổi tổng doanh thu khi lọc ngày dù bảng nguồn chưa đổi; nhóm cần phân biệt ngày đặt hàng và ngày sự kiện.",
    "data_analyst_q03": "Báo cáo tuần và dashboard dùng hai định nghĩa conversion khác nhau; marketing cần công bố một chỉ số trước cuộc họp ngày mai.",
    "data_analyst_q04": "Hai tệp CSV chiến dịch có kiểu ngày khác nhau, cột khách hàng có null và dữ liệu trùng; script Python phải chạy lại với kết quả đối soát được.",
    "data_analyst_q05": "Bảng Excel xuất từ CRM có dòng trùng, ngày dạng text và doanh thu âm do hoàn tiền; cần lập pivot theo chiến dịch có thể tái kiểm tra.",
    "data_analyst_q06": "Marketing và tài chính bất đồng về doanh thu chiến dịch vì một nhóm tính đơn đã hoàn; bạn phải khoanh vùng nguyên nhân trước khi sửa dashboard.",
    "backend_developer_java_q01": "Dịch vụ Java nhận hai yêu cầu đặt cùng sản phẩm gần đồng thời khi tồn kho còn một; đơn hàng, giá tiền và trạng thái phải nhất quán.",
    "backend_developer_java_q02": "Endpoint tạo đơn Spring Boot nhận request thiếu số lượng và mã sản phẩm; nhóm muốn lỗi 400 rõ ràng mà không đưa stack trace ra client.",
    "backend_developer_java_q03": "Client gửi POST tạo đơn rồi timeout và thử lại; API cần phản hồi HTTP rõ ràng và tránh ghi đơn trùng theo hợp đồng đã thống nhất.",
    "backend_developer_java_q04": "Hai request đồng thời trừ cùng một đơn vị tồn kho; bảng đơn và tồn kho phải đồng bộ nếu ghi dữ liệu thất bại giữa chừng.",
    "backend_developer_java_q05": "Hai pull request cùng sửa contract tạo đơn và file migration; trước merge xuất hiện conflict và CI báo một integration test lỗi.",
    "backend_developer_java_q06": "Tỷ lệ 5xx của endpoint tạo đơn tăng sau triển khai, một số request đã ghi đơn trước khi lỗi; nhóm cần giảm ảnh hưởng rồi tìm nguyên nhân.",
    "backend_developer_java_q07": "Frontend hiểu phản hồi lỗi 409 là 400 trong khi QA dùng contract cũ; bạn phải thống nhất request/response trước bản phát hành.",
}

PROMPT_OVERRIDES = {
    "frontend_developer_react_q01": "Danh sách 500 sản phẩm có ảnh thiếu và phải dùng được bằng bàn phím. Bạn sẽ chọn cấu trúc HTML, nhãn và trạng thái rỗng/lỗi nào? Nêu cách kiểm tra với trình đọc màn hình và một dữ liệu biên.",
    "frontend_developer_react_q02": "Thẻ sản phẩm tràn ở màn hình 320 px khi tên dài và focus khó thấy. Bạn sẽ tổ chức CSS grid/flex, breakpoint, xử lý ảnh và focus ra sao? Kiểm tra ở các độ rộng nào?",
    "frontend_developer_react_q03": "Người dùng đổi bộ lọc liên tiếp, response cũ tới sau và đôi khi API trả 500 hoặc thiếu giá. Bạn xử lý request, state và dữ liệu lỗi thế nào để danh sách không hiển thị kết quả sai?",
    "frontend_developer_react_q04": "Sau khi sắp xếp 500 sản phẩm, state của thẻ bị gắn sang sản phẩm khác. Bạn chia component, đặt state và key thế nào; sẽ viết test gì để bắt lỗi này?",
    "frontend_developer_react_q05": "Bộ lọc được dùng ở hai khu vực và request có trạng thái tải/lỗi. Trường hợp nào cần Redux Toolkit, trường hợp nào chỉ cần state cục bộ? Nêu slice, selector và phép thử cụ thể.",
    "backend_developer_java_q01": "Hai khách cùng đặt sản phẩm còn một đơn vị trong kho. Bạn thiết kế luồng Java để giữ giá tiền và trạng thái đơn nhất quán, xử lý lỗi và kiểm thử cạnh tranh thế nào?",
    "backend_developer_java_q04": "Hai request đồng thời trừ tồn kho cuối cùng và bước lưu đơn có thể lỗi. Bạn dùng SQL, ràng buộc và transaction nào; kiểm tra rollback và query plan ra sao?",
    "backend_developer_java_q05": "Hai pull request cùng đổi contract tạo đơn và migration nên conflict; CI báo integration test lỗi. Bạn tổ chức commit, resolve và xác minh trước merge thế nào?",
    "frontend_developer_react_q06": "API sản phẩm đổi tên trường giữa sprint khi phần frontend đang review. Bạn sẽ chia trách nhiệm, xử lý bất đồng với backend/QA và lưu quyết định để kịp nghiệm thu như thế nào? Nêu hành vi và bằng chứng có thể quan sát.",
    "frontend_developer_react_q07": "Designer muốn cả thẻ sản phẩm bấm được nhưng QA phát hiện không dùng được bằng bàn phím. Bạn trao đổi với hai bên và xác nhận tiêu chí chấp nhận ra sao? Nêu tài liệu hoặc bản thử sẽ dùng.",
    "data_analyst_q03": "Báo cáo tuần và dashboard có hai định nghĩa conversion, cuộc họp marketing diễn ra ngày mai. Bạn xác minh khác biệt, trao đổi với owner và quyết định trình bày chỉ số nào thế nào?",
    "data_analyst_q06": "Marketing và tài chính bất đồng về doanh thu vì một bên loại đơn hoàn tiền, bên kia không. Bạn thu thập bằng chứng, kiểm tra giả thuyết và thống nhất cách sửa báo cáo ra sao?",
    "backend_developer_java_q06": "Sau triển khai, lỗi 5xx ở API tạo đơn tăng và có request đã ghi đơn trước khi lỗi. Bạn giảm ảnh hưởng, thu thập bằng chứng và kiểm tra bản sửa thế nào?",
    "backend_developer_java_q07": "Frontend hiểu lỗi 409 là 400, QA dùng contract cũ. Bạn dẫn dắt trao đổi để chốt phản hồi API, test và thông báo thay đổi trước phát hành ra sao?",
}

# (skill, level, context, question, three observable criteria, reference answer)
MISSING = {
    "sales_executive": [
        ("làm việc nhóm", 2, "Đội bán hàng hứa demo CRM trong 4 ngày nhưng đội triển khai chưa xác nhận môi trường và kịch bản; hợp đồng SME chờ quyết định.",
         "Bạn phối hợp sales, presales và triển khai để giữ buổi demo thế nào? Nêu ai xác nhận phạm vi, cách xử lý bất đồng và bằng chứng bàn giao.",
         ["Nhận ra ba nhóm có trách nhiệm khác nhau và ghi phần demo chưa xác nhận.", "Phân công owner và hạn phản hồi, đồng bộ kịch bản với khách; giải quyết bất đồng bằng nhu cầu/khả năng thực tế.", "Lưu quyết định và tiêu chí demo, theo dõi việc thực hiện và rút kinh nghiệm sau phản hồi khách."],
         "Tôi xác nhận nhu cầu demo của khách, hỏi presales kịch bản có thể chạy và đội triển khai về môi trường. Tôi lập bảng phần đã xác nhận/chưa xác nhận, phân công người chốt từng mục trước mốc gửi lịch cho khách. Nếu không đủ điều kiện, tôi báo phương án thu hẹp phạm vi hoặc đổi lịch để khách quyết định; không tự hứa tính năng. Sau demo, tôi ghi phản hồi, trách nhiệm và bước tiếp theo trong CRM."),
        ("giải quyết vấn đề", 2, "Hai tuần gần đây 60 lead mới chỉ tạo 6 cơ hội đủ điều kiện, thấp hơn tỷ lệ trước đó; CRM có lead trùng và kênh mới chưa được kiểm tra.",
         "Bạn khoanh vùng nguyên nhân tỷ lệ lead đủ điều kiện giảm thế nào trước khi đề nghị đổi kênh hoặc thông điệp? Nêu dữ liệu, giả thuyết và cách xác minh.",
         ["Xác định lại định nghĩa lead đủ điều kiện và kiểm tra trùng/thời gian.", "So sánh theo kênh, nguồn, nhóm khách và mốc xử lý; kiểm tra ít nhất hai giả thuyết bằng mẫu bản ghi.", "Thử thay đổi có giới hạn, theo dõi tỷ lệ sau can thiệp và nêu điều chưa thể kết luận."],
         "Tôi xác nhận cách tính cơ hội đủ điều kiện và thời gian ghi nhận, lọc lead trùng rồi so sánh hai tuần với giai đoạn trước theo kênh và nhóm khách. Tôi kiểm tra mẫu cuộc gọi và tốc độ theo dõi để phân biệt chất lượng lead với vấn đề quy trình. Sau đó tôi đề xuất thử một kênh/thông điệp trên phạm vi nhỏ, đặt tiêu chí đo trước, theo dõi kết quả và không kết luận nguyên nhân khi chưa đủ dữ liệu."),
        ("quản lý thời gian", 2, "Cùng tuần bạn có 12 lead cần phản hồi, hai buổi demo đã hẹn và một khách gia hạn sau 48 giờ; người hỗ trợ chỉ rảnh nửa ngày.",
         "Bạn sắp xếp ưu tiên và cam kết thời hạn với các bên thế nào? Khi một buổi demo kéo dài ngoài dự kiến, bạn điều chỉnh lịch ra sao?",
         ["Liệt kê deadline và tác động của gia hạn, demo, lead thay vì xử lý theo thứ tự đến.", "Đặt lịch và thời lượng dự phòng, giao việc có xác nhận, báo lại người bị ảnh hưởng khi lịch đổi.", "Theo dõi hoàn thành, cập nhật CRM và điều chỉnh ưu tiên dựa trên rủi ro thực tế, không hứa quá năng lực."],
         "Tôi khóa trước hạn gia hạn 48 giờ và hai demo đã xác nhận, sau đó phân loại lead theo mức phù hợp và hạn phản hồi. Tôi hỏi người hỗ trợ nhận phần chuẩn bị nào và ghi owner/thời hạn; chừa khoảng dự phòng sau demo. Nếu demo kéo dài, tôi thông báo sớm cho lead hoặc đồng đội, đề xuất mốc mới khả thi và cập nhật CRM để không mất việc."),
    ],
    "frontend_developer_react": [
        ("git", 2, "Hai nhánh cùng sửa component sản phẩm và hợp đồng API; khi merge có conflict, CI báo test danh sách thất bại.",
         "Bạn xử lý conflict, kiểm tra diff và đưa thay đổi lên pull request ra sao để không mất logic của nhánh kia?",
         ["Xác định file và ý định của hai nhánh trước khi chọn phần cần giữ.", "Resolve theo contract đã thống nhất, chia commit có nghĩa, chạy test liên quan và kiểm tra diff/secret.", "Yêu cầu review, giải thích quyết định conflict và xác minh lại sau merge; biết cách revert nếu phát hành lỗi."],
         "Tôi đọc hai nhánh và hỏi owner API về contract cuối, không chọn nguyên một phía theo công cụ. Tôi resolve từng vùng, chạy test component và tích hợp, đọc diff để bảo đảm không bỏ mất hành vi hoặc đưa secret vào repo. Trong PR tôi ghi thay đổi contract, cách kiểm tra và vùng conflict để reviewer xác nhận; sau merge tôi theo dõi CI."),
        ("rest api", 2, "Trang sản phẩm gọi GET /products, đôi khi nhận 429, 500 hoặc item thiếu giá; người dùng có thể đổi bộ lọc trong lúc tải.",
         "Bạn xử lý status, dữ liệu và request cũ thế nào? Nêu trạng thái giao diện và test cho từng trường hợp.",
         ["Phân biệt HTTP thành công với lỗi, xác nhận shape tối thiểu của sản phẩm.", "Hiển thị loading/empty/error, tránh kết quả cũ ghi đè bộ lọc mới và chỉ retry 429 theo chính sách API.", "Kiểm tra bằng mock response cho 200, 429, 500, dữ liệu sai và request đến không theo thứ tự."],
         "Tôi kiểm tra response.ok và validate item trước khi render, tách trạng thái tải/rỗng/lỗi. Khi bộ lọc đổi, tôi hủy request cũ hoặc bỏ qua kết quả không còn khớp. Với 429, tôi chỉ thử lại nếu API cho phép và dùng mốc chờ phù hợp; với 500 báo lỗi và cho thử lại. Test mô phỏng phản hồi đảo thứ tự và item thiếu giá."),
        ("typescript", 1, "Payload sản phẩm có id/name bắt buộc nhưng price có thể null; một item test thiếu cả id.",
         "Bạn khai báo type và kiểm tra dữ liệu ở ranh giới API thế nào để thẻ sản phẩm không lỗi hoặc hiển thị giá sai?",
         ["Khai báo id/name và price tùy chọn/null theo contract, không dùng any để bỏ qua lỗi.", "Kiểm tra đầu vào runtime trước render, xử lý price null và item không có id bằng trạng thái rõ ràng.", "Nêu test type/runtime với item hợp lệ, price null và payload thiếu id; không coi type assertion là validation."],
         "Tôi khai báo Product theo contract, với price: number | null nếu API cho phép. Vì JSON không được TypeScript xác thực lúc chạy, tôi kiểm tra id/name/price sau fetch. Item không có id được ghi lỗi và bỏ khỏi danh sách hoặc báo dữ liệu lỗi theo thiết kế; price null hiện 'Chưa có giá'. Tôi test ba payload này thay vì ép kiểu bằng as Product."),
        ("thiết kế ui ux", 1, "Trên màn hình 320 px, bộ lọc che sản phẩm; QA báo nút áp dụng khó dùng bằng bàn phím và trạng thái rỗng thiếu hướng dẫn.",
         "Bạn kiểm tra luồng tìm sản phẩm và đề xuất điều chỉnh đầu tiên nào? Bạn xác nhận với người dùng/QA ra sao?",
         ["Nhận ra các vấn đề khả dụng: lọc che nội dung, bàn phím, trạng thái rỗng.", "Đề xuất một bố cục/nhãn và thứ tự thao tác rõ, thử bản mẫu ở màn hình nhỏ và bàn phím.", "Thu phản hồi theo nhiệm vụ tìm sản phẩm, đối chiếu tiêu chí và ghi giới hạn của kết quả thử."],
         "Tôi quan sát nhiệm vụ tìm một sản phẩm trên màn 320 px, thử tab qua bộ lọc và ghi bước bị kẹt. Tôi đề xuất bộ lọc có nhãn rõ, nút áp dụng dễ thấy, trả focus hợp lý và thông điệp rỗng có cách xóa lọc. Tôi thử prototype với QA/người dùng theo cùng nhiệm vụ, ghi thay đổi và điểm chưa kiểm chứng."),
    ],
    "data_analyst": [
        ("thống kê", 2, "Hai biến thể landing page có tỷ lệ chuyển đổi quan sát 4,8% và 5,2%; số phiên và thời gian chạy chưa được cung cấp, chiến dịch có thể trùng mùa vụ.",
         "Bạn hỏi thêm dữ liệu gì và phân tích thế nào trước khi kết luận B tốt hơn A?",
         ["Nhận ra chênh lệch quan sát không đủ để tuyên bố tác động; hỏi cỡ mẫu và cách phân nhóm.", "Kiểm tra randomization, thời gian, mẫu và khoảng tin cậy/phép thử phù hợp với metric đã định nghĩa.", "Trình bày bất định, phân đoạn/thử nghiệm tiếp theo và giới hạn nhân quả, không tự khẳng định ý nghĩa thống kê."],
         "Tôi xin số phiên và chuyển đổi từng nhóm, cách phân bổ, khoảng thời gian và định nghĩa conversion. Tôi kiểm tra mất cân bằng mẫu và biến động theo ngày trước khi tính khoảng tin cậy hoặc phép thử đã chọn trước. Nếu chưa đủ dữ liệu, tôi báo chênh lệch 0,4 điểm phần trăm chỉ là quan sát và đề xuất tiếp tục thu thập thay vì tuyên bố B thắng."),
        ("giao tiếp", 2, "Marketing muốn báo tăng doanh thu chiến dịch, tài chính dùng số đã trừ hoàn tiền nên thấp hơn; cuộc họp điều hành trong ngày.",
         "Bạn giải thích khác biệt cho hai bên và chốt cách trình bày số liệu thế nào để người nghe không hiểu sai?",
         ["Nêu rõ hai định nghĩa, nguồn và kỳ dữ liệu khác nhau.", "Dùng ví dụ đối soát hoặc bảng cầu nối, xác nhận với hai owner trước khi công bố.", "Ghi quyết định, mức độ chắc chắn và việc còn thiếu; điều chỉnh cách giải thích theo người nghe."],
         "Tôi đặt hai công thức cạnh nhau và lấy một mẫu đơn hoàn tiền để minh họa vì sao số khác. Tôi hỏi owner của mỗi chỉ số về mục đích báo cáo, đối soát tổng và xác nhận cách gắn nhãn. Trong họp tôi trình bày cả số gross/net nếu cần, ghi rõ nguồn/kỳ và không gọi hai số là cùng một KPI."),
        ("làm việc nhóm", 2, "Nhà phân tích, kỹ sư dữ liệu và marketing cùng xây dashboard; cột campaign_id đổi kiểu khi pipeline cập nhật trước buổi nghiệm thu.",
         "Bạn phối hợp ba bên để sửa lỗi và bảo đảm mọi người kiểm tra cùng một định nghĩa dữ liệu thế nào?",
         ["Xác định tác động đổi kiểu và người sở hữu nguồn, báo sớm cho các bên.", "Chốt contract/schema và tiêu chí kiểm tra, phân việc có hạn và đối soát mẫu dữ liệu cùng nhau.", "Ghi quyết định, test hồi quy và phản hồi sau nghiệm thu; không nhận công việc nhóm là kết quả cá nhân."],
         "Tôi đưa ví dụ campaign_id lỗi cho kỹ sư dữ liệu, hỏi marketing trường nào dùng trong báo cáo và thống nhất contract mới. Tôi chịu trách nhiệm kiểm tra dashboard trên mẫu trước/sau, ghi số bản ghi không join được và hạn sửa. Trước nghiệm thu cả nhóm đối soát một báo cáo chuẩn, lưu quyết định và test tránh lỗi tái diễn."),
        ("tableau", 1, "Tệp chiến dịch có ngày, kênh, spend và conversion; người xem cần lọc theo kênh, nhưng một dòng thiếu ngày.",
         "Bạn tạo một biểu đồ Tableau nhập môn thế nào và kiểm tra bộ lọc, dữ liệu thiếu trước khi chia sẻ?",
         ["Chọn đúng trường/ngữ nghĩa và nhận ra dòng thiếu ngày cần xử lý rõ.", "Tạo view cơ bản với bộ lọc kênh, nhãn/đơn vị rõ và đối chiếu tổng với tệp gốc.", "Thử lọc nhiều kênh, kiểm tra quyền chia sẻ và giải thích giới hạn dữ liệu thiếu; không tuyên bố đã đạt năng lực nâng cao."],
         "Tôi kiểm tra kiểu ngày và đánh dấu dòng thiếu trước khi dựng view spend/conversion theo ngày. Tôi thêm bộ lọc kênh và nhãn đơn vị, đối chiếu tổng trên từng lựa chọn với tệp nguồn. Tôi ghi quy tắc xử lý dòng thiếu, thử bộ lọc và chia sẻ bản xem theo quyền được cấp."),
    ],
    "backend_developer_java": [
        ("docker", 1, "Dịch vụ Spring Boot chạy trên máy lập trình nhưng container không khởi động vì thiếu biến môi trường; image cần được chia sẻ để QA thử.",
         "Bạn tạo Dockerfile và cấu hình chạy tối thiểu thế nào? Bạn kiểm tra log, cổng và tránh đưa secret vào image ra sao?",
         ["Biết image/container, cổng dịch vụ và biến cấu hình cần thiết.", "Build/run image, truyền cấu hình khi chạy thay vì nhúng secret; xem log và health endpoint để tìm lỗi.", "Ghi lệnh tái hiện cho QA, kiểm tra image không chứa secret và nêu giới hạn của bài thực hành nhập môn."],
         "Tôi tạo Dockerfile dùng runtime phù hợp, build JAR rồi chạy với port và biến cấu hình được truyền từ môi trường an toàn. Tôi không COPY file secret vào image. Khi container thoát, tôi xem logs và exit code, xác nhận port/health endpoint; sau đó cung cấp QA lệnh chạy và biến bắt buộc đã được ẩn giá trị."),
        ("làm việc nhóm", 2, "Frontend nhận API tạo đơn khác contract, QA viết test theo mẫu cũ và backend phải chốt thay đổi trong sprint.",
         "Bạn phân chia việc và xử lý bất đồng về mã lỗi/trường dữ liệu ra sao để tích hợp không bị chặn?",
         ["Xác định contract sai khác và người liên quan; không đổ lỗi cho một nhóm.", "Thống nhất request/response bằng ví dụ, owner và hạn cập nhật backend/frontend/test.", "Chạy test contract cùng nhau, lưu quyết định và theo dõi lỗi sau tích hợp."],
         "Tôi lấy hai request/response cụ thể để chỉ ra khác biệt, mời frontend và QA cùng chọn contract theo yêu cầu sản phẩm. Tôi ghi các trường, mã lỗi và hạn cập nhật cho từng bên. Sau sửa, chúng tôi chạy integration/contract test trên cùng fixture, lưu quyết định trong PR và theo dõi kết quả CI."),
        ("linux", 1, "Dịch vụ Java trong môi trường thử nghiệm không mở cổng; process có vẻ đang chạy nhưng health endpoint trả lỗi.",
         "Bạn dùng thao tác Linux cơ bản nào để kiểm tra process, log và cổng trước khi chuyển cấp? Nêu điều không nên làm trên máy dùng chung.",
         ["Biết kiểm tra process, trạng thái service, log và cổng theo quyền được cấp.", "Dùng kết quả log/cổng để khoanh vùng cấu hình hoặc quyền, ghi lệnh và thời điểm kiểm tra.", "Báo người phụ trách với bằng chứng, không sudo bừa bãi, xóa log hay đổi quyền rộng trên máy dùng chung."],
         "Tôi xác nhận service/process, xem log ứng dụng và journal theo quyền được cấp, rồi kiểm tra cổng lắng nghe và biến cấu hình không nhạy cảm. Tôi ghi timestamp và lỗi cụ thể, đối chiếu health endpoint. Nếu cần quyền cao hơn hoặc đổi cấu hình hệ thống, tôi chuyển cho người vận hành; không chmod 777 hay in secret ra log."),
    ],
}


def _draft_provenance() -> dict:
    return {"source_url": None, "author_origin": "Codex (AI) biên soạn tình huống giả lập",
            "curated_by": None, "review_tier": "ai_assisted_draft", "reviewed_at": None,
            "rights_basis": None, "license_notes": None}


def _rubric(points: list[str], context: str) -> dict:
    """Derive observable L1/L2/L3 criteria from question-specific editorial points."""
    return {
        "level_1_criteria": f"Nhận diện đúng dữ kiện và rủi ro trong ca: {context} {points[0]}",
        "level_2_criteria": f"Thực hiện có giải thích và đầu ra kiểm tra được: {points[0]} {points[1]}",
        "level_3_criteria": f"Đáp ứng mức 2, chủ động kiểm chứng và xử lý giới hạn: {points[2]} Ghi rõ giả định, người xác nhận và bằng chứng kết quả; không tự tạo số liệu.",
    }


def _new_question(role_id: str, number: int, spec: tuple, *, weight: int) -> dict:
    skill, level, context, question, points, answer = spec
    qid = f"{role_id}_q{number:02d}"
    return {
        "id": qid, "type": "scenario" if skill in {"làm việc nhóm", "giao tiếp", "giải quyết vấn đề", "quản lý thời gian", "thiết kế ui ux"} else "technical",
        "skill": skill, "level": level, "weight": weight,
        "question": f"Tình huống giả lập: {context} {question}",
        "good_answer_points": points, "red_flags": [
            "Tự khẳng định dữ liệu, kết quả hoặc quyền phê duyệt chưa được cung cấp trong tình huống.",
            "Không có bước xác minh, người phụ trách hoặc bằng chứng để kiểm tra kết quả.",
        ],
        "time_minutes": 5, "reference_answer": answer, "context_scenario": context,
        "evaluation_rubric": _rubric(points, context), "quality": "unreviewed",
        "quality_note": "Bản nháp AI, tình huống giả lập; rubric chưa được người có chuyên môn duyệt và không dùng để chấm tự động.",
        "quality_reviewer": None, "quality_reviewed_at": None, "quality_review_note": None,
        "quality_sources": [], "provenance": _draft_provenance(),
    }


def complete(bank_dir: Path = BANK_DIR, *, apply: bool = False,
             backup_dir: Path = BACKUP_DIR) -> dict:
    roles = {role["id"]: role for role in json.loads((bank_dir.parent / "roles.json").read_text(encoding="utf-8"))}
    role_weights = {role_id: {skill["name"]: skill["weight"] for skill in roles[role_id]["skills"]} for role_id in ROLES}
    files = sorted(bank_dir.glob("part_*.json"))
    expected_missing = {role: len(items) for role, items in MISSING.items()}
    plans = []
    question_changes = []
    for path in files:
        original = path.read_bytes()
        bank = json.loads(original.decode("utf-8"))
        changed = False
        for role_id in ROLES:
            if role_id not in bank["roles"]:
                continue
            records = bank["roles"][role_id]
            if len({record["id"] for record in records}) != len(records):
                raise ValueError(f"Duplicate question ID in {role_id}")
            for question in records:
                qid = question["id"]
                if qid not in CONTEXTS:
                    continue
                # Existing editor content is allowed only in the original state
                # or in the exact state generated by a previous run.
                context = CONTEXTS[qid]
                points = question["good_answer_points"]
                updates = {"context_scenario": context,
                           "evaluation_rubric": _rubric(points, context)}
                if qid in PROMPT_OVERRIDES:
                    updates["question"] = PROMPT_OVERRIDES[qid]
                if all(question.get(key) == value for key, value in updates.items()):
                    continue
                if question.get("context_scenario") is not None or any(
                    (question.get("evaluation_rubric") or {}).values()
                ):
                    raise ValueError(f"Refusing to overwrite previous editorial work: {qid}")
                if question.get("quality") not in {"reviewed", "ai_reviewed_internal"}:
                    raise ValueError(f"Unexpected original quality: {qid}")
                previous = {key: deepcopy(question.get(key)) for key in (
                    "quality", "quality_reviewer", "quality_reviewed_at",
                    "quality_review_note", "quality_sources", "provenance")}
                question["prior_review_metadata"] = previous
                question.update(updates)
                question.update({"quality": "unreviewed",
                                 "quality_note": "Bối cảnh và rubric bổ sung do AI biên soạn; metadata review trước được lưu trong prior_review_metadata nhưng không duyệt phần mới.",
                                 "quality_reviewer": None, "quality_reviewed_at": None,
                                 "quality_review_note": None, "quality_sources": [],
                                 "provenance": _draft_provenance()})
                question_changes.append(qid)
                changed = True
            expected = expected_missing[role_id]
            start = {"sales_executive": 6, "frontend_developer_react": 8,
                     "data_analyst": 7, "backend_developer_java": 8}[role_id]
            for offset, spec in enumerate(MISSING[role_id]):
                candidate = _new_question(role_id, start + offset, spec, weight=role_weights[role_id][spec[0]])
                matches = [record for record in records if record["id"] == candidate["id"]]
                if matches:
                    if len(matches) != 1 or matches[0] != candidate:
                        raise ValueError(f"Refusing to overwrite existing question: {candidate['id']}")
                    continue
                records.append(candidate)
                question_changes.append(candidate["id"])
                changed = True
            assert expected == len(MISSING[role_id])
        if changed:
            plans.append((path, original, _format_json(bank).encode("utf-8") + b"\n"))
    result = {"mode": "apply" if apply else "dry_run", "questions_changed": len(question_changes),
              "ids": question_changes, "files_changed": len(plans)}
    if not apply:
        return result
    for path, original, _ in plans:
        backup = backup_dir / hashlib.sha256(original).hexdigest() / path.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists() and backup.read_bytes() != original:
            raise ValueError(f"Backup mismatch: {backup}")
        if not backup.exists():
            backup.write_bytes(original)
        if backup.read_bytes() != original or path.read_bytes() != original:
            raise ValueError(f"Source or backup changed: {path}")
    for path, _, updated in plans:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as output:
                temporary = Path(output.name)
                output.write(updated)
            temporary.replace(path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(complete(apply=args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
