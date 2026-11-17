---
{
  "type": "Runbook",
  "title": "FXRT 缓存补丁未安装：核对模块导入链与实际部署版本",
  "description": "模块末尾的 bootstrap 依赖模块被导入；排查时同时核对 worker 的包路径、初始化导入段和补丁标记，避免混用 fxrt_pkg 与 site-packages。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# FXRT 缓存补丁未安装：核对模块导入链与实际部署版本

## 适用场景

vLLM/Inductor/FXRT 部署中设置了缓存环境变量，但实际 worker 中补丁未出现的情况。具体硬件未知。

## 触发与观测

记录中手动导入与真实 worker 的表现不同，部署包与工作副本也存在差异。

## 探针与操作

分别在真实 worker 与排查进程打印 fxrt.__file__、包版本及补丁标记。读取部署包 __init__.py、compile_cache.py 的 bootstrap 调用和显式导入调用点。

源码函数单元（依赖所属模块上下文）：

```python
from fxrt.torch.fx_wrapper import install_torch_npu_fx_wrapper  # pylint: disable=wrong-import-position


install_torch_npu_fx_wrapper()

from fxrt import ops  # pylint: disable=wrong-import-position

__all__ = ['ops', 'install_torch_npu_fx_wrapper', '__version__']
```

原始导入探针的异常：

```text
ImportError: cannot import name 'compile_cache_level' from 'fxrt.compile_cache'
```

## 机制与判别

所读部署包初始化段导入 fx_wrapper 和 ops；如果 compile_cache 未进入执行链，其模块级 bootstrap 不会仅因环境变量存在而自动执行。此处的静态搜索和手动 import 不能证明所有 worker 的动态导入路径均已穷尽。

## 验证信号

原始输出给出部署包初始化段和导入搜索。另一次显式 import 报 cannot import name compile_cache_level，说明排查还必须核对部署版本和可用导出；没有完成修复部署后的 worker 复验。

## 适用与失效边界

新增 import 只是待验证方向，须检查循环导入、初始化顺序和多 worker 实际标记。不能用手动进程安装成功代替 worker 成功，也不能把公开导出名缺失直接归因于未导入。
