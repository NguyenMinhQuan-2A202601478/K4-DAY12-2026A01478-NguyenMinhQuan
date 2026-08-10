# Phiếu Phản Ánh — K4 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> *Câu trả lời của bạn*` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Nguyễn Minh Quân  Mã học viên: ..........................

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Nếu `api_token` có mặc định `"changeme"`: khi deploy lên Railway/Render mà
> quên set biến `API_TOKEN`, app vẫn khởi động và chạy bình thường, chấp nhận
> mọi request gửi `Bearer changeme`. Vì đây là giá trị đoán được, bất kỳ ai
> (hoặc bot quét) cũng gọi được `/chat` miễn phí bằng chi phí LLM của mình, và
> mình chỉ phát hiện ra khi nhìn hoá đơn cuối tháng. Với thiết kế hiện tại
> (không mặc định), thiếu `API_TOKEN` làm `pydantic-settings` ném
> `ValidationError` ngay lúc khởi động — container crash, health check fail,
> deploy đỏ ngay trong log, trong khi mình còn đang ngồi nhìn màn hình chứ
> không phải một tháng sau.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Dòng log thật lấy được khi chạy service cục bộ và gọi `/chat`:
> ```json
> {"event": "chat_completed", "severity": "INFO", "ts": "2026-08-10T13:07:42.460543+00:00", "client_id": "sv-demo", "prompt_tokens": 3, "completion_tokens": 41, "usd_cost": 2.505e-05}
> ```
> Hai việc làm được mà `print("đã trả lời xong")` không làm được:
> 1. Lọc/tổng hợp theo trường: `grep '"client_id":"X"'` hoặc filter trên
>    Cloud Logging để trả lời "client nào tốn tiền nhất hôm nay" bằng cách
>    cộng dồn `usd_cost` — với print thì không có trường nào để cộng.
> 2. Alert theo `severity` (viết hoa để khớp quy ước Google Cloud Logging) —
>    dashboard có thể tự tô đỏ/cảnh báo khi thấy `"severity":"ERROR"` tăng
>    đột biến, còn chuỗi tự do thì máy không phân biệt được "lỗi" với
>    "thông báo bình thường".

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1700 MB |
| Multi-stage | 270 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Số đo thật lấy từ `docker images` sau khi build cả hai bản: bản 1-stage
> (dựng lại đúng như mô tả trong LAB_GUIDE: `python:3.11` đầy đủ, chạy root,
> `COPY . .` trước `pip install`) nặng **1.7GB**; bản multi-stage hiện tại
> nặng **270MB**. Chênh lệch ~1.43GB chủ yếu là: (1) base image `python:3.11`
> đầy đủ mang theo compiler (gcc), header dev, apt cache, docs — thứ runtime
> không bao giờ dùng tới; (2) bản 1-stage giữ luôn cache pip và toàn bộ
> source đã `COPY . .`. Bản multi-stage chỉ `COPY --from=builder /install
> /usr/local` — tức chỉ mang theo *kết quả cài đặt*, còn cả stage `builder`
> (compiler, cache pip) bị vứt bỏ hoàn toàn, không lọt vào image cuối.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Sửa 1 dòng `app/main.py` rồi build lại, log build thật cho thấy:
> - **Cache lại**: `WORKDIR /build`, `COPY requirements.txt .`,
>   `RUN pip install...` (stage builder), `WORKDIR /app`,
>   `COPY --from=builder /install /usr/local` — tất cả `CACHED`.
> - **Chạy lại**: `COPY app ./app`, `COPY utils ./utils`, và
>   `RUN useradd...chown -R appuser /app` (chạy lại vì nó đụng tới `/app`
>   vừa đổi).
>
> Nếu đặt `COPY . .` lên **trước** `RUN pip install`: layer `COPY . .` sẽ
> đổi hash mỗi lần sửa dù chỉ 1 ký tự, và theo cơ chế cache-theo-thứ-tự của
> Docker, mọi layer **sau** nó (kể cả `pip install`) bị coi là invalid theo,
> dù `requirements.txt` không hề đổi. Kết quả: mỗi lần sửa code là cài lại
> toàn bộ thư viện từ đầu — vài giây build thành vài phút.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện: một lỗ hổng trong code Python (vd: deserialize dữ liệu
> không kiểm soát, dependency có RCE, hay lệnh shell nối chuỗi không escape)
> cho attacker chạy được mã tuỳ ý bên trong tiến trình. Vì container mặc
> định chạy `root`, tiến trình đó *đã là root* ngay bên trong container — có
> quyền ghi mọi file, cài package, đọc mọi biến môi trường/secret của
> container. Nếu container có thêm một điều kiện phụ (mount `docker.sock`,
> chạy `--privileged`, hoặc lỗ hổng kernel container-escape), root-trong-
> container leo tiếp thành root-trên-host. Lệnh `USER appuser` cắt đứt chuỗi
> ngay ở bước đầu: kể cả attacker chạy được mã, tiến trình đó chỉ có quyền
> của `appuser` — không ghi được ngoài `/app`, không cài được package hệ
> thống, không đủ capability để khai thác hầu hết đường escape cần root.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

