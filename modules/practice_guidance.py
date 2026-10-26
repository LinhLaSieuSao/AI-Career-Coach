"""Experience-first development routes for soft skills and work traits."""

from collections.abc import Mapping

from .resource_policy import resource_review_status, skill_scope_caution
from .skill_extractor import normalize_skill


_SALES_SKILLS = {
    "bán hàng",
    "bán hàng b2b",
    "bán hàng bất động sản",
    "bán hàng kỹ thuật",
    "tìm kiếm khách hàng",
    "tư vấn bán hàng",
    "thuyết phục",
    "chăm sóc khách hàng",
    "đàm phán",
    "thương lượng",
    "xây dựng mối quan hệ",
}
_COMMUNICATION_SKILLS = {"giao tiếp", "lắng nghe", "giao tiếp khách hàng", "thuyết trình"}
_TEAMWORK_SKILLS = {"làm việc nhóm", "phối hợp nhóm", "cộng tác"}
_PROBLEM_SKILLS = {"giải quyết vấn đề", "xử lý tình huống", "xử lý sự cố"}
_LEADERSHIP_SKILLS = {"quản lý đội ngũ", "quản lý công nhân", "quản lý nhân sự"}
_EVENT_SKILLS = {"tổ chức sự kiện", "điều phối sự kiện"}
_TRANSVERSAL_SKILLS = {
    "giải quyết vấn đề", "tiếng anh chuyên ngành", "excel", "cẩn thận",
    "đọc bản vẽ kỹ thuật", "chăm sóc khách hàng",
}
_OBSERVATION_CHECKLISTS = {
    "giải quyết vấn đề": [
        "Tách dữ kiện đã kiểm chứng khỏi giả định và ghi điều còn thiếu.",
        "Nêu ít nhất hai lựa chọn, rủi ro và lý do chọn cách thử.",
        "Kiểm tra kết quả, tác dụng phụ và ghi phản hồi của người quan sát.",
    ],
    "cẩn thận": [
        "Xác định trường/chi tiết trọng yếu trước khi bàn giao.",
        "Đối chiếu với nguồn đầu vào độc lập hoặc checklist, không chỉ đọc lại bằng mắt.",
        "Ghi sai lệch, sửa có dấu vết và xin người phụ trách xác nhận khi vượt thẩm quyền.",
    ],
    "chăm sóc khách hàng": [
        "Hỏi và nhắc lại nhu cầu hoặc sự cố bằng lời trung tính.",
        "Nêu bước tiếp theo, thời điểm cập nhật và giới hạn điều mình có thể cam kết.",
        "Không ghi dữ liệu nhận dạng khách hàng vào portfolio; xin phản hồi sau khi xử lý.",
    ],
    "excel": [
        "Công thức, phạm vi dữ liệu và đơn vị được kiểm tra bằng bộ dữ liệu giả lập.",
        "Đối chiếu tổng số bằng phép tính hoặc cách lọc độc lập; kiểm tra dữ liệu thiếu/trùng.",
        "Lưu file, giả định, bước tái lập và một nhận xét của người rà soát.",
    ],
    "đọc bản vẽ kỹ thuật": [
        "Xác nhận mã bản vẽ, phiên bản, đơn vị, tỷ lệ và ghi chú trước khi đọc kích thước.",
        "Đánh dấu kích thước/dung sai chưa rõ, không tự suy từ hình minh họa.",
        "Nhờ kỹ sư/người hướng dẫn kiểm tra diễn giải trước khi gia công hoặc thi công.",
    ],
    "tiếng anh chuyên ngành": [
        "Chỉ ra câu hoặc đoạn nguồn chứa thuật ngữ, phiên bản và bối cảnh sử dụng.",
        "Viết lại ý chính bằng tiếng Việt rồi diễn đạt lại bằng tiếng Anh, tách phần chưa chắc nghĩa.",
        "Nhờ người am hiểu chuyên ngành rà thuật ngữ; không dùng bản dịch để tự ra quyết định chuyên môn.",
    ],
}
_ENGLISH_TRACKS = [
    {
        "name": "IT/phần mềm", "terms": "issue, endpoint, rollback, changelog, pull request",
        "exercise": "Đọc một đoạn tài liệu API hoặc Git; viết ticket lỗi 5 câu gồm tái hiện, kỳ vọng và kết quả thực tế.",
        "reference_url": "https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging",
    },
    {
        "name": "Kinh doanh/tài chính", "terms": "revenue, expense, cash flow, variance, disclosure",
        "exercise": "Đọc một đoạn bảng thuật ngữ IFRS và viết ghi chú song ngữ về một chênh lệch giả lập; không dùng làm kết luận kế toán/thuế.",
        "reference_url": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2024/issued/part-a/glossary.pdf?bypass=on",
    },
    {
        "name": "Logistics/chuỗi cung ứng", "terms": "shipment, bill of lading, carrier, delivery, risk transfer",
        "exercise": "Đọc phần giới thiệu Incoterms của ICC; viết email giả lập hỏi rõ địa điểm giao và chứng từ, không tự diễn giải nghĩa vụ hợp đồng.",
        "reference_url": "https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/",
    },
    {
        "name": "Kỹ thuật/bản vẽ", "terms": "dimension, tolerance, revision, datum, drawing note",
        "exercise": "Đọc phần giới thiệu GD&T, ghi chú song ngữ năm chi tiết cần hỏi lại trên bản vẽ giả lập; xin kỹ sư rà trước khi áp dụng.",
        "reference_url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=936463",
    },
    {
        "name": "Y tế/dược và thử nghiệm", "terms": "protocol, informed consent, adverse event, deviation, essential record",
        "exercise": "Đọc một đoạn tài liệu ICH GCP, tóm tắt thuật ngữ và câu hỏi cần xác minh; không dùng để hướng dẫn điều trị hay vận hành thử nghiệm.",
        "reference_url": "https://admin.ich.org/sites/default/files/elearning-contents/27d6f78b-c8aa-4d50-ab13-9ce13a220b19/ICH%20E6%28R3%29%20Module%204.1%20Publication/story.html",
    },
]


