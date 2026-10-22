from modules.cv_parser import extract_text

def test_real_cv():
    # Hãy đổi "CV_NguyenVanA.pdf" thành tên chính xác của tệp CV bạn vừa tải lên
    file_cv = "CV_Data_Engineer.pdf" 

    print(f"=== ĐANG ĐỌC TỆP: {file_cv} ===")
    try:
        noi_dung = extract_text(file_cv)
        print(f"✅ ĐỌC THÀNH CÔNG! Số lượng ký tự tìm thấy: {len(noi_dung)}")
        print("Trích xuất 300 ký tự đầu tiên để kiểm tra:\n")
        print(noi_dung[:300])
    except Exception as e:
        print(f"❌ Lỗi khi đọc tệp: {e}")

if __name__ == "__main__":
    test_real_cv()