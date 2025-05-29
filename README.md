# Activate python environment
```
source /software-testing-final-project/backend/venv/bin/activate
```
# Proxy settings
## Nginx
```
sudo vim /etc/nginx/sites-available/apply
sudo nginx -t
sudo systemctl reload nginx
```
## OpenResty + Lua 驗證 JWT
### 1️⃣ 安裝 OpenResty（支援 Lua）
Ubuntu 安裝：
```
sudo apt install software-properties-common
sudo add-apt-repository -y ppa:openresty/ppa
sudo apt update
sudo apt install openresty
```
```
sudo vim /usr/local/openresty/nginx/conf/nginx.conf
sudo /usr/local/openresty/nginx/sbin/nginx -p /usr/local/openresty/nginx/ -c conf/nginx.conf

sudo lsof -i :80
sudo systemctl stop nginx
sudo /usr/local/openresty/nginx/sbin/nginx -s stop
sudo /usr/local/openresty/nginx/sbin/nginx -s reload

```
### 2️⃣ 安裝 Lua JWT 套件
```
luarocks install lua-resty-jwt
```

# 傳藝推薦
## 套件管理推薦
peotry, uv
## 測試相關
unittest

# Run service
```
uvicorn main:app --host 0.0.0.0 --port 8005
```

## OpenAPI
描述有什麼endpoint、需要什麼參數、回傳什麼資料
```
http://localhost:8005/openapi.json
```
## Swagger UI
可以直接在這個介面測試endpoint
```
http://localhost:8005/docs
```
## ReDoc
```
http://localhost:8005/redoc
```

# Testing
```
pip install pytest httpx pytest-cov
cd software-testing-final-project/backend/apply_service
pytest tests/
```
## Converage report
```
pytest --cov=routers --cov-report=term-missing tests/
# 以HTML展示
pytest --cov=routers --cov-report=html tests/

```


# Note
## Microservices Architecture
將 applications 分成一組小型、自治的服務，每個服務負責處理一個具體功能。這些服務可以獨立開發、部署、擴展和更新，並且每個服務通常都有自己的資料庫。

## TDD
* Test-Driven Development 測試驅動開發
* 一種開發方法，通過先寫測試案例來驅動程式碼的實現。這樣可以幫助開發者更好地理解需求，並確保程式碼是可靠且可維護的。

### 步驟
1. 確定需求和功能
2. 編寫測試
3. 程式碼實現
4. 持續測試與重構

## Apply
本服務是負責處理「申請表單」的微服務，包含建立、查詢、更新、刪除申請資料。
目前資料使用**模擬資料庫（in-memory dictionary）**儲存，尚未接正式資料庫。
### API
| API                           | 方法   | 功能說明                     |
|-------------------------------|--------|------------------------------|
| /                             | POST   | 建立新的申請表單             |
| /                             | GET    | 查詢所有申請表單             |
| /{application_id}             | GET    | 依 ID 查詢單一申請表單       |
| /{application_id}             | PUT    | 依 ID 更新申請表單內容       |
| /{application_id}             | DELETE | 依 ID 刪除申請表單           |
| /apply/{application_id}/approve | PUT    | 核准申請，並（未來）啟動付款流程 |

### 內部狀態：
* Pending（待處理）：用戶提交申請後，系統會將其狀態設為 Pending，表示該申請尚未開始處理。

* Under Review（審核中）：當申請被系統或審核人員審查時，狀態可以是 Under Review，表示正在進行審核或資料檢查。

* Approved（已批准）：當申請被審核通過並且所有條件滿足時，狀態變為 Approved，即已批准，申請進入下一步。也許要去繳費(?)

* Rejected（已拒絕）：如果申請未通過審核，狀態可以變為 Rejected，並附上拒絕原因。

* Completed（已完成）：當申請完成（例如，支付已經處理完畢，或者服務已經提供）時，狀態可以設為 Completed。

* Canceled（已取消）：如果用戶或系統中斷了申請流程，可以設為 Canceled。

### 與繳費的狀態
* Pending（待處理）：還沒繳費
* Successful(成功)：繳費成功
* Failed(失敗)：某些原因所以失敗了(e.g.逾期)
* Canceled（已取消）：中斷申請流程

# Docker
## Rebuild
```
docker stop data-apply-1 && docker rm data-apply-1
docker build -t data-apply .

docker run -d \
  --name data-apply-1 \
  -p 8002:8000 \
  --network data_app-network \
  --restart unless-stopped \
  -e DATABASE_URL=mysql://user:password@db:3306/appdb \
  data-apply

docker exec -it data-apply-1 python3 -c "import mysql.connector; print('OK')"

sudo docker exec -it data-apply-1 bash
sudo docker-compose logs data-apply

```

```
curl -X GET http://localhost/apply/my-applications -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IjMxMzU4MTAxNyIsImVtYWlsIjoieXV4dW4uaWkxM0BueWN1LmVkdS50dyIsInJvbGUiOiJzdHVkZW50IiwiZXhwIjoxNzQ4NDMwMTg5fQ.HDwtyQmfxoQZwBlhbx0hP-XY9FYAjkSQrBMtQA548o0"
```