> `WWW-Authenticate: Bearer` bắt buộc theo RFC 7235/6750: đó là cách chuẩn
> để client (browser, SDK, công cụ generic) biết *phải xác thực bằng scheme
> nào* mà không cần đọc tài liệu riêng của từng API — một mã 401 trần trụi
> không nói được điều đó. Trả cùng một thông báo lỗi cho cả 3 trường hợp
> (thiếu header / sai scheme / sai token) vì nếu phân biệt rõ, kẻ dò token sẽ
> được cấp thông tin miễn phí: "scheme của mày đúng rồi, chỉ còn token sai"
> giúp họ thu hẹp không gian brute-force xuống một chiều duy nhất. Thông báo
> mơ hồ buộc họ phải đoán mù trên mọi chiều cùng lúc — đúng người dùng hợp lệ
> thì đã biết cách gọi đúng ngay từ tài liệu, không cần API tự "gợi ý".

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

> Với `capacity=10`, `refill_per_minute=10` (0.1667 token/giây):
> - **Có `min(capacity, ...)`**: dù im lặng bao lâu, xô chỉ đầy tối đa 10
>   token. Client gửi liên tiếp: 10 request đầu (`available` từ 10 xuống 0)
>   đều 200, request thứ **11 bị 429**.
> - **Bỏ `min(...)`**: nếu trước khi im lặng xô đã đầy ở 10 (trường hợp thực
>   tế — client mới hoặc vừa nghỉ), sau 10 phút (600 giây) không dùng, token
>   cộng dồn thêm `600 × 0.1667 ≈ 100`, tổng **≈110 token** không bị chặn
>   trần. Client bắn liên tiếp sẽ được **110 request** thành công trước khi
>   bị 429 ở request thứ 111 — gấp 11 lần hạn mức thiết kế. Đây chính là lỗ
>   hổng mà docstring trong `rate_limiter.py` cảnh báo: im lặng cả ngày sẽ
>   tích được ~14.400 token và xả hết trong một giây.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

> Cùng một sự cố khiến client gọi liên tục từ 2h sáng, so sánh hai cách:
> - **$30/tháng**: thiệt hại tối đa = toàn bộ $30 (không có gì chặn cho tới
>   khi chạm mốc đó), và vì hạn mức chỉ reset **1 lần/tháng**, một khi đã bị
>   chặn thì service **bị khoá tới hết tháng** — hôm sau sự cố được fix
>   nhưng client đó vẫn không gọi được tới kỳ reset kế tiếp, tự tạo thêm một
>   sự cố "tự đóng băng" kéo dài hàng chục ngày.
> - **$1/ngày**: thiệt hại tối đa = $1 cho lần sự cố đó (dù chạy suốt đêm,
>   `check()` chặn ngay khi vượt), và vì key Redis theo
>   `spend:<client>:<YYYY-MM-DD>`, sang 0h UTC là **tự động reset** — sáng
>   hôm sau service phục vụ lại bình thường mà không ai phải can thiệp
>   thủ công.
>
> Ngân sách ngày giới hạn thiệt hại xuống 1/30 và tự hồi phục nhanh hơn
> nhiều so với ngân sách tháng.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu gộp `/healthz` và `/readyz` thành một endpoint có kiểm tra Redis, với
> cụm 3 container khi Redis mất kết nối 30 giây, thứ tự sự kiện sẽ là:
> 1. Redis rớt kết nối.
> 2. Ở lượt probe kế tiếp (chu kỳ ~30s theo cấu hình healthcheck), **cả 3
>    container** cùng gọi Redis, cùng fail → endpoint gộp trả 503 **đồng
>    loạt trên cả 3**.
> 3. Vì endpoint này giờ vừa đóng vai liveness vừa readiness, orchestrator
>    hiểu 503 là "process chết, cần restart" (đúng lẽ ra chỉ nên "ngừng gửi
>    traffic") → **restart cả 3 container cùng lúc**.
> 4. Trong lúc cả 3 đang restart/khởi động lại, **không còn container nào
>    phục vụ** — mất trắng dịch vụ trong khoảng thời gian này, thay vì chỉ
>    độ trễ nhỏ khi failover.
> 5. 30 giây sau Redis hồi phục, nhưng 3 container vẫn đang trong chu trình
>    khởi động lại/vượt qua `start_period`, nên downtime thực tế **dài hơn**
>    chính sự cố Redis ban đầu.
>
> Đây đúng là lý do lab tách riêng: `/healthz` (không phụ thuộc gì, quyết
> định restart) và `/readyz` (kiểm tra Redis, chỉ quyết định có nhận traffic
> hay không).

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Lỗi gặp phải khi deploy lên Railway: health check timeout dù build và
> start container thành công. `railway.toml` bản đầu của mình có dòng
> `startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"` để
> ghi đè `CMD` của Dockerfile. Nguyên nhân: khi Railway chạy một
> `startCommand` ghi đè trên image Docker, nó thực thi ở dạng *exec* (không
> qua shell), nên `$PORT` không được shell expand mà bị coi là chuỗi ký tự
> `$PORT` theo đúng nghĩa đen — uvicorn cố bind vào một "port" không hợp lệ,
> nên container không bao giờ thực sự mở cổng và healthcheck `/healthz` cứ
> timeout dù process không hề crash. Mình tìm ra bằng cách xem `railway logs`
> và so sánh với cách Dockerfile tự chạy `CMD ["sh", "-c", "uvicorn ... --port
> ${PORT:-8000}"]` — `sh -c` mới là thứ expand được `${PORT:-8000}`, còn
> `startCommand` của Railway thì không. Sửa bằng cách xoá hẳn `startCommand`
> khỏi `railway.toml`, để Railway dùng đúng `CMD` có sẵn trong Dockerfile
> (chạy qua `sh -c` nên `$PORT` được expand đúng).