def _route(skill: str, category: str) -> dict:
    normalized = normalize_skill(skill)
    if normalized == "tiếng anh chuyên ngành":
        return {
            "skill": skill, "category": "practice", "title": "Đọc và viết tiếng Anh theo nhóm nghề",
            "framing": "Năm bộ từ khóa là bài tập do dự án biên soạn từ trang nguồn, chưa được chuyên gia ngôn ngữ/ngành xác nhận. Chọn một nhóm phù hợp, không xem đây là học liệu Level 2–3 đã review.",
            "steps": [
                "Chọn một trong năm nhóm nghề và mở phần nguồn được dẫn; đọc một đoạn ngắn thay vì học thuộc danh sách từ.",
                "Ghi bối cảnh của năm thuật ngữ, viết lại ý chính và làm bài tập của nhóm đã chọn.",
                "Xin người am hiểu ngành sửa cách dùng thuật ngữ, lưu bản trước/sau và ghi điểm còn chưa chắc chắn.",
            ],
            "evidence": "đoạn nguồn, ghi chú từ trong ngữ cảnh, sản phẩm viết song ngữ và phản hồi đã ẩn danh.",
            "tracks": _ENGLISH_TRACKS,
        }
    if normalized == "excel":
        return {
            "skill": skill, "category": "practice", "title": "Kiểm tra một bảng tính có dữ liệu giả lập",
            "framing": "Bài thực hành tự tạo không chứng nhận Excel Level 3; cần người dùng và người rà soát kiểm tra file, công thức và diễn giải.",
            "steps": [
                "Tạo bảng 30–50 dòng dữ liệu bán hàng giả lập có bản ghi trùng, giá trị trống và một giá trị ngoại lệ.",
                "Làm sạch có ghi quy tắc, tính tổng theo nhóm và tạo biểu đồ; không xóa dữ liệu bất thường khi chưa giải thích.",
                "Đối chiếu một tổng bằng cách tính độc lập, kiểm tra khi thêm một dòng mới và xin người khác rà công thức.",
            ],
            "evidence": "file bảng tính không chứa dữ liệu thật, README giải thích công thức, phép đối chiếu và nhận xét của người rà soát.",
        }
    if normalized == "đọc bản vẽ kỹ thuật":
        return {
            "skill": skill, "category": "practice", "title": "Diễn giải bản vẽ mẫu có người giám sát",
            "framing": "Chỉ dùng bản vẽ mẫu được phép chia sẻ. Bài tập không thay cho chứng nhận thiết kế, kiểm tra bản vẽ thi công hoặc hướng dẫn an toàn tại nơi làm việc.",
            "steps": [
                "Chọn bản vẽ mẫu, ghi mã phiên bản, đơn vị, tỷ lệ, ghi chú và các hình chiếu trước khi suy kích thước.",
                "Đánh dấu ba kích thước/dung sai quan trọng và những điểm chưa rõ; không tự điền thông số thiếu.",
                "Nhờ kỹ sư hoặc người hướng dẫn rà diễn giải, ghi lại một sai khác và cách sửa.",
            ],
            "evidence": "bản ghi chú trên bản vẽ mẫu, câu hỏi làm rõ và phản hồi có tên vai trò người rà soát.",
        }
    if normalized in _COMMUNICATION_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện giao tiếp bằng mô phỏng và phản hồi",
            "framing": "Tài liệu giúp chuẩn bị; năng lực giao tiếp cần được luyện trong tình huống và điều chỉnh theo phản hồi quan sát được.",
            "steps": [
                "Chọn một tình huống gần công việc như nhận yêu cầu, báo tiến độ hoặc giải thích một quyết định.",
                "Role-play theo cặp: một người trình bày, người kia hỏi làm rõ; người nghe tóm tắt lại điều đã hiểu trước khi trả lời.",
                "Nhờ người quan sát ghi ví dụ cụ thể về sự rõ ràng, lắng nghe và xác nhận thông tin; tránh nhận xét chung về tính cách.",
                "Thử lại sau khi nhận phản hồi, rồi lưu điểm đã sửa và câu hỏi còn cần làm rõ.",
            ],
            "evidence": "kịch bản role-play đã ẩn danh, checklist của người quan sát, phản hồi mentor/đồng nghiệp và bản thực hành đã chỉnh sửa.",
        }
    if normalized in _TEAMWORK_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện phối hợp qua nhiệm vụ nhóm có giám sát",
            "framing": "Đọc tài liệu chỉ là bước chuẩn bị; phối hợp cần được thực hiện trong một nhiệm vụ có vai trò, phụ thuộc và phản hồi thật.",
            "steps": [
                "Chọn nhiệm vụ nhỏ có người hướng dẫn, mục tiêu và thời hạn rõ; thống nhất vai trò và cách báo trở ngại.",
                "Thực hiện một lần bàn giao công việc có tiêu chí hoàn thành và xác nhận người nhận đã hiểu.",
                "Nhờ đồng nghiệp/mentor quan sát cách chia sẻ thông tin, xử lý bất đồng và xin hỗ trợ; ghi lại ví dụ cụ thể.",
                "Debrief cùng nhóm, chọn một cách phối hợp cần thay đổi và thử lại ở nhiệm vụ kế tiếp.",
            ],
            "evidence": "mục tiêu nhiệm vụ đã ẩn danh, checklist bàn giao, phản hồi thành viên/mentor và một thay đổi đã thử.",
        }
    if normalized in _SALES_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Thực hành tư vấn và phản hồi khách hàng",
            "framing": "Ưu tiên luyện với khách hàng giả lập, quan sát người có kinh nghiệm và nhận phản hồi cụ thể. Khóa học sản phẩm có thể hỗ trợ, nhưng không thay cho luyện tình huống.",
            "steps": [
                "Chọn một sản phẩm/dịch vụ và chân dung khách hàng giả lập; không đưa thông tin nhận dạng khách hàng thật vào ghi chép.",
                "Luyện một cuộc trao đổi ngắn: hỏi nhu cầu, ngân sách và ràng buộc; tóm tắt lại để xác nhận trước khi đề xuất.",
                "Nhờ đồng nghiệp đóng vai khách hàng nêu 2–3 phản đối; trả lời bằng câu hỏi làm rõ và thông tin đã kiểm chứng, không gây áp lực hoặc hứa quá mức.",
                "Xin người quan sát góp ý bằng ví dụ cụ thể, sửa một điểm trong kịch bản rồi diễn tập lại; nếu đang đi làm, xin shadow một ca và phản tư cùng quản lý.",
            ],
            "evidence": "kịch bản đã ẩn danh, ghi chú phản hồi của người quan sát và một phiên bản đã sửa; theo dõi chất lượng hỏi/lắng nghe/xác nhận bước tiếp theo, không chỉ đếm tỷ lệ chốt.",
        }
    if normalized in _PROBLEM_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện xử lý tình huống bằng ca thực tế",
            "framing": "Năng lực này tiến bộ qua nhiều lần xử lý, xem lại hệ quả và nhận góp ý; một khóa học không thay thế được trải nghiệm theo bối cảnh.",
            "steps": [
                "Chọn một vấn đề thật đã ẩn thông tin nhạy cảm hoặc một tình huống mô phỏng gần với công việc.",
                "Viết rõ mục tiêu, dữ kiện đã biết, điều còn chưa rõ và người cần tham vấn trước khi chọn cách xử lý.",
                "Thử một hành động có thể đảo ngược khi phù hợp, theo dõi kết quả và ghi lại tác dụng phụ hoặc rủi ro.",
                "Nhờ đồng nghiệp/mentor phản biện giả định, sau đó ghi một điều sẽ làm khác ở lần sau.",
            ],
            "evidence": "bản tóm tắt ca đã ẩn danh gồm dữ kiện, lựa chọn, kết quả quan sát được và góp ý nhận được.",
        }
    if normalized in _LEADERSHIP_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Luyện điều phối nhóm qua một nhiệm vụ nhỏ",
            "framing": "Kỹ năng quản lý cần được luyện với con người và bối cảnh thật. Dùng phạm vi có giám sát; không suy ra năng lực lãnh đạo từ một bài học hay một chỉ số duy nhất.",
            "steps": [
                "Nhận điều phối một nhiệm vụ nhỏ có mục tiêu, thời hạn và quyền quyết định rõ ràng.",
                "Cùng nhóm thống nhất vai trò, phụ thuộc, cách báo trở ngại và tiêu chí hoàn thành trước khi bắt đầu.",
                "Trong quá trình làm, hỏi từng người về trở ngại và hỗ trợ cần thiết; ghi nhận quyết định thay vì chỉ nhắc tiến độ.",
                "Sau khi kết thúc, xin phản hồi riêng từ thành viên/mentor, xác định một hành vi cần điều chỉnh và thử lại ở nhiệm vụ kế tiếp.",
            ],
            "evidence": "mục tiêu nhiệm vụ, quyết định điều phối đã ẩn danh, phản hồi của thành viên và một thay đổi bạn đã thử.",
        }
    if normalized in _EVENT_SKILLS:
        return {
            "skill": skill,
            "category": category,
            "title": "Tập điều phối sự kiện có người hướng dẫn",
            "framing": "Tổ chức sự kiện được củng cố khi thực hiện từng phần việc, phối hợp nhà cung cấp và tổng kết sự cố; lý thuyết chỉ hỗ trợ bước chuẩn bị.",
            "steps": [
                "Shadow một sự kiện nhỏ hoặc nhận một hạng mục có phạm vi rõ như đăng ký, hậu cần hay lịch trình.",
                "Dùng checklist, người phụ trách, thời điểm bàn giao và phương án dự phòng; xác nhận thay đổi với người có thẩm quyền.",
                "Trong lúc diễn ra, ghi nhận tình huống và quyết định xử lý; bảo vệ dữ liệu người tham dự.",
                "Debrief với người hướng dẫn về điều diễn ra đúng/sai và sửa checklist trước lần tiếp theo.",
            ],
            "evidence": "checklist đã ẩn danh, một ví dụ xử lý thay đổi/sự cố và cập nhật rút ra sau debrief.",
        }
    if normalized == "viết nội dung":
        return {
            "skill": skill,
            "category": category,
            "title": "Xây portfolio nội dung và nhận biên tập",
            "framing": "Khóa học kỹ thuật viết chỉ phù hợp với một số loại nội dung; năng lực viết nội dung nói chung cần sản phẩm thật, phản hồi của biên tập viên và chỉnh sửa nhiều vòng.",
            "steps": [
                "Chọn một nhóm độc giả và mục tiêu rõ cho một bài ngắn, trang sản phẩm hoặc email.",
                "Viết bản đầu dựa trên thông tin có nguồn; đánh dấu riêng dữ kiện cần xác nhận.",
                "Nhờ biên tập viên/đồng nghiệp thuộc nhóm độc giả đọc thử và chỉ ra chỗ khó hiểu, thiếu bằng chứng hoặc không đúng giọng.",
                "Sửa bài, lưu trước/sau cùng ghi chú quyết định biên tập; tạo thêm mẫu khác cho một kênh hoặc đối tượng khác.",
            ],
            "evidence": "2–3 mẫu nội dung, góp ý đã nhận và bản sửa có ghi rõ nguồn cho các dữ kiện.",
        }
    if category == "trait":
        return {
            "skill": skill,
            "category": category,
            "title": "Biến phẩm chất thành hành vi có thể quan sát",
            "framing": "Không gắn nhãn hay chấm tính cách. Chọn hành vi liên quan đến công việc, luyện trong nhiệm vụ nhỏ và kiểm tra bằng bằng chứng cùng phản hồi.",
            "steps": [
                "Viết một hành vi cụ thể thể hiện kỹ năng này trong vị trí đang nhắm tới.",
                "Chọn nhiệm vụ sắp tới để thử hành vi đó; ghi lại bối cảnh và quyết định của bạn.",
                "Nhờ người làm cùng phản hồi điều họ quan sát được, không yêu cầu nhận xét chung về tính cách.",
                "Lặp lại trong một tình huống khác và so sánh điều kiện nào giúp hành vi hiệu quả hơn.",
            ],
            "evidence": "ghi chú ngắn về bối cảnh, hành vi, kết quả và nhận xét quan sát được; không xem đây là điểm năng lực.",
        }
    return {
        "skill": skill,
        "category": category,
        "title": "Luyện qua nhiệm vụ và phản hồi",
        "framing": "Ưu tiên cơ hội thực hành trong công việc hoặc mô phỏng có người quan sát. Tài liệu có thể giúp biết cách làm, còn năng lực cần được củng cố bằng áp dụng và phản hồi.",
        "steps": [
            "Chọn một tình huống sắp tới cần dùng kỹ năng này và xác định một hành vi cụ thể muốn thử.",
            "Thực hành trong nhiệm vụ thật có giám sát hoặc diễn tập với đồng nghiệp; xin phép trước nếu ghi âm/ghi hình.",
            "Xin phản hồi gắn với hành động cụ thể: điều gì hiệu quả, lúc nào, và có thể thử gì khác.",
            "Thử lại ở tình huống tiếp theo và ghi nhận kết quả quan sát được để tự điều chỉnh.",
        ],
            "evidence": "một ví dụ công việc đã ẩn danh, ghi chú của người quan sát, phản hồi mentor/đồng nghiệp và điều chỉnh đã thử lần tiếp theo.",
    }


