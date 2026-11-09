#!/usr/bin/env python3
"""Read-only batch audit of public Markdown; never echo matches or rewrite knowledge."""

import argparse
import json
from pathlib import Path

from model_trace_common import child, write_new_json
from trace_privacy import PROFILE, publication_findings


def audit(root, files=None, policy=None):
    root = Path(root).absolute()
    if files is None:
        files = [str(p.relative_to(root)) for p in sorted(root.rglob('*.md'))]
    if not isinstance(files, list) or not all(isinstance(path, str) for path in files):
        raise ValueError('files must be a JSON array of relative Markdown paths')
    if len(set(files)) != len(files):
        raise ValueError('duplicate publication path')
    findings = []
    for relative in files:
        path = child(root, relative)
        if path.suffix != '.md' or not path.is_file():
            raise ValueError('publication target must be an existing Markdown file')
        findings.extend({'path': relative, **row} for row in publication_findings(path.read_text(), policy))
    return {'ok': not findings, 'profile': PROFILE, 'checked': len(files), 'findings': findings,
            'knowledge_written': False, 'semantic_review_pass': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--files', type=Path)
    parser.add_argument('--redaction-policy', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.root, json.loads(args.files.read_text()) if args.files else None,
                       json.loads(args.redaction_policy.read_text()) if args.redaction_policy else None)
        if args.report:
            if args.report.resolve().is_relative_to((args.root / 'knowledge').resolve()):
                raise ValueError('publication report cannot be written into knowledge')
            write_new_json(args.report, result)
            print(json.dumps({key: value for key, value in result.items() if key != 'findings'} |
                             {'findings_count': len(result['findings']), 'report': str(args.report)}, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['ok'] else 1
    except (ValueError, TypeError, OSError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
