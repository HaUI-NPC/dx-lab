#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

# Kịch bản kiểm thử E2E qua APISIX Gateway (:9080/api) bằng curl (TEST-02).
# Thực hiện toàn bộ chu trình xử lý sự cố lab-repair: báo hỏng -> khảo sát -> xác nhận -> duyệt chi phí -> sửa chữa -> nghiệm thu -> tìm kiếm.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Nạp cấu hình từ .env nếu có
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

API_URL="${DXLAB_API_URL:-http://localhost:9080/api}"
API_URL="${API_URL%/}"
ISSUER="${DXLAB_OIDC_ISSUER:-http://localhost:8180/realms/dxlab}"
ISSUER="${ISSUER%/}"
DEMO_PASSWORD="${DXLAB_DEMO_PASSWORD:-}"
DEMO_OTP_SECRET="${DXLAB_DEMO_OTP_SECRET:-}"
CLIENT_ID="${DXLAB_CLI_CLIENT_ID:-dxlab-cli}"

# Màu thông báo terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_step() {
  echo -e "\n${BLUE}==>${NC} ${GREEN}$1${NC}"
}

log_info() {
  echo -e "    ${YELLOW}*${NC} $1"
}

log_error() {
  echo -e "    ${RED}ERROR:${NC} $1" >&2
}

# Sinh mã TOTP 6 số theo RFC 6238 từ DEMO_OTP_SECRET
gen_totp() {
  python3 -c "
import hashlib, hmac, os, struct, time
secret = os.environ.get('DEMO_OTP_SECRET', '')
if not secret:
    print('')
    exit(0)
counter = int(time.time() // 30)
digest = hmac.new(secret.encode('utf-8'), struct.pack('>Q', counter), hashlib.sha1).digest()
offset = digest[-1] & 0x0F
code = (struct.unpack('>I', digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
print(f'{code:06d}')
"
}

# Lấy Bearer token của tài khoản demo qua Keycloak Direct Grant
get_token() {
  local user="$1"
  local totp_code
  totp_code="$(DEMO_OTP_SECRET="$DEMO_OTP_SECRET" gen_totp)"

  local response
  local http_code
  local body

  for attempt in 1 2; do
    response="$(curl -s -w "\n%{http_code}" -X POST "${ISSUER}/protocol/openid-connect/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "client_id=${CLIENT_ID}" \
      --data-urlencode "grant_type=password" \
      --data-urlencode "username=${user}" \
      --data-urlencode "password=${DEMO_PASSWORD}" \
      --data-urlencode "totp=${totp_code}")"

    http_code="$(echo "$response" | tail -n1)"
    body="$(echo "$response" | sed '$d')"

    if [ "$http_code" -eq 200 ]; then
      echo "$body" | jq -r .access_token
      return 0
    fi

    # Nếu Keycloak từ chối do trùng TOTP trong cửa sổ 30s, đợi sang chu kỳ tiếp theo
    if [ "$http_code" -eq 400 ] && [ "$attempt" -eq 1 ]; then
      local wait_sec
      wait_sec=$(( 31 - ($(date +%s) % 30) ))
      log_info "Keycloak từ chối TOTP của ${user}, đợi ${wait_sec}s sang chu kỳ mới..." >&2
      sleep "$wait_sec"
      totp_code="$(DEMO_OTP_SECRET="$DEMO_OTP_SECRET" gen_totp)"
      continue
    fi
  done

  log_error "Không thể lấy token cho ${user}: HTTP ${http_code} - ${body}"
  exit 1
}

# Gọi API qua APISIX Gateway: api_call <METHOD> <PATH> <TOKEN> [JSON_DATA] [EXPECTED_HTTP_CODE]
api_call() {
  local method="$1"
  local path="$2"
  local token="$3"
  local data="${4:-}"
  local expected="${5:-200}"

  local url="${API_URL}${path}"
  local response
  local http_code
  local body

  if [ -n "$data" ]; then
    response="$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
      -H "Authorization: Bearer ${token}" \
      -H "Content-Type: application/json" \
      -d "$data")"
  else
    response="$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
      -H "Authorization: Bearer ${token}")"
  fi

  http_code="$(echo "$response" | tail -n1)"
  body="$(echo "$response" | sed '$d')"

  if [ "$http_code" -ne "$expected" ]; then
    log_error "${method} ${path} mong đợi HTTP ${expected} nhưng nhận ${http_code}:"
    echo "$body" | jq . 2>/dev/null || echo "$body" >&2
    exit 1
  fi

  LAST_BODY="$body"
  LAST_HTTP_CODE="$http_code"
}

