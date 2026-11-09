"""Local hashing, path boundaries and credential redaction for Agent traces."""

import hashlib
import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[4]
def redact(value, redactor=None):
    from trace_privacy import Redactor
    redactor = redactor or Redactor()
    before = sum(redactor.counts.values())
    result = redactor.clean(value)
    return result, sum(redactor.counts.values()) - before


def redact_event(event, redactor=None):
    return redact(event, redactor)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8', 'backslashreplace')


def child(root, relative):
    """Reject lexical traversal and symlink components, including broken links."""
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or any(p in {'.', '..'} for p in relative.parts):
        raise ValueError('unsafe relative path')
    current = Path(root).absolute()
    for parent in (current, *current.parents):
        if parent.is_symlink():
            raise ValueError('symlink in root path')
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError('symlink in destination path')
    return current


def write_new_json(path, value):
    """Create a local artifact without replacing files or following destination links."""
    path = Path(path).absolute()
    child(path.parent, path.name)
    if path.resolve().is_relative_to(REPOSITORY / 'knowledge'):
        raise ValueError('artifact output cannot be knowledge')
    if path.exists() or path.is_symlink():
        raise ValueError('artifact output must be new')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