def get_practice_routes(skills, resources: Mapping) -> list[dict]:
    """Build non-course practice plans for soft skills and observable traits."""
    categories = {}
    for name, group in resources.items():
        if isinstance(name, str) and isinstance(group, Mapping):
            categories[normalize_skill(name)] = group.get("category")
    routes = []
    for skill in skills:
        normalized = normalize_skill(skill)
        category = categories.get(normalized)
        if normalized in _SALES_SKILLS:
            route = _route(skill, "soft_skill")
        elif normalized in _COMMUNICATION_SKILLS | _TEAMWORK_SKILLS | _LEADERSHIP_SKILLS | _EVENT_SKILLS | {"viết nội dung"}:
            route = _route(skill, "soft_skill")
        elif normalized in _TRANSVERSAL_SKILLS:
            route = _route(skill, category or "practice")
        elif category in {"soft_skill", "trait"}:
            route = _route(skill, category)
        else:
            continue
        if normalized in _OBSERVATION_CHECKLISTS:
            route["observation_checklist"] = _OBSERVATION_CHECKLISTS[normalized]
        routes.append(route)
    return routes


def get_partial_resource_assignment(
    skill: str,
    resource: Mapping,
    resources: Mapping,
    *,
    role_context: str | None = None,
) -> dict | None:
    """Turn a partial learning resource into a bounded, reviewable work sample."""
    if not isinstance(resource, Mapping) or resource_review_status(resource) != "partial":
        return None
    normalized = normalize_skill(skill)
    context = f" cho vị trí {role_context}" if role_context else " trong bối cảnh nghề bạn đang nhắm tới"
    scope = resource.get("review_note", "")

    routes = get_practice_routes([skill], resources)
    if routes:
        route = routes[0]
        return {
            "skill": skill,
            "title": "Bài thực hành có phản hồi sau phần tài liệu",
            "scope": scope,
            "steps": [
                f"Chọn một ý trong tài liệu và dùng nó để chuẩn bị một tình huống mô phỏng{context}.",
                *route["steps"],
            ],
            "evidence": route["evidence"],
            "caution": skill_scope_caution(skill),
        }

    if normalized == "sql":
        artifact = "một file truy vấn SQL, dữ liệu giả lập nhỏ, kết quả mong đợi và README nêu giả định/giới hạn."
        steps = [
            f"Tạo dữ liệu giả lập cho một câu hỏi nghiệp vụ{context}; không dùng dữ liệu cá nhân hoặc dữ liệu công ty chưa được phép.",
            "Viết truy vấn chỉ cho chủ đề mà ghi chú phạm vi nguồn xác nhận; lưu truy vấn và kết quả mẫu.",
            "Kiểm tra trường hợp thiếu dữ liệu, trùng bản ghi và đối chiếu một kết quả bằng cách độc lập.",
            "Nhờ đồng nghiệp/mentor review tính đúng, cách đặt tên và giới hạn của truy vấn; ghi lại phần đã sửa.",
        ]
    elif normalized in {"python", "pandas", "phân tích dữ liệu", "thống kê", "power bi", "tableau", "trực quan hóa dữ liệu"}:
        artifact = "notebook hoặc dashboard chạy lại được, bộ dữ liệu tổng hợp, mô tả trường dữ liệu, 2–3 kết quả và giới hạn phân tích."
        steps = [
            f"Chọn một câu hỏi nghiệp vụ cụ thể{context} và tạo hoặc tìm dữ liệu tổng hợp phù hợp.",
            "Thực hiện phần kỹ thuật được nguồn partial hỗ trợ; ghi rõ thao tác và phiên bản công cụ.",
            "Kiểm tra đầu vào, cách tính và một kết quả mẫu; không diễn giải tương quan thành quan hệ nhân quả.",
            "Xin mentor/đồng nghiệp phản biện tính hữu ích của đầu ra; lưu nhận xét và bản chỉnh sửa.",
        ]
    elif normalized == "kiến trúc hệ thống":
        artifact = "sơ đồ ranh giới hệ thống và một ADR ngắn gồm bối cảnh, lựa chọn, trade-off, rủi ro vận hành và câu hỏi còn mở."
        steps = [
            f"Chọn một case mô phỏng gần domain của vị trí{context}; ghi rõ các giả định và thành phần nằm ngoài phạm vi.",
            "Chỉ áp dụng phần nguồn hỗ trợ (kiến trúc phần mềm hoặc nền tảng cụ thể); không suy rộng thành kiến trúc toàn hệ thống.",
            "Nêu ít nhất hai lựa chọn, yêu cầu chất lượng liên quan và trade-off về bảo mật, độ tin cậy, chi phí hoặc vận hành.",
            "Nhờ kiến trúc sư/mentor có kinh nghiệm trong domain phản biện sơ đồ và ADR; cập nhật ranh giới và quyết định.",
        ]
    else:
        artifact = "một sản phẩm nhỏ có thể xem lại (bản phân tích, checklist, demo hoặc tài liệu quyết định) cùng nguồn và giả định."
        steps = [
            f"Chọn một nhiệm vụ gần vị trí mục tiêu{context}, xác định đầu ra và tiêu chí hoàn thành trước khi làm.",
            "Dùng tài liệu partial cho đúng phần được ghi trong phạm vi review; nêu riêng các phần tài liệu không bao quát.",
            "Tạo đầu ra có thể kiểm tra, dùng dữ liệu tổng hợp/đã được phép và ghi lại các giả định.",
            "Nhờ người có kinh nghiệm hoặc đồng nghiệp review bằng tiêu chí cụ thể; chỉnh sửa và lưu minh chứng trước/sau.",
        ]
    return {
        "skill": skill,
        "title": "Bài tập/portfolio theo bối cảnh",
        "scope": scope,
        "steps": steps,
        "evidence": artifact,
        "caution": skill_scope_caution(skill),
    }