TODAY="$(date +%Y-%m-%d)"

log_step "Bước 0: Kiểm tra trạng thái hệ thống qua APISIX (Health check)"
HEALTH_RESP="$(curl -s -w "\n%{http_code}" "${API_URL}/health")"
HEALTH_CODE="$(echo "$HEALTH_RESP" | tail -n1)"
HEALTH_BODY="$(echo "$HEALTH_RESP" | sed '$d')"
if [ "$HEALTH_CODE" -ne 200 ]; then
  log_error "GET /health thất bại: HTTP ${HEALTH_CODE} - ${HEALTH_BODY}"
  exit 1
fi
log_info "APISIX Gateway và Core API hoạt động bình thường: $(echo "$HEALTH_BODY" | jq -r .status)"

log_step "Bước 1: Sinh viên (sv.an) báo hỏng điều hòa qua APISIX"
TOKEN_SV="$(get_token "sv.an")"
REPORT_DATA=$(cat <<EOF
{
  "app_id": "lab-repair",
  "data": {
    "room_id": "lab-a1-305",
    "asset_id": "TS-2024-0005",
    "asset_category": "air_conditioner",
    "issue_title": "[E2E] Điều hòa A1-305 chảy nước",
    "issue_description": "Điều hòa âm trần nhỏ nước xuống bàn máy, làm lạnh kém.",
    "urgency": "normal",
    "impact": "single",
    "safety_hazard": false,
    "data_processing_consent": true,
    "consent_notice_version": "v1.0",
    "reporter_name": "Nguyễn Văn An",
    "reporter_id": "SV2024001",
    "reporter_phone": "0912000001",
    "reporter_email": "sv.an@dx-lab.example"
  }
}
EOF
)
api_call "POST" "/workflows" "$TOKEN_SV" "$REPORT_DATA" 201
WORKFLOW_ID="$(echo "$LAST_BODY" | jq -r .id)"
STATUS_1="$(echo "$LAST_BODY" | jq -r .status)"
log_info "Phiếu tạo thành công: ID = ${WORKFLOW_ID}"
log_info "DMN tự động phân loại & định tuyến: Trạng thái = ${STATUS_1}"
if [ "$STATUS_1" != "pending_assessment" ]; then
  log_error "Trạng thái mong đợi 'pending_assessment', thực tế: '${STATUS_1}'"
  exit 1
fi

log_step "Bước 2: Kỹ thuật viên CSVC (ktv.dung) khảo sát hiện trạng & lập dự toán"
TOKEN_KTV="$(get_token "ktv.dung")"
api_call "GET" "/tasks?workflow_id=${WORKFLOW_ID}" "$TOKEN_KTV" "" 200
TASK_ID_2="$(echo "$LAST_BODY" | jq -r '.items[0].id')"
log_info "Nhận việc từ hộp việc kỹ thuật: Task ID = ${TASK_ID_2}"

