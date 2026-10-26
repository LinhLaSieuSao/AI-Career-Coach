"""Apply the manually inspected dispositions for the 187 outstanding mappings."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.data_quality import audit_project  # noqa: E402


TODAY = date.today().isoformat()
RESOURCES_PATH = ROOT / "Data" / "resources.json"
CATALOG_PATH = ROOT / "Data" / "skill_catalog.json"
ALIASES_PATH = ROOT / "Data" / "skill_aliases.json"
REPORT_PATH = ROOT / "docs" / "reports" / "resource-review-2026-10-25.json"

# The linked page was opened and checked. Evidence is paraphrased so this file
# records the relevant section without copying publisher text into the app.
SOURCE_EVIDENCE = {
    "https://learnenglish.britishcouncil.org/": "Trang LearnEnglish giới thiệu tài nguyên theo nhóm tuổi và người học; có bài luyện tiếng Anh và nội dung chuẩn bị kỳ thi. Đây là cổng tổng hợp, không phải khóa tiếng Anh chuyên ngành.",
    "https://git-scm.com/doc": "Cổng tài liệu Git chính thức; liên kết chuyển hướng tới trang tài liệu.",
    "https://www.freecodecamp.org/news/how-to-run-freecodecamps-relational-databases-curriculum-using-docker-vscode-and-coderoad": "Bài khóa relational database nêu PostgreSQL, SQL, Linux/Unix và các dự án; không đề cập MongoDB.",
    "https://www.kaggle.com/learn": "Trang Kaggle Learn là danh mục học dữ liệu và trực quan hóa; nội dung trang tải động nên không xác nhận được từng course cụ thể trong phiên review.",
    "https://www.khanacademy.org/math/statistics-probability": "Danh mục Khan Academy Statistics and Probability; trang tải nội dung động, giới hạn đánh giá ở toán/thống kê nền tảng.",
    "https://docs.python.org/3/tutorial/": "Python Tutorial mô tả cú pháp, cấu trúc dữ liệu, hàm và module; đây không phải tài liệu chuyên biệt về bộ nhớ hay biểu thức chính quy.",
    "https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Client-side_APIs/Introduction": "MDN giải thích cách dùng Web APIs phía client và Fetch; không phải hướng dẫn thiết kế REST API phía server.",
    "https://docs.docker.com/get-started/": "Docker Get Started hướng dẫn cài đặt và chạy ứng dụng/container; không bao quát pipeline CI/CD.",
    "https://openstax.org/books/organizational-behavior/pages/14-4-negotiation-behavior": "Mục 14.4 trình bày hành vi và các giai đoạn thương lượng; đây là kiến thức nền, không thay thế luyện tình huống và phản hồi.",
    "https://www.netacad.com/catalogs/learn?courseLang=en-US": "Danh mục Cisco Networking Academy là ứng dụng JavaScript; phiên review chỉ xác nhận được danh tính cổng học, không xác nhận course cụ thể.",
    "https://developer.mozilla.org/en-US/docs/MDN/Tutorials": "Danh mục tutorial web development của MDN; hữu ích cho HTML/CSS/JavaScript nền tảng, không chứng minh khóa riêng cho Angular/TypeScript.",
    "https://www.autodesk.com/learning.autodesk": "Trang Autodesk Learning nêu Technical Drawing for AutoCAD, modeling cho Revit và các pathway thực hành; phạm vi theo sản phẩm Autodesk.",
    "https://skillbuilder.aws/": "AWS Skill Builder là cổng học tập AWS; trang tải bằng JavaScript nên không xác minh một course cụ thể hoặc thời lượng.",
    "https://www.atlassian.com/agile/tutorials/how-to-do-scrum-with-jira": "Tutorial hướng dẫn quy trình Scrum bằng Jira; phù hợp để làm quen thao tác Jira nhưng không đại diện toàn bộ năng lực quản lý dự án.",
    "https://learning.sap.com/learning-journeys?trk=public_post_comment-text": "SAP Learning Journeys là danh mục học tập nhiều chủ đề, có UX, phát triển phần mềm, dữ liệu và cloud; cần chọn journey SAP/ERP cụ thể.",
    "https://learn.microsoft.com/training/powerplatform/power-bi/": "Microsoft Learn mô tả kết nối, làm sạch, mô hình hóa và trực quan hóa dữ liệu bằng Power BI.",
    "https://academy.hubspot.com/": "HubSpot Academy cung cấp học liệu on-demand về HubSpot và kỹ năng kinh doanh; không dạy quản lý LinkedIn.",
    "https://www.canva.com/designschool/": "Canva Design School/Design giới thiệu thiết kế số, tài liệu, bài trình bày, mạng xã hội và video bằng Canva.",
    "https://f8.edu.vn/": "Danh mục F8 hiện hiển thị các lộ trình/khóa web như React, Node.js, Express, Redux và PostgreSQL; nội dung từng khóa có thể yêu cầu đăng nhập hoặc thanh toán.",
    "https://learn.microsoft.com/en-us/training/azure/": "Microsoft Learn for Azure tập trung xây dựng và vận hành ứng dụng/cloud services trên Azure.",
    "https://www.atlassian.com/agile/project-management/user-stories": "Trang Atlassian về user stories hỗ trợ viết yêu cầu dạng story; không bao quát SRS hoặc UML.",
    "https://www.capcut.com/resource/capcut-tutorial-for-beginners": "Hướng dẫn CapCut cho người mới bao gồm thao tác biên tập video và tạo nội dung ngắn.",
    "https://www.gdt.gov.vn/": "Cổng Tổng cục Thuế là cổng cơ quan thuế; phiên review không lấy được nội dung hướng dẫn/chính sách cụ thể và đây không phải tài liệu MISA hay nghiệp vụ hải quan.",
    "https://vanban.chinhphu.vn/?classid=2629&docid=217002&pageid=27160": "Trang chính thức dẫn tới Bộ luật Lao động hợp nhất 18/VBHN-VPQH; chưa đối chiếu toàn văn và văn bản sửa đổi sau thời điểm ban hành nên không dùng làm tư vấn pháp luật hiện hành.",
    "https://www.who.int/teams/integrated-health-services/clinical-services-and-systems/emergency-and-critical-care/bec": "WHO Basic Emergency Care dành cho người cung cấp chăm sóc ban đầu trong bối cảnh khẩn cấp; không tương đương chứng chỉ sơ cấp cứu được công nhận tại Việt Nam.",
    "https://developer.android.com/courses": "Android Developers có khóa Android Basics with Compose và các pathway do Google xây dựng; hướng dẫn dùng Android Studio/Kotlin và nền tảng Android.",
    "https://developer.apple.com/documentation/xcode": "Tài liệu Xcode chính thức của Apple; nội dung dùng JavaScript trong browser viewer nhưng trang định danh là documentation cho công cụ Xcode.",
    "https://www.freecodecamp.org/news/learn-programming-free-software-development-courses-for-beginners": "Bài freeCodeCamp liệt kê khóa C++ riêng và nêu nội dung con trỏ, kế thừa, mảng, điều kiện; đây là danh mục liên kết đến course/video.",
    "https://www.selenium.dev/documentation/": "Selenium documentation tập trung WebDriver, locator, interactions, waits và browser automation.",
    "https://learning.postman.com/docs/": "Postman Docs v12 giới thiệu cách dùng Postman trong API projects và có hướng dẫn workflows/requests.",
    "https://huggingface.co/learn/nlp-course/chapter1/1": "Liên kết đã chuyển tới Hugging Face LLM Course; mục lục có transformer models và sử dụng Transformers, không còn là khóa NLP tổng quát cũ.",
    "https://github.com/opencv/opencv/wiki/": "Wiki OpenCV trỏ tới official documentation mới; wiki chính có nội dung tổng hợp và một số trang lịch sử/legacy.",
    "https://owasp.org/www-project-web-security-testing-guide/": "OWASP WSTG là hướng dẫn kiểm thử bảo mật ứng dụng web, gồm bản stable 4.2 và nhánh đang phát triển.",
    "https://www.facebook.com/business/learn": "Meta Blueprint chuyển sang yêu cầu đăng nhập và chặn truy cập trong lần review; chưa xác nhận được nội dung khóa học cụ thể.",
    "https://skillshop.withgoogle.com/": "Google Skillshop hiển thị các khóa Google Ads và Google Marketing Platform; chỉ hỗ trợ thử nghiệm trong sản phẩm Google Ads, không phải A/B testing tổng quát.",
    "https://developers.google.com/search/docs/fundamentals/seo-starter-guide": "Google SEO Starter Guide dạy nguyên tắc hiển thị trong Google Search; không phải khóa chuyên sâu keyword research hoặc off-page SEO.",
    "https://support.google.com/webmasters/answer/9128668?hl=en": "Search Console Help mô tả theo dõi crawl/indexing, truy vấn, traffic, backlinks và lỗi site.",
    "https://developers.google.com/search/docs/essentials": "Google Search Essentials nói về technical requirements, spam policies, lựa chọn từ người dùng dùng để tìm trang, title/headings và crawlable links.",
    "https://support.google.com/google-ads/answer/6261395?hl=en": "Google Ads Help hướng dẫn custom experiments: so sánh campaign, chia traffic, chọn success metric và theo dõi kết quả trong Google Ads.",
    "https://docs.opencv.org/4.x/d9/df8/tutorial_root.html": "OpenCV Tutorials 4.x có core functionality, image processing, camera calibration, object detection, DNN và GPU computer vision.",
    "https://www.tiktokacademy.com/": "TikTok Academy mở danh mục hoạt động gồm TikTok basics, creative guidance, brand awareness, conversions, leads, policy và trend research.",
    "https://openstax.org/books/principles-marketing/pages/13-1-the-promotion-mix-and-its-elements": "Mục 13.1 giải thích promotion mix và vai trò truyền thông marketing; không dạy trend spotting, conversion optimization hay kể chuyện.",
    "https://www.teachingenglish.org.uk/teaching-resources": "British Council TeachingEnglish có hơn 400 lesson plans, activities, tools và nội dung phát triển chuyên môn cho lớp tiếng Anh.",
    "https://spring.io/guides": "Spring Guides là hướng dẫn chính thức về Spring; các mục bao gồm web, REST APIs, data access, testing và cloud.",
    "https://redis.io/docs/latest/": "Redis Docs bao gồm phát triển, data types, tools, API và vận hành Redis; tài liệu kỹ thuật nền tảng.",
    "https://learn.microsoft.com/en-us/ef/core/": "EF Core overview mô tả ORM, truy cập database bằng .NET objects và các database providers.",
    "https://vuejs.org/guide/introduction.html": "Vue Guide chính thức giải thích Vue framework và các phần tutorial/API liên quan.",
    "https://vuex.vuejs.org/": "Tài liệu Vuex hiện là dòng v4; đây là tham chiếu cho dự án đang dùng Vuex, không phải khuyến nghị mặc định cho dự án Vue mới.",
    "https://tailwindcss.com/docs/installation": "Trang Tailwind hiện chuyển tới tài liệu cài đặt v4 với Vite; phạm vi là setup và utility CSS của Tailwind.",
    "https://rxjs.dev/guide/overview": "RxJS Overview là tài liệu chính thức giới thiệu reactive extensions cho JavaScript; browser cần JavaScript để hiển thị nội dung.",
    "https://sass-lang.com/guide/": "Sass Basics giải thích preprocessing, nesting, mixins, inheritance và biên dịch stylesheet.",
    "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/": "Swift Language Book là tài liệu ngôn ngữ chính thức; trang mới yêu cầu JavaScript để render.",
    "https://developer.apple.com/documentation/coredata": "Apple Core Data Documentation là tham chiếu chính thức cho framework Core Data; nội dung web yêu cầu JavaScript.",
    "https://kotlinlang.org/docs/getting-started.html": "Kotlin Getting Started giới thiệu ngôn ngữ, Kotlin tour, JVM/backend và Kotlin Multiplatform.",
    "https://www.sqlite.org/quickstart.html": "SQLite quickstart dạy tạo database, thao tác CLI và bắt đầu dùng SQLite; không bao quát quản trị database production.",
    "https://developer.android.com/topic/architecture": "Android Guide to App Architecture nói về UI/data layers, ViewModel, navigation và kiến trúc app; không phải giáo trình riêng về mọi biến thể MVVM.",
    "https://dart.dev/learn": "Dart Learn có tutorial xây dựng ứng dụng CLI và đường học kết hợp Dart/Flutter.",
    "https://docs.flutter.dev/get-started/codelab": "Liên kết codelab cũ chuyển tới Flutter Learning Pathway; nội dung có UI, state và app architecture.",
    "https://reactnative.dev/docs/getting-started": "React Native Introduction liên kết fundamentals, input, scrolling, setup, UI, debugging và testing.",
    "https://learn.unity.com/": "Unity Learn có khóa nhập môn tạo scene, pathways và courses; trang chủ không xác nhận riêng kỹ thuật shader/hiệu năng.",
    "https://docs.arduino.cc/": "Arduino documentation có hardware, software, programming, tutorials và ví dụ cho hệ sinh thái Arduino.",
    "https://www.freertos.org/Documentation/RTOS_book.html": "Liên kết chuyển hướng tới sách/tài liệu FreeRTOS chính thức; nội dung tài liệu đọc không có metadata khóa học hay thời lượng.",
    "https://docs.kicad.org/": "KiCad Documentation gồm Getting Started, schematic editor, PCB editor và CLI.",
    "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/": "Airflow Tutorials gồm workflow đầu tiên, TaskFlow API, data pipeline và object storage.",
    "https://www.tensorflow.org/tutorials": "TensorFlow tutorials có ML basics, data preprocessing, vision, text, audio và structured data.",
    "https://learn.microsoft.com/en-us/windows-server/": "Windows Server documentation bao quát nền tảng server, triển khai và vận hành hạ tầng mạng/dịch vụ.",
    "https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/active-directory-domain-services": "AD DS overview giải thích directory, đối tượng mạng và quản lý định danh/tài khoản trong Windows Server.",
    "https://www.broadcom.com/support/education/vmware": "Trang VCF/Broadcom Learning tải nội dung bằng JavaScript; không xác nhận được course VMware cụ thể trong phiên này.",
    "https://docs.metasploit.com/": "Metasploit documentation hướng dẫn dùng framework trong hoạt động kiểm thử được phép, thiết lập môi trường, module và quy trình pentest.",
    "https://support.microsoft.com/en-us/windows/deployment/install-upgrade/fix-problems-that-block-programs-from-being-installed-or-removed": "Microsoft Support hướng dẫn khắc phục lỗi cài hoặc gỡ chương trình trên Windows; phạm vi là troubleshooting cụ thể.",
    "https://learn.microsoft.com/en-us/troubleshoot/windows-client/welcome-windows-client": "Windows client troubleshooting tập hợp hướng dẫn hỗ trợ hệ điều hành, identity, networking, storage và application management.",
    "https://learn.microsoft.com/training/paths/deploy-configure-azure-monitor/": "Azure Monitor learning path có sáu module về Log Analytics và giám sát telemetry từ VM, network và web app.",
    "https://www.atlassian.com/agile/tutorials/jira-confluence-sprint-refinement": "Atlassian tutorial trình bày sprint planning/refinement bằng Jira và Confluence; mang tính quy trình/tool-specific.",
    "https://creatoracademy.youtube.com/": "URL Creator Academy chuyển thẳng tới channel YouTube chung; không còn trang học liệu Academy để review.",
    "https://trailhead.salesforce.com/": "Salesforce Trailhead có badges, trails, journeys và hands-on Superbadges cho Salesforce platform.",
    "https://openstax.org/books/introduction-business-2e/pages/10-4-pulling-it-together-resource-planning": "Mục 10.4 bao quát resource planning, dự báo nhu cầu, nguyên liệu, procurement và inventory trong sản xuất.",
    "https://openstax.org/books/introduction-business-2e/pages/10-5-production-and-operations-control": "Mục 10.5 nói về production control, routing, scheduling, value-stream mapping và hiệu quả chi phí.",
    "https://openstax.org/books/principles-finance/pages/5-why-it-matters": "Chương 5 giới thiệu income statement, balance sheet, equity và cash-flow statements; không nói về nghiệp vụ giao dịch ngân hàng.",
    "https://openstax.org/books/principles-economics-3e/pages/1-introduction": "Mục mở đầu giới thiệu economics, micro/macro, theories/models và economic systems.",
    "https://support.microsoft.com/en-us/word": "Microsoft Word Help & Learning có hướng dẫn định dạng, layout, ảnh, lưu/in và cộng tác.",
    "https://academy.iccwbo.org/wp-content/uploads/2020/08/803E_Incoterms-2020-Wallchart-A4.pdf": "ICC Incoterms 2020 chart chỉ tóm tắt trách nhiệm/chi phí/rủi ro; chính chart cảnh báo phải dùng cùng Incoterms 2020 rulebook.",
    "https://help.ecus.net.vn/": "ECUS5VNACCS manual có khai báo VNACCS, biểu thuế 2026, thủ tục và lịch sử cập nhật đến 2026; vẫn là tài liệu thao tác sản phẩm, không thay văn bản pháp luật.",
    "https://sitrain.siemens.com/gb/web/en/app/toc/simatic-programming-1-in-tia-portal-0144478865067704321706/overview": "Course title là SIMATIC Programming in TIA Portal; không có bằng chứng page cover sensor selection, inverter maintenance or repair tasks.",
    "https://creativecloud.adobe.com/learn": "Adobe Learn chuyển tới trang học kỹ năng với các ứng dụng Creative Cloud; cần chọn bài After Effects cụ thể.",
}

PARTIAL = {
    "https://learnenglish.britishcouncil.org/": ["tiếng anh giao tiếp", "tiếng anh cơ bản", "ielts preparation"],
    "https://git-scm.com/doc": ["git"],
    "https://www.freecodecamp.org/news/how-to-run-freecodecamps-relational-databases-curriculum-using-docker-vscode-and-coderoad": ["sql"],
    "https://www.kaggle.com/learn": ["phân tích dữ liệu", "thuật toán học máy"],
    "https://www.khanacademy.org/math/statistics-probability": ["tư duy phân tích", "tư duy logic", "thống kê", "toán học"],
    "https://docs.python.org/3/tutorial/": ["python"],
    "https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Client-side_APIs/Introduction": ["rest api"],
    "https://docs.docker.com/get-started/": ["docker"],
    "https://openstax.org/books/organizational-behavior/pages/14-4-negotiation-behavior": ["thương lượng", "đàm phán"],
    "https://www.netacad.com/catalogs/learn?courseLang=en-US": ["linux", "quản trị mạng", "mạng máy tính", "ccna", "routing & switching", "cisco", "bảo mật hệ thống", "firewall"],
    "https://developer.mozilla.org/en-US/docs/MDN/Tutorials": ["html", "css", "javascript"],
    "https://www.autodesk.com/learning.autodesk": ["autocad", "revit mep", "revit architecture"],
    "https://skillbuilder.aws/": ["aws"],
    "https://www.atlassian.com/agile/tutorials/how-to-do-scrum-with-jira": ["jira"],
    "https://learning.sap.com/learning-journeys?trk=public_post_comment-text": ["erp", "sap erp"],
    "https://learn.microsoft.com/training/powerplatform/power-bi/": ["power bi", "lập báo cáo", "báo cáo doanh thu"],
    "https://academy.hubspot.com/": ["crm"],
    "https://www.canva.com/designschool/": ["canva", "thiết kế cơ bản", "layout design"],
    "https://f8.edu.vn/": ["reactjs", "nodejs", "expressjs", "redux"],
    "https://learn.microsoft.com/en-us/training/azure/": ["azure", "kiến trúc hệ thống"],
    "https://www.atlassian.com/agile/project-management/user-stories": ["phân tích yêu cầu", "viết user story"],
    "https://www.capcut.com/resource/capcut-tutorial-for-beginners": ["capcut", "quay dựng video"],
    "https://www.who.int/teams/integrated-health-services/clinical-services-and-systems/emergency-and-critical-care/bec": ["sơ cứu cấp cứu"],
    "https://developer.android.com/courses": ["lập trình android", "android sdk", "android studio"],
    "https://developer.apple.com/documentation/xcode": ["lập trình ios", "ios sdk", "xcode"],
    "https://www.freecodecamp.org/news/learn-programming-free-software-development-courses-for-beginners": ["c++"],
    "https://www.selenium.dev/documentation/": ["selenium"],
    "https://learning.postman.com/docs/": ["api testing", "postman"],
    "https://huggingface.co/learn/nlp-course/chapter1/1": ["transformer"],
    "https://github.com/opencv/opencv/wiki/": ["computer vision", "opencv"],
    "https://owasp.org/www-project-web-security-testing-guide/": ["đánh giá lỗ hổng", "pentest", "bảo mật web"],
    "https://skillshop.withgoogle.com/": ["google ads", "a/b testing"],
    "https://developers.google.com/search/docs/fundamentals/seo-starter-guide": ["seo on-page", "seo off-page", "nghiên cứu từ khóa"],
    "https://support.google.com/webmasters/answer/9128668?hl=en": ["google search console"],
    "https://www.tiktokacademy.com/": ["tiktok"],
    "https://www.teachingenglish.org.uk/teaching-resources": ["kỹ năng giảng dạy", "soạn giáo án", "quản lý lớp học"],
    "https://spring.io/guides": ["spring boot"],
    "https://redis.io/docs/latest/": ["redis"],
    "https://learn.microsoft.com/en-us/ef/core/": ["entity framework"],
    "https://vuejs.org/guide/introduction.html": ["vuejs"],
    "https://vuex.vuejs.org/": ["vuex"],
    "https://tailwindcss.com/docs/installation": ["tailwind css"],
    "https://rxjs.dev/guide/overview": ["rxjs"],
    "https://sass-lang.com/guide/": ["sass"],
    "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/": ["swift"],
    "https://developer.apple.com/documentation/coredata": ["core data"],
    "https://kotlinlang.org/docs/getting-started.html": ["kotlin"],
    "https://www.sqlite.org/quickstart.html": ["sqlite"],
    "https://developer.android.com/topic/architecture": ["mvvm"],
    "https://dart.dev/learn": ["dart"],
    "https://docs.flutter.dev/learn/pathway": ["flutter framework", "state management"],
    "https://reactnative.dev/docs/getting-started": ["react native"],
    "https://learn.unity.com/": ["unity engine"],
    "https://docs.arduino.cc/": ["vi điều khiển", "giao thức giao tiếp"],
    "https://www.freertos.org/Documentation/RTOS_book.html": ["rtos"],
    "https://docs.kicad.org/": ["thiết kế mạch"],
    "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/": ["airflow"],
    "https://www.tensorflow.org/tutorials": ["tensorflow"],
    "https://learn.microsoft.com/en-us/windows-server/": ["windows server", "quản lý thiết bị"],
    "https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/active-directory-domain-services": ["active directory"],
    "https://docs.metasploit.com/": ["metasploit"],
    "https://support.microsoft.com/en-us/windows/deployment/install-upgrade/fix-problems-that-block-programs-from-being-installed-or-removed": ["cài đặt phần mềm"],
    "https://learn.microsoft.com/en-us/troubleshoot/windows-client/welcome-windows-client": ["windows os"],
    "https://learn.microsoft.com/training/paths/deploy-configure-azure-monitor/": ["giám sát hệ thống"],
    "https://www.atlassian.com/agile/tutorials/jira-confluence-sprint-refinement": ["quản lý backlog"],
    "https://trailhead.salesforce.com/": ["quản lý tài khoản", "tư vấn giải pháp"],
    "https://openstax.org/books/introduction-business-2e/pages/10-4-pulling-it-together-resource-planning": ["quản lý đơn hàng", "thu mua", "quản lý kho", "hoạch định chuỗi cung ứng"],
    "https://openstax.org/books/introduction-business-2e/pages/10-5-production-and-operations-control": ["theo dõi tiến độ", "tối ưu hóa chi phí", "quản lý tiến độ", "sơ đồ chuỗi giá trị vsm", "lập kế hoạch sản xuất"],
    "https://openstax.org/books/principles-economics-3e/pages/1-introduction": ["phân tích kinh tế vĩ mô"],
    "https://support.microsoft.com/en-us/word/": ["word"],
    "https://academy.iccwbo.org/wp-content/uploads/2020/08/803E_Incoterms-2020-Wallchart-A4.pdf": ["incoterms"],
    "https://help.ecus.net.vn/": ["phần mềm ecus/vnaccs"],
    "https://creativecloud.adobe.com/learn": ["adobe after effects"],
}

BLOCKED = {
    "https://www.gdt.gov.vn/": ["kế toán thuế", "kê khai thuế", "htkk", "thuế tncn"],
    "https://vanban.chinhphu.vn/?classid=2629&docid=217002&pageid=27160": ["luật lao động"],
    "https://www.facebook.com/business/learn": ["facebook ads", "quản lý fanpage", "facebook"],
    "https://www.broadcom.com/support/education/vmware": ["vmware"],
    "https://creatoracademy.youtube.com/": ["kịch bản video", "youtube", "sáng tạo kịch bản"],
}

REPLACEMENTS = {
    ("https://developers.google.com/search/docs/fundamentals/seo-starter-guide", "google search console"): "https://support.google.com/webmasters/answer/9128668?hl=en",
    ("https://developers.google.com/search/docs/fundamentals/seo-starter-guide", "nghiên cứu từ khóa"): "https://developers.google.com/search/docs/essentials",
    ("https://developers.google.com/search/docs/fundamentals/seo-starter-guide", "seo off-page"): "https://developers.google.com/search/docs/essentials",
    ("https://developers.google.com/search/docs/fundamentals/seo-starter-guide", "seo on-page"): "https://developers.google.com/search/docs/essentials",
    ("https://skillshop.withgoogle.com/", "a/b testing"): "https://support.google.com/google-ads/answer/6261395?hl=en",
    ("https://github.com/opencv/opencv/wiki/", "computer vision"): "https://docs.opencv.org/4.x/d9/df8/tutorial_root.html",
    ("https://github.com/opencv/opencv/wiki/", "opencv"): "https://docs.opencv.org/4.x/d9/df8/tutorial_root.html",
    ("https://huggingface.co/learn/nlp-course/chapter1/1", "nlp"): "https://huggingface.co/learn/llm-course/chapter1/1",
    ("https://huggingface.co/learn/nlp-course/chapter1/1", "transformer"): "https://huggingface.co/learn/llm-course/chapter1/1",
    ("https://docs.flutter.dev/get-started/codelab", "flutter framework"): "https://docs.flutter.dev/learn/pathway",
    ("https://docs.flutter.dev/get-started/codelab", "state management"): "https://docs.flutter.dev/learn/pathway",
    ("https://support.microsoft.com/en-us/word", "word"): "https://support.microsoft.com/en-us/word/",
}

SPECIAL_NOTES = {
    ("https://openstax.org/books/organizational-behavior/pages/14-4-negotiation-behavior", "thương lượng"): "Nội dung có khung giai đoạn thương lượng để tham khảo; năng lực cần role-play, quan sát và phản hồi trong tình huống thực tế.",
    ("https://openstax.org/books/organizational-behavior/pages/14-4-negotiation-behavior", "đàm phán"): "Nội dung giải thích hành vi/giai đoạn đàm phán ở mức giáo trình; không xem việc đọc là đạt kỹ năng. Hãy ghép route role-play có phản hồi.",
    ("https://www.who.int/teams/integrated-health-services/clinical-services-and-systems/emergency-and-critical-care/bec", "sơ cứu cấp cứu"): "Nền tảng BEC dành cho nhân viên y tế ở tuyến đầu; không phải chứng nhận sơ cấp cứu cho cộng đồng hoặc chứng chỉ hành nghề Việt Nam.",
    ("https://www.netacad.com/catalogs/learn?courseLang=en-US", "linux"): "Cổng Cisco Academy có thể hỗ trợ kỹ năng nền tảng; nội dung tải động nên hãy xem như catalog cần người dùng tự chọn course Linux cụ thể.",
    ("https://www.netacad.com/catalogs/learn?courseLang=en-US", "ccna"): "Danh mục chính thức của Cisco Academy hỗ trợ tìm nội dung CCNA; chưa gắn một module/đề cương CCNA cụ thể.",
    ("https://learn.microsoft.com/en-us/training/azure/", "kiến trúc hệ thống"): "Chỉ phù hợp kiến trúc/giải pháp trong hệ sinh thái Azure; không phải khung thiết kế hệ thống trung lập hay hướng dẫn mọi domain.",
    ("https://developers.google.com/search/docs/essentials", "seo off-page"): "Google nêu best practices về chia sẻ/nói về website; không phải khóa xây dựng backlink hoặc chiến lược off-page đầy đủ.",
    ("https://vuex.vuejs.org/", "vuex"): "Dùng cho dự án hiện hữu trên Vuex v4. Vue hiện khuyến nghị Pinia cho dự án mới; kiểm tra stack thực tế trước khi học.",
    ("https://developer.android.com/topic/architecture", "mvvm"): "Hướng dẫn kiến trúc Android có ViewModel và phân lớp; không quy giản nội dung thành khóa MVVM đầy đủ.",
    ("https://learn.unity.com/", "unity engine"): "Cổng học Unity chính thức có bài tạo scene và pathways; chọn course theo editor/version và xác minh khóa cụ thể trước khi lập kế hoạch.",
    ("https://trailhead.salesforce.com/", "quản lý tài khoản"): "Chỉ hỗ trợ thao tác/account workflows trên Salesforce; không đánh giá kỹ năng quản lý quan hệ khách hàng hay năng lực doanh số.",
    ("https://trailhead.salesforce.com/", "tư vấn giải pháp"): "Nội dung platform/Salesforce có thể bổ trợ kiến thức sản phẩm; tư vấn nhu cầu khách hàng phải được luyện qua tình huống và phản hồi.",
    ("https://openstax.org/books/introduction-business-2e/pages/10-4-pulling-it-together-resource-planning", "quản lý kho"): "Giáo trình nêu resource/inventory/procurement planning; không thay thực hành SKU, WMS/ERP, kiểm kê và quy trình kho tại doanh nghiệp.",
    ("https://openstax.org/books/introduction-business-2e/pages/10-5-production-and-operations-control", "sơ đồ chuỗi giá trị vsm"): "Mục này giới thiệu value-stream mapping trong kiểm soát sản xuất; cần bài tập VSM trên quy trình thực tế để sử dụng thành thạo.",
    ("https://academy.iccwbo.org/wp-content/uploads/2020/08/803E_Incoterms-2020-Wallchart-A4.pdf", "incoterms"): "Bản đồ ICC Incoterms 2020 hữu ích để đối chiếu phân bổ chi phí/rủi ro; ICC ghi rõ không dùng chart một mình, cần rulebook đầy đủ.",
    ("https://help.ecus.net.vn/", "phần mềm ecus/vnaccs"): "Hướng dẫn thao tác sản phẩm được cập nhật đến 2026; không thay đổi yêu cầu pháp lý, mã HS hoặc văn bản hải quan cần đối chiếu riêng.",
    ("https://www.freecodecamp.org/news/learn-programming-free-software-development-courses-for-beginners", "c++"): "Bài tổng hợp liên kết một khóa C++ cụ thể nhưng bản thân bài không phải course; kiểm tra nguồn video/khóa đích và phiên bản trước khi dùng.",
}


def main() -> None:
    resources = json.loads(RESOURCES_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    aliases = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    source_counts = Counter()
    decisions = []
    for skill, group in resources.items():
        for record in group["resources"]:
            if record.get("content_review_status") != "unreviewed":
                continue
            old_url = record["url"]
            new_url = REPLACEMENTS.get((old_url, skill), old_url)
            source_note = SOURCE_EVIDENCE.get(new_url) or SOURCE_EVIDENCE.get(old_url)
            if source_note is None:
                raise ValueError(f"No source evidence for {old_url} / {new_url}")
            if skill in BLOCKED.get(new_url, BLOCKED.get(old_url, [])):
                status = "blocked"
                reason = "Nguồn cần xác minh thêm trước khi được gợi ý: " + source_note
                verified = False
            elif skill in PARTIAL.get(new_url, PARTIAL.get(old_url, [])):
                status = "partial"
                reason = SPECIAL_NOTES.get((new_url, skill), SPECIAL_NOTES.get((old_url, skill)))
                if reason is None:
                    reason = f"Nguồn có nội dung liên quan đến {skill} nhưng chỉ hỗ trợ một phần; không xem là bằng chứng đã đạt năng lực. {source_note}"
                verified = True
            else:
                status = "unsuitable"
                reason = f"Đã mở và đối chiếu nguồn; mapping với {skill} không được nội dung trong nguồn chứng minh nên không đưa vào gợi ý. {source_note}"
                verified = False
            record.update({
                "url": new_url,
                "verified": verified,
                "last_checked": TODAY,
                "content_review_status": status,
                "content_reviewed_at": TODAY,
                "verification_origin": "browser_content_review_2026-10-25",
                "review_note": reason,
                "evidence_locator": source_note,
            })
            source_counts[status] += 1
            decisions.append({
                "id": record["id"],
                "skill": skill,
                "title": record["title"],
                "provider": record["provider"],
                "original_url": old_url,
                "url": new_url,
                "status": status,
                "verified": verified,
                "review_note": reason,
                "evidence_locator": source_note,
            })

    # PostgreSQL is a specific database platform, not an alias for SQL.
    if "postgresql" not in catalog:
        catalog.append("postgresql")
    aliases["postgre sql"] = "postgresql"
    aliases["postgres"] = "postgresql"
    if "postgresql" not in resources:
        resources["postgresql"] = {
            "skill_name": "postgresql",
            "category": "database",
            "resources": [{
                "id": "postgresql_official_001",
                "title": "PostgreSQL Tutorial",
                "type": "doc",
                "provider": "PostgreSQL Global Development Group",
                "url": "https://www.postgresql.org/docs/current/tutorial.html",
                "language": "en",
                "cost": "free",
                "level_from": 1,
                "level_to": 2,
                "duration_hours": None,
                "verified": True,
                "last_checked": TODAY,
                "content_review_status": "partial",
                "verification_origin": "browser_content_review_2026-10-25",
                "content_reviewed_at": TODAY,
                "review_note": "Tutorial chính thức bao gồm cài đặt, tạo database, truy vấn, join, aggregate, view, khóa ngoại và transaction; trang nói rõ đây không phải nội dung toàn diện, vì vậy dùng làm nhập môn và thực hành theo tài liệu Part II/III/IV khi cần.",
                "evidence_locator": "PostgreSQL 18 Tutorial, Part I, mục 1–3; trang liệt kê Getting Started, SQL Language, Advanced Features.",
            }],
        }

    RESOURCES_PATH.write_text(json.dumps(resources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ALIASES_PATH.write_text(json.dumps(aliases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    snapshot = audit_project(ROOT / "Data")
    report = {
        "report": "remaining-unreviewed-resource-mapping-review",
        "date": TODAY,
        "scope": "187 unreviewed skill-resource mappings across 80 URLs; source content checked in browser, mapping adjudicated per skill",
        "reviewed_mappings": len(decisions),
        "unique_original_urls": len({item["original_url"] for item in decisions}),
        "mapping_dispositions": dict(Counter(item["status"] for item in decisions)),
        "source_pages": len({item["original_url"] for item in decisions}),
        "url_replacements": [item for item in decisions if item["original_url"] != item["url"]],
        "decisions": decisions,
        "post_review_data_audit": snapshot,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "reviewed_mappings": len(decisions),
        "unique_original_urls": len({item["original_url"] for item in decisions}),
        "dispositions": dict(Counter(item["status"] for item in decisions)),
        "post_review_counts": snapshot["stats"],
        "errors": snapshot["errors"],
        "report": str(REPORT_PATH),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
