# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị token vào đây.**
> Repo này công khai — dán token vào là mất token.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Nguyen Minh Quan |
| Mã học viên | 2026A01478 |
| Repo | https://github.com/NguyenMinhQuan-2A202601478/K4-DAY12-2026A01478-NguyenMinhQuan |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://day12-chat-production-8e49.up.railway.app |
| Platform | Railway |
| Ngày deploy | 2026-08-10 |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | platform tự gán |
| `API_TOKEN` | ✅ | đặt trong dashboard, không nằm trong repo |
| `REDIS_URL` | ✅ | Railway Redis service qua reference variable |
| `BUCKET_CAPACITY` | ✅ | 10 |
| `REFILL_PER_MINUTE` | ✅ | 10 |
| `DAILY_BUDGET_USD` | ✅ | 1.0 |
| `LOG_LEVEL` | ✅ | INFO |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i <URL>/healthz

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i <URL>/readyz

# 3. Không có token — mong đợi 401 kèm header WWW-Authenticate
curl -i -X POST <URL>/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'

# 4. Có token — mong đợi 200 kèm câu trả lời
curl -i -X POST <URL>/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "X-Client-Id: sv-test" \
  -d '{"message":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "X-Client-Id: sv-test" \
    -d '{"message":"test"}'
done; echo
```

## Kết Quả Chạy Thật

Dán output của các lệnh trên vào đây:

```
GET /healthz
HTTP 200
{"status":"ok","service":"day12-chat-service","version":"1.0.0"}

GET /readyz
HTTP 200
{"status":"ready","redis":true}

POST /chat không gửi Authorization header
HTTP 401
WWW-Authenticate: Bearer
{"detail":"invalid or missing bearer token"}

POST /chat có token đúng
HTTP 200
{"reply":"Ngắn gọn: Deploy la gi phụ thuộc vào ba yếu tố — cấu hình qua biến môi trường, health check để orchestrator biết trạng thái, và giới hạn tài nguyên.","client_id":"sv-test","turns_before":0,"usd_cost":2.265e-05,"usage":{"prompt":3,"completion":37}}

POST /chat gọi liên tiếp 15 lần (rate limit)
200 200 200 200 200 200 200 200 200 429 429 429 429 200 429
```

9 request đầu tiên qua được (bucket_capacity=10, tính cả token dùng cho lần
test #4 trước đó nên xô còn 9). Sau đó bị 429 liên tục — nhưng có 1 request
"200" lọt vào giữa dãy 429 (vị trí thứ 14): vì mỗi request tốn thời gian
round-trip qua mạng thật tới Railway, đủ để xô kịp nạp lại đúng 1 token
(refill_per_minute=10 → ~0.167 token/giây) trước khi request đó tới. Đây là
bằng chứng token bucket đang hoạt động đúng thời gian thực, không phải hiện
tượng ngẫu nhiên.

## Ảnh Chụp Màn Hình

- `screenshots/dashboard.jpg` — trang quản lý service trên Railway (2 service: `day12-chat`, `day12-chat-redis`, đều Online)
- `screenshots/healthz.jpg` — kết quả gọi `/healthz` từ trình duyệt trên URL production
