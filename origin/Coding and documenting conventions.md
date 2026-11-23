# Coding and documenting conventions (v2)

Chú thích: **(Human)** = người dùng làm/cập nhật. **(Agent)** = AI làm. Không ghi gì = áp dụng cho cả hai.

Ba nguyên tắc gốc:
1. **Truy vết được**: mọi con số trong báo cáo/markdown phải đến từ một cell chạy được.
2. **Không đổi ngoài yêu cầu**: chỉ sửa đúng phần được nhờ.
3. **Giả định phải nói ra**: điều chưa kiểm chứng phải được gắn nhãn, không viết như sự thật.

---

## 1. Folder `origin` (cấp project)
Dùng để tạo context khi mở chat mới hoặc để agent tự tìm.
1. (Human) Bối cảnh chung: project phân tích HMDA 2024, nguồn: https://ffiec.cfpb.gov/data-publication/one-year-national-loan-level-dataset/2024
2. Các file trong `origin` (agent tự đọc hoặc Human gửi):
   * File đề bài
   * (Human) File data dictionary
   * (Human) File proposal
   * (Human) File này (conventions)
   * (Human) `decisions.md` bản mới nhất (xem mục 6)

## 2. Cấu trúc folder và đặt tên
1. Tên file code = `Mã Task - tên phiên bản`, ví dụ `B04 - 29 Oct.ipynb`. File code là đầu mối để đặt tên mọi file khác.
2. (Human) File code nằm trong folder cùng tên:
```
B04 - 29 Oct/
├── B04 - 29 Oct.ipynb
├── input/        # chỉ input ban đầu (dataset nhỏ, dictionary...)
├── output/       # MỌI file do code sinh ra (parquet, csv, png, xlsx...)
└── documents/    # kế hoạch, nguyên tắc áp dụng cho file code
```
3. Dataset gốc (4.3 GB) nằm ngoài, tại `D:\H-NEU\004\44 - Big Data\Final project\2024_public_lar_one_year_csv.csv`. **Không ghi đường dẫn này rải rác**: chỉ khai báo một lần trong cell cấu hình (mục 3.1).
4. Version mới = file code mới. **Không ghi đè** bản cũ (cần quay lại được).
5. File sinh ra có tiền tố/hậu tố là mã task để biết nguồn gốc, ví dụ `B04_analytic_sample.parquet`.

## 3. Quy tắc cho notebook
1. **Cell cấu hình đầu notebook**: import, đường dẫn (dùng `Path`, đường dẫn tương đối nếu được), hằng số, random seed. Không hard-code đường dẫn hay ngày tải ở nơi khác.
2. **Mỗi code cell đi kèm 1 md cell** ngay trên nó, mô tả: *Input* là gì, *xử lý* như thế nào, *Output* là gì.
3. Thư viện/kỹ thuật lạ (os, pyarrow, seaweedfs, hash, window function...) hoặc hàm dài: md cell phải giải thích "cái này là gì và vì sao dùng". Mặc định coi người đọc chỉ biết pandas và scikit-learn cơ bản.
4. Code cell có comment đánh dấu từng bước (`# Step 1: ...`).
5. **md cell và code cell viết bằng tiếng Anh.** Chat với agent dùng tiếng Việt.
6. **Code cell ngắn**: khoảng ≤ 40 dòng. Ngoại lệ có lý do (danh sách 99 cột, bảng cấu hình). Hàm dùng lại thì đưa vào cell riêng, có docstring.
7. Output user-friendly: bảng đã đặt tên cột dễ đọc, chart có title, nhãn trục, đơn vị. Không in dump dài.
8. Output là file mới thì ghi vào `output/` và **in ra đường dẫn + kích thước + số dòng/cột** của file đó.
9. Notebook phải chạy được từ trên xuống dưới (Restart & Run All) mà không lỗi.
10. **(Agent) Cấm tự ý ghi đè/can thiệp file `.ipynb` đang làm việc:** Agent không được tự ý dùng công cụ ghi file lên notebook mà phải xuất code qua khung chat để Human tự paste, tránh làm mất dữ liệu chưa lưu trong bộ nhớ của IDE.

