# SPDX-FileCopyrightText: 2026 DX-Lab contributors
#
# SPDX-License-Identifier: Apache-2.0

"""Lưu tệp theo nội dung: `<documents_dir>/<sha256[:2]>/<sha256>`. Tên tệp người dùng gửi không bao giờ thành đường dẫn."""

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO

CHUNK = 1024 * 1024
MAX_BYTES = 20 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")


class TooLarge(Exception):
    pass


def path_for(documents_dir: Path, sha256: str) -> Path:
    if not _SHA256.fullmatch(sha256):
        raise ValueError("sha256 không hợp lệ")
    return documents_dir / sha256[:2] / sha256


def save(documents_dir: Path, source: BinaryIO, max_bytes: int = MAX_BYTES) -> tuple[str, int]:
    """Ghi luồng vào volume, trả `(sha256, số byte)`. Quá `max_bytes` thì ném `TooLarge` và không để lại tệp nào.

    Ghi ra tệp tạm cùng thư mục rồi đổi tên nguyên tử, nên người đọc không bao giờ thấy tệp dở dang. Cùng nội dung
    thì cùng một tệp: lần tải lên sau không ghi lại.
    """
    documents_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    fd, tmp_name = tempfile.mkstemp(dir=documents_dir, prefix=".upload-")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := source.read(CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    raise TooLarge
                digest.update(chunk)
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        sha256 = digest.hexdigest()
        target = path_for(documents_dir, sha256)
        if target.exists():
            tmp.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(tmp, target)
        return sha256, size
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
