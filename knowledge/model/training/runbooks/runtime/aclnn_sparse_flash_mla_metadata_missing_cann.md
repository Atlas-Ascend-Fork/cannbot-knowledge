---
{
  "type": "Runbook",
  "title": "SparseFlashMlaMetadata 环境诊断：核对候选版本、实际加载库与导出符号",
  "description": "历史成功组合的工具包版本未定位；提供只读版本、进程映射与导出符号探针，不据路径切换推荐替换版本。",
  "tags": [
    "task.debugging",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-17T02:15:12Z",
  "platforms": [
    "a3"
  ]
}
---
# SparseFlashMlaMetadata 环境诊断：核对候选版本、实际加载库与导出符号

## 适用场景

torchtitan-npu 训练入口报告 `aclnnSparseFlashMlaMetadata` 不可用、多套 CANN 共存且加载来源不清时的诊断。历史记录上下文为 A3 单机八卡、CP=2/EP=4；失败与成功两侧的 CANN 版本、实际库名及加载文件对应关系未还原，历史成功组合未定位。

## 触发与观测

历史摘要提到默认环境缺少该接口，切换启动环境后有两步训练完成输出；没有绑定两侧版本、原始符号检查和进程映射，不能据此推荐某个替换版本，或断言刚找到的 `.so` 就是训练进程加载的那份。

## 探针与操作

在目标 Python 训练 worker 仍存活、且与探针处于同一容器/挂载命名空间时采集。`TRAIN_PID` 是该 worker 的 PID；`CANN_A/B` 是两套候选安装根，`LIB_A/B` 是要比对的具体共享库文件，不能仅填目录。先从进程映射确定候选库名，不把通用示例名当作历史实测。以下完整脚本保存为 `toolkit_probe.py`，只读版本元数据、文件摘要、进程映射和动态导出表，不 source 环境、不动态加载 CANN 库。

```python
import hashlib
import os
from pathlib import Path
import shutil
import subprocess


def process_libraries(pid):
    libraries = {}
    for line in (Path('/proc') / str(pid) / 'maps').read_text().splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) != 6 or not parts[5].startswith('/') or '.so' not in parts[5]:
            continue
        major, minor = (int(value, 16) for value in parts[3].split(':'))
        inode = int(parts[4])
        if not inode:
            continue
        path = parts[5]
        key = (major, minor, inode, path)
        libraries[key] = {'path': path, 'device': [major, minor], 'inode': inode,
                          'deleted': path.endswith(' (deleted)')}
    return list(libraries.values())


def exported_symbol(path, symbol):
    nm = shutil.which('nm')
    if nm is None:
        return 'unknown', 'nm is unavailable', []
    result = subprocess.run([nm, '-D', '--defined-only', '--', str(path)],
                            capture_output=True, text=True)
    if result.returncode:
        return 'unknown', result.stderr.strip(), []
    names = {line.split()[-1]
             for line in result.stdout.splitlines() if line.split()}
    variants = sorted(name for name in names if name.split('@', 1)[0] == symbol)
    return ('present' if variants else 'absent'), None, variants


def toolkit_versions(root):
    root = Path(root).resolve()
    versions = []
    for relative in ('version.info', 'compiler/version.info', 'runtime/version.info',
                     'ascend_toolkit_install.info',
                     'aarch64-linux/ascend_toolkit_install.info',
                     'x86_64-linux/ascend_toolkit_install.info'):
        path = root / relative
        try:
            lines = path.read_text().splitlines()
        except (OSError, UnicodeError):
            continue
        # Installation metadata may also contain usernames/paths: retain only
        # explicitly named version fields, never print the entire file.
        values = [line.strip() for line in lines
                  if ('=' in line or ':' in line)
                  and 'version' in line.replace(':', '=').split('=', 1)[0].lower()]
        if values:
            versions.append({'file': relative, 'version_fields': values})
    return {'root': str(root), 'version_status': 'found' if versions else 'unknown',
            'version_sources': versions}


def inspect_toolkits(pid, roots, libraries,
                     symbol='aclnnSparseFlashMlaMetadata'):
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ValueError('pid must be the live training worker PID')
    try:
        mapped = process_libraries(pid)
        maps_error = None
    except OSError as error:
        mapped, maps_error = [], str(error)
    report = {'pid': pid, 'symbol': symbol, 'maps_error': maps_error,
              'toolkits': [toolkit_versions(root) for root in roots],
              'mapped_libraries': mapped, 'candidates': []}
    for name in libraries:
        path = Path(name).resolve()
        row = {'path': str(path), 'loaded_in_pid': None,
               'symbol_status': 'unknown', 'sha256': None}
        try:
            before = path.stat()
            identity = [os.major(before.st_dev), os.minor(before.st_dev), before.st_ino]
            digest = hashlib.sha256()
            with path.open('rb') as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b''):
                    digest.update(block)
            state, error, variants = exported_symbol(path, symbol)
            after = path.stat()
            stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            matches = [m for m in mapped
                       if m['device'] + [m['inode']] == identity]
            path_hints = [m for m in mapped
                          if m['path'].removesuffix(' (deleted)') == str(path)]
            comparable_device = any(m['device'] == identity[:2] for m in mapped)
            # A namespace/filesystem view may expose a different device ID.
            # Same path is only a hint; never turn that mismatch into False.
            loaded = None
            if stable and maps_error is None:
                if matches:
                    loaded = True
                elif comparable_device and not path_hints:
                    loaded = False
            row.update(identity=identity, sha256=digest.hexdigest(),
                       file_stable_during_probe=stable, matching_mappings=matches,
                       path_hint_mappings=path_hints, loaded_in_pid=loaded,
                       symbol_status=state if stable else 'unknown',
                       symbol_variants=variants if stable else [],
                       symbol_error=error if stable else 'file changed during probe')
        except OSError as error:
            row['error'] = str(error)
        report['candidates'].append(row)
    return report


if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--root', action='append', required=True)
    parser.add_argument('--library', action='append', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_toolkits(args.pid, args.root, args.library),
                     ensure_ascii=False, indent=2))
```

```bash
python3 toolkit_probe.py --pid "${TRAIN_PID}" --root "${CANN_A}" --root "${CANN_B}" \
  --library "${LIB_A}" --library "${LIB_B}"
```

判读时分别核对：候选根的 `version_sources`；`mapped_libraries` 的实际路径/库名；候选的 `identity`、`matching_mappings`、`sha256` 与 `symbol_variants`。`version_status=unknown` 表示未读到所列版本字段，不能猜版本；`symbol_status=absent` 只表示该候选动态导出表没有目标名称，不是全进程没有该接口。权限、工具缺失、文件变化或文件系统/命名空间标识无法对齐时保留 `unknown` 或 `loaded_in_pid=null`；`path_hint_mappings` 只是路径线索，不能替代身份匹配。输出路径仅留本地；公开时用角色变量替换账号与安装根，同时保留同一文件身份和符号输出的对应关系。

## 机制与判别

候选文件与进程映射按设备号和 inode 对应；同名库、环境变量或另一个进程的检查不能替代该快照。导出表中的名称存在也不证明符号版本、解析顺序、ABI 或算子执行成功。版本元数据必须与实际映射候选关联后解读，并逐库检查混装；仅选择一套 set_env 路径不证明最终进程全部依赖来自同一套工具包。历史报告另提到负载均衡选项调整，但与该两步成功运行的版本对应关系未确认，也没有单变量对照；不能将成功单点归因于 CANN 路径。

映射字段见 [Linux proc_pid_maps(5)](https://man7.org/linux/man-pages/man5/proc_pid_maps.5.html)，动态/已定义符号与版本后缀见 [GNU nm](https://sourceware.org/binutils/docs/binutils/nm.html)。

## 验证信号

原始运行输出包含两步 loss=12.25368、12.24471，随后 `Training completed` 和 `Process group destroyed`；只能保留为工具包身份未定位的历史成功组合，不为候选版本背书。新探针仅在 CPU 自建的两份同名模拟共享库上检查缺/有符号、实际映射身份及未知状态，没有恢复历史 CANN 版本，也没有新增 NPU 验收。

## 适用与失效边界

`/proc` 权限、容器路径和采样时刻必须对应目标 worker；快照不保证后续加载状态不变，已删除/替换文件需按身份另行取证。`symbol_status=present` 仅说明名称出现在该文件的已定义动态表，仍要检查原样保留的版本后缀与实际调用链。脚本退出码不代表模型验收。历史单机通过不外推多机；原双机记录仍有 checkpoint 重计算 metadata 问题，环境修正后还需独立验证符号解析、前后向与数值。
