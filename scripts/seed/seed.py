# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Nạp dữ liệu demo cho `lab-repair` CHỈ qua API (APISIX), bằng token của chính các tài khoản demo.

Trình tự (mỗi bước bỏ qua phần đã có nên chạy lại không nhân đôi dữ liệu):
  1. `qt.son` (process_admin) nạp gói `apps/lab-repair` → phiên bản chờ duyệt.
  2. `pgd.minh` (process_owner) duyệt áp dụng phiên bản đó.
  3. `csvc.lan` (facility_officer) nạp danh mục phòng, tài sản (`data/rooms.json`, `data/assets.json`) và SOP (`data/sop/*.md`).
  4. Tạo phiếu mẫu ở nhiều trạng thái, mỗi bước do đúng người làm (scenarios.py).

Chạy qua `scripts/seed.sh`. Không ghi thẳng database, không dùng tài khoản dịch vụ.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from api import ApiError, Client, LoginError, load_env
from scenarios import REPORTERS, Scenario, scenarios

ROOT = Path(__file__).resolve().parents[2]
APP_ID = "lab-repair"
APP_DIR = ROOT / "apps" / APP_ID

PUBLISHER = "qt.son"
APPROVER = "pgd.minh"
CATALOG_OWNER = "csvc.lan"

# Loại bản ghi của gói lab-repair (apps/lab-repair/records/<loại>-record.json) và tệp dữ liệu mẫu tương ứng
RECORD_FILES = (("room", "data/rooms.json"), ("asset", "data/assets.json"))
FALLBACK_LICENSE = "CC-BY-4.0"
FALLBACK_SOURCE = "Dữ liệu mẫu do đội DX-Lab tự tạo (giả định)"


class SeedError(Exception):
    pass


def say(text: str = "") -> None:
    print(text, flush=True)


# --- nguồn dữ liệu ---------------------------------------------------------------------------------


