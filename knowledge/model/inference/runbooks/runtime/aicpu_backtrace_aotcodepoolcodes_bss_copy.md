---
{
  "type": "Runbook",
  "title": "AICPU 回溯落在 aotCodePoolCodes+0x5c0 时核对代码池槽位",
  "description": "来源 AICPU signal 11 回溯有 aotCodePoolCodes+0x5c0，代码池 entry 大小为 0x1000000。若帧地址确在池内，该偏移属于 entry 0；当前执行还是旧槽位引用仍需精确 PC、故障地址和槽位生命周期证据。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# AICPU 回溯落在 aotCodePoolCodes+0x5c0 时核对代码池槽位

## 适用场景

AICPU 动态代码池回溯包含 `aotCodePoolCodes+N`，需要核对符号偏移、槽位范围与生命周期的场景。

## 触发与观测

来源用户提供 signal 11，frame 2 为 `aotCodePoolCodes+0x5c0`。源码显示 entry 大小 `4096 * 0x1000 = 0x1000000`；也读到了代码复制与 clear_cache 路径。回溯符号偏移不等于已读取故障时的精确 PC。

## 探针与操作

先核对该构建的代码池基址与 entry 大小。若故障 PC 确在池内，计算 `(pc - pool_base) // entry_size` 和槽内偏移，并与 active/LRU 槽位记录比较。以下是来源中提出、后来回退的 SigAct 示意，含省略部分，不是可直接编译执行的已验证补丁：

```
void SigAct(int signum, siginfo_t* info, void* act)
{
    auto *uc = reinterpret_cast<ucontext_t*>(act);
    uintptr_t faultPc = uc->uc_mcontext.pc;
    uintptr_t faultAddr = reinterpret_cast<uintptr_t>(info->si_addr);
    DEV_ERROR(ThreadErr::SIGNAL_HANDLER_ABNORMAL,
        "#sche.except.signal: signum=%d faultPc=%p faultAddr=%p", signum, (void*)faultPc, (void*)faultAddr);
    // 计算 aotCodePoolCodes 基址，打印偏移，并 dump 周围 0x100 字节
    ...
    PrintBacktrace(...);
    ...
}
```

## 机制与判别

`0x5c0 = 1472 < 0x1000000`，所以在“该帧真实指向池代码”的前提下偏移位于 entry 0。它既可能是当前槽位执行异常，也可能与旧槽位/生命周期有关；还应检查错误控制流或内存破坏，不能仅凭这一个帧认定 use-after-evict。

## 验证信号

已核对的是回溯报告、entry 大小宏和代码复制路径。SigAct 增强没有完成运行验证，也没有故障时 PC/si_addr 或槽位 dump。

## 适用与失效边界

本卡止于偏移计算与后续取证方向。active entry、过期指针与其他内存错误尚未区分，不是 UAF 修复配方。
