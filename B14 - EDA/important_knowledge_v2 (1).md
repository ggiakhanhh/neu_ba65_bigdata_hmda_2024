# Cẩm nang Toán Thống kê & Data Analytics Chuyên sâu trong Task B14 (EDA HMDA 2024)

**Dự án:** Decomposing Racial Gaps in Mortgage Denial Rates: A Large-Scale Analysis of the 2024 U.S. HMDA Market  
**Đối tượng đọc:** Thành viên nhóm (đã qua 1 khóa Xác suất Thống kê cơ bản: Biến ngẫu nhiên, Phân phối Chuẩn, Bernoulli/Binomial, Định lý Giới hạn Trung tâm - CLT, Khoảng tin cậy & Kiểm định giả thuyết cơ bản).  
**Mục đích:** Giải thích mạch lạc **"Tại sao thống kê cơ bản bị gãy?"** $\rightarrow$ **"Bản chất toán học của phương pháp nâng cao là gì?"** $\rightarrow$ **"Nó được code và đọc kết quả như thế nào trong `B14 - EDA.ipynb`?"**  
**Truy vết số liệu (Convention 4.3):** Mọi con số thực tế dưới đây được trích xuất từ kết quả chạy `B14 - 11 Nov v2.ipynb` (file notebook trong project không lưu output, nên cần chạy lại để xác nhận từng số; các vị trí được trích bằng **tên Step**, không dùng số cell vì số cell thay đổi theo phiên bản) (*as of run 2026-11-10 và 2026-11-11*).

---

## Mục lục Hệ thống Phương pháp theo Luồng Phân tích B14

1. **Nền tảng Ước lượng & Suy diễn trên Big Data** ($N = 8.14\text{ triệu}$)
   - **1.1.** Cái bẫy $p$-value (The Big Data $p$-value Trap) & Quy tắc Làm mờ Ô nhỏ (`low_n`, Decision D-M)
   - **1.2.** Khoảng tin cậy **Wilson Score CI** cho tỷ lệ từ chối (Section 0.2, A2, B3, B5, C1)
   - **1.3.** Các thước đo Khoảng cách Bất bình đẳng: **pp Gap, Risk Ratio (RR), Odds Ratio (OR)** & **Woolf CI** (Step C0, C1a)
   - **1.4.** Khoảng tin cậy **Newcombe Hybrid Score CI** cho hiệu hai tỷ lệ $\hat{p}_1 - \hat{p}_0$ (Step C4, F0, F1, F9, G5)
   - **1.5.** **Lender-Cluster Bootstrap** trên bảng gộp trước (Pre-aggregated Multinomial Matrix Bootstrap) (Step C1b, Decision D-Q)
