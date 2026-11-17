---
{
  "type": "Runbook",
  "title": "torch 主机张量 madvise 返回 -1：先采集 errno 和 VMA 边界",
  "description": "原记录只观察到 madvise 返回 -1，不能据此判定 EINVAL 或 VMA 越界根因。保留原始失败与 VMA 裁剪候选，提供明确标为后续采证的探针。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": [
    "agnostic"
  ]
}
---
# torch 主机张量 madvise 返回 -1：先采集 errno 和 VMA 边界

## 适用场景

Linux 主机 CPU 张量的大页建议；不针对设备显存。需要进程可读 /proc/self/maps，张量连续且其存储仍存活。

## 触发与观测

原始输出为 madvise return: (-1, ...)，随后未观测到非零 AnonHugePages；没有打印 errno。

## 探针与操作

后续诊断应先记录 data_ptr、字节范围、对应 VMA、syscall 返回值及 errno，再决定错误类型。下方探针是本次整理的采证示例，只做了语法检查，未在原轨迹运行。

本次整理的后续采证示例：默认只检查，apply=True 才发起 syscall：

```python
def inspect_host_madvise(tensor, hugepage_bytes=2 * 1024 * 1024, apply=False):
    import ctypes
    import mmap
    import os

    if tensor.device.type != "cpu" or not tensor.is_contiguous():
        raise ValueError("requires a live contiguous CPU tensor")
    page = os.sysconf("SC_PAGESIZE")
    if hugepage_bytes <= 0 or hugepage_bytes % page:
        raise ValueError("hugepage_bytes must be a positive page multiple")
    addr = tensor.data_ptr()
    nbytes = tensor.numel() * tensor.element_size()
    vma = None
    with open("/proc/self/maps", encoding="utf-8") as handle:
        for line in handle:
            low, high = (int(value, 16) for value in line.split()[0].split("-"))
            if low <= addr < high:
                vma = low, high
                break
    result = {"address": addr, "nbytes": nbytes, "vma": vma,
              "returncode": None, "errno": None}
    if vma is None or nbytes == 0:
        return result
    hp = hugepage_bytes
    low, high = vma
    start = max((low + hp - 1) // hp * hp, (addr + hp - 1) // hp * hp)
    end = min(high // hp * hp, (addr + nbytes) // hp * hp)
    result["requested_rounded_range"] = (addr // hp * hp, (addr + nbytes + hp - 1) // hp * hp)
    result["contained_range"] = (start, end)
    if not apply or end <= start:
        return result
    advice = getattr(mmap, "MADV_HUGEPAGE", None)
    if advice is None:
        raise RuntimeError("MADV_HUGEPAGE is unavailable on this host")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.madvise.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int)
    libc.madvise.restype = ctypes.c_int
    ctypes.set_errno(0)
    result["returncode"] = libc.madvise(ctypes.c_void_p(start), end - start, advice)
    if result["returncode"] == -1:
        result["errno"] = ctypes.get_errno()
    return result
```

原始信号摘要；原记录未输出 errno：

```text
madvise return: (-1, ... )
regions with AnonHugePages != 0: 0
```

## 机制与判别

2MiB 取整与 VMA 边界是否越界是需要检查的候选条件；返回 -1 不能独自确定 errno。原记录提出的 VMA 内裁剪方案尚无 syscall 成功返回和大页生效的完整观测，不能写成修复已闭合。

## 验证信号

已确认的原始信号只有 syscall 返回 -1、AnonHugePages 非零区域数为 0，以及后续填充计时。填充耗时不能证明 madvise 成功或大页生效。

## 适用与失效边界

大页大小、系统 THP 策略和分配器均影响结果。探针调用会改变该映射的内存建议，须在隔离的主机内存实验中运行；不得对未知设备指针照搬。此卡不承诺 EINVAL 根因或性能收益。