ASSESSMENT_DATA=$(cat <<EOF
{
  "data": {
    "technician_name": "Phạm Thị Dung",
    "inspection_date": "${TODAY}",
    "fault_cause": "Ống thoát nước ngưng bị tắc, dàn lạnh bám bụi dày",
    "action_type": "repair",
    "assessment_result": "needs_cost",
    "is_emergency": false,
    "estimated_cost_vnd": 3500000,
    "technician_recommendation": "Cần thông tắc đường ống nước thải và bổ sung gas lạnh.",
    "quotes": [
      {
        "supplier_name": "Công ty TNHH Thiết bị Trường học Hà Nội (giả định)",
        "quote_amount_vnd": 3500000,
        "quote_reference": "BG-2026-E2E",
        "quote_date": "${TODAY}"
      }
    ],
    "quote_count": 1
  }
}
EOF
)
api_call "POST" "/tasks/${TASK_ID_2}/complete" "$TOKEN_KTV" "$ASSESSMENT_DATA" 200
STATUS_2="$(echo "$LAST_BODY" | jq -r .status)"
log_info "Khảo sát hoàn tất: Trạng thái chuyển sang '${STATUS_2}'"
if [ "$STATUS_2" != "awaiting_endorsement" ]; then
  log_error "Trạng thái mong đợi 'awaiting_endorsement', thực tế: '${STATUS_2}'"
  exit 1
fi

log_step "Bước 3: Trưởng phòng lab (tl.giang) xác nhận nhu cầu sửa chữa"
TOKEN_TL="$(get_token "tl.giang")"
api_call "GET" "/tasks?workflow_id=${WORKFLOW_ID}" "$TOKEN_TL" "" 200
TASK_ID_3="$(echo "$LAST_BODY" | jq -r '.items[0].id')"
log_info "Nhận việc từ hộp việc trưởng lab: Task ID = ${TASK_ID_3}"

CONFIRM_DATA=$(cat <<EOF
{
  "data": {
    "lab_manager_name": "Hoàng Thu Giang",
    "confirm_date": "${TODAY}",
    "need_confirmed": true,
    "urgency_level": "normal",
    "replacement_procurement_requested": false,
    "manager_comment": "Xác nhận nhu cầu sửa chữa phục vụ kỳ thi thực hành sắp tới."
  }
}
EOF
)
api_call "POST" "/tasks/${TASK_ID_3}/complete" "$TOKEN_TL" "$CONFIRM_DATA" 200
STATUS_3="$(echo "$LAST_BODY" | jq -r .status)"
log_info "Xác nhận nhu cầu thành công: Trạng thái chuyển sang '${STATUS_3}'"
if [ "$STATUS_3" != "awaiting_approval" ]; then
  log_error "Trạng thái mong đợi 'awaiting_approval', thực tế: '${STATUS_3}'"
  exit 1
fi

log_step "Bước 4: Trưởng khoa (tk.hai) phê duyệt chi phí (xác thực 2 bước OTP)"
TOKEN_TK="$(get_token "tk.hai")"
api_call "GET" "/tasks?workflow_id=${WORKFLOW_ID}" "$TOKEN_TK" "" 200
TASK_ID_4="$(echo "$LAST_BODY" | jq -r '.items[0].id')"
log_info "Nhận việc từ hộp việc cấp duyệt: Task ID = ${TASK_ID_4}"

APPROVAL_DATA=$(cat <<EOF
{
  "data": {
    "approver_name": "Vũ Đức Hải",
    "approver_role": "faculty_head",
    "signing_type": "direct",
    "decision": "approved",
    "approved_amount_vnd": 3500000,
    "approval_date": "${TODAY}",
    "approval_comment": "Đồng ý phê duyệt phương án và kinh phí sửa chữa."
  }
}
EOF
)
api_call "POST" "/tasks/${TASK_ID_4}/complete" "$TOKEN_TK" "$APPROVAL_DATA" 200
STATUS_4="$(echo "$LAST_BODY" | jq -r .status)"
log_info "Phê duyệt thành công: Trạng thái chuyển sang '${STATUS_4}'"
if [ "$STATUS_4" != "repairing" ]; then
  log_error "Trạng thái mong đợi 'repairing', thực tế: '${STATUS_4}'"
  exit 1
fi