## 4. Quy tắc dữ liệu và số liệu
1. Raw layer đọc toàn bộ dạng string, giữ nguyên `""`, `NA`, `Exempt`, `1111`, `8888`, `9999`. Không impute, không đổi `NA` thành 0.
2. Chỉ nhóm F (filter) mới được bỏ dòng. Mỗi quy tắc cleaning **in số dòng/cột trước-sau** (log waterfall).
3. **Cấm hard-code số liệu vào md cell hoặc bảng** (ví dụ "~5.5M applications"). Số phải được tính bằng code và hiển thị từ output. Nếu buộc phải trích số, ghi "as of run <ngày>, cell <số>".
4. Diễn giải ý nghĩa mã đặc biệt/biến phải gắn nhãn **[Verified: nguồn]** hoặc **[Hypothesis]**. Chỉ [Verified] mới được đưa vào báo cáo như sự thật.
5. Mỗi phép tính quan trọng nên có một kiểm tra nhanh đi kèm (số dòng cộng lại đủ, tỷ lệ nằm trong 0-100%, không có nhóm bị mất do NULL...).
6. Mọi quy tắc cho Pandas phải có bản tương đương cho PySpark (và ngược lại), ghi trong `Documents/`.

## 5. Quy tắc giao việc của Agent (phần giúp bạn giữ kiểm soát)

**Bảo vệ code của Human (Quy tắc sống còn):**
0. **Tuyệt đối không tự ý ghi đè/sửa trực tiếp file notebook (`.ipynb`) đang mở:** Khi Human đang làm việc/soạn thảo trên notebook trong IDE, Agent **CẤM** tự ý dùng tool `write_file`/`edit_file` lên file notebook đó. Việc ghi đè từ bên ngoài sẽ làm mất sạch các cell Human vừa viết trong buffer của IDE mà không thể `Ctrl + Z` khôi phục được. Agent **chỉ được hiển thị code trong khung chat** (kèm hướng dẫn cell nào, sửa dòng nào) để Human tự dán, trừ khi Human có chỉ thị rõ ràng: *"Hãy ghi trực tiếp vào file notebook"* hoặc *"Tạo file notebook mới cho tôi"*.

**Trước khi code:**
1. Nhắc lại task bằng 1-2 câu và liệt kê **giả định** (ví dụ "coi `1111` là Exempt").
2. Nếu có lựa chọn ảnh hưởng đến kết quả (lọc dòng nào, ngưỡng nào, xử lý `NA` ra sao), **hỏi/đề xuất trước**, không tự quyết rồi giấu trong code.

**Khi giao kết quả:**
3. Chỉ sửa đúng phần được yêu cầu. Muốn sửa thêm thì đề xuất, chờ Human đồng ý.
4. Với mỗi lần sửa code có sẵn, ghi rõ `[ADD]` / `[CHANGE]` / `[REMOVE]` và lý do (có thể dưới dạng comment hoặc bảng tóm tắt).
5. Nói rõ **đã chạy thử hay chưa**, chạy trên dữ liệu nào (thật / mẫu / giả lập). Không viết "đã kiểm tra" khi chưa chạy.
6. Kết thúc bằng 3 mục ngắn: **Kết quả chính**, **Điều chưa chắc/rủi ro**, **Việc cần Human quyết**.
7. Khi thấy lỗi hoặc điểm bất thường trong output (ví dụ tỷ lệ phi lý), **báo ngay**, đừng im lặng làm tiếp.

## 6. Decision log (Human cập nhật, Agent đề xuất dòng mới)
File `origin/decisions.md`, mỗi quyết định một dòng:

| ID | Date | Decision | Reason | Impact (rows/metric) | Status |
|---|---|---|---|---|---|
| D01 | 2026-10-30 | Exclude commercial-purpose loans (F02) | Focus on consumer credit | −X rows (tính bằng code) | Agreed / Open / Revisit |

Những thứ **phải** vào log: quy tắc lọc, xử lý mã đặc biệt, thay đổi so với proposal, chọn nhóm tham chiếu (race), biến thể robustness.

## 7. Checklist nhanh khi Human nhận output (Human)
- [ ] Notebook chạy từ đầu đến cuối không lỗi?
- [ ] Mỗi code cell có md cell mô tả Input/Process/Output, bằng tiếng Anh?
- [ ] File mới nằm đúng `output/`, tên theo mã task?
- [ ] Số trong md khớp output của cell (không phải số gõ tay)?
- [ ] Số dòng trước/sau mỗi bước lọc có được in ra?
- [ ] Agent đã báo: đã đổi gì, chạy thử gì, giả định gì?
- [ ] Có quyết định mới nào cần ghi vào `decisions.md`?