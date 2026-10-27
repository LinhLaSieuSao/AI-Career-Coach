"""Build a sourced academic curriculum overlay for every skill in roles.json."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(title, provider, url, kind, scope, basis, practice_url=None, practice_title=None, jurisdiction=None):
    open_kinds = {
        "peer_reviewed_open_textbook", "higher_education_open_textbook", "university_course_collection",
        "university_course", "university_open_textbook", "university_oer_discipline_guide",
        "university_open_course_resource", "open_academic_textbook", "academic_medical_textbook",
        "university_textbook", "university_course_text",
    }
    access = "free_open_access" if kind in open_kinds else "may_require_library_or_paid_access"
    item = {"title": title, "provider": provider, "url": url, "kind": kind, "scope": scope, "basis": basis, "access": access}
    if practice_url:
        item["practice_url"] = practice_url
        item["practice_title"] = practice_title or "Nguồn thực hành bổ sung"
    if jurisdiction:
        item["jurisdiction"] = jurisdiction
    return item


SOURCES = {
    "data": source("Principles of Data Science · Using Technology for Data Science", "OpenStax · Rice University", "https://openstax.org/books/principles-data-science/pages/1-4-using-technology-for-data-science", "peer_reviewed_open_textbook", "Nền tảng khoa học dữ liệu; có ví dụ Excel, SQL, Python, Tableau và Power BI. Phần mềm cụ thể cần luyện thêm theo tài liệu nhà sản xuất.", "Giáo trình bậc đại học OpenStax; mục 1.4 nêu rõ các công cụ được đề cập."),
    "stats": source("Principles of Data Science · Statistics and Probability", "OpenStax · Rice University", "https://openstax.org/books/principles-data-science/pages/3-introduction", "peer_reviewed_open_textbook", "Nền tảng thống kê, xác suất và suy luận từ dữ liệu; cần kiểm tra giả định trên dữ liệu theo ngành.", "Giáo trình bậc đại học OpenStax; chương 3 giới thiệu thống kê và xác suất trong khoa học dữ liệu."),
    "python": source("Introduction to Python Programming", "OpenStax · Rice University", "https://openstax.org/books/introduction-python-programming/pages/1-introduction", "peer_reviewed_open_textbook", "Lập trình Python nhập môn, giải quyết vấn đề và bài tập; đối chiếu cú pháp với tài liệu Python hiện hành.", "Giáo trình đại học OpenStax có bài tập và môi trường thực hành mã nguồn."),
    "java": source("Java, Java, Java: Object-Oriented Problem Solving", "Open Textbook Library · University of Minnesota", "https://open.umn.edu/opentextbooks/textbooks/218", "higher_education_open_textbook", "Lập trình Java và tư duy hướng đối tượng; đối chiếu phiên bản JDK theo tài liệu Java chính thức.", "Giáo trình đại học trong Open Textbook Library; thư viện yêu cầu sách gắn với cơ sở học thuật và có giấy phép mở."),
    "csharp": source("C# Yellow Book", "Rob Miles · giáo trình khóa lập trình năm nhất tại University of Hull", "https://www.robmiles.com/c-yellow-book", "university_course_text", "Nền tảng C# từ nguyên lý lập trình; đối chiếu phiên bản .NET hiện hành.", "Tác giả ghi sách được dùng làm giáo trình khóa lập trình năm nhất tại University of Hull; không gắn nhãn phản biện đồng cấp."),
    "cs": source("Introductory Programming", "MIT OpenCourseWare", "https://ocw.mit.edu/collections/introductory-programming/", "university_course_collection", "Nền tảng lập trình, thuật toán và giải quyết vấn đề; framework/thư viện cụ thể cần học thêm theo tài liệu nhà phát triển.", "Tập hợp học phần lập trình nhập môn công khai của MIT OpenCourseWare."),
    "se": source("Software Engineering · Introduction to Engineering Concepts", "MIT OpenCourseWare", "https://ocw.mit.edu/courses/res.ll-004-ll-educate-introduction-to-engineering-concepts-spring-2022/pages/software-engineering/", "university_course", "Nền tảng thiết kế, kiểm thử, kiến trúc và quy trình phần mềm; năng lực cần thể hiện qua sản phẩm chạy được và review.", "Trang học phần MIT OpenCourseWare về khái niệm kỹ thuật phần mềm."),
    "db": source("Database Design, 2nd Edition", "Open Textbook Library · University of Minnesota", "https://open.umn.edu/opentextbooks/textbooks/database-design-2nd-edition", "higher_education_open_textbook", "Mô hình dữ liệu, ER, ràng buộc, chuẩn hóa và SQL; MongoDB/Redis cần thêm bài tập theo tài liệu chính thức.", "Giáo trình đại học có các chương thiết kế cơ sở dữ liệu, mô hình quan hệ và SQL."),
    "network": source("An Introduction to Computer Networks", "Open Textbook Library · University of Minnesota", "https://open.umn.edu/opentextbooks/textbooks/353", "higher_education_open_textbook", "Nguyên lý mạng máy tính và giao thức; cấu hình Cisco cần lab an toàn và tài liệu hãng.", "Giáo trình mạng máy tính trong Open Textbook Library."),
    "is": source("Foundations of Information Systems", "OpenStax · Rice University", "https://openstax.org/books/foundations-information-systems/pages/1-1-introduction-to-information-systems", "peer_reviewed_open_textbook", "Nền tảng hệ thống thông tin, phần mềm, dữ liệu và công nghệ trong tổ chức; không phải hướng dẫn cấu hình chuyên sâu.", "Giáo trình bậc đại học OpenStax về hệ thống thông tin."),
    "office": source("Workplace Software and Skills", "OpenStax · Rice University", "https://openstax.org/books/workplace-software-skills/pages/preface", "peer_reviewed_open_textbook", "Phần mềm văn phòng, bảng tính, tài liệu và cộng tác; thao tác cụ thể tùy phiên bản ứng dụng.", "Giáo trình OpenStax về kỹ năng phần mềm nơi làm việc."),
    "ml": source("Dive into Deep Learning", "D2L · giáo trình mở do nhà nghiên cứu/giảng viên biên soạn", "https://d2l.ai/", "open_academic_textbook", "Nền tảng học máy/học sâu kèm notebook thực hành; phải đánh giá trên dữ liệu phù hợp và ghi giới hạn.", "Giáo trình mở có nội dung toán, giải thích và notebook thực hành."),
    "business": source("Fundamentals of Business, 4th Edition", "Open Textbook Library · University of Minnesota; Virginia Tech", "https://open.umn.edu/opentextbooks/textbooks/319", "higher_education_open_textbook", "Tổng quan quản trị, vận hành, nhân sự, marketing, kế toán, tài chính và dịch vụ; học phần theo đúng chủ đề.", "Giáo trình nhập môn kinh doanh dùng cho khóa học đại học tại Virginia Tech."),
    "management": source("Principles of Management", "OpenStax · Rice University", "https://openstax.org/books/principles-management/pages/1-introduction", "peer_reviewed_open_textbook", "Nền tảng lập kế hoạch, tổ chức, vận hành và quản trị; áp dụng qua case và phản hồi.", "Giáo trình quản trị bậc đại học OpenStax."),
    "org": source("Organizational Behavior", "OpenStax · Rice University", "https://openstax.org/books/organizational-behavior/pages/1-introduction", "peer_reviewed_open_textbook", "Hành vi tổ chức, động lực, giao tiếp, nhóm và xung đột; cần luyện hành vi trong bối cảnh có phản hồi.", "Giáo trình hành vi tổ chức bậc đại học OpenStax."),
    "marketing": source("Principles of Marketing", "Open Textbook Library · University of Minnesota", "https://open.umn.edu/opentextbooks/textbooks/1325", "higher_education_open_textbook", "Nghiên cứu thị trường, phân khúc, khách hàng, truyền thông và bán hàng; nền tảng quảng cáo cần bổ sung tài liệu phiên bản hiện hành.", "Giáo trình marketing đại học có chương nghiên cứu, digital marketing, quảng cáo và bán hàng."),
    "acct": source("Principles of Financial Accounting", "OpenStax · Rice University", "https://openstax.org/books/principles-financial-accounting/pages/3-1-describe-principles-assumptions-and-concepts-of-accounting-and-their-relationship-to-financial-statements", "peer_reviewed_open_textbook", "Chu trình kế toán và báo cáo tài chính; đây là nền tảng kế toán Hoa Kỳ, cần đối chiếu chuẩn mực và biểu mẫu Việt Nam hiện hành.", "Giáo trình kế toán tài chính bậc đại học OpenStax; mục được dẫn giải thích nguyên tắc và giả định kế toán."),
    "acct_managerial": source("Principles of Managerial Accounting", "OpenStax · Rice University", "https://openstax.org/books/principles-managerial-accounting/pages/preface", "peer_reviewed_open_textbook", "Chi phí, ngân sách và thông tin cho quyết định nội bộ; không thay chuẩn mực kế toán Việt Nam.", "Giáo trình kế toán quản trị OpenStax dùng cho khóa học đại học."),
    "finance": source("Principles of Finance", "OpenStax · Rice University", "https://openstax.org/books/principles-finance/pages/preface", "peer_reviewed_open_textbook", "Giá trị thời gian của tiền, rủi ro, dòng tiền và quyết định tài chính; không phải tư vấn đầu tư hay quy định Việt Nam.", "Giáo trình tài chính bậc đại học OpenStax; trang giới thiệu liên kết toàn bộ chương học."),
    "economics": source("Principles of Economics 3e", "OpenStax · Rice University", "https://openstax.org/books/principles-economics-3e/pages/1-introduction", "peer_reviewed_open_textbook", "Nền tảng kinh tế học vi mô/vĩ mô; phân tích Việt Nam cần số liệu chính thức, đúng kỳ và định nghĩa.", "Giáo trình kinh tế học đại học OpenStax."),
    "law": source("Business Law and the Legal Environment", "Open Textbook Library · University of Minnesota", "https://open.umn.edu/opentextbooks/textbooks/business-law-and-the-legal-environment", "higher_education_open_textbook", "Giáo trình trình bày luật Hoa Kỳ, chỉ dùng học khái niệm và đọc tình huống. Áp dụng ở Việt Nam phải tra văn bản Việt Nam còn hiệu lực.", "Giáo trình luật kinh doanh có review từ giảng viên luật; trang thư viện xác định phạm vi hệ thống Hoa Kỳ.", "https://vbpl.vn/", "Cơ sở dữ liệu quốc gia về văn bản pháp luật Việt Nam", "US"),
    "supply": source("Inventory Analytics", "Open Textbook Library · University of Minnesota; University of Edinburgh Business School", "https://open.umn.edu/opentextbooks/textbooks/1008", "higher_education_open_textbook", "Mô hình tồn kho, dự báo nhu cầu và phân tích chuỗi cung ứng; chứng từ/quy trình cần tra nguồn áp dụng.", "Giáo trình do giáo sư University of Edinburgh biên soạn, có review học thuật về inventory control và forecasting."),
    "nursing": source("Clinical Nursing Skills · Nursing Assessment", "OpenStax · Rice University", "https://openstax.org/books/clinical-nursing-skills/pages/24-3-nursing-assessment", "peer_reviewed_open_textbook", "Kiến thức nền về đánh giá và kỹ năng điều dưỡng; không thay thực hành có giám sát hoặc giấy phép hành nghề.", "Giáo trình điều dưỡng bậc đại học OpenStax, hướng tới chuẩn bị cho clinical rotations.", "https://openstax.org/books/clinical-nursing-skills/pages/9-competency-based-assessments", "Đánh giá năng lực trong chương trình điều dưỡng"),
    "clinical": source("Clinical Methods: The History, Physical, and Laboratory Examinations", "NCBI Bookshelf · National Library of Medicine", "https://www.ncbi.nlm.nih.gov/books/NBK201/", "academic_medical_textbook", "Nền tảng bệnh sử và khám lâm sàng. Sách xuất bản cũ; phải đối chiếu hướng dẫn hiện hành và học/thực hành dưới giám sát.", "Giáo trình y khoa được lưu tại NCBI Bookshelf; không phải hướng dẫn lâm sàng cập nhật."),
    "pharmacy": source("Public Health in Pharmacy Practice: A Casebook, 2nd Edition", "Open Textbook Library · University of Minnesota", "https://open.umn.edu/opentextbooks/textbooks/public-health-in-pharmacy-practice-a-casebook", "higher_education_open_textbook", "Casebook về y tế công cộng trong thực hành dược; không hướng dẫn tự kê đơn, cấp phát hoặc tư vấn cho người bệnh.", "Casebook học thuật về y tế công cộng trong thực hành dược, có trong Open Textbook Library."),
    "education": source("Educational Psychology", "Nicole Arduini-Van Hoose · Hudson Valley Community College", "https://open.umn.edu/opentextbooks/textbooks/educational-psychology-2020", "higher_education_open_textbook", "Tâm lý học giáo dục, phát triển và động lực người học, dạy học và đánh giá; điều chỉnh hoạt động theo chương trình và quy định Việt Nam.", "Giáo trình đại học do giảng viên Hudson Valley Community College viết; có phản biện của giáo sư tâm lý học giáo dục tại Western Oregon University trong Open Textbook Library."),
    "communication": source("Introduction to Professional Communications", "BCcampus Open Education", "https://pressbooks.bccampus.ca/professionalcomms/", "university_open_textbook", "Giao tiếp nơi làm việc, teamwork, viết, người đọc, trình bày và đánh giá nguồn.", "Giáo trình mở BCcampus có mục lục bài học và giấy phép Creative Commons."),
    "english": source("Advanced Academic Grammar for ESL Students", "Open Textbook Library · University of Minnesota", "https://open.umn.edu/opentextbooks/textbooks/advanced-academic-grammar-for-esl-students", "higher_education_open_textbook", "Ngữ pháp tiếng Anh học thuật cho người học ESL; nghe/nói nghề nghiệp cần luyện thêm theo tình huống.", "Giáo trình tiếng Anh học thuật có trong Open Textbook Library."),
    "math": source("Algebra and Trigonometry", "OpenStax · Rice University", "https://openstax.org/books/algebra-and-trigonometry/pages/preface", "peer_reviewed_open_textbook", "Nền tảng đại số, hàm số và lượng giác; bài toán kỹ thuật cần thêm bản vẽ và phần mềm đúng ngành.", "Giáo trình toán bậc đại học OpenStax có bài tập theo chủ đề."),
    "design": source("Graphic Design and Print Production Fundamentals", "BCcampus · British Columbia Institute of Technology và Emily Carr University", "https://open.umn.edu/opentextbooks/textbooks/graphic-design-and-print-production-fundamentals", "higher_education_open_textbook", "Nguyên lý thiết kế đồ họa, bố cục, màu sắc, chữ và sản xuất; thao tác phần mềm cần bài thực hành riêng.", "Giáo trình mở của BCcampus do giảng viên BCIT/Emily Carr University và chuyên gia ngành biên soạn; có phản biện trong Open Textbook Library."),
    "ux": source("Textbook of Usability", "Open-access usability textbook", "https://www.textbookofusability.com/", "open_academic_textbook", "Nguyên lý usability và đánh giá khả năng sử dụng; phải kiểm chứng bằng nghiên cứu người dùng.", "Trang giới thiệu là textbook mở về cơ sở khoa học của thiết kế usability; không gắn nhãn phản biện đồng cấp."),
    "media": source("Moving Pictures: An Introduction to Cinema", "Russell Leigh Sharman · University of Arkansas", "https://open.umn.edu/opentextbooks/textbooks/moving-pictures-an-introduction-to-cinema", "higher_education_open_textbook", "Ngôn ngữ hình ảnh, kể chuyện, mise-en-scène, quay phim, âm thanh và biên tập; kỹ thuật phần mềm/camera cần bài tập và hướng dẫn thiết bị riêng.", "Giáo trình đại học nhập môn nghiên cứu phim của University of Arkansas, có đánh giá học thuật và nội dung về tiền kỳ, sản xuất, hậu kỳ."),
    "electrical": source("Electrical Engineering · OER by Discipline Guide", "eCampusOntario Pressbooks", "https://ecampusontario.pressbooks.pub/oerdiscipline/chapter/electrical-engineering/", "university_oer_discipline_guide", "Điện/điện tử, đo kiểm, cảm biến, PLC, điều khiển và truyền động; thực hành phải theo quy trình an toàn và có người hướng dẫn.", "Danh mục học liệu điện của eCampusOntario liên kết khóa học, giáo trình và tài liệu PLC."),
    "mechanical": source("Introduction to Mechanical Design and Manufacturing", "University of Arkansas · Open Textbook Library", "https://open.umn.edu/opentextbooks/textbooks/introduction-to-mechanical-design-and-manufacturing", "university_open_textbook", "Thiết kế cơ khí, tạo mẫu, lắp ráp, dung sai và gia công; máy móc chỉ vận hành trong xưởng đã huấn luyện/giám sát.", "Giáo trình mở do giảng viên University of Arkansas viết, có chương thiết kế và sản xuất."),
    "construction": source("Construction Technology I", "University of Cape Town · OpenUCT", "https://open.uct.ac.za/handle/11427/2507", "university_open_course_resource", "Kiến thức nền về công nghệ/cấu kiện xây dựng; định mức, quy chuẩn và nghiệm thu phải theo quy định Việt Nam và hồ sơ được duyệt.", "Tài nguyên giáo dục mở của Khoa Kỹ thuật và Môi trường xây dựng, University of Cape Town.", "https://vbpl.vn/", "Tra cứu quy định xây dựng Việt Nam hiện hành"),
    "tourism": source("Introduction to Tourism and Hospitality in BC", "Open Textbook Library · University of Minnesota; BCcampus", "https://open.umn.edu/opentextbooks/textbooks/introduction-to-tourism-and-hospitality-in-bc", "higher_education_open_textbook", "Nền tảng du lịch, dịch vụ lưu trú và trải nghiệm khách; tuyến điểm/lịch trình phải xác minh theo điểm đến thật.", "Giáo trình du lịch/khách sạn mở của BCcampus có review trong Open Textbook Library."),
    "safety": source("Health and Safety in Canadian Workplaces", "Athabasca University Press · Open Textbook Library", "https://open.umn.edu/opentextbooks/textbooks/health-and-safety-in-canadian-workplaces", "higher_education_open_textbook", "Nền tảng nhận diện nguy cơ và quản lý an toàn lao động theo bối cảnh Canada; phải tra quy định/huấn luyện Việt Nam hiện hành trước khi áp dụng.", "Giáo trình an toàn lao động mở của Athabasca University Press, được review trong Open Textbook Library.", "https://vbpl.vn/", "Tra cứu quy định an toàn Việt Nam hiện hành"),
    "environment": source("Sustainability: A Comprehensive Foundation", "Open Textbook Library · University of Illinois faculty", "https://open.umn.edu/opentextbooks/textbooks/96", "higher_education_open_textbook", "Nền tảng quản lý môi trường, tài nguyên, chỉ số và chính sách; không thay yêu cầu pháp luật Việt Nam hoặc tiêu chuẩn ISO hiện hành.", "Giáo trình đại học liên ngành do giảng viên University of Illinois biên soạn, có chương environmental management và metrics.", "https://vbpl.vn/", "Tra cứu quy định môi trường Việt Nam hiện hành"),
    "quality": source("Quality Control 1: Introduction to QC Tools and Techniques", "Penerbit UTHM · Universiti Tun Hussein Onn Malaysia", "https://publisher.uthm.edu.my/omp/index.php/penerbituthm/catalog/book/449", "university_textbook", "Nền tảng công cụ kiểm soát chất lượng; bài tập nên dùng dữ liệu mẫu và tiêu chí của ngành/tiêu chuẩn áp dụng.", "Giáo trình do nhà xuất bản đại học UTHM phát hành, trình bày công cụ và kỹ thuật QC."),
    "culture": source("Perspectives: An Open Invitation to Cultural Anthropology · 2nd Edition", "American Anthropological Association · Open Textbook Library", "https://open.umn.edu/opentextbooks/textbooks/464", "peer_reviewed_open_textbook", "Cách nghiên cứu văn hóa, lịch sử và thực hành xã hội; phân tích theo bối cảnh, không xem niềm tin văn hóa như kết luận khoa học tự nhiên.", "Giáo trình mở của American Anthropological Association, cập nhật 2023; được giảng viên đại học phản biện trong Open Textbook Library."),
    "feng_shui": source("An Introduction to Feng Shui · A Brief History of Feng Shui", "Cambridge University Press", "https://www.cambridge.org/core/books/abs/an-introduction-to-feng-shui/brief-history-of-feng-shui/463E07D18D67257B821EE9AC062B6F9D", "academic_book_chapter", "Chương học thuật về lịch sử và ý nghĩa văn hóa của phong thủy; không xác nhận các tuyên bố siêu nhiên hay hiệu quả khoa học.", "Chương sách học thuật do Cambridge University Press phát hành; nội dung lịch sử/văn hóa, không phải hướng dẫn kỹ thuật xây dựng."),
}


EXACT = {
    "bảo mật dữ liệu": "is", "core data": "cs", "digital marketing": "marketing", "chọn thiết bị lạnh": "mechanical", "debug phần cứng": "electrical",
    "iso 14001": "environment", "iso 9001": "quality", "7 công cụ qc": "quality", "kiểm soát chất lượng": "quality",
    "cài đặt phần mềm": "is", "erp": "is", "sap erp": "is", "misa": "acct", "htkk": "law", "kiểm soát tuân thủ": "law", "kê khai thuế": "law", "kế toán thuế": "acct",
    "phân tích sop": "management", "xây dựng mối quan hệ": "org", "xây dựng tài liệu": "communication", "metasploit": "is", "linkedin": "marketing",
    "gọi điện thoại": "marketing", "thuyết phục": "marketing", "đàm phán": "org", "thương lượng": "org", "tối ưu chuyển đổi": "marketing", "pos": "business",
    "theo dõi tiến độ": "management", "theo dõi đơn hàng": "supply", "quản lý bộ nhớ": "cs", "quản lý thiết bị": "mechanical", "quản lý hồ sơ": "office",
    "quản lý hợp đồng": "law", "quản lý kênh phân phối": "marketing", "quản lý rủi ro hệ thống": "is", "quản lý tài khoản": "marketing", "quản lý đơn hàng": "supply",
    "vẽ quy trình": "management", "phát triển kinh doanh": "business", "nghiệp vụ giao dịch": "finance", "lập kế hoạch sản xuất": "supply", "tối ưu hóa hiệu suất": "se",
    "tối ưu sản phẩm": "management", "đào tạo nhân sự": "business", "đào tạo và phát triển": "business", "c&b": "business", "kỹ năng phỏng vấn": "communication",
    "tiếng anh giao tiếp": "english", "giao thức giao tiếp": "network", "tư duy phân tích": "data", "kiến thức kỹ thuật": "cs", "phong thủy cơ bản": "feng_shui", "kiến thức lịch sử văn hóa": "culture",
    "fmea": "quality",
    "python": "python", "java": "java", "c#": "csharp", "c++": "cs", "sql": "db", "sql server": "db", "sqlite": "db", "mongodb": "db", "redis": "db", "entity framework": "db",
    "excel": "office", "word": "office", "power bi": "data", "tableau": "data", "thống kê": "stats", "phân tích dữ liệu": "data", "thuật toán học máy": "ml", "nlp": "ml", "transformer": "ml", "computer vision": "ml", "pytorch": "ml", "tensorflow": "ml", "opencv": "ml",
    "asp.net core": "csharp", "spring boot": "java", "rest api": "se", "thiết kế api": "se", "api testing": "se", "kiến trúc hệ thống": "se", "phân tích yêu cầu": "se", "viết test case": "se", "viết tài liệu srs": "se", "viết user story": "se", "agile/scrum": "se", "quản lý backlog": "se",
    "chẩn đoán bệnh": "clinical", "khám lâm sàng": "clinical", "kiểm soát dược phẩm": "pharmacy", "kê đơn thuốc": "pharmacy", "tư vấn sử dụng thuốc": "pharmacy", "quản lý nhà thuốc": "pharmacy",
    "toán học": "math", "toán học 3d": "math", "ielts preparation": "english", "tiếng anh cơ bản": "english", "tiếng anh chuyên ngành": "english", "tiếng anh pháp lý": "english",
    "nghiên cứu người dùng": "ux", "phỏng vấn người dùng": "ux", "thiết kế ui ux": "ux", "thiết kế giao diện": "ux", "prototyping": "ux", "figma": "ux",
    "thiết kế nhận diện thương hiệu": "design", "màu sắc và typography": "design", "adobe illustrator": "design", "adobe photoshop": "design", "layout design": "design", "canva": "design", "tư duy hình ảnh": "design", "tư duy thẩm mỹ": "design",
    "adobe premiere": "media", "adobe premiere pro": "media", "adobe after effects": "media", "biên tập video": "media", "quay dựng video": "media", "quay video bằng điện thoại": "media", "chỉnh sửa âm thanh": "media", "capcut": "media", "kịch bản video": "media",
    "autocad": "mechanical", "autocad electrical": "electrical", "solidworks": "mechanical", "dung sai lắp ghép": "mechanical", "gia công cơ khí": "mechanical", "dụng cụ đo cơ khí": "mechanical", "g-code cơ bản": "mechanical", "vận hành máy cnc": "mechanical", "sửa chữa máy móc": "mechanical",
    "revit architecture": "construction", "revit mep": "construction", "etabs": "construction", "bóc tách khối lượng": "construction", "dự toán công trình": "construction", "giám sát thi công": "construction", "nghiệm thu công trình": "construction", "đọc bản vẽ kỹ thuật": "construction", "định mức xây dựng": "construction",
    "bloomberg terminal": "finance", "mô hình tài chính": "finance", "phân tích đầu tư": "finance", "thẩm định tín dụng": "finance", "định giá doanh nghiệp": "finance", "phân tích kinh tế vĩ mô": "economics", "mô hình rủi ro": "finance",
    "chuẩn mực kế toán": "acct", "kế toán doanh nghiệp": "acct", "kế toán tổng hợp": "acct", "lập báo cáo tài chính": "acct", "đọc báo cáo tài chính": "acct", "kiểm toán": "acct", "kiểm toán nội bộ": "acct", "kế toán quản trị": "acct_managerial", "kiểm soát tài chính": "acct_managerial",
    "quản lý tồn kho": "supply", "quản lý kho": "supply", "hoạch định chuỗi cung ứng": "supply", "chiến lược chuỗi cung ứng": "supply", "quản lý chuỗi cung ứng": "supply", "dự báo nhu cầu": "supply",
    "incoterms": "law", "hs code": "law", "luật doanh nghiệp": "law", "luật ngân hàng": "law", "luật bất động sản": "law", "luật kế toán": "law", "luật thuế": "law", "luật lao động": "law", "luật an toàn lao động": "law", "luật hải quan": "law", "giải quyết tranh chấp": "law", "rà soát hợp đồng": "law", "soạn thảo hợp đồng": "law", "tư vấn pháp lý": "law",
    "an toàn lao động": "safety", "an toàn điện": "electrical", "pccc": "safety", "đào tạo an toàn": "safety", "thiết kế hệ thống điện": "electrical", "thiết bị điện công nghiệp": "electrical", "lập trình plc": "electrical", "plc basic": "electrical", "plc siemens": "electrical", "biến tần": "electrical", "cảm biến công nghiệp": "electrical", "scada": "electrical", "thiết kế mạch": "electrical", "vi điều khiển": "electrical", "rtos": "electrical", "linux nhúng": "electrical",
    "thành thạo tuyến điểm du lịch": "tourism", "thiết kế tour du lịch": "tourism", "quản lý đoàn khách": "tourism", "phần mềm quản lý khách sạn smile": "tourism",
    "giao tiếp": "communication", "thuyết trình": "communication", "lắng nghe": "communication", "lắng nghe chủ động": "communication", "làm việc nhóm": "org", "quản lý xung đột": "org", "quản lý đội ngũ": "org", "quản lý công nhân": "org", "quản lý nhân sự": "org",
    "kỹ năng giảng dạy": "education", "soạn giáo án": "education", "quản lý lớp học": "education", "tâm lý học lứa tuổi": "education", "tư duy thiết kế": "ux", "tư duy không gian": "math",
}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in text if not unicodedata.combining(char))


def source_for(skill: str) -> str:
    if skill.casefold() in EXACT:
        return EXACT[skill.casefold()]
    text = fold(skill)
    if any(x in text for x in ("luat ", "thue", "phap ly", "hop dong", "tranh chap", "tuan thu", "hai quan", "xuat nhap khau", "chung tu xuat nhap", "bao hiem xa hoi", "incoterm", "hs code", "ecus", "vnaccs")):
        return "law"
    if any(x in text for x in ("benh nhan", "cham soc benh", "sinh ton", "tinh mach", "ho so benh an", "so cuu", "cap cuu")):
        return "nursing"
    if any(x in text for x in ("duoc", "ke don", "thuoc", "nha thuoc")):
        return "pharmacy"
    if any(x in text for x in ("an toan", "pccc", "iso 45001")):
        return "safety"
    if any(x in text for x in ("plc", "scada", "bien tan", "cam bien", "mach dien", "dien cong nghiep", "vi dieu khien", "rtos", "linux nhung", "autocad electrical")):
        return "electrical"
    if any(x in text for x in ("co khi", "cnc", "dung sai", "bao tri", "sua chua may", "g-code", "5s", "7 cong cu qc", "fmea", "lean", "kaizen", "kiem soat chat luong", "vsm")):
        return "mechanical"
    if any(x in text for x in ("xay dung", "cong trinh", "thi cong", "revit", "etabs", "cap thoat nuoc", "hvac", "tai nhiet", "ban ve", "du toan", "nghiem thu", "boc tach")):
        return "construction"
    if any(x in text for x in ("du lich", "tour", "khach san", "doan khach", "su kien")):
        return "tourism"
    if any(x in text for x in ("thong ke", "du lieu", "data", "excel", "power bi", "tableau", "etl", "spark", "airflow", "analytics", "a/b testing", "du bao doanh so", "nghien cuu thi truong", "nghien cuu tu khoa", "google analytics", "search console")):
        return "data"
    if any(x in text for x in ("sql", "database", "mongodb", "redis", "sqlite")):
        return "db"
    if any(x in text for x in ("python", "java", "javascript", "typescript", "nodejs", "express", "react", "vue", "angular", "html", "css", "sass", "tailwind", "c#", "c++", "kotlin", "swift", "dart", "flutter", "android", "ios", "api", "git", "ci/cd", "regex", "selenium", "postman", "xcode", "core data", "mvvm", "redux", "rxjs", "state management", "unity", "shader", "game", "uml", "jira", "software", "phan tich yeu cau", "kiem thu", "test case", "srs", "user story", "backlog", "agile", "scrum", "phan mem", "erp")):
        return "se" if any(x in text for x in ("jira", "agile", "scrum", "kiem thu", "test case", "srs", "user story", "backlog", "phan tich yeu cau", "uml", "kien truc he thong", "api")) else "cs"
    if any(x in text for x in ("ke toan", "tai chinh", "kiem toan", "bao cao doanh thu", "bao cao tai chinh", "bloomberg", "dinh gia", "tin dung", "ngan sach", "dem tien")):
        return "acct" if any(x in text for x in ("ke toan", "kiem toan", "bao cao tai chinh")) else "finance"
    if any(x in text for x in ("marketing", "ban hang", "khach hang", "crm", "seo", "ads", "thuong hieu", "noi dung", "quang cao", "facebook", "google ads", "tiktok", "youtube", "shopee", "pos ", "fanpage", "dai ly", "tim kiem khach", "xu huong", "trend", "content")):
        return "marketing"
    if any(x in text for x in ("chuoi cung ung", "ton kho", "quan ly kho", "nha cung cap", "thu mua", "van tai", "don hang", "fwd")):
        return "supply"
    if any(x in text for x in ("bao mat", "security", "firewall", "pentest", "siem", "lo hong", "ccna", "cisco", "mang may tinh", "routing", "switching", "active directory", "linux", "windows server", "vmware", "kubernetes", "docker", "aws", "azure", "terraform", "quan tri mang", "giam sat he thong")):
        return "network" if any(x in text for x in ("ccna", "cisco", "mang may tinh", "routing", "switching", "quan tri mang")) else "is"
    if any(x in text for x in ("du lieu", "thong ke", "phan tich", "tu duy logic", "tu duy kiem thu")):
        return "data" if any(x in text for x in ("du lieu", "thong ke", "phan tich")) else "cs"
    if any(x in text for x in ("giao tiep", "thuyet trinh", "lang nghe", "dam phan", "thuong luong", "giai quyet van de", "quan ly cam xuc", "chiu ap luc", "chu y chi tiet", "can than", "kien nhan", "xay dung moi quan he", "lam viec nhom", "dieu phoi cuoc hop", "quan ly thoi gian", "xu ly tinh huong", "xu ly khieu nai", "xu ly khung hoang", "xu ly su co", "quan he bao chi", "truyen thong", "viet thong cao", "soan thao van ban")):
        return "communication" if any(x in text for x in ("giao tiep", "thuyet trinh", "lang nghe", "quan he bao chi", "truyen thong", "viet thong cao", "soan thao van ban")) else "org"
    if any(x in text for x in ("tieng anh", "ielts")):
        return "english"
    if any(x in text for x in ("marketing", "ban hang", "khach hang", "crm", "seo", "ads", "thuong hieu", "noi dung", "facebook", "google ads", "tiktok", "youtube", "shopee", "fanpage", "dai ly", "trend")):
        return "marketing"
    if any(x in text for x in ("nhan su", "ung vien", "tuyen dung", "dao tao", "lop hoc", "giang day", "giao an", "tinh luong", "danh gia nang luc")):
        return "education" if any(x in text for x in ("lop hoc", "giang day", "giao an")) else "business"
    if any(x in text for x in ("thiet ke", "design", "figma", "canva", "photoshop", "illustrator", "after effects", "premiere", "capcut", "video", "am thanh", "quay", "3ds max", "sketchup", "mau sac", "typography", "hinh anh", "tham my", "sang tao", "ke chuyen", "kich ban", "phong thuy")):
        return "media" if any(x in text for x in ("video", "quay", "am thanh", "premiere", "after effects", "capcut", "kich ban")) else "design"
    if any(x in text for x in ("quan ly", "ke hoach", "kinh doanh", "ngan sach", "kiem soat", "quy trinh", "sop", "ho tro kinh doanh", "cong tac hanh chinh", "nghiep vu giao dich", "danh gia rui ro", "xay dung tai lieu")):
        return "management"
    if "toan" in text or "khong gian" in text:
        return "math"
    return "business"


def learning_plan(skill: str, source_id: str):
    name = skill
    if source_id == "feng_shui":
        task = "Ghi nhận một ví dụ lịch sử/văn hóa về phong thủy rồi tách riêng điều thuộc tư liệu văn hóa với tuyên bố cần kiểm chứng bằng phương pháp khoa học; không kết luận đây là quy tắc kỹ thuật có hiệu lực."
        evidence = "ghi chú một trang phân biệt bối cảnh lịch sử, niềm tin văn hóa, bằng chứng kiểm chứng được và điều chưa thể kết luận."
    elif source_id == "culture":
        task = f"Đọc một trường hợp văn hóa liên quan tới {name}; nêu bối cảnh, nguồn, góc nhìn của người trong cộng đồng và giới hạn của cách diễn giải."
        evidence = "bản tóm tắt có nguồn trích dẫn, bối cảnh và giới hạn diễn giải."
    elif source_id == "quality":
        task = f"Dùng bộ dữ liệu giả lập để thử một công cụ kiểm soát chất lượng cho {name}; nêu tiêu chí, ngưỡng và cách xác minh kết quả."
        evidence = "biểu đồ/checklist QC trên dữ liệu giả lập cùng tiêu chí và nhận xét của người hướng dẫn."
    elif source_id == "environment":
        task = f"Lập checklist mô phỏng về {name}; đối chiếu một yêu cầu môi trường Việt Nam đang hiệu lực và ghi ngày/nguồn tra cứu."
        evidence = "checklist mô phỏng có nguồn văn bản Việt Nam, ngày tra cứu và điểm cần người phụ trách môi trường xác nhận."
    elif source_id in {"clinical", "nursing", "pharmacy"}:
        task = f"Dùng ca mô phỏng đã ẩn danh để luyện {name}; nhờ giảng viên/người có chuyên môn kiểm tra. Không thao tác trên người bệnh hoặc tự đưa chỉ định."
        evidence = "phiếu ca mô phỏng, tài liệu đã dùng và nhận xét của người hướng dẫn."
    elif source_id == "law":
        task = f"Làm case giả định về {name}; xác định văn bản Việt Nam cần tra và nhờ người có chuyên môn kiểm tra. Không dùng giáo trình Hoa Kỳ như luật Việt Nam."
        evidence = "bản ghi nhớ ngắn có tình huống giả định, link văn bản Việt Nam, ngày tra cứu và câu hỏi còn mở."
    elif source_id in {"safety", "electrical", "mechanical", "construction", "environment"}:
        task = f"Tạo bài tập mô phỏng cho {name} bằng sơ đồ/bản vẽ/dữ liệu giả lập; nhờ người hướng dẫn đủ chuyên môn kiểm tra trước thao tác thực tế."
        evidence = "sơ đồ/tính toán/checklist mô phỏng, giả định, tiêu chuẩn đã tra và góp ý người hướng dẫn."
    elif source_id in {"data", "stats", "ml", "db"}:
        task = f"Dùng dữ liệu tổng hợp làm bài tập nhỏ về {name}; ghi câu hỏi, bước xử lý, kết quả và giới hạn; nhờ người khác kiểm tra hoặc tái lập."
        evidence = "notebook/truy vấn/dashboard chạy lại được, dữ liệu giả lập, kết quả và giới hạn."
    elif source_id in {"acct", "acct_managerial", "finance", "economics"}:
        task = f"Giải case giả lập về {name}; ghi giả định, công thức/nguồn số liệu và cách kiểm tra kết quả. Đối chiếu quy định Việt Nam khi có yếu tố tuân thủ."
        evidence = "bảng tính hoặc memo với dữ liệu giả lập, công thức, nguồn và bước kiểm tra độc lập."
    elif source_id in {"design", "ux", "media"}:
        task = f"Tạo sản phẩm nhỏ thể hiện {name}; nêu mục tiêu/người dùng, xin phản hồi rồi chỉnh sửa một vòng."
        evidence = "sản phẩm trước/sau góp ý, mục tiêu và ghi chú thay đổi."
    elif source_id in {"marketing", "business", "management", "supply", "tourism"}:
        task = f"Giải tình huống mô phỏng về {name}; nêu mục tiêu, lựa chọn, chỉ số và rủi ro, rồi nhờ người trong ngành phản biện."
        evidence = "brief/kế hoạch ngắn có mục tiêu, giả định, chỉ số, bước làm và phản hồi."
    else:
        task = f"Thực hành {name} trong tình huống nghề nghiệp mô phỏng; nhờ người quan sát góp ý vào hành vi/đầu ra cụ thể rồi thử lại."
        evidence = "bài nói/viết hoặc sản phẩm thực hành trước và sau phản hồi."
    src = SOURCES[source_id]
    return {
        "title": f"Học và luyện {name}",
        "source_scope": src["scope"],
        "steps": [
            f"Đọc phần được chỉ định trong ‘{src['title']}’; ghi 3 ý áp dụng cho {name}.",
            task,
            "So đầu ra với tiêu chí/ví dụ trong tài liệu; ghi điều làm được và câu hỏi còn thiếu.",
            "Xin giảng viên/mentor/người có kinh nghiệm góp ý rồi sửa sản phẩm một lần.",
        ],
        "evidence": evidence,
        "self_paced": True,
    }


def main():
    roles = json.loads((ROOT / "data" / "roles.json").read_text(encoding="utf-8"))
    skills = sorted({item["name"].strip() for role in roles for item in role["skills"]}, key=str.casefold)
    mappings = {}
    for skill in skills:
        sid = source_for(skill)
        if sid not in SOURCES:
            raise ValueError(f"No academic source for {skill}: {sid}")
        mappings[skill] = {"source_id": sid, "learning_plan": learning_plan(skill, sid)}
    payload = {
        "schema_version": 1,
        "description": "A skill-by-skill learning overlay that links to academic/OER sources and applied work; text is not redistributed.",
        "sources": SOURCES,
        "skills": mappings,
    }
    output = ROOT / "data" / "academic_curriculum.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(mappings)} mappings across {len(set(m['source_id'] for m in mappings.values()))} source tracks: {output}")


if __name__ == "__main__":
    main()