log_step "Bước 5: Kỹ thuật viên (ktv.dung) thực hiện sửa chữa và báo cáo hoàn thành"
api_call "GET" "/tasks?workflow_id=${WORKFLOW_ID}" "$TOKEN_KTV" "" 200
TASK_ID_5="$(echo "$LAST_BODY" | jq -r '.items[0].id')"
log_info "Nhận việc sửa chữa: Task ID = ${TASK_ID_5}"

REPAIR_DATA=$(cat <<EOF
{
  "data": {
    "technician_name": "Phạm Thị Dung",
    "repair_date": "${TODAY}",
    "work_performed": "Đã thông ống thoát nước ngưng, vệ sinh lưới lọc dàn lạnh, nạp bổ sung gas R410A.",
    "parts_replaced": "Gas R410A",
    "actual_cost_vnd": 3500000,
    "repair_status": "completed",
    "technical_notes": "Thiết bị hoạt động êm ái, đạt nhiệt độ làm lạnh tiêu chuẩn, không còn rỉ nước."
  }
}
EOF
)
api_call "POST" "/tasks/${TASK_ID_5}/complete" "$TOKEN_KTV" "$REPAIR_DATA" 200
STATUS_5="$(echo "$LAST_BODY" | jq -r .status)"
log_info "Sửa chữa hoàn tất: Trạng thái chuyển sang '${STATUS_5}'"
if [ "$STATUS_5" != "awaiting_acceptance" ]; then
  log_error "Trạng thái mong đợi 'awaiting_acceptance', thực tế: '${STATUS_5}'"
  exit 1
fi

log_step "Bước 6: Trưởng lab (tl.giang) nghiệm thu và bàn giao thiết bị"
api_call "GET" "/tasks?workflow_id=${WORKFLOW_ID}" "$TOKEN_TL" "" 200
TASK_ID_6="$(echo "$LAST_BODY" | jq -r '.items[0].id')"
log_info "Nhận việc nghiệm thu: Task ID = ${TASK_ID_6}"

ACCEPTANCE_DATA=$(cat <<EOF
{
  "data": {
    "acceptor_name": "Hoàng Thu Giang",
    "acceptor_role": "lab_manager",
    "acceptance_date": "${TODAY}",
    "operational_status": "normal",
    "acceptance_result": "accepted",
    "acceptance_notes": "Kiểm tra thực tế điều hòa hoạt động tốt, không rỉ nước. Bàn giao đưa vào sử dụng.",
    "handover_signed": true
  }
}
EOF
)
api_call "POST" "/tasks/${TASK_ID_6}/complete" "$TOKEN_TL" "$ACCEPTANCE_DATA" 200
STATUS_6="$(echo "$LAST_BODY" | jq -r .status)"
log_info "Nghiệm thu hoàn tất: Trạng thái kết thúc = '${STATUS_6}'"
if [ "$STATUS_6" != "completed" ]; then
  log_error "Trạng thái mong đợi 'completed', thực tế: '${STATUS_6}'"
  exit 1
fi

log_step "Bước 7: Kiểm tra Audit log & Tra cứu tri thức (/api/search)"
api_call "GET" "/workflows/${WORKFLOW_ID}" "$TOKEN_SV" "" 200
FINAL_STATUS="$(echo "$LAST_BODY" | jq -r .status)"
TOTAL_STEPS="$(echo "$LAST_BODY" | jq -r '.steps | length')"
log_info "Kiểm tra phiếu ${WORKFLOW_ID}: status='${FINAL_STATUS}', số bước đã ghi nhận=${TOTAL_STEPS}"

api_call "GET" "/search?q=m%C3%A1y+l%E1%BA%A1nh+nh%E1%BB%8F+n%C6%B0%E1%BB%9Bc" "$TOKEN_SV" "" 200
SEARCH_MATCH="$(echo "$LAST_BODY" | jq -r '.items[0].title // empty')"
log_info "Kết quả tra cứu SOP: '${SEARCH_MATCH}'"

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}✔ KỊCH BẢN E2E THÀNH CÔNG: Hoàn thành đầu-cuối qua APISIX Gateway${NC}"
echo -e "${GREEN}================================================================${NC}\n"