2. **Phân rã Khoảng cách & Kiểm tra Nghịch lý Simpson (RQ1 & RQ2 — Phần C & D)**
   - **2.1.** Nghịch lý Simpson (Simpson's Paradox) & Kiểm định Phân tầng theo Sản phẩm (Step C4, D2b — Decision D-AE)
   - **2.2.** Phân rã **Kitagawa (1955)** (Direct Standardization: Composition Effect vs. Rate Effect) & Bẫy Gộp nhóm `low_reliability` (Step C5, D4, F8, G2 — Decisions D-P, D-U, D-X)
   - **2.3.** Phân rã Lý do Từ chối theo **Số ca từ chối trên 100 hồ sơ** (Additive Primary Denial Reason Accounting) (Step D7c — Decision D-AD)
3. **Đo lường Tương quan, Đa cộng tuyến & Mất cân bằng Phân phối (Phần E)**
   - **3.1.** Tương quan hạng **Spearman's** $\rho$ vs. Pearson's $r$ trên dữ liệu tài chính lệch phải (Step E1)
   - **3.2.** Đo lường mối liên hệ Biến phân loại – Kết cục: **Bias-Corrected Cramér's** $V$ (**Bergsma, 2013**) & **Normalised Mutual Information (NMI)** (Step E2)
   - **3.3.** Đa cộng tuyến cấu trúc & **Nhân tử Phóng đại Phương sai (VIF)** qua Nghịch đảo Ma trận Tương quan (Step E3 — Decision D-AF)
   - **3.4.** Khoảng cách Trung bình Chuẩn hóa (**Standardised Mean Difference — SMD** / Love Plot) (Step E4)
   - **3.5.** **Univariate AUC** thông qua Thống kê Hạng Mann-Whitney $U$ (Step E5)
4. **Kinh tế lượng Không gian & Cấu trúc Thị trường Cho vay (RQ3 — Phần F)**
   - **4.1.** Đo lường Mức độ Tập trung Thị trường: **Chỉ số HHI (Herfindahl-Hirschman Index)**, **Đường cong Lorenz** & **Hệ số Gini** (Step F6)
   - **4.2.** **Biểu đồ Phễu (Funnel Plot)** & **Hệ số Phân tán Quá mức (Overdispersion** $\phi$) tách Nhiễu mẫu khỏi Khác biệt Thực (Step F7)

---

## Phần 1. Nền tảng Ước lượng & Suy diễn trên Big Data ($N = 8.14\text{ triệu}$)

### 1.1. Cái bẫy $p$-value (P-Value Trap) & Quy tắc Ngưỡng Cỡ mẫu Tối thiểu (Decision D-M, D-Q)

#### A. Từ kiến thức Thống kê cơ bản
Trong khóa thống kê cơ bản, khi kiểm định giả thuyết $H_0: p_B - p_W = 0$, ta tính thống kê $Z$:
$$Z = \frac{\hat{p}_B - \hat{p}_W}{\text{SE}}, \quad \text{với } \text{SE} \propto \frac{1}{\sqrt{n}}$$
Nếu $|Z| > 1.96$ (tức $p\text{-value} < 0.05$), ta bác bỏ $H_0$ và kết luận "có sự khác biệt có ý nghĩa thống kê".

#### B. Tại sao cách làm cơ bản bị gãy trên HMDA 2024?
1. **Khi cỡ mẫu cực lớn** ($N = 8,136,664$ ở mẫu $S0$):
   Mẫu số $\sqrt{N} = \sqrt{8,136,664} \approx 2,852.5$. Với **một** tỷ lệ trên toàn $S0$, $\text{SE} \approx 0.00015$ ($0.015\text{ pp}$). Nhưng khi so sánh **hai nhóm**, sai số chuẩn của hiệu là $\text{SE}_\Delta = \sqrt{\frac{\hat{p}_1(1-\hat{p}_1)}{n_1} + \frac{\hat{p}_0(1-\hat{p}_0)}{n_0}}$ và bị chi phối bởi nhóm nhỏ hơn. Với Black vs. White ($n_1 = 733{,}103$, $n_0 = 5{,}360{,}624$): $\text{SE}_\Delta \approx 0.00059$ ($\approx 0.059\text{ pp}$). *[CHANGE v2: bản v1 dùng SE của một mẫu nên ví dụ Z = 3.33 không đúng cho hai nhóm]*
   Khi đó mọi chênh lệch lớn hơn $1.96 \times 0.059 \approx 0.12\text{ pp}$ đều có $p < 0.05$. Ví dụ một chênh lệch chỉ $0.15\text{ pp}$ — vô nghĩa về mặt kinh tế tài chính — cho:
   $$Z \approx \frac{0.0015}{0.00059} \approx 2.5 \implies p\text{-value} < 0.05$$
   Hệ quả: giữa các nhóm lớn, $p$-value gần như luôn nhỏ, nên nó không còn phân biệt được chênh lệch $0.2\text{ pp}$ với $15\text{ pp}$; thông tin nằm ở **độ lớn** chứ không ở $p$-value. (Ngược lại, ở các ô nhỏ $p$-value lại thiếu lực — xem điểm 2.) Do đó, **Decision D-Q** quy định: *Không in bảng $p$-value; thay vào đó báo cáo Độ lớn Hiệu ứng (Effect Size: pp gap, RR, OR) kèm Khoảng tin cậy (CI)*.

2. **Ngược lại, khi chia nhỏ dữ liệu thành các "Ô" (Cells) rất nhỏ (Small-Sample Noise):**
   Khi ta cắt dữ liệu theo $(\text{Bang} \times \text{Chủng tộc})$ hoặc $(\text{Ngân hàng} \times \text{Chủng tộc})$, có những ô chỉ có $n = 20$ hồ sơ và $d = 5$ hồ sơ bị từ chối ($\hat{p} = 25\%$). Khoảng tin cậy 95% của ô này rộng từ $11.2\%$ đến $46.9\%$ (sai số $\pm 17.8\text{ pp}$). Nếu ta xếp hạng các bang hoặc các ngân hàng mà giữ nguyên các ô này, top đầu và top cuối sẽ toàn là các ô mẫu nhỏ do may rủi ngẫu nhiên!

#### C. Giải pháp Toán học trong B14 (Decision D-M)
Ta thiết lập quy tắc chặn kép `low_n` cho mọi ô phân tích:
$$n_{\text{apps}} \ge N_{\text{MIN\_APPS}} = 1,000 \quad \text{VÀ} \quad d_{\text{denied}} \ge N_{\text{MIN\_DENIED}} = 100$$
- **Tại sao là** $1,000$? Với tỷ lệ từ chối chung của thị trường $\hat{p} \approx 0.2462$ (*as of run 2026-11-10, cell A2*) và $n = 1,000$:
  $$\text{SE}(\hat{p}) = \sqrt{\frac{0.2462 \times (1 - 0.2462)}{1,000}} \approx 0.0136 \quad (1.36\text{ pp})$$
  Biên độ sai số 95% (Margin of Error) là $\text{MoE} = 1.96 \times 1.36\text{ pp} \approx \pm 2.67\text{ pp}$. Đây là biên độ tại $\hat{p} \approx 24.6\%$. Trường hợp xấu nhất ($\hat{p} = 50\%$) là $1.96 \times \sqrt{0.25/1{,}000} \approx \pm 3.1\text{ pp}$. Vậy mọi ô vượt D-M có biên độ sai số tối đa khoảng $\pm 3\text{ pp}$ (điều kiện $d \ge 100$ còn chặn các ô có tỷ lệ từ chối rất thấp). *[CHANGE v2: v1 viết "tối đa ±2.6 pp", chỉ đúng tại p = 24.6%]*

---

### 1.2. Khoảng tin cậy Wilson Score CI (Section 0.2, A2, B3, B5, C1)

*(Phần này nối tiếp trực tiếp từ bản nháp PDF của bạn và chuẩn hóa vào code B14).*

#### A. Từ Wald CI cơ bản đến Wilson Score CI
Trong thống kê cơ bản, mỗi hồ sơ vay là một phép thử Bernoulli với xác suất bị từ chối là $p$. Với $n$ hồ sơ và $d$ hồ sơ bị từ chối, tỷ lệ mẫu là $\hat{p} = \frac{d}{n}$.
Để tìm khoảng tin cậy $95\%$ ($z = 1.95996 \approx 1.96$), phương pháp **Wald CI** lấy $\hat{p}$ thế thẳng vào công thức sai số chuẩn của tổng thể:
$$\text{CI}_{\text{Wald}} = \hat{p} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$
**Điểm yếu chí mạng của Wald trong HMDA:**
- Trong Step B5, nhóm `preapproval == '1'` có $n = 191,373$ nhưng số ca từ chối trong $S0$ là $d = 0 \implies \hat{p} = 0$. Nếu dùng Wald CI, phần căn bậc hai bằng $0$, dẫn tới khoảng tin cậy là $[0, 0]$ (sai bản chất vì mẫu hữu hạn không thể chắc chắn tuyệt đối 100%).
- Ở các ô có $n$ nhỏ hoặc $\hat{p}$ sát $0$ hay $1$, Wald CI có thể cho cận dưới **âm** ($< 0\%$) hoặc cận trên **vượt quá** $100\%$.

#### B. Cách Wilson (1927) giải bài toán (Đảo ngược Kiểm định Score Test)
Thay vì thay $\hat{p}$ vào mẫu số, Wilson giữ nguyên tham số **chưa biết** $p$ ở mẫu số của thống kê chuẩn hóa $Z$:
$$Z = \frac{\hat{p} - p}{\sqrt{\frac{p(1-p)}{n}}}$$
Để tìm các giá trị $p$ hợp lý ở mức tin cậy $95\%$, ta đặt điều kiện $|Z| \le z$, rồi bình phương hai vế:
$$(\hat{p} - p)^2 \le z^2 \frac{p(1-p)}{n}$$
Khai triển biểu thức trên theo biến số $p$, ta thu được một **phương trình bậc hai theo** $p$:
$$\left(1 + \frac{z^2}{n}\right) p^2 - 2\left(\hat{p} + \frac{z^2}{2n}\right) p + \hat{p}^2 \le 0$$
Giải nghiệm phương trình bậc hai $Ap^2 + Bp + C = 0$ bằng công thức $\frac{-B \pm \sqrt{B^2 - 4AC}}{2A}$, ta rút ra chính xác công thức **Wilson Score CI** được code trong hàm `wilson_ci(denied, total)` tại **Section 0.2**:
$$\text{CI}_{\text{Wilson}} = \frac{\underbrace{\hat{p} + \frac{z^2}{2n}}_{\text{Tâm mới (kéo nhẹ về 0.5)}} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{\underbrace{1 + \frac{z^2}{n}}_{\text{Mẫu số co khoảng lại}}}$$

#### C. Trực giác & Ứng dụng trong B14
1. **Không đối xứng và không bao giờ lố biên** $[0, 1]$: Tâm của khoảng tin cậy không phải là $\hat{p}$ mà là $\frac{\hat{p} + \frac{z^2}{2n}}{1 + \frac{z^2}{n}}$ — tức là trung bình có trọng số giữa $\hat{p}$ và $0.5$. Khi $\hat{p} = 0$ (như `preapproval = 1` ở B5), cận dưới bằng $0\%$ nhưng cận trên vẫn dương một chút, phản ánh đúng sự bất định của cỡ mẫu.
2. **Khi** $n$ **cực lớn (như toàn bộ mẫu** $S0$, $n = 8,136,664$, $d = 2,003,276$): Đại lượng $\frac{z^2}{n} = \frac{1.96^2}{8.14 \times 10^6} \approx 4.7 \times 10^{-7} \approx 0$. Lúc này Wilson CI hội tụ hoàn hảo về khoảng đối xứng $[24.59\%, 24.65\%]$ quanh $\hat{p} = 24.62\%$ (*as of run 2026-11-10, cell A2*).

---

### 1.3. Các thước đo Khoảng cách Bất bình đẳng: pp Gap, Risk Ratio (RR), Odds Ratio (OR) & Woolf CI (Step C0, C1a)

Khi so sánh tỷ lệ từ chối của một nhóm thiểu số $g$ (ví dụ: `Black`, $\hat{p}_1$) với nhóm tham chiếu `White` ($\hat{p}_0$, **Decision D-J**), hàm `rate_gap_table` trong **Step C0** tính đồng thời 3 thước đo. Tại sao phải dùng cả 3?

#### A. Định nghĩa Toán học & Ý nghĩa của 3 Thước đo
Giả sử ở mẫu $S0$ (*as of run 2026-11-10, Step C1a*; $n_0, n_1$ và các tỷ lệ có trong phần diễn giải của notebook, còn **số ca từ chối** $d_0, d_1$ **không có trong text notebook — [Verify] đối chiếu `B14_rq1_raw_gap.csv`**):
- Nhóm `White` ($0$): $n_0 = 5,360,624$, số bị từ chối $d_0 = 1,174,897 \implies \hat{p}_0 = 21.917\%$ ($\approx 21.92\%$).
- Nhóm `Black` ($1$): $n_1 = 733,103$, số bị từ chối $d_1 = 269,759 \implies \hat{p}_1 = 36.797\%$ ($\approx 36.80\%$).

1. **Chênh lệch Điểm Phần trăm (Percentage Point Gap — `gap_pp`):**
   $$\Delta_{\text{pp}} = (\hat{p}_1 - \hat{p}_0) \times 100 = 36.80\% - 21.92\% = +14.88\text{ pp}$$
   - *Lưu ý thuật ngữ:* Luôn viết là **pp (percentage points)**, không viết là `%` để tránh nhầm với phần trăm tăng trưởng tương đối.
   - *Ý nghĩa:* Đo **quy mô tuyệt đối**. Cứ 100 hồ sơ nộp vào, nhóm Black có thêm gần 15 hồ sơ bị từ chối so với nhóm White.

2. **Tỷ số Rủi ro (Risk Ratio / Disparity Ratio — `risk_ratio`):**
   $$\text{RR} = \frac{\hat{p}_1}{\hat{p}_0} = \frac{0.36797}{0.21917} \approx 1.68$$
   - *Ý nghĩa:* Xác suất bị từ chối của người vay Black **gấp** $1.68$ **lần** (cao hơn $68\%$) so với người vay White.

3. **Tỷ số Chênh (Odds Ratio — `odds_ratio`):**
   - Trước hết, **Odds (Chênh)** của một biến cố là tỷ số giữa xác suất xảy ra và xác suất *không* xảy ra: $\text{Odds} = \frac{p}{1 - p} = \frac{d}{n - d}$.
     - Với `White`: $\text{Odds}_0 = \frac{0.21917}{1 - 0.21917} \approx 0.2807$ (cứ $\sim 3.56$ hồ sơ đậu thì có $1$ hồ sơ trượt).
     - Với `Black`: $\text{Odds}_1 = \frac{0.36797}{1 - 0.36797} \approx 0.5822$ (cứ $\sim 1.72$ hồ sơ đậu thì có $1$ hồ sơ trượt).
   - **Odds Ratio (OR)** là tỷ số của hai Odds:
     $$\text{OR} = \frac{\text{Odds}_1}{\text{Odds}_0} = \frac{d_1 / (n_1 - d_1)}{d_0 / (n_0 - d_0)} = \frac{0.5822}{0.2807} \approx 2.074 \quad (\approx 2.07)$$
   - *Tại sao cần OR bên cạnh RR?* Vì trong Task tiếp theo (B15 / Phần 6 của Proposal), nhóm sẽ chạy **Hồi quy Logistic**: $\ln\left(\frac{p}{1-p}\right) = \beta_0 + \beta_1 \text{Black} + \dots$. Khi chỉ có biến Black, $e^{\beta_1}$ đúng bằng OR thô ở trên; khi thêm biến kiểm soát, $e^{\beta_1}$ là **OR đã hiệu chỉnh** (adjusted OR).
   - **[ADD v2] Ba cạm bẫy khi đọc OR:**
     1. **OR** $\ne$ **RR khi biến cố phổ biến**. Tỷ lệ từ chối chung là $\approx 24.6\%$ nên OR $= 2.07$ lớn hơn RR $= 1.68$. Không được đọc "OR = 2.07" là "khả năng bị từ chối gấp đôi"; câu đúng là "odds gấp ~2.07 lần" hoặc "gấp 1.68 lần xác suất".
     2. **Tính không gộp được (non-collapsibility).** OR đã hiệu chỉnh có thể khác OR thô ngay cả khi biến kiểm soát *không* gây nhiễu (confounding). Vì vậy đừng suy ra "biến kiểm soát giải thích bao nhiêu %" chỉ từ sự thay đổi của OR.
     3. **Hệ quả cho khung phân tích tuần tự:** khi báo cáo mức "thu hẹp" của khoảng cách qua các giai đoạn, hãy báo cả khoảng cách bằng **pp** (ví dụ hiệu ứng biên trung bình) song song với OR.

#### B. Khoảng tin cậy Log-Odds Ratio (Phương pháp Woolf, 1955)
Vì $\text{OR} \in (0, +\infty)$ bị chặn dưới tại $0$ và bằng $1$ khi hai nhóm ngang nhau, phân phối mẫu của $\text{OR}$ bị lệch phải rất mạnh. Tuy nhiên, nếu lấy logarit tự nhiên $\ln(\text{OR})$, thì $\ln(\text{OR}) \in (-\infty, +\infty)$ có phân phối xấp xỉ **Phân phối Chuẩn** theo Định lý Giới hạn Trung tâm (CLT) với sai số chuẩn (Standard Error):
$$\text{SE}\big(\ln(\text{OR})\big) = \sqrt{\frac{1}{d_1} + \frac{1}{n_1 - d_1} + \frac{1}{d_0} + \frac{1}{n_0 - d_0}}$$
Ta dựng khoảng tin cậy 95% trên thang $\ln$ trước, rồi mũ hóa ($\exp$) ngược lại về thang $\text{OR}$ (code tại `rate_gap_table`, Step C0):
$$\text{CI}_{95\%}(\text{OR}) = \exp\Big( \ln(\text{OR}) \pm 1.96 \times \text{SE}\big(\ln(\text{OR})\big) \Big)$$
*(Lưu ý: Đây được gọi là khoảng tin cậy **ngây thơ - naive Woolf CI** vì nó giả định các dòng dữ liệu độc lập với nhau).*

---

### 1.4. Khoảng tin cậy Newcombe Hybrid Score CI cho Hiệu hai Tỷ lệ $\hat{p}_1 - \hat{p}_0$ (Step C4, F0, F1, F9, G5)

#### A. Vấn đề cần giải quyết
Ở Step C4 (khoảng cách trong từng ô `loan_purpose` $\times$ `loan_type`), Step F1 (theo từng Bang) và Step F9 (theo từng Ngân hàng), ta cần tìm khoảng tin cậy 95% cho **hiệu hai tỷ lệ**:
$$\Delta = \hat{p}_1 - \hat{p}_0$$
Nếu dùng công thức Wald cơ bản: $\Delta \pm 1.96 \sqrt{\frac{\hat{p}_1(1-\hat{p}_1)}{n_1} + \frac{\hat{p}_0(1-\hat{p}_0)}{n_0}}$, ta lại dính đúng nhược điểm của Wald khi cỡ mẫu trong từng bang hoặc từng sản phẩm nhỏ dần.

#### B. Công thức Newcombe (1998) — Kết hợp hai khoảng Wilson
Newcombe chứng minh rằng: thay vì dùng sai số chuẩn Wald, ta hãy lấy chính **biên dưới và biên trên của khoảng tin cậy Wilson** của từng nhóm để ghép lại theo định lý Pythagoras!
- Gọi $[l_1, u_1]$ là khoảng tin cậy Wilson 95% của nhóm $1$ (quanh $\hat{p}_1$).
- Gọi $[l_0, u_0]$ là khoảng tin cậy Wilson 95% của nhóm tham chiếu $0$ (quanh $\hat{p}_0$).
- Chú ý tư duy:
  - Hiệu $\hat{p}_1 - \hat{p}_0$ sẽ đạt **cực tiểu (cận dưới)** khi nhóm $1$ rơi xuống thấp ($l_1$) và nhóm $0$ vọt lên cao ($u_0$).
  - Hiệu $\hat{p}_1 - \hat{p}_0$ sẽ đạt **cực đại (cận trên)** khi nhóm $1$ vọt lên cao ($u_1$) và nhóm $0$ rơi xuống thấp ($l_0$).

Do hai nhóm độc lập, độ dài nhánh dưới và nhánh trên của hiệu $\Delta = \hat{p}_1 - \hat{p}_0$ bằng căn bậc hai tổng bình phương hai nhánh thành phần (code tại **Step C4** và hàm `gap_vs_ref` **Step F0**):
$$\text{CI}_{\text{lo}}(\Delta) = (\hat{p}_1 - \hat{p}_0) - \sqrt{(\hat{p}_1 - l_1)^2 + (u_0 - \hat{p}_0)^2}$$
$$\text{CI}_{\text{hi}}(\Delta) = (\hat{p}_1 - \hat{p}_0) + \sqrt{(u_1 - \hat{p}_1)^2 + (\hat{p}_0 - l_0)^2}$$
Phương pháp này thừa hưởng toàn bộ tính chất ưu việt của Wilson CI và cực kỳ ổn định khi vẽ biểu đồ Forest Plot theo bang (Fig 27) hay theo phân khúc sản phẩm (Fig 13, Fig 34).

> **[ADD v2] Cảnh báo:** Cả Woolf CI (mục 1.3) lẫn Newcombe CI đều giả định các dòng độc lập và **bỏ qua phân cụm theo ngân hàng** — tức là đều *quá hẹp* như đã chứng minh ở mục 1.5. Trong B14 chỉ các khoảng cách tổng thể (headline) ở Step C1b mới có Cluster CI; các CI Newcombe theo bang, MSA, ngân hàng, tầng sản phẩm (Step C4, F1, F9, G5) cần được ghi chú là "naive". Với 41 bang được kiểm cùng lúc, một vài giá trị cực đoan xuất hiện chỉ do ngẫu nhiên.

---

### 1.5. Lender-Cluster Bootstrap trên Bảng Gộp trước (Step C1b — Decision D-Q)

Đây là một trong những kỹ thuật đắt giá nhất của notebook B14, kết hợp giữa **Kinh tế lượng (Clustered Standard Errors)** và **Kỹ thuật Tối ưu hóa Dữ liệu lớn (Vectorized Matrix Algebra)**.

#### A. Tại sao Khoảng tin cậy thông thường (Naive CI) bị sai lệch nghiêm trọng?
Trong khóa thống kê cơ bản, Định lý Giới hạn Trung tâm (CLT) đòi hỏi các quan sát phải **Độc lập và Cùng phân phối (i.i.d. — Independent and Identically Distributed)**: hồ sơ vay của người A không liên quan gì đến hồ sơ của người B.
- **Thực tế tín dụng HMDA:** $8,136,664$ hồ sơ không hề độc lập! Chúng được nộp vào $L = 4,808$ tổ chức cho vay (`lei`). Các hồ sơ nộp vào cùng một ngân hàng (ví dụ: cùng nộp vào ngân hàng `L0001`) chịu chung một bộ quy tắc thẩm định nội bộ (credit overlays), chung hệ thống chấm điểm tự động, và chung khẩu vị rủi ro của ngân hàng đó.
- Trong thống kê, hiện tượng này gọi là **Tương quan nội cụm (Intra-cluster correlation)**. Khi các quan sát trong cùng một cụm giống nhau, "lượng thông tin thực sự độc lập" nhỏ hơn con số $8.14\text{ triệu}$ rất nhiều (nó phụ thuộc vào số lượng ngân hàng $L = 4,808$).
- Nếu ta lờ đi điều này và dùng công thức Naive CI (chia cho $\sqrt{8,136,664}$), khoảng tin cậy sẽ **hẹp một cách giả tạo** (quá tự tin).

#### B. Giải pháp: Cluster Bootstrap (Lấy mẫu lại theo Cụm Ngân hàng)
1. **Bootstrap là gì?** Thay vì dùng công thức lý thuyết, ta coi tập dữ liệu gốc như một "quần thể giả lập", rồi rút mẫu ngẫu nhiên **có hoàn lại (with replacement)** $B = 1,000$ lần để xem chỉ số $\Delta$ dao động như thế nào. Từ $1,000$ kết quả đó, ta chặt bỏ $2.5\%$ đầu và $2.5\%$ đuôi (lấy phân vị $2.5\text{th}$ và $97.5\text{th}$) là có ngay khoảng tin cậy $95\%$!
2. **Cluster Bootstrap là gì?** Vì sự phụ thuộc nằm ở cấp độ ngân hàng, ta **không** bốc thăm từng dòng hồ sơ, mà **bốc thăm nguyên cả ngân hàng**:
   - Có $L = 4,808$ ngân hàng. Ở mỗi lượt lặp $b \in \{1, \dots, 1000\}$, ta bốc ngẫu nhiên có hoàn lại đúng $4,808$ ngân hàng.
   - Có ngân hàng được bốc trúng $2, 3$ lần (trọng số $w_l = 2, 3$), có ngân hàng không được bốc lần nào ($w_l = 0$), sao cho tổng số ngân hàng được bốc luôn là $\sum_{l=1}^L w_l = L$.

#### C. Thủ thuật Toán học & Kỹ thuật Dữ liệu Lớn trong B14 (Step C1b)
Nếu làm theo cách thông thường: lặp $1,000$ lần trên bảng $8.14\text{ triệu}$ dòng $\implies$ máy tính phải xử lý $8.14\text{ tỷ}$ dòng, tốn hàng giờ đồng hồ và tràn RAM!
Notebook B14 giải quyết bài toán này trong **vài giây** nhờ 2 bước toán học tương đương tuyệt đối:

- **Bước 1 — Gộp trước (Pre-aggregation):**
  Để tính tỷ lệ từ chối của chủng tộc $r$, ta chỉ cần tổng số hồ sơ $N_r$ và tổng số ca từ chối $D_r$. Vì vậy, ta gom bảng $8.14\text{ triệu}$ dòng thành hai ma trận kích thước cực nhỏ $(L \times R) = (4,808 \text{ ngân hàng} \times 7 \text{ chủng tộc chính})$:
  - Ma trận $\mathbf{N}$ kích thước $(4808 \times 7)$: phần tử $N_{l,r}$ là số hồ sơ của chủng tộc $r$ tại ngân hàng $l$.
  - Ma trận $\mathbf{D}$ kích thước $(4808 \times 7)$: phần tử $D_{l,r}$ là số ca từ chối của chủng tộc $r$ tại ngân hàng $l$.

- **Bước 2 — Biểu diễn việc bốc thăm bằng Phân phối Đa thức (Multinomial Distribution) & Nhân Ma trận:**
  Việc bốc có hoàn lại $L$ lần từ $L$ ngân hàng với xác suất đều nhau $\left(\frac{1}{L}, \dots, \frac{1}{L}\right)$ chính là một phép thử **Phân phối Đa thức** $\text{Multinomial}\left(L, \left[\frac{1}{L}, \dots, \frac{1}{L}\right]\right)$!
  Ta sinh một lần duy nhất ma trận trọng số $\mathbf{W}$ kích thước $(B \times L) = (1000 \times 4808)$ bằng lệnh:
  ```python
  W = rng.multinomial(L, np.full(L, 1.0 / L), size=BOOT_B).astype("float64")  # (1000, 4808)
  ```
  Trong đó dòng thứ $b$ của $\mathbf{W}$ chứa số lần mỗi ngân hàng được bốc trúng ở lượt thứ $b$.
  Khi đó, tổng số hồ sơ và tổng số ca từ chối của cả $1,000$ lượt bootstrap chỉ là **hai phép nhân ma trận** (`@`):
  $$\mathbf{N}_{\text{boot}} = \mathbf{W} \times \mathbf{N}, \qquad \mathbf{D}_{\text{boot}} = \mathbf{W} \times \mathbf{D}$$
  $\mathbf{N}_{\text{boot}}$ và $\mathbf{D}_{\text{boot}}$ có kích thước $(1000 \times 7)$, tính xong trong tích tắc!

#### D. Kết quả Thực chứng trong B14 (As of run 2026-11-10, cell C1b)
Cột `cluster_vs_naive_or_ci_width` trong bảng `B14_rq1_raw_gap.csv` cho thấy:
- Với nhóm **Black**, khoảng tin cậy 95% của Odds Ratio khi tính theo cụm ngân hàng (**Cluster Bootstrap CI**) **rộng gấp** $13.9$ **lần** so với khoảng tin cậy Woolf ngây thơ (Naive CI)! Với nhóm **Asian**, nó rộng gấp $17.6$ **lần**!
- Khoảng cách Black–White là $+14.88\text{ pp}$ với Cluster 95% CI là $[12.94\text{ pp}, 16.99\text{ pp}]$ — chứng minh khoảng cách này vẫn cực kỳ vững chắc ngay cả khi đã tính đến sự phân cụm theo ngân hàng.
- **[ADD v2] Giới hạn của phương pháp:** (i) Phân phối quy mô ngân hàng rất lệch (top 100 ngân hàng nắm $\approx 61\%$ hồ sơ), nên khoảng tin cậy phụ thuộc mạnh vào vài ngân hàng lớn, và số cụm thực sự "có thông tin" ít hơn $L = 4{,}808$ nhiều. (ii) Cluster bootstrap chỉ sửa **tương quan nội cụm**; nó không sửa chệch do thiếu biến (điểm tín dụng, tài sản) và không biến kết quả thành nhân quả. (iii) Bootstrap bốc ngân hàng với xác suất đều $1/L$ — đây là lựa chọn thiết kế, không phải duy nhất.

---

## Phần 2. Phân rã Khoảng cách & Kiểm tra Nghịch lý Simpson (RQ1 & RQ2 — Phần C & D)

### 2.1. Nghịch lý Simpson (Simpson's Paradox) & Kiểm định Phân tầng (Step C4, D2b — Decision D-AE)

#### A. Bản chất Toán học của Nghịch lý Simpson
Nghịch lý Simpson xảy ra khi một xu hướng xuất hiện trên dữ liệu gộp chung (pooled data) lại **biến mất hoặc đảo chiều hoàn toàn** khi ta chia dữ liệu thành các nhóm con (strata).
Về mặt toán học, tỷ lệ từ chối chung của nhóm $g$ là trung bình có trọng số của các tỷ lệ trong từng phân khúc sản phẩm $s$:
$$\bar{Y}_g = \sum_{s=1}^S w_s^g \, r_s^g$$
Trong đó $w_s^g$ là tỷ trọng hồ sơ của nhóm $g$ nộp vào phân khúc $s$ ($\sum_s w_s^g = 1$), và $r_s^g$ là tỷ lệ từ chối của nhóm $g$ trong phân khúc $s$.
Hai nhóm có thể có $\bar{Y}_A \approx \bar{Y}_W$ trên tổng thể, nhưng thực chất trong hầu hết mọi phân khúc $s$ thì $r_s^A > r_s^W$, chỉ vì nhóm $A$ nộp phần lớn hồ sơ ($w_s^A$ lớn) vào một phân khúc có tỷ lệ từ chối cực thấp!

> **[ADD v2] Lưu ý thuật ngữ:** Nghịch lý Simpson đúng nghĩa là đảo chiều dấu khi gộp/tách nhóm. Trường hợp Asian (gộp $-0.16\text{ pp}$, nhưng dương ở 10/11 tầng) gần với đảo chiều thật. Trường hợp `CLTV <= 60%` là **hiệu ứng gộp do cơ cấu sản phẩm** (aggregation/mix effect) — cùng họ "Simpson-type" nhưng không phải đảo chiều. Hai ví dụ dưới đây nên gọi là "kiểu Simpson".

#### B. Hai phát hiện Nghịch lý Simpson cực kỳ quan trọng trong B14
1. **Khoảng cách của nhóm Asian vs. White (Step C4):**
   - Trên toàn mẫu $S0$ (C1), khoảng cách thô của nhóm Asian so với White là $-0.16\text{ pp}$ ($21.77\%$ vs. $21.92\%$) — nhìn qua tưởng như người vay Asian có tỷ lệ từ chối thấp hơn hoặc ngang bằng White.
   - Nhưng khi chia thành các tầng `loan_purpose` $\times$ `loan_type` (Step C4), trong **10 trên 11 phân tầng hợp lệ**, người vay Asian lại có tỷ lệ từ chối **cao hơn** White (lên tới $+14.86\text{ pp}$), và chỉ thấp hơn White ở duy nhất phân khúc *Conventional Home Purchase* ($-3.80\text{ pp}$).
   - *Lý do:* Người vay Asian tập trung tới $62.1\%$ hồ sơ vào phân khúc *Home Purchase* (vốn có tỷ lệ từ chối chung rất thấp, chỉ $14.47\%$), kéo trung bình gộp của Asian xuống!

2. **Tại sao tỷ lệ từ chối ở `CLTV <= 60%` và `DTI < 20%` lại cao bất thường? (Step D2b — Decision D-AE):**
   - Theo lý thuyết tài chính, vay càng ít so với giá trị nhà ($\text{CLTV} \le 60\%$) và nợ trên thu nhập càng thấp ($\text{DTI} < 20\%$) thì rủi ro càng thấp, tỷ lệ từ chối phải thấp nhất. Thế nhưng trên đường cong gộp toàn mẫu $S0$ (Step D2), tỷ lệ từ chối tại $\text{CLTV} \le 60\%$ lại vọt lên tới $28.43\%$ (cao hơn cả mức $12.72\%$ tại $\text{CLTV} = 80\%$), và tại $\text{DTI} < 20\%$ vọt lên $29.21\%$ (cao gần gấp đôi mức $15.93\%$ tại $\text{DTI } 20\text{–}<30\%$)!
   - Để kiểm tra xem đây có phải là ảo ảnh do **Nghịch lý Simpson (trộn lẫn các sản phẩm)** hay không, Step D2b chia $S0$ thành 6 phân khúc sản phẩm loại trừ lẫn nhau và kiểm tra trọng số $w_{s|b}$ trong từng bin $b$:
     - **Với `CLTV <= 60%` (Product Mix giải thích phần lớn mức tăng ở số liệu gộp — hiệu ứng gộp kiểu Simpson):** Trong phân khúc *First-lien Purchase*, tỷ lệ từ chối tại $\text{CLTV} \le 60\%$ thực chất rất thấp, chỉ $6.87\%$ (thấp hơn mức trung bình $14.33\%$ của phân khúc đó tới $-7.46\text{ pp}$). Sở dĩ con số gộp toàn thị trường lên tới $28.43\%$ là vì ở bin $\text{CLTV} \le 60\%$, có tới $60.47\%$ **hồ sơ** thuộc ba phân khúc rủi ro cao hơn: *Open-end HELOC* ($39.93\%$ tỷ trọng, từ chối $33.17\%$), *Subordinate closed-end* ($13.37\%$, $37.12\%$) và *First-lien other purpose* ($7.17\%$, $42.56\%$); $39.93 + 13.37 + 7.17 = 60.47$. *[CHANGE v2: v1 chỉ liệt kê hai phân khúc đầu nên tổng không khớp 60.47%]* Còn *First-lien refinance* ở $\text{CLTV} \le 60\%$ là $27.84\%$ — chỉ thấp hơn mức trung bình phân khúc $1.23\text{ pp}$, nên "vay ít thì an toàn" chỉ thể hiện rõ ở phân khúc mua nhà. [Hypothesis] Các khoản này có thể là vay lấy tiền mặt trên căn nhà đã trả gần hết nợ.
     - **Với `DTI < 20%` (Bác bỏ giả thuyết Product Mix):** Ngay cả khi đã tách riêng từng phân khúc một, tỷ lệ từ chối tại $\text{DTI} < 20\%$ vẫn cao hơn bin $\text{DTI } 20\text{–}<30\%$ trên $10\text{ pp}$ ở **tất cả mọi phân khúc** (ví dụ: trong *First-lien Purchase* là $20.38\%$ vs. $9.66\%$, chênh $+10.72\text{ pp}$). Vậy cơ cấu sản phẩm **không** giải thích được chữ J ở $\text{DTI} < 20\%$. Nguyên nhân vẫn chưa rõ — **[Hypothesis]** có thể là điểm tín dụng, chất lượng tài sản đảm bảo, loại nhà (ví dụ nhà lắp ghép) hoặc hồ sơ không chuẩn mà dữ liệu công khai không quan sát được. Hệ quả thiết kế (đã được notebook chốt): đưa DTI vào mô hình dưới dạng **biến phân loại (bins)** thay vì một hàm tuyến tính.

---

### 2.2. Phân rã Kitagawa (1955) (Direct Standardization) & Bẫy Gộp nhóm `low_reliability` (Step C5, D4, F8, G2 — Decisions D-P, D-U, D-X)

Đây là công cụ toán học trung tâm trả lời trực tiếp câu hỏi nghiên cứu chính của nhóm ở bước EDA.

#### A. Bài toán đặt ra
Ta biết khoảng cách từ chối thô giữa nhóm Black ($B$) và nhóm White ($W$) là:
$$\Delta = \bar{Y}_B - \bar{Y}_W = 36.80\% - 21.92\% = +14.88\text{ pp}$$
Câu hỏi: Trong $+14.88\text{ pp}$ này, có **bao nhiêu điểm phần trăm** là do người vay Black nộp hồ sơ vào các sản phẩm/mức tài chính rủi ro hơn (**Hiệu ứng Cấu trúc / Composition Effect**), và **bao nhiêu điểm phần trăm** là do ngay trong cùng một sản phẩm/mức tài chính như nhau, người vay Black vẫn bị từ chối nhiều hơn (**Hiệu ứng Tỷ lệ nội tầng / Rate Effect**)?

#### B. Chứng minh Đại số từ Sơ cấp đến Công thức Kitagawa (1955)
Chia toàn bộ thị trường thành $K$ tầng (strata) không giao nhau $k \in \{1, \dots, K\}$ (ví dụ ở Step C5: mỗi tầng $k$ là một tổ hợp `loan_type` $\times$ `loan_purpose` $\times$ `lien_status` $\times$ `occupancy_type`).
Với mỗi nhóm $g \in \{B, W\}$ tại tầng $k$:
- Tỷ trọng hồ sơ rơi vào tầng $k$: $w_k^g = \frac{n_k^g}{n^g}$ (với $\sum_{k=1}^K w_k^g = 1$).
- Tỷ lệ từ chối trong tầng $k$: $r_k^g = \frac{d_k^g}{n_k^g}$.

Tỷ lệ từ chối tổng thể của mỗi nhóm là tổng có trọng số:
$$\bar{Y}_B = \sum_{k=1}^K w_k^B r_k^B, \qquad \bar{Y}_W = \sum_{k=1}^K w_k^W r_k^W$$
Hiệu số giữa hai nhóm là:
$$\Delta = \bar{Y}_B - \bar{Y}_W = \sum_{k=1}^K \left( w_k^B r_k^B - w_k^W r_k^W \right)$$
Bây giờ, bằng phép biến đổi đại số sơ cấp, với mỗi số hạng $w_k^B r_k^B - w_k^W r_k^W$, ta đặt:
- Trọng số trung bình của hai nhóm tại tầng $k$: $\bar{w}_k = \frac{w_k^B + w_k^W}{2}$
- Tỷ lệ từ chối trung bình của hai nhóm tại tầng $k$: $\bar{r}_k = \frac{r_k^B + r_k^W}{2}$

Bạn hãy thử khai triển tổng của hai cụm sau tại tầng $k$:
$$\bar{r}_k (w_k^B - w_k^W) + \bar{w}_k (r_k^B - r_k^W) = \frac{r_k^B + r_k^W}{2}(w_k^B - w_k^W) + \frac{w_k^B + w_k^W}{2}(r_k^B - r_k^W)$$
$$= \frac{1}{2}\Big( r_k^B w_k^B - r_k^B w_k^W + r_k^W w_k^B - r_k^W w_k^W + w_k^B r_k^B - w_k^B r_k^W + w_k^W r_k^B - w_k^W r_k^W \Big)$$
Các số hạng chéo $(-r_k^B w_k^W + w_k^W r_k^B)$ và $(+r_k^W w_k^B - w_k^B r_k^W)$ triệt tiêu nhau hoàn toàn! Kết quả còn lại đúng bằng:
$$= \frac{1}{2}\left( 2 w_k^B r_k^B - 2 w_k^W r_k^W \right) = w_k^B r_k^B - w_k^W r_k^W$$
Cộng qua toàn bộ $K$ tầng, ta thu được **Đồng nhất thức Phân rã Kitagawa (Kitagawa Accounting Identity)** được code trong hàm `kitagawa(st, group, ref, strata_cols)` tại **Step C5**:
$$\Delta = \underbrace{\sum_{k=1}^K \left(\frac{r_k^B + r_k^W}{2}\right) (w_k^B - w_k^W)}_{\text{Composition Effect (Do khác biệt cơ cấu } w_k \text{)}} + \underbrace{\sum_{k=1}^K \left(\frac{w_k^B + w_k^W}{2}\right) (r_k^B - r_k^W)}_{\text{Rate Effect (Do khác biệt tỷ lệ nội tầng } r_k \text{)}}$$

> **Tính chất cốt lõi cần nhớ khi bảo vệ đồ án:**
> 1. Đây là một **đồng nhất thức toán học chính xác 100%** (sai số dư `identity_residual_pp` $< 10^{-9}$, được kiểm tra bằng `assert` trong code), **không phải mô hình ước lượng**, không có sai số phần dư, không giả định hàm tuyến tính hay phân phối chuẩn.
> 2. **Composition Effect:** Giả sử trong mỗi tầng $k$, cả hai nhóm đều chịu chung một mức tỷ lệ từ chối trung bình $\bar{r}_k$, thì chỉ riêng việc hai nhóm nộp hồ sơ vào các tầng với tỷ trọng khác nhau ($w_k^B \ne w_k^W$) tạo ra bao nhiêu pp chênh lệch?
> 3. **Rate Effect:** Giả sử cả hai nhóm có cùng cơ cấu sản phẩm/tài chính $\bar{w}_k$ như nhau, thì việc tỷ lệ từ chối nội trong từng tầng khác nhau ($r_k^B \ne r_k^W$) tạo ra bao nhiêu pp chênh lệch?

#### B2. [ADD v2] Giới hạn khi diễn giải Kitagawa
- **Không cộng được giữa các phân rã khác nhau.** C5 (chỉ sản phẩm: Composition $-1.19\text{ pp}$) và G2 (chỉ tài chính: Composition $+3.92\text{ pp}$) dùng các tầng khác nhau; không được cộng hai con số này. Cũng cần trích phương án (a) của G2 (bỏ hồ sơ thiếu): $13.73 = 3.15 + 10.58$ ($77.03\%$) bên cạnh phương án (b) ($73.65\%$).
- **Phụ thuộc cách chia tầng.** Cùng một khoảng cách có thể cho tỷ lệ Composition/Rate khác khi đổi biến tầng. Đây là lý do notebook luôn nêu rõ biến tầng và quy tắc gộp.
- **"Bad control".** Biến có thể do chủng tộc ảnh hưởng ngược lại (ví dụ khu phố cư trú) không nên được coi là biến kiểm soát vô tội; Composition khi đó không đồng nghĩa "rủi ro tín dụng chính đáng".
- **Từ ngữ trong Proposal.** Proposal nói khoảng cách "thu hẹp" khi thêm kiểm soát. Với sản phẩm, Composition âm nên khoảng cách thực ra *nới rộng* (Rate $+16.07\text{ pp}$ > khoảng cách thô $+14.88\text{ pp}$); chỉ tài chính mới thu hẹp.

#### C. Tại sao chia tầng quá mịn lại dẫn đến Bẫy `low_reliability`? (Decisions D-U, D-X; **[Verify]** D-AG chưa thấy trong notebook, kiểm tra `decisions.md`)
Trong hàm `kitagawa()`, theo quy tắc **D-M**, bất kỳ tầng $k$ nào mà nhóm thiểu số hoặc nhóm White có $n < 1,000$ hoặc $d < 100$ đều bị coi là nhiễu mẫu nhỏ và được **gom chung vào một tầng duy nhất tên là `"Other (pooled)"`** (**Decision D-U**).
- **Khi số tầng vừa phải (như Step C5 — Product Mix hoặc Step G2 — Coarse Financial Strata** $5 \times 5 \times 5$):
  - Ở **Step C5** (*as of run 2026-11-10, Step C5*): Chỉ có một tỷ lệ rất nhỏ hồ sơ (notebook ghi khoảng $0.82\%$–$6.08\%$ cho bốn nhóm đáng tin; **[Verify]** giá trị riêng của Black trong `B14_rq1_kitagawa.csv`, cột `pooled_share_max_pct`) bị rơi vào `"Other (pooled)"`. Kết quả cực kỳ đáng tin cậy:
    $$\Delta_{\text{Black–White}} (+14.88\text{ pp}) = \text{Composition } (-1.19\text{ pp}) + \text{Rate } (+16.07\text{ pp})$$
    *Giải thích âm $-1.19\text{ pp}$:* Người vay Black nộp nhiều hồ sơ hơn vào các khoản vay chính phủ bảo lãnh (FHA $23.4\%$, VA $11.7\%$) vốn có tỷ lệ từ chối thấp hơn khoản vay thông thường (Conventional). Do đó, cơ cấu sản phẩm thực chất giúp **giảm** khoảng cách cho nhóm Black đi $1.19\text{ pp}$, và khoảng cách nội trong từng sản phẩm thực chất là $+16.07\text{ pp}$!
  - Ở **Step G2** (Tầng tài chính thô: 5 nhóm DTI $\times$ 5 nhóm CLTV $\times$ 5 nhóm Thu nhập, giữ biến thiếu làm nhóm riêng — phương án `(b)`, *Step G2*): Chỉ có $2.54\%$ hồ sơ rơi vào `"Other (pooled)"` (`low_reliability = False`). Kết quả:
    $$\Delta_{\text{Black–White}} (+14.88\text{ pp}) = \text{Composition } (+3.92\text{ pp}, \, 26.35\%) + \text{Rate } (+10.96\text{ pp}, \, 73.65\%)$$
    Nghĩa là hồ sơ tài chính (DTI cao hơn, CLTV cao hơn, thu nhập thấp hơn) giải thích được $3.92\text{ pp}$ ($26.35\%$) khoảng cách, còn $10.96\text{ pp}$ ($73.65\%$) vẫn nằm ở sự khác biệt tỷ lệ từ chối giữa các hồ sơ có cùng khung DTI $\times$ CLTV $\times$ Thu nhập.

- **Khi chia tầng quá mịn (Lời nguyền Đa chiều — Curse of Dimensionality ở Step D4 và Step F8):**
  - Ở **Step D4** (`FIN`: 10 nhóm DTI × 10 nhóm CLTV × 12 nhóm Thu nhập = 1,200 tầng lý thuyết, trong đó 1,149 tầng có dữ liệu) và **Step F8** ($4,808$ ngân hàng là $4,808$ tầng): Vì chia quá nhỏ, có tới $47.55\%$ hồ sơ của nhóm Black ở `FIN` và $44.10\%$ ở `F8` không đủ điều kiện $n \ge 1,000, d \ge 100$ trong từng ô, nên bị dồn hết vào cái túi `"Other (pooled)"`! Thậm chí với nhóm `NHPI` hoặc `2+ minority races`, $100\%$ các tầng đều bị gộp thành 1 cục duy nhất!
  - **Hậu quả toán học khi gộp:** Khi $47.55\%$ dữ liệu bị nhét chung vào 1 tầng `"Other (pooled)"`, mọi sự khác biệt về cấu trúc tài chính bên trong cái túi khổng lồ đó không còn được tách tầng nữa, mà bị quy hết thành **Rate Effect**!
  - Do đó, **Decision D-U & D-X** đặt ra quy tắc kiểm soát chất lượng: Nếu tỷ lệ hồ sơ bị gộp (`pooled_share_max_pct`) vượt quá $10\%$, bảng tự động gắn cờ `low_reliability = True` và **không được trích dẫn làm kết quả ước lượng chính thức**.

---

### 2.3. Phân rã Lý do Từ chối theo Số ca trên 100 Hồ sơ (Step D7c — Decision D-AD)

#### A. Bẫy xác suất có điều kiện (Conditional Probability Trap) ở bảng D7 thông thường
Các cột `denial_reason_1..4` chỉ tồn tại khi hồ sơ **đã bị từ chối** ($\text{is\_denied} = 1$).
Nếu ta chỉ tính tỷ trọng phần trăm từng lý do **trong số các hồ sơ bị từ chối** (như ở Step D7, *Step D7*):
$$s_r^g = P(\text{Reason } = r \mid \text{Denied}, \text{Race } = g)$$
Ta sẽ thấy một nghịch lý: Trong số những người bị từ chối, nhóm **Black** bị ghi lý do chính là DTI chiếm $31.08\%$, **thấp hơn** so với nhóm **White** ($33.09\%$)! Nếu nhìn vào đó mà kết luận "Người vay Black ít bị từ chối vì DTI hơn người vay White" là **sai lầm nghiêm trọng**!
Tại sao? Vì mẫu số của hai phần trăm đó khác nhau: tổng tỷ lệ bị từ chối của Black là $36.80\%$, còn của White chỉ là $21.92\%$. $31.08\%$ của một chiếc bánh to ($36.80\%$) lớn hơn rất nhiều so với $33.09\%$ của một chiếc bánh nhỏ ($21.92\%$)!

#### B. Công thức Chuẩn hóa về Mẫu số Chung (Số ca từ chối trên 100 hồ sơ nộp vào — Step D7c)
Áp dụng công thức xác suất đồng thời $P(\text{Reason } = r \cap \text{Denied} \mid g) = P(\text{Reason } = r \mid \text{Denied}, g) \times P(\text{Denied} \mid g)$, ta định nghĩa mức đóng góp $c_r^g$ (tính trên 100 hồ sơ nộp vào của nhóm $g$):
$$c_r^g = \frac{s_r^g}{100} \times \bar{Y}_g$$
Vì mỗi hồ sơ bị từ chối có **đúng 1 lý do chính** (`denial_reason_1`), nên $\sum_r s_r^g = 100\%$, dẫn đến tổng các $c_r^g$ bằng đúng tỷ lệ từ chối của nhóm $g$:
$$\sum_r c_r^g = \bar{Y}_g$$
Suy ra, khoảng cách từ chối thô $\Delta = \bar{Y}_B - \bar{Y}_W$ được phân rã **cộng tính chính xác 100%** thành tổng chênh lệch của từng lý do chính:
$$\Delta = \bar{Y}_B - \bar{Y}_W = \sum_r \left( c_r^B - c_r^W \right)$$
Kết quả thực tế (*as of run 2026-11-11, cell D7c*):
- **Lịch sử tín dụng (`Credit history`):** Black có $13.18$ ca / 100 hồ sơ vs. White có $6.05$ ca / 100 hồ sơ $\implies$ Chênh lệch $+7.13\text{ pp}$ (chiếm $47.90\%$ toàn bộ khoảng cách thô $+14.88\text{ pp}$).
- **Tỷ lệ nợ trên thu nhập (`DTI`):** Black có $11.43$ ca / 100 hồ sơ vs. White có $7.25$ ca / 100 hồ sơ $\implies$ Chênh lệch $+4.18\text{ pp}$ (chiếm $28.10\%$ khoảng cách thô).
- Chỉ riêng 2 lý do này đã chiếm $76.0\%$ khoảng cách từ chối Black–White!
- **[ADD v2] Giới hạn (Decision D-AD):** (i) Lý do là do **ngân hàng khai báo sau quyết định**, không phải đo lường độc lập; "lịch sử tín dụng" không đồng nghĩa điểm FICO. (ii) Đây là **kế toán mô tả**, không phải phản thực: "Credit history chiếm $47.90\%$ khoảng cách" **không** có nghĩa "credit history giải thích $47.90\%$" — bỏ một lý do thì hồ sơ vẫn có thể bị từ chối vì lý do khác. (iii) Phiên bản "any of 4" (tối đa 4 lý do/hồ sơ) **chồng lấn** nên các chênh lệch không cộng lại bằng khoảng cách thô; chỉ phiên bản *primary* cộng chính xác. (iv) Mã `1111` (Exempt) và các mã khác được giữ như hạng mục riêng.

---

## Phần 3. Đo lường Tương quan, Đa cộng tuyến & Mất cân bằng Phân phối (Phần E)

### 3.1. Tương quan hạng Spearman's $\rho$ vs. Pearson's $r$ (Step E1)

- **Từ thống kê cơ bản:** Hệ số tương quan **Pearson** ($r$) đo mức độ quan hệ **tuyến tính (đường thẳng)** dựa trên giá trị trung bình và độ lệch chuẩn:
  $$r_{XY} = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$$
- **Tại sao Pearson bị bóp méo trên dữ liệu HMDA?** Như đã thấy ở Step B1 và Step E0, biến `income` (đơn vị: nghìn USD) có những giá trị cực đoan — notebook ghi $138$ dòng có thu nhập trên $100{,}000$ (tức trên $100\text{ triệu USD}$) và độ lệch chuẩn $38{,}459$; `combined_loan_to_value_ratio` có độ lệch chuẩn $1{,}728{,}718$. **[Verify]** giá trị lớn nhất của `income` (notebook chỉ in `nlargest(5)` mà không ghi lại kết quả) và ghi kèm đơn vị. Chỉ cần vài điểm cực đoan (outliers) này sẽ kéo $\bar{x}$ và làm hỏng Pearson's $r$. Hơn nữa, quan hệ giữa các biến tài chính thường là **đơn điệu phi tuyến** (cong theo hàm logarit) chứ không thẳng.
- **Giải pháp — Spearman's Rank Correlation** ($\rho$):
  Thay vì tính trên giá trị gốc $x_i, y_i$, ta sắp xếp dữ liệu từ nhỏ đến lớn và thay bằng **Thứ hạng (Rank)** $R(x_i), R(y_i) \in \{1, 2, \dots, n\}$, rồi tính hệ số tương quan Pearson trên các thứ hạng đó!
  - Vì làm việc trên thứ hạng, một người có thu nhập $10\text{ triệu USD}$ hay $100\text{ tỷ USD}$ thì cũng chỉ đứng ở hạng cuối cùng $n$, không thể kéo lệch toàn bộ ma trận tương quan.
  - Trong **Step E1**, Spearman $\rho$ giữa `loan_amount` và `income` trên mẫu phân tầng $500\text{k}$ dòng khớp với toàn bộ $8.14\text{ triệu}$ dòng $S0$ ($\rho \approx 0.464$, sai lệch $< 0.01$).
- **[ADD v2] Giới hạn của Spearman:** (i) Chỉ đo quan hệ **đơn điệu**; nó bỏ sót quan hệ hình chữ U/J như đường cong DTI (Step B3, D2), vì vậy các quan hệ đó được phân tích bằng bin và đường cong tỷ lệ từ chối, không bằng tương quan. (ii) Biến có nhiều giá trị trùng (ties) như `dti_mid` — là điểm giữa của bin, một [Hypothesis] chỉ dùng làm proxy — cho hệ số kém chính xác hơn. (iii) Hệ số tính từng cặp trên các tập hồ sơ đầy đủ khác nhau, mà dữ liệu thiếu mang thông tin (Step D6).

---

### 3.2. Đo lường Liên hệ Biến Phân loại – Kết cục: Bias-Corrected Cramér's $V$ & Mutual Information (Step E2)

Làm sao để biết trong 25 biến phân loại (`dti_cat`, `loan_purpose`, `derived_race`, `state_code`, `derived_msa_md`,...), biến nào có mối liên hệ mạnh nhất với biến kết cục nhị phân `is_denied` ($0/1$)? Ta không thể dùng Spearman vì các biến như `state_code` hay `loan_purpose` không có thứ tự tự nhiên!

#### A. Từ Kiểm định Chi-bình phương ($\chi^2$) đến Bias-Corrected Cramér's $V$ (Bergsma, 2013)
1. **Kiểm định** $\chi^2$ **cơ bản**:
   Lập bảng chéo (contingency table) kích thước $r \times k$ (ở đây $r = 2$ dòng là `Denied` / `Not Denied`, và $k$ cột là các mức của biến phân loại).
   Gọi $O_{ij}$ là số đếm thực tế ở ô $(i, j)$, và $E_{ij} = \frac{\text{Tổng dòng } i \times \text{Tổng cột } j}{N}$ là số đếm kỳ vọng nếu hai biến độc lập. Thống kê Chi-bình phương là:
   $$\chi^2 = \sum_{i=1}^r \sum_{j=1}^k \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$$
2. **Tại sao không dùng trực tiếp** $\chi^2$ **hay Cramér's** $V$ **cổ điển?**
   - $\chi^2$ tỷ lệ thuận với cỡ mẫu $N$, nên ta chia cho $N$ để được $\phi^2 = \frac{\chi^2}{N}$.
   - Tuy nhiên, nếu một biến có **rất nhiều mức** $k$ (ví dụ `derived_msa_md` có $k = 418$ vùng đô thị), thì ngay cả khi hoàn toàn độc lập, giá trị kỳ vọng của $\chi^2$ vẫn bằng bậc tự do $(r-1)(k-1) = k - 1$. Do đó, các biến nhiều mức sẽ bị **thổi phồng (upward bias)** chỉ số Cramér's $V$ cổ điển!
3. **Công thức Hiệu chỉnh Chệch của Bergsma (2013) trong hàm `assoc_from_counts` (Step E2):**
   Ta trừ đi phần kỳ vọng nhiễu $\frac{(r-1)(k-1)}{N-1}$ khỏi $\phi^2$, đồng thời hiệu chỉnh số dòng và số cột:
   $$\tilde{\phi}^2 = \max\left(0, \; \frac{\chi^2}{N} - \frac{(r-1)(k-1)}{N - 1}\right)$$
   $$\tilde{k} = k - \frac{(k-1)^2}{N - 1}, \qquad \tilde{r} = r - \frac{(r-1)^2}{N - 1}$$
   $$V_{\text{BC}} = \sqrt{\frac{\tilde{\phi}^2}{\min(\tilde{k} - 1, \; \tilde{r} - 1)}} \in [0, 1]$$
   - $V_{\text{BC}} = 0$: Hai biến hoàn toàn độc lập.
   - $V_{\text{BC}} = 1$: Biến phân loại xác định hoàn toàn kết cục từ chối.

#### B. Thông tin Tương hỗ Chuẩn hóa (Normalised Mutual Information — NMI)
Bên cạnh Cramér's $V$ (dựa trên khoảng cách bình phương), Step E2 còn tính **Mutual Information (MI)** từ Lý thuyết Thông tin (Shannon):
1. **Entropy của biến kết cục** $Y$ (**`is_denied`**): Đo mức độ "bất định" ban đầu của kết cục từ chối:
   $$H(Y) = -\sum_{y \in \{0,1\}} P(Y=y) \ln P(Y=y)$$
2. **Mutual Information** $\text{MI}(X; Y)$: Đo lượng thông tin mà biến phân loại $X$ cung cấp giúp làm giảm sự bất định về $Y$:
   $$\text{MI}(X; Y) = \sum_{y \in \{0,1\}} \sum_{x=1}^k P(X=x, Y=y) \ln\left(\frac{P(X=x, Y=y)}{P(X=x)P(Y=y)}\right)$$
3. **Chuẩn hóa (`mi_norm_by_entropy_y`):** Chia $\text{MI}(X; Y)$ cho $H(Y)$:
   $$\text{NMI} = \frac{\text{MI}(X; Y)}{H(Y)} \in [0, 1]$$
   Ý nghĩa cực kỳ trực giác: **Biết được giá trị của biến** $X$ **giúp giải thích được bao nhiêu phần trăm sự bất định (entropy) của quyết định từ chối** $Y$?
   - **Kết quả trong B14 (*Step E2*):** `dti_cat` đứng số 1 toàn thị trường với $V_{\text{BC}} = 0.488$ và $\text{NMI} = 0.191$ (riêng một mình DTI giải thích được $19.1\%$ entropy của quyết định từ chối). So với chủng tộc, **cùng một thước đo** là $V_{\text{BC}}$: $0.488$ so với $0.118$, tức gấp $\approx 4.1$ lần (gấp $\approx 17$ lần nếu so $V^2$, tỷ lệ "phương sai chung"). NMI của `derived_race` chưa được tính trong notebook. *[CHANGE v2: v1 so NMI của DTI với V của chủng tộc]*
- **[ADD v2] Cách đọc đúng bảng E2:** (i) **MI cũng bị chệch mẫu hữu hạn** ở biến nhiều mức (`state_code`, `derived_msa_md`); notebook ước lượng $\approx (k-1)/(2N)$ nats, nhỏ so với giá trị quan sát nên chấp nhận được. (ii) `dti_cat` có cả mức `MISSING`; bỏ hai mức này $V$ tăng nhẹ từ $0.488$ lên $0.499$ (ô kiểm tra sau Checkpoint 5) nên mối liên hệ không phải do thiếu dữ liệu. (iii) Xếp hạng cao **không** có nghĩa nên đưa vào mô hình: `aus_1` (hạng 2) và `applicant_credit_score_type` (hạng 5) bị loại khỏi mô hình chính theo D-Y vì là proxy quy trình; `preapproval` có $V = 0.089$ chỉ do F01 loại các hồ sơ preapproval bị từ chối (artefact chọn mẫu). (iv) $V$ là **mức liên hệ**, không phải độ quan trọng hay quan hệ nhân quả.

---

### 3.3. Đa cộng tuyến Cấu trúc & Nhân tử Phóng đại Phương sai (VIF) (Step E3 — Decision D-AF)

#### A. Định nghĩa VIF (Variance Inflation Factor)
Khi chuẩn bị đưa một nhóm $p$ biến số học $X_1, X_2, \dots, X_p$ vào mô hình hồi quy ở Task tiếp theo (B15), nếu một biến $X_j$ có thể được biểu diễn gần như tuyến tính qua các biến còn lại, hiện tượng **Đa cộng tuyến (Multicollinearity)** xảy ra.
Gọi $R_j^2$ là hệ số xác định ($R$-squared) khi lấy biến $X_j$ làm biến phụ thuộc và hồi quy theo tất cả $p - 1$ biến số còn lại. Khi đó:
$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$
- Nếu $X_j$ hoàn toàn độc lập với các biến khác ($R_j^2 = 0$) $\implies \text{VIF}_j = 1$ (tối ưu).
- Nếu $R_j^2 = 0.90$ (90% biến thiên của $X_j$ đã bị các biến khác giải thích mất) $\implies \text{VIF}_j = \frac{1}{1 - 0.90} = 10$ (ngưỡng báo động đỏ: phương sai của hệ số ước lượng $\hat{\beta}_j$ bị phóng đại gấp 10 lần, làm hệ số nhảy loạn xạ).

#### B. Thủ thuật Tính VIF bằng Ma trận Tương quan (Không cần chạy $p$ mô hình hồi quy)
Trong **Step E3**, thay vì dùng vòng lặp chạy 9 mô hình OLS chậm chạp, một định lý chuẩn của đại số tuyến tính cho biết: Nếu gọi $\mathbf{R}$ là ma trận tương quan Pearson $(p \times p)$ giữa các biến, thì **các phần tử nằm trên đường chéo chính của ma trận nghịch đảo** $\mathbf{R}^{-1}$ **chính là** $\text{VIF}_j$:
$$\text{VIF}_j = (\mathbf{R}^{-1})_{jj}$$
Trong code B14, hàm `np.diag(np.linalg.pinv(R))` tính toàn bộ 9 giá trị VIF chỉ trong 1 dòng lệnh!

#### C. Bài học Kinh điển từ Kết quả E3 (Tại sao kiểm tra từng cặp $\rho_{ij}$ không phát hiện được?)
Trong kết quả Step E3 (*as of run 2026-11-11*):
- Khi kiểm tra từng cặp biến đơn lẻ (`B14_rel_redundant_pairs.csv`), **không có bất kỳ cặp biến nào có** $|r| > 0.80$ (**[Verify]** giá trị $|r|$ lớn nhất do cell E3 in ra chưa được ghi lại trong notebook — chạy lại và điền vào đây. Lưu ý $0.707$ của cặp `ltv_calc`–CLTV là hệ số **Spearman** ở E1, không phải Pearson của E3). Nếu chỉ nhìn ma trận tương quan cặp, ta sẽ tưởng không có đa cộng tuyến!
- Thế nhưng khi tính VIF, 3 biến nổ tung: `log_loan_amount` ($\text{VIF} = 84.16$), `log_lti` ($\text{VIF} = 63.81$), và `log_income` ($\text{VIF} = 36.24$)!
- **Tại sao?** Vì đây là **Đa cộng tuyến Cấu trúc 3 biến (Triangular Structural Identity)**:
  $$\text{LTI} = \frac{\text{Loan Amount}}{\text{Income} \times 1000} \implies \ln(\text{LTI}) = \ln(\text{Loan Amount}) - \ln(\text{Income}) - \ln(1000)$$
  Từng cặp 2 biến thì tương quan vừa phải, nhưng khi bỏ cả 3 biến vào chung một mô hình, biết 2 biến sẽ suy ra chính xác biến thứ 3 ($R^2 \approx 98.8\%$)! Tương tự với bộ ba $(\text{Loan Amount}, \text{Property Value}, \text{ltv\_calc})$.
- Nhờ phát hiện này, **Decision D-AF** khóa thiết kế mô hình: **Loại bỏ `log_lti`/`lti_bin` và `ltv_calc` khỏi mô hình chính**, chỉ giữ `log_loan_amount`, `income_decile` và `cltv_bin`!
- **[ADD v2] Lưu ý:** (i) Nếu đẳng thức cấu trúc đúng chính xác, VIF $= \infty$ (ma trận suy biến, nên code dùng `pinv`); giá trị hữu hạn $84.2$ xuất hiện vì các biến đã bị cắt ở p1/p99 (winsorise) chỉ cho phép chẩn đoán này. (ii) VIF chỉ áp dụng cho **khối biến số**; với các biến phân loại/bin (dti_cat, cltv_bin, income_decile) cần GVIF hoặc kiểm tra bằng Cramér's $V$. (iii) VIF thấp (CLTV $2.32$, DTI $1.53$) chỉ nói chúng không trùng lặp với biến khác, không nói chúng là biến kiểm soát hợp lệ.

---

### 3.4. Khoảng cách Trung bình Chuẩn hóa (Standardised Mean Difference — SMD / Love Plot) (Step E4)

#### A. Tại sao không dùng hiệu hai trung bình $\bar{X}_B - \bar{X}_W$?
Để biết biến kiểm soát nào (Thu nhập, DTI, CLTV, hay Tỷ lệ dân thiểu số của khu phố) khác biệt mạnh nhất giữa người vay Black và người vay White, ta không thể so sánh trực tiếp hiệu số trung bình $\bar{X}_B - \bar{X}_W$ vì mỗi biến có **đơn vị đo khác nhau** (USD, phần trăm, logarit).

#### B. Công thức SMD (Cohen's $d$ hai mẫu)
Trong **Step E4**, ta chia hiệu hai trung bình cho **Độ lệch chuẩn gộp (Pooled Standard Deviation)** để triệt tiêu đơn vị đo:
$$\text{SMD} = \frac{\bar{X}_g - \bar{X}_{\text{White}}}{\sqrt{\frac{s_g^2 + s_{\text{White}}^2}{2}}}$$
- $\text{SMD}$ đo khoảng cách bằng số lần "độ lệch chuẩn". Quy ước chuẩn trong kinh tế lượng và dịch tễ học: $|\text{SMD}| > 0.10$ là có sự **mất cân bằng có ý nghĩa (meaningful covariate imbalance)** giữa hai nhóm.
- **Kết quả nổi bật trong B14 (*Step E4*):** Giữa nhóm Black và White, biến lệch mạnh nhất không phải là thu nhập ($\text{SMD} = -0.334$) hay DTI ($\text{SMD} = +0.328$), mà là **Tỷ lệ dân số thiểu số của khu phố (`tract_minority_pct`**, $\text{SMD} = +1.116$) — trung bình người vay Black mua nhà ở khu phố có $57.99\%$ dân thiểu số, so với $30.45\%$ của người vay White!
- **[ADD v2] Cách đọc:** (i) SMD tính trên giá trị **hợp lệ** của từng biến (xem `pct_valid_group`), và dữ liệu thiếu mang thông tin. (ii) Ngưỡng $|0.1|$ là quy ước, [Hypothesis]. (iii) SMD cho thấy biến nào *có thể* thu hẹp khoảng cách, không chứng minh nó giải thích khoảng cách. Đặc biệt `tract_minority_pct` có thể là "bad control": nó phản ánh nơi cư trú — kênh có thể trùng với chính chủng tộc — nên việc có đưa vào mô hình hay không là quyết định thiết kế cần bàn riêng.

---

### 3.5. Univariate AUC thông qua Thống kê Hạng Mann-Whitney $U$ (Step E5)

- **Ý nghĩa của AUC (Area Under the ROC Curve):** Nếu bốc ngẫu nhiên 1 hồ sơ bị từ chối ($Y = 1$) và 1 hồ sơ được duyệt ($Y = 0$), $\text{AUC}$ chính là xác suất để biến $X$ của hồ sơ bị từ chối lớn hơn biến $X$ của hồ sơ được duyệt:
  $$\text{AUC} = P(X_{\text{denied}} > X_{\text{approved}})$$
  $\text{AUC} = 0.50$ là tung đồng xu (biến không có khả năng phân loại); $\text{AUC}$ càng gần $1.0$ (hoặc gần $0.0$ nếu ngược chiều) thì biến đó phân tách Đậu/Trượt càng mạnh. (Trong bảng `B14_rel_univariate_auc.csv`, cột `auc_oriented` lấy $\max(\text{AUC}, 1 - \text{AUC}) \in [0.5, 1.0]$ để xếp hạng độ mạnh bất kể chiều thuận hay nghịch).
- **Công thức tính siêu tốc không cần vẽ đường cong ROC (Định lý Mann-Whitney – Wilcoxon):**
  Thay vì chạy thuật toán phân ngưỡng ROC, **Step E5** xếp hạng toàn bộ $n = n_1 + n_0$ quan sát từ $1$ đến $n$ (với $n_1$ là số hồ sơ bị từ chối, $n_0$ là số hồ sơ được duyệt). Gọi $R_1 = \sum_{y_i = 1} \text{rank}(x_i)$ là tổng thứ hạng của các hồ sơ bị từ chối. Khi đó:
  $$\text{AUC} = \frac{R_1 - \frac{n_1(n_1 + 1)}{2}}{n_1 \cdot n_0}$$
  Công thức này cho kết quả chính xác tuyệt đối chỉ bằng một phép `.rank()` của Pandas! Kết quả cho thấy trong các biến liên tục, `dti_mid` có khả năng phân loại đơn biến mạnh nhất ($\text{AUC}_{\text{oriented}} = 0.683$), tiếp theo là `loan_amount` ($0.654$) và `income` ($0.642$).

---

## Phần 4. Kinh tế lượng Không gian & Cấu trúc Thị trường Cho vay (RQ3 — Phần F)

### 4.1. Đo lường Tập trung Thị trường: Chỉ số HHI, Đường cong Lorenz & Hệ số Gini (Step F6)

Để biết thị trường thế chấp Mỹ năm 2024 nằm trong tay vài "ông lớn" (Mega lenders) hay phân tán đều cho hàng ngàn ngân hàng nhỏ, **Step F6** sử dụng 2 công cụ kinh tế học công nghiệp chuẩn mực:

1. **Chỉ số Herfindahl-Hirschman Index (HHI):**
   Gọi $s_l = \frac{n_l}{N} \in [0, 1]$ là thị phần hồ sơ của tổ chức cho vay $l$ trong một thị trường (toàn quốc hoặc từng bang), với $\sum_{l=1}^K s_l = 1$. Chỉ số HHI (theo thang chuẩn của Bộ Tư pháp Mỹ - DOJ, nhân với $10,000$) là:
   $$\text{HHI} = 10,000 \times \sum_{l=1}^K s_l^2 \in \left[\frac{10,000}{K}, \; 10,000\right]$$
   - Nếu 1 ngân hàng độc quyền 100% thị trường ($s_1 = 1$) $\implies \text{HHI} = 10,000$.
   - Nếu hàng ngàn ngân hàng chia đều thị phần ($s_l \approx 0$) $\implies \text{HHI} \approx 0$. (Hướng dẫn sáp nhập **2010** dùng ngưỡng $1{,}500$ / $2{,}500$; Hướng dẫn sáp nhập DOJ/FTC **2023** hiện hành coi $\text{HHI} > 1{,}800$ là "highly concentrated" và suy đoán vi phạm khi HHI sau sáp nhập $> 1{,}800$ và tăng $> 100$. Các ngưỡng này dành cho thẩm định sáp nhập trên *thị trường được xác định*; ở đây "thị trường" là bang và thị phần là tỷ trọng hồ sơ HMDA, nên chỉ dùng làm thang tham khảo.) *[CHANGE v2: v1 dùng ngưỡng 2010]*
   - **Kết quả B14:** HHI toàn quốc là $100.4$ và trung vị HHI các bang là $214.9$ ($52/54$ bang có $\text{HHI} < 1,000$). Tại sao Top 100 ngân hàng nắm tới $61.31\%$ hồ sơ mà HHI vẫn thấp? Vì hàm bình phương $s_l^2$ phạt nặng sự độc quyền của 1–2 cá thể: ở Mỹ không có 1 ngân hàng nào chiếm tới $20\text{–}30\%$ thị trường, mà thị phần được chia cho khoảng 50–100 tổ chức lớn cạnh tranh nhau.

2. **Đường cong Lorenz & Hệ số Bất bình đẳng Gini (`gini_approx`):**
   - Sắp xếp $K = 4,808$ ngân hàng theo quy mô từ **nhỏ nhất đến lớn nhất**.
   - Trục hoành vẽ tỷ lệ cộng dồn số lượng ngân hàng $\left(\frac{1}{K}, \frac{2}{K}, \dots, 1\right)$; trục tung vẽ tỷ lệ cộng dồn số lượng hồ sơ (`cum`). Nếu mọi ngân hàng có quy mô bằng nhau, đường Lorenz là đường chéo $45^\circ$ (diện tích dưới đường chéo bằng $0.5$).
   - **Hệ số Gini** là tỷ số giữa diện tích phần võng xuống (giữa đường chéo $45^\circ$ và đường Lorenz) chia cho diện tích tam giác dưới đường chéo ($0.5$):
     $$\text{Gini} = \frac{0.5 - \int_0^1 L(x)\,dx}{0.5} = 1 - 2 \times \text{mean}(\text{cum})$$
   - Trong B14 (*Step F6*), $\text{Gini} \approx 0.878$ (rất sát $1.0$): $1\%$ ngân hàng lớn nhất ($48$ tổ chức) nắm giữ tới $50.60\%$ tổng số hồ sơ toàn nước Mỹ, trong khi một nửa số ngân hàng có quy mô dưới $166$ hồ sơ/năm!

---

### 4.2. Biểu đồ Phễu (Funnel Plot) & Hệ số Phân tán Quá mức (Overdispersion $\phi$) (Step F7)

#### A. Câu hỏi Phân tích tại Step F7
Khi vẽ tỷ lệ từ chối của $4,808$ ngân hàng, ta thấy có ngân hàng từ chối $4\%$, có ngân hàng từ chối $75\%$. Làm sao tách biệt được:
1. Ngân hàng có tỷ lệ cực đoan chỉ vì **cỡ mẫu của họ quá nhỏ** (nhiễu ngẫu nhiên nhị thức)?
2. Ngân hàng thực sự có tỷ lệ từ chối khác biệt hoàn toàn với mặt bằng chung của thị trường $p_0 = 24.62\%$?

#### B. Toán học của Đường Giới hạn Kiểm soát Hình Phễu (Binomial Control Limits)
Giả sử giả thuyết $H_0$ đúng: Mọi ngân hàng đều có chung một tỷ lệ từ chối nền của thị trường là $p_0 = 0.2462$, và sự khác biệt giữa các ngân hàng chỉ là sai số lấy mẫu ngẫu nhiên quanh $p_0$.
Khi đó, với một ngân hàng có quy mô $n_l$ hồ sơ, tỷ lệ từ chối mẫu $r_l = \frac{d_l}{n_l}$ của ngân hàng đó sẽ có độ lệch chuẩn lý thuyết là:
$$\text{SE}_0(n_l) = \sqrt{\frac{p_0 (1 - p_0)}{n_l}}$$
- Ở mức tin cậy $95\%$ ($z = 1.96$) và $99.8\%$ ($z = 3.09$), một ngân hàng chỉ do dao động ngẫu nhiên sẽ phải nằm trong **Đường bao hình phễu**:
  $$\text{Funnel Limit}(n) = p_0 \pm z \sqrt{\frac{p_0 (1 - p_0)}{n}}$$
- *Tại sao nó có hình cái phễu?* Vì khi quy mô ngân hàng $n$ nhỏ (bên trái trục hoành), $\sqrt{\frac{p_0(1-p_0)}{n}}$ lớn $\implies$ miệng phễu loe rộng. Khi quy mô ngân hàng $n$ lên tới hàng chục nghìn hồ sơ (bên phải trục hoành), $\text{SE}_0(n)$ tiến về $0$ $\implies$ cuống phễu thu hẹp sát vào đường $p_0 = 24.62\%$!

#### C. Điểm chuẩn hóa $z_l$ và Hệ số Phân tán Quá mức (Overdispersion Parameter $\phi$)
Với mỗi ngân hàng $l$, ta tính khoảng cách chuẩn hóa từ tỷ lệ của ngân hàng đó đến mức trung bình thị trường $p_0$:
$$z_l = \frac{r_l - p_0}{\sqrt{\frac{p_0 (1 - p_0)}{n_l}}}$$
Nếu các ngân hàng chỉ khác nhau do nhiễu lấy mẫu ngẫu nhiên, thì $z_l \sim \mathcal{N}(0, 1)$, tức là bình phương $z_l^2$ có kỳ vọng bằng $1$.
Do đó, trung bình cộng của $z_l^2$ trên $K_{\text{valid}} = 731$ ngân hàng đạt chuẩn D-M được gọi là **Hệ số Phân tán Quá mức (Overdispersion** $\phi$):
$$\phi = \frac{1}{K_{\text{valid}} - 1} \sum_{l=1}^{K_{\text{valid}}} z_l^2$$
- **Ý nghĩa:**
  - Nếu $\phi \approx 1$: Sự khác biệt giữa các ngân hàng 100% chỉ là nhiễu ngẫu nhiên.
  - **Kết quả thực tế trong B14 (*Step F7*):** $\phi = 2,014.6$, và có tới $86.5\%$ số ngân hàng nằm văng ra ngoài biên phễu $99.8\%$ ($|z_l| > 3.09$)!
  - **Cách diễn giải chuẩn mực tài chính (Decision D-O):** $\phi = 2,014.6$ chứng minh phương sai thực tế giữa các ngân hàng lớn gấp hơn $2,000$ lần phương sai ngẫu nhiên. Điều này khẳng định thị trường ngân hàng Mỹ **cực kỳ phân mảnh theo phân khúc (heterogeneous)**: mỗi ngân hàng phục vụ một tệp khách hàng khác nhau và chuyên môn hóa vào các dòng sản phẩm khác nhau (ví dụ ngân hàng chuyên cho vay mua nhà mới vs. ngân hàng chuyên cho vay HELOC/FHA), do đó ở Giai đoạn 4 của mô hình bắt buộc phải kiểm soát hiệu ứng cố định theo ngân hàng (Lender Fixed Effects) và **tuyệt đối không dùng tỷ lệ từ chối thô để kết luận một ngân hàng cụ thể phân biệt đối xử**.

---

#### D. [ADD v2] Lưu ý phương pháp cho Funnel Plot
- $\phi$ trong notebook tính từ $z_l$ **không winsorise**. Spiegelhalter (2005) khuyến nghị winsorise $z$ (ví dụ $10\%$) trước khi ước lượng hệ số phân tán để vài ngân hàng cực đoan không chi phối $\phi$.
- Với $\phi \approx 2{,}000$, đường giới hạn đặt quanh $p_0$ gần như vô nghĩa (hầu hết ngân hàng nằm ngoài). Hướng tự nhiên tiếp theo là mô hình **hiệu ứng ngẫu nhiên** (random effects) với phương sai giữa các ngân hàng $\tau^2$, hoặc fixed effects theo ngân hàng ở Giai đoạn 4.
- Chỉ $731 / 4{,}808$ ngân hàng qua D-M được dùng để tính $\phi$; $\approx 85\%$ ngân hàng không được diễn giải.
- Kết quả mô tả sự khác biệt giữa ngân hàng, **không** nói gì về chính sách của một ngân hàng cụ thể (Decision D-O).

## Bảng Tóm tắt Nhanh: Khi nào dùng Công cụ nào trong Báo cáo & Bảo vệ Đồ án?

| Câu hỏi của Giảng viên khi Bảo vệ (Defense) | Công cụ Toán / Analytics trong B14 | Vị trí Cell / Bảng Output | Câu trả lời Cốt lõi (Key Takeaway) |
|---|---|---|---|
| *"Tại sao nhóm không báo cáo $p$-value trong các bảng so sánh?"* | **P-Value Trap & Decision D-Q** ($\text{SE} \propto 1/\sqrt{N}$) | Section 0.1, Decision D-Q | Với $N = 8.14\text{M}$, $\text{SE} \approx 0.015\text{ pp}$, mọi chênh lệch nhỏ vô nghĩa đều cho $p \approx 0$. Nhóm dùng **Effect Size** (pp, RR, OR) + **Khoảng tin cậy (CI)**. |
| *"Tại sao dùng Wilson CI và Newcombe CI thay vì công thức $\hat{p} \pm 1.96\text{SE}$?"* | **Wilson Score CI** (đảo ngược Score Test bậc 2) & **Newcombe Hybrid CI** | Section 0.2 (`wilson_ci`), Step C4, Step F0 (`gap_vs_ref`) | Wald CI bị hỏng hoặc văng khỏi $[0, 100\%]$ khi $\hat{p}$ sát $0/1$ (như `preapproval=1` có $0$ ca từ chối) hoặc khi chia nhỏ ô theo bang/ngân hàng. Wilson & Newcombe luôn nằm trong $[0, 100\%]$ và giữ đúng độ bao phủ $95\%$. |
| *"Làm sao nhóm tính được Cluster Bootstrap trên 8.14 triệu dòng chỉ trong vài giây?"* | **Pre-aggregated Multinomial Matrix Bootstrap** ($\mathbf{W} \times \mathbf{N}$) | Step C1b (`B14_rq1_raw_gap.csv`) | Gom trước thành ma trận $(4808 \text{ ngân hàng} \times 7 \text{ chủng tộc})$, rồi nhân với ma trận trọng số Đa thức $(1000 \times 4808)$. CI thực tế rộng gấp **13.9–17.6 lần** Naive CI do tương quan nội cụm ngân hàng. |
| *"Tại sao nói khoảng cách của người vay Asian ($-0.16\text{ pp}$) là Nghịch lý Simpson?"* | **Simpson's Paradox & Kitagawa Decomposition** | Step C4 (`B14_rq1_stratified_gap.csv`), Step C5 (`B14_rq1_kitagawa.csv`) | Gộp chung là $-0.16\text{ pp}$. Ba phân tích khác nhau cần trích riêng: (C3) Asian có $62.1\%$ hồ sơ là mua nhà; (C4, tầng purpose × type) $10/11$ tầng hợp lệ có gap dương; (C5, tầng 4 chiều sản phẩm) Composition $= -3.71\text{ pp}$, Rate $= +3.56\text{ pp}$. *[CHANGE v2: v1 gộp ba kết quả này vào một câu]* |
| *"Phân rã Kitagawa cho biết sản phẩm và tài chính giải thích được bao nhiêu phần của khoảng cách Black–White $+14.88\text{ pp}$?"* | **Kitagawa Accounting Identity** & Quy tắc `low_reliability` (**D-U, D-X**) | Step C5 (`B14_rq1_kitagawa.csv`), Step G2 (`B14_rq4_missing_handling.csv`) | - Cơ cấu sản phẩm (C5) không giải thích được mà còn làm giảm gap ($-1.19\text{ pp}$).<br>- Cơ cấu tài chính thô (G2b) giải thích được $+3.92\text{ pp}$ ($26.35\%$), còn lại $+10.96\text{ pp}$ ($73.65\%$) là Rate Effect nội tầng.<br>- Khi chia tầng quá mịn (D4, F8), $> 10\%$ dữ liệu rơi vào tầng gộp nên phải gắn cờ `low_reliability`. |
| *"Tại sao không đưa cả Loan Amount, Income và LTI vào cùng một mô hình?"* | **VIF** qua đường chéo nghịch đảo ma trận tương quan $\text{diag}(\mathbf{R}^{-1})$ | Step E3 (`B14_rel_vif.csv`), Decision D-AF | Tương quan cặp $\lvert r \rvert \le 0.8$ không phát hiện được, nhưng $\ln(\text{LTI}) = \ln(\text{Loan}) - \ln(\text{Income})$ tạo đa cộng tuyến 3 biến làm VIF nổ lên **84.2 / 63.8 / 36.2**. |
| *"OR = 2.07 có nghĩa người Black bị từ chối gấp đôi?"* | **RR vs OR** & non-collapsibility | Step C1a (`B14_rq1_raw_gap.csv`) | Không. Xác suất gấp $\approx 1.68$ lần (RR); odds gấp $\approx 2.07$ lần (OR). OR lớn hơn RR vì biến cố phổ biến ($\approx 24.6\%$). Khi thêm biến kiểm soát, theo dõi cả pp lẫn OR. |
| *"CI Newcombe theo bang/ngân hàng có tính đến phân cụm không?"* | **Naive vs Cluster CI** | Step C1b vs Step C4, F1, F9, G5 | Không. Chỉ khoảng cách tổng thể ở C1b có Cluster CI; các CI Newcombe là naive và quá hẹp. |

---

## Nhật ký thay đổi (v2) — theo Convention 5.4

| Loại | Vị trí | Nội dung |
|---|---|---|
| [CHANGE] | §1.1B | Ví dụ $p$-value dùng SE của hiệu hai nhóm ($0.059\text{ pp}$), không dùng SE một mẫu |
| [CHANGE] | §1.1C | Biên độ sai số D-M: $\pm 2.67\text{ pp}$ chỉ tại $p = 24.6\%$; tối đa $\approx \pm 3.1\text{ pp}$ |
| [CHANGE] | §2.1 | $60.47\% = 39.93 + 13.37 + 7.17$ (thêm First-lien other purpose); bỏ "100%" và "chứng minh … FICO" (gắn [Hypothesis]); tách ba phân tích Asian |
| [CHANGE] | §2.2C | $10 \times 10 \times 12 = 1{,}200$ (1,149 là số tầng có dữ liệu); $0.82\%$ của Black gắn [Verify]; D-AG gắn [Verify] |
| [CHANGE] | §3.1 | Bỏ khẳng định "100 tỷ USD" (gắn [Verify]); sửa ký tự lỗi |
| [CHANGE] | §3.2 | So sánh cùng thước đo ($V$ với $V$) |
| [CHANGE] | §3.3C | "0.71" là Spearman E1, không phải Pearson E3 (gắn [Verify]) |
| [CHANGE] | §4.1 | Ngưỡng HHI cập nhật theo Hướng dẫn sáp nhập 2023 |
| [CHANGE] | Toàn file | Bỏ số cell (đã lỗi thời), chỉ dùng tên Step |
| [ADD] | §1.3, §1.4, §1.5, §2.2 (B2), §2.3, §3.1–3.4, §4.2 (D), bảng tóm tắt | Cạm bẫy OR, CI naive, giới hạn bootstrap/Kitagawa/Spearman/VIF/SMD/MI/funnel, 2 dòng FAQ |
| [VERIFY] | $d_0, d_1$; max `income`; $\lvert r \rvert$ lớn nhất của E3; pooled share của Black ở C5; D-AG | Cần đối chiếu với output thật sau khi chạy lại notebook |
