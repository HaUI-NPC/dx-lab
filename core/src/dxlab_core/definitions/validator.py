# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Kiểm gói ứng dụng trước khi nạp. Dùng chung cho `POST /api/definitions/...` và lệnh `dxlab validate`.

Quy trình và bảng luật là **dữ liệu**, không phải mã: SpiffWorkflow đánh giá điều kiện gateway và ô DMN bằng
`eval` của Python, nên mọi biểu thức phải qua kiểm tra cú pháp (chỉ so sánh, phép logic, số học, hằng số, tên
biến) và chỉ những phần tử BPMN trong danh sách cho phép mới được nạp.
"""

import ast
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from lxml import etree
from SpiffWorkflow.dmn.parser.DMNParser import DMNParser

from dxlab_core.definitions.engine import (
    FORM_SCHEMA_PROPERTY,
    FORM_UI_SCHEMA_PROPERTY,
    PROCESS_MODEL,
    Files,
    load_package,
    read_process_model,
    task_properties,
    user_task_specs,
)

ALLOWED_EXTENSIONS = {".bpmn", ".dmn", ".json", ".md"}
IGNORED_DIRS = {"eval"}
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_PACKAGE_BYTES = 10 * 1024 * 1024

# Lane là vai trò trừu tượng core biết cách tìm người (docs/AUTHZ.md mục 3) hoặc khóa vai trò cụ thể.
KNOWN_LANES = {
    "reporter", "technician", "lab_manager", "approver", "system",
    "lab_technician", "it_technician", "facility_technician", "faculty_head", "faculty_deputy", "school_head",
    "facility_officer", "facility_director", "finance_officer", "vice_president", "president", "internal_auditor",
    "process_admin", "rule_admin", "process_owner",
}

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
SPIFF_NS = "http://spiffworkflow.org/bpmn/schema/1.0/core"
DIAGRAM_NAMESPACES = {
    "http://www.omg.org/spec/BPMN/20100524/DI",
    "http://www.omg.org/spec/DD/20100524/DC",
    "http://www.omg.org/spec/DD/20100524/DI",
}
ALLOWED_BPMN_TAGS = {
    "definitions", "collaboration", "participant", "process", "laneSet", "lane", "childLaneSet", "flowNodeRef",
    "startEvent", "endEvent", "userTask", "manualTask", "task", "businessRuleTask",
    "exclusiveGateway", "parallelGateway", "sequenceFlow", "conditionExpression", "incoming", "outgoing",
    "extensionElements", "documentation", "textAnnotation", "text", "association",
}
ALLOWED_SPIFF_TAGS = {"properties", "property", "calledDecisionId", "instructionsForEndUser"}

_COMPARE_OPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Is, ast.IsNot)
_CONDITION_NODES = (
    ast.Expression, ast.Compare, ast.BoolOp, ast.UnaryOp, ast.Name, ast.Load, ast.Constant,
    ast.And, ast.Or, ast.Not, ast.Tuple, ast.List, *_COMPARE_OPS,
)
_ARITHMETIC_NODES = (ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd)
_DMN_NODES = _CONDITION_NODES + _ARITHMETIC_NODES


@dataclass(frozen=True)
class Issue:
    file: str
    element: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"file": self.file, "element": self.element, "message": self.message}

    def __str__(self) -> str:
        return f"{self.file} [{self.element}]: {self.message}" if self.element else f"{self.file}: {self.message}"


def package_files(files: Mapping[str, bytes]) -> dict[str, bytes]:
    """Bỏ thư mục không thuộc gói nạp (`eval/`) và tệp ẩn; chuẩn hóa đường dẫn."""
    kept: dict[str, bytes] = {}
    for raw, content in files.items():
        path = PurePosixPath(raw.replace("\\", "/"))
        if any(part.startswith(".") for part in path.parts) or (path.parts and path.parts[0] in IGNORED_DIRS):
            continue
        kept[str(path)] = content
    return kept


def validate_package(files: Files, previous: Files | None = None) -> list[Issue]:
    """Danh sách lỗi; rỗng = gói hợp lệ. `previous` là phiên bản đang áp dụng (để kiểm giữ cột kết quả DMN)."""
    files = package_files(files)
    previous = package_files(previous) if previous else None
    issues = _check_files(files)
    if issues:
        return issues
    issues += _check_process_model(files)
    for path, content in sorted(files.items()):
        if path.endswith(".bpmn"):
            issues += _check_bpmn_xml(path, content)
        elif path.endswith(".dmn"):
            issues += _check_dmn(path, content)
        elif path.endswith(".json") and path != PROCESS_MODEL:
            issues += _check_json(path, content)
    if issues:
        return issues
    issues += _check_spec(files)
    if previous:
        issues += _check_dmn_outputs_kept(files, previous)
    return issues


def _check_files(files: Files) -> list[Issue]:
    issues: list[Issue] = []
    if not files:
        return [Issue("", "", "Gói không có tệp nào.")]
    total = 0
    for path, content in files.items():
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts:
            issues.append(Issue(path, "", "Đường dẫn tệp không hợp lệ."))
        if pure.suffix not in ALLOWED_EXTENSIONS:
            issues.append(Issue(path, "", f"Loại tệp không được phép; chỉ nhận {', '.join(sorted(ALLOWED_EXTENSIONS))}."))
        if len(content) > MAX_FILE_BYTES:
            issues.append(Issue(path, "", "Tệp lớn hơn 2 MB."))
        total += len(content)
    if total > MAX_PACKAGE_BYTES:
        issues.append(Issue("", "", "Gói lớn hơn 10 MB."))
    return issues


def _check_process_model(files: Files) -> list[Issue]:
    if PROCESS_MODEL not in files:
        return [Issue(PROCESS_MODEL, "", "Thiếu process_model.json.")]
    try:
        model = read_process_model(files)
    except (ValueError, KeyError) as exc:
        return [Issue(PROCESS_MODEL, "", f"process_model.json thiếu hoặc sai trường: {exc}.")]
    if model.primary_file_name not in files:
        return [Issue(PROCESS_MODEL, "primary_file_name", f"Không có tệp quy trình chính {model.primary_file_name}.")]
    return []


def _parse_xml(path: str, content: bytes) -> tuple[etree._Element | None, list[Issue]]:
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
        return etree.fromstring(content, parser), []
    except etree.XMLSyntaxError as exc:
        return None, [Issue(path, "", f"XML không hợp lệ: {exc.msg}.")]


def _element_label(element: etree._Element) -> str:
    return element.get("id") or etree.QName(element).localname


def _check_bpmn_xml(path: str, content: bytes) -> list[Issue]:
    root, issues = _parse_xml(path, content)
    if root is None:
        return issues
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue  # comment, processing instruction
        qname = etree.QName(element)
        if qname.namespace == BPMN_NS and qname.localname not in ALLOWED_BPMN_TAGS:
            issues.append(Issue(path, _element_label(element), f"Phần tử bpmn:{qname.localname} không được phép."))
        elif qname.namespace == SPIFF_NS and qname.localname not in ALLOWED_SPIFF_TAGS:
            issues.append(Issue(path, _element_label(element.getparent()),
                                f"Phần mở rộng spiffworkflow:{qname.localname} không được phép."))
        elif qname.namespace not in {BPMN_NS, SPIFF_NS, *DIAGRAM_NAMESPACES}:
            issues.append(Issue(path, _element_label(element), f"Phần tử ngoài chuẩn BPMN: {qname.localname}."))
    for condition in root.iter(f"{{{BPMN_NS}}}conditionExpression"):
        flow = condition.getparent()
        issues += _check_expression(path, _element_label(flow), condition.text or "", _CONDITION_NODES, "Điều kiện")
    return issues


def _check_expression(path: str, element: str, text: str, allowed: tuple[type, ...], what: str) -> list[Issue]:
    source = text.strip()
    if not source:
        return []
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError:
        return [Issue(path, element, f"{what} '{source[:60]}' sai cú pháp.")]
    bad = sorted({type(node).__name__ for node in ast.walk(tree) if not isinstance(node, allowed)})
    if bad:
        return [Issue(path, element, f"{what} '{source[:60]}' dùng cú pháp không được phép: {', '.join(bad)}.")]
    return []


_QUESTION_MARK = re.compile(r"(\?)(?=(?:[^'\"]|['\"][^'\"]*['\"])*$)")


def _dmn_entry_source(entry: str) -> str:
    """Viết ô điều kiện DMN thành biểu thức Python đầy đủ, theo đúng cách SpiffWorkflow ghép khi chạy."""
    replaced = _QUESTION_MARK.sub("dmn_input", entry)
    if "dmn_input" in replaced:
        return replaced
    try:
        ast.parse(entry, mode="eval")
        return f"(dmn_input) == ({entry})"
    except SyntaxError:
        return f"dmn_input {entry}"


def _check_dmn(path: str, content: bytes) -> list[Issue]:
    root, issues = _parse_xml(path, content)
    if root is None:
        return issues
    namespaces = dict(root.nsmap)
    if None in namespaces:
        namespaces["dmn"] = namespaces.pop(None)
    decisions = root.findall(".//{*}decision")
    if len(decisions) != 1:
        return [Issue(path, "", "Mỗi tệp .dmn phải có đúng một decision (giới hạn của SpiffWorkflow).")]
    try:
        parser = DMNParser(None, root, namespaces, filename=path)
        parser.parse()
        decision = parser.decision
        for table in decision.decisionTables:
            for column in table.inputs:
                issues += _check_expression(path, column.id, column.expression or "", _DMN_NODES, "Biểu thức đầu vào")
            for rule in table.rules:
                label = f"{decision.id} dòng {rule.row_number}"
                for input_entry in rule.inputEntries:
                    for lhs in input_entry.lhs:
                        if lhs and lhs.strip() not in {"-", ""}:
                            issues += _check_expression(path, label, _dmn_entry_source(lhs), _DMN_NODES, "Ô điều kiện")
                for output_entry in rule.outputEntries:
                    issues += _check_expression(path, label, output_entry.text or "", _DMN_NODES, "Ô kết quả")
    except Exception as exc:  # noqa: BLE001 — lỗi parse của thư viện trả về người nạp, không làm sập core
        issues.append(Issue(path, "", f"Bảng luật không đọc được: {exc}"))
    return issues


def _check_json(path: str, content: bytes) -> list[Issue]:
    try:
        document = json.loads(content)
    except ValueError as exc:
        return [Issue(path, "", f"JSON không hợp lệ: {exc}.")]
    is_form_schema = path.endswith("-schema.json") and not path.endswith("-uischema.json")
    if is_form_schema or path.endswith("-record.json"):
        try:
            Draft202012Validator.check_schema(document)
        except SchemaError as exc:
            return [Issue(path, "/".join(str(p) for p in exc.path), f"JSON Schema không hợp lệ: {exc.message}")]
    return []


def _check_spec(files: Files) -> list[Issue]:
    model = read_process_model(files)
    try:
        package = load_package(files)
    except Exception as exc:  # noqa: BLE001 — lỗi parse (thiếu decision, id trùng…) trả về người nạp
        return [Issue(model.primary_file_name, "", f"SpiffWorkflow không đọc được quy trình: {exc}")]
    issues: list[Issue] = []
    specs = [package.spec, *package.subprocess_specs.values()]
    for spec in specs:
        for task_spec in user_task_specs(spec):
            label = task_spec.bpmn_id or task_spec.name
            lane = getattr(task_spec, "lane", None)
            if not lane:
                issues.append(Issue(model.primary_file_name, label, "Bước người dùng phải nằm trong một lane."))
            elif lane not in KNOWN_LANES:
                issues.append(Issue(model.primary_file_name, label, f"Lane '{lane}' không phải vai trò đã biết."))
            props = task_properties(task_spec)
            for prop in (FORM_SCHEMA_PROPERTY, FORM_UI_SCHEMA_PROPERTY):
                name = props.get(prop)
                if name and name not in files:
                    issues.append(Issue(model.primary_file_name, label, f"Form {name} không có trong gói."))
            if FORM_SCHEMA_PROPERTY not in props:
                issues.append(Issue(model.primary_file_name, label, "Bước người dùng thiếu form (formJsonSchemaFilename)."))
    return issues


def dmn_outputs(files: Files) -> dict[str, set[str]]:
    """Tên cột kết quả của từng decision trong gói."""
    outputs: dict[str, set[str]] = {}
    for path, content in files.items():
        if not path.endswith(".dmn"):
            continue
        root = etree.fromstring(content, etree.XMLParser(resolve_entities=False, no_network=True))
        for decision in root.iter("{*}decision"):
            names = {out.get("name") or out.get("label") or out.get("id") for out in decision.iter("{*}output")}
            outputs[decision.get("id")] = {n for n in names if n}
    return outputs


def _check_dmn_outputs_kept(files: Files, previous: Files) -> list[Issue]:
    issues: list[Issue] = []
    new = dmn_outputs(files)
    for decision_id, old_names in dmn_outputs(previous).items():
        missing = old_names - new.get(decision_id, set())
        if missing:
            issues.append(Issue(
                "", decision_id,
                f"Bảng luật bỏ cột kết quả mà quy trình đang đọc: {', '.join(sorted(missing))}.",
            ))
    return issues


def changed_kinds(files: Files, previous: Files | None) -> set[str]:
    """Loại tệp thay đổi so với phiên bản trước (`dmn`, `bpmn`, `json`, `md`); phiên bản đầu = mọi loại có trong gói."""
    kinds: set[str] = set()
    paths: Iterable[str] = set(files) | set(previous or {})
    for path in paths:
        if previous is None or files.get(path) != previous.get(path):
            kinds.add(PurePosixPath(path).suffix.lstrip("."))
    return kinds