def read_sources() -> dict[str, dict[str, str]]:
    """Đọc `DATA_SOURCES.yml` (YAML phẳng, đọc bằng regex để không cần thư viện): đường dẫn → tiêu đề, giấy phép, nguồn."""
    path = ROOT / "DATA_SOURCES.yml"
    sources: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return sources
    current: dict[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^  - id:", line):
            current = {}
            continue
        match = re.match(r'^    (title|path|license|origin): "?(.*?)"?\s*$', line)
        if match and current is not None:
            current[match.group(1)] = match.group(2)
            if match.group(1) == "path":
                sources[match.group(2)] = current
    return sources


def provenance(sources: dict[str, dict[str, str]], rel_path: str) -> tuple[str, str]:
    entry = sources.get(rel_path, {})
    return entry.get("origin") or FALLBACK_SOURCE, entry.get("license") or FALLBACK_LICENSE


# --- 1, 2: publish và duyệt áp dụng ---------------------------------------------------------------




def publish_and_activate(client: Client) -> None:
    say("[1/4] Nạp và duyệt áp dụng ứng dụng lab-repair")
    _, definitions = client.request(PUBLISHER, "GET", "/definitions")
    for item in definitions.get("items", []):
        if item.get("app_id") == APP_ID and item.get("status") == "active":
            say(f"    đã có phiên bản đang áp dụng ({item.get('version')}), bỏ qua")
            return
    # Dùng phiên của qt.son đã đăng nhập để CLI không phải dùng lại mã OTP trong cùng chu kỳ.
    session = client.sessions[PUBLISHER]
    with tempfile.TemporaryDirectory(prefix="dxlab-seed-") as directory:
        token_file = Path(directory) / "token.json"
        token_file.write_text(json.dumps({
            "issuer": client.issuer,
            "client_id": client.client_id,
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at,
        }), encoding="utf-8")
        token_file.chmod(0o600)
        env = dict(os.environ, DXLAB_TOKEN_FILE=str(token_file), DXLAB_API_URL=client.api_url,
                   DXLAB_OIDC_ISSUER=client.issuer)
        try:
            result = subprocess.run(
                ["uv", "run", "dxlab", "publish", str(APP_DIR)],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False,
            )
        except FileNotFoundError as error:
            raise SeedError("Cần uv và CLI-01 để chạy dxlab publish.") from error
    if result.returncode:
        raise SeedError(f"dxlab publish thất bại: {(result.stderr or result.stdout).strip()}")
    match = re.search(r"phiên bản (\d+), trạng thái pending_approval", result.stdout)
    if not match:
        raise SeedError(f"Không đọc được phiên bản từ dxlab publish: {result.stdout.strip()}")
    version = int(match.group(1))
    say(f"    phiên bản {version}: chờ duyệt")
    _, activated = client.request(APPROVER, "POST", f"/definitions/{APP_ID}/versions/{version}/activate")
    if activated.get("status") != "active":
        raise SeedError(f"Duyệt phiên bản {version} xong nhưng trạng thái là {activated.get('status')!r}, mong đợi 'active'.")
    say(f"    {APPROVER} duyệt: phiên bản {version} đang áp dụng")


# --- 3: danh mục và SOP ----------------------------------------------------------------------------


def load_catalog() -> dict[str, list[dict[str, Any]]]:
    catalog = {}
    for record_type, rel in RECORD_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise SeedError(f"Không thấy {rel}: cần dữ liệu mẫu APP-03.")
        catalog[record_type] = json.loads(path.read_text(encoding="utf-8"))
    return catalog


def load_records(client: Client, sources: dict[str, dict[str, str]]) -> None:
    catalog = load_catalog()
    for record_type, rel in RECORD_FILES:
        items = catalog[record_type]
        source, license_ = provenance(sources, rel)
        created = updated = unchanged = 0
        for item in items:
            key = item["id"]
            path = f"/records/{APP_ID}/{record_type}/{key}"
            status, current = client.request(CATALOG_OWNER, "GET", path, ok=(200, 404))
            if status == 200 and current.get("data") == item:
                unchanged += 1
                continue
            body = {"data": item, "source": source, "license": license_, "source_ref": f"{rel}#{key}"}
            put_status, _ = client.request(CATALOG_OWNER, "PUT", path, json_body=body, ok=(200, 201))
            if put_status == 201:
                created += 1
            else:
                updated += 1
        say(f"    {rel}: {len(items)} bản ghi `{record_type}` (mới {created}, cập nhật {updated}, giữ nguyên {unchanged})")


def existing_document_hashes(client: Client) -> set[str]:
    hashes: set[str] = set()
    offset = 0
    while True:
        _, page = client.request(
            CATALOG_OWNER, "GET", f"/documents?app_id={APP_ID}&kind=sop&limit=200&offset={offset}"
        )
        hashes.update(item["sha256"] for item in page["items"])
        offset += len(page["items"])
        if not page["items"] or offset >= page["total"]:
            return hashes


def load_sops(client: Client, sources: dict[str, dict[str, str]]) -> None:
    files = sorted((ROOT / "data" / "sop").glob("*.md"))
    if not files:
        raise SeedError("Không thấy data/sop/*.md: cần dữ liệu mẫu APP-03.")
    known = existing_document_hashes(client)
    uploaded = 0
    for path in files:
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() in known:
            continue
        rel = path.relative_to(ROOT).as_posix()
        source, license_ = provenance(sources, rel)
        title = sources.get(rel, {}).get("title") or _first_heading(content.decode("utf-8")) or path.stem
        fields = [
            ("app_id", None, APP_ID.encode()),
            ("kind", None, b"sop"),
            ("title", None, title.encode()),
            ("source", None, source.encode()),
            ("license", None, license_.encode()),
            ("source_ref", None, rel.encode()),
            ("file", path.name, content),
        ]
        client.request(CATALOG_OWNER, "POST", "/documents", multipart=fields, ok=(201,))
        uploaded += 1
    say(f"    data/sop: {len(files)} SOP (tải lên {uploaded}, đã có {len(files) - uploaded})")


def _first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def load_catalogs(client: Client) -> None:
    say("[2/4] Nạp danh mục phòng, tài sản và SOP")
    sources = read_sources()
    load_records(client, sources)
    load_sops(client, sources)


# --- 4: phiếu mẫu ----------------------------------------------------------------------------------


def find_workflow(client: Client, scenario: Scenario) -> dict[str, Any] | None:
    """Tìm phiếu của kịch bản trong danh sách phiếu của chính người báo, khớp `issue_title`."""
    offset = 0
    while True:
        _, page = client.request(
            scenario.reporter, "GET", f"/workflows?app_id={APP_ID}&limit=200&offset={offset}"
        )
        for item in page["items"]:
            data = item.get("data")
            if data is None:
                _, detail = client.request(scenario.reporter, "GET", f"/workflows/{item['workflow_id']}")
                data = detail.get("data", {})
            if data.get("issue_title") == scenario.title:
                return item
        offset += len(page["items"])
        if not page["items"] or offset >= page["total"]:
            return None


def drive(client: Client, scenario: Scenario, workflow: dict[str, Any]) -> str:
    """Đưa phiếu tới trạng thái đích: mỗi lần lấy việc đang chờ trong hộp việc đúng người rồi hoàn thành bước đó."""
    plan = {step.step_id: step for step in scenario.steps}
    status = workflow["status"]
    for _ in range(len(scenario.steps) + 3):
        if status == scenario.target:
            return status
        step = plan.get(status)
        if step is None:
            raise SeedError(
                f"Phiếu {workflow['workflow_id']} ({scenario.key}) đang ở trạng thái '{status}', "
                f"kịch bản không có bước cho trạng thái này (đích '{scenario.target}')."
            )
        _, inbox = client.request(step.actor, "GET", "/tasks?limit=200")
        task = next(
            (
                t
                for t in inbox.get("items", [])
                if t.get("workflow_id") == workflow["workflow_id"] and t.get("step_id") == step.step_id
            ),
            None,
        )
        if task is None:
            raise SeedError(
                f"Hộp việc của {step.actor} không có việc '{step.step_id}' của phiếu {workflow['workflow_id']} "
                f"({scenario.key}); core giao việc này cho người khác hoặc chưa định tuyến."
            )
        _, result = client.request(step.actor, "POST", f"/tasks/{task['task_id']}/complete", json_body={"data": step.data})
        new_status = result.get("status")
        say(f"        {step.actor}: {step.step_id} → {new_status}")
        status = new_status
    raise SeedError(f"Phiếu {workflow['workflow_id']} ({scenario.key}) chưa tới '{scenario.target}' sau số bước tối đa; dừng ở '{status}'.")


def create_tickets(client: Client) -> None:
    say("[3/4] Tạo phiếu mẫu (AUTHZ mục 12)")
    summary: list[tuple[str, str, str]] = []
    for scenario in scenarios():
        workflow = find_workflow(client, scenario)
        if workflow is None:
            body = {"app_id": APP_ID, "data": {**REPORTERS[scenario.reporter], **scenario.report}}
            _, workflow = client.request(scenario.reporter, "POST", "/workflows", json_body=body, ok=(201,))
            say(f"    {scenario.key} ({scenario.ref}): {scenario.reporter} tạo phiếu {workflow['workflow_id']}")
        else:
            say(f"    {scenario.key} ({scenario.ref}): phiếu {workflow['workflow_id']} đã có, ở '{workflow['status']}'")
        status = drive(client, scenario, workflow)
        summary.append((scenario.key, workflow["workflow_id"], status))
    say("[4/4] Kết quả")
    for key, workflow_id, status in summary:
        say(f"    {key:12} {workflow_id}  {status}")


# --- chạy ------------------------------------------------------------------------------------------


def make_client() -> Client:
    env = load_env(ROOT)
    missing = [name for name in ("DXLAB_DEMO_PASSWORD", "DXLAB_DEMO_OTP_SECRET") if not env.get(name)]
    if missing:
        raise SeedError(f"Thiếu biến {', '.join(missing)} trong .env (chạy scripts/up.sh để tạo .env và sinh giá trị).")
    return Client(
        api_url=env.get("DXLAB_API_URL", "http://localhost:9080/api").rstrip("/"),
        issuer=env.get("DXLAB_OIDC_ISSUER", "http://localhost:8180/realms/dxlab").rstrip("/"),
        password=env["DXLAB_DEMO_PASSWORD"],
        otp_secret=env["DXLAB_DEMO_OTP_SECRET"],
    )


def main() -> int:
    try:
        client = make_client()
        say(f"Seed qua {client.api_url} (không ghi thẳng database)")
        publish_and_activate(client)
        load_catalogs(client)
        create_tickets(client)
    except ApiError as error:
        say(f"\nLỖI: {error}")
        if error.status == 404 and error.error_code() == "NOT_FOUND" and "đường dẫn" in json.dumps(error.body, ensure_ascii=False):
            say("    Core chưa có route này (kiểm tra core đang chạy đã gồm CORE-03, CORE-04a/b, CORE-06 chưa).")
        return 1
    except (SeedError, LoginError, ConnectionError) as error:
        say(f"\nLỖI: {error}")
        return 1
    say("\nSeed xong.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
