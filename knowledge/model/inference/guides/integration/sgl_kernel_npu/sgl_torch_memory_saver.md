---
type: Guide
title: SGLang Torch Memory Saver：region、暂停恢复与内容保留边界
description: 说明NPU虚拟地址保留、物理内存暂停恢复、tag与CPU备份，以及C++配对调用、同步和错误处理边界。
tags:
- task.implementation
- topic.memory
- topic.implementation.resource_lifecycle
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/README.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/entrypoint.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/binary_wrapper.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/hooks/base.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/hooks/mode_torch.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/hooks/mode_preload.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/utils.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/csrc/core.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/csrc/core.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/csrc/entrypoint.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/csrc/api_forwarder.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/csrc/utils.h
  role: implementation
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-09T06:04:04Z'
platforms: []
aliases:
- Torch Memory Saver
- torch_memory_saver
---

# SGLang Torch Memory Saver：region、暂停恢复与内容保留边界

## 语义与适用前提

Torch Memory Saver 将 `region(...)` 中分配的张量登记为可暂停内存：`pause()` 释放物理设备内存，保持虚拟地址；`resume()` 在原虚拟地址重新申请物理内存。地址相同不意味着内容相同：默认不保存原内容，适用于将失效的 KV Cache 或将重载/更新的权重。

来源没有为该独立模块提供覆盖 A2/A3/950 的完整产品支持声明，因此本卡保持平台未确认草稿；主仓其他组件的支持列表不为这个分配器扩展背书。

## region、tag 与 CPU 备份

`region(tag="default", enable_cpu_backup=False)` 使用专用 `torch.npu.MemPool` 和 region 配置。只暂停指定 tag 可用 `pause("weights")/resume("weights")`，`tag=None` 操作全部受管内存。需要恢复原数值时必须在 region 分配阶段设置 `enable_cpu_backup=True`，接受 CPU 内存与复制开销。

region 入口断言当前不在另一个 interesting region 内，退出时在 finally 中恢复默认配置。不能把它当作支持任意嵌套标签的上下文。只在 region 外创建的张量也不会因为之后调用 pause 自动获得受管属性。

## 初始化和 hook 选择

对象惰性初始化。未显式指定时读取 `TMS_HOOK_MODE`，默认 `torch`。该模式使用 `NPUPluggableAllocator` 的 `tms_torch_malloc/tms_torch_free` 入口；应在首次调用任何会触发初始化的接口前设置 `hook_mode`。

README 描述另一种 preload 模式，通过 `LD_PRELOAD` 拦截分配释放，但同时明确 PTA 通过 dlopen+dlsym 访问 `aclrtMallocAlign32`，当前不能靠 preload 覆盖，因此 preload 与图模式激活内存释放不受支持。Python `cuda_graph` 虽保留名称并调用 `torch.npu.graph`，又断言只允许 preload；有代码入口不等于该组合可运行。

当前 `_sanity_checks` 明确检查 `PYTORCH_CUDA_ALLOC_CONF` 中的 `expandable_segments:True` 并拒绝该配置；保留变量的实际名称，不自行改写为另一个未检查的环境变量。

## disable 与资源边界

`disable()` 仅能在 active region 内调用。实现暂不允许 `dispose_mem_pool_after_use=False`；会临时使用新的默认 pool，避免 torch_npu 重用已暂停虚拟地址，然后同步、释放临时 pool 并恢复 region 标记。源码注释说明设备内存不一定立即释放，可能要等对应 region 恢复并调用 empty_cache；不能把 pool 对象销毁解释成已回收显存。

暂停期间不能依赖受管张量可访问；恢复后若没有 CPU backup，应先重建数据再参与推理。元数据互斥不等于并发设备流已经停止访问，暂停和恢复前需由调用方建立使用边界，并在目标软件/设备组合验收。

## C++ 分配与暂停恢复的边界

`core.cpp` 的受管分配依次创建物理内存、保留虚拟地址、建立映射，再登记 size、device、handle、tag 和 CPU backup 指针。`pause` 解除映射并释放物理 handle，但没有释放虚拟地址；`resume` 创建新的物理 handle、映射回原地址，必要时从备份恢复数值。`core.free` 的内部流程才解除映射、释放物理内存及地址保留，并释放仍持有的 Host 备份；未登记的指针转交真实 `aclrtFree`。

能否进入该释放流程还取决于 hook 入口：`tms_torch_free` 先检查当前线程仍处于 interesting region，失败会经 `SIMPLE_CHECK` 退出进程，然后才可能调用 `core.free`。Python 退出 region 时把该标记恢复为 False；不能把完成 pause/resume 配对视为已保障在 region 外或另一线程触发原生回收。这里仅确认回调入口的静态限制，张量对象删除、缓存池回收与原生 free 回调并非同一个事件，不能据此断言每次在 region 外删除张量都会立即退出进程。

这不是通用幂等状态机：`AllocationMetadata` 没有 paused 标志，`pause/resume` 不检查是否已执行过同一步，也没有为部分失败提供回滚。应按同一 tag 的活动分配配对调用，不把重复 pause、重复 resume、暂停期间释放或仍有设备访问当作已有保障的路径。

C++ 的显式设备同步出现在受管 `free` 中，超时参数为 3000ms；`pause/resume` 本身没有同样的显式同步。两者持有的是分配元数据 mutex，不能用它证明 device work 或其他线程的推理已经结束。Torch hook 的 region、tag 和 CPU backup 配置是 thread_local，操作 tag 的 `pause/resume` 则遍历进程单例的分配表；在线程A设置 region 不会自动为线程B设置相同配置。

启用备份后，Host 缓冲首次需要时分配，resume 后继续保留以避免重复分配，直到最终 free；显存回收不等于 Host 备份内存也被回收。源码没有逐次检查所有 map/memcpy 返回值；`SIMPLE_CHECK` 失败直接 `exit(1)`，不是可由 Python 异常处理自动回滚的协议。上述是固定实现的静态生命周期边界，不是本次执行的故障复现或线程安全验证。

## 验证入口

来源提供 `simple.py torch`、`cpu_backup.py torch` 与 `rl_example.py torch`。验证时分别观察 pause/resume 前后设备内存、虚拟地址、带备份的数值保留和 tag 隔离；仅地址相同不能证明内容保留。本次未执行这些脚本、编译、真机、数值或性能测试。

## Evidence

- [contrib/torch_memory_saver/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/README.md)（primary）
- [contrib/torch_memory_saver/python/torch_memory_saver/entrypoint.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/entrypoint.py)（implementation）
- [contrib/torch_memory_saver/python/torch_memory_saver/binary_wrapper.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/binary_wrapper.py)（implementation）
- [contrib/torch_memory_saver/python/torch_memory_saver/hooks/base.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/hooks/base.py)（implementation）
- [contrib/torch_memory_saver/python/torch_memory_saver/hooks/mode_torch.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/hooks/mode_torch.py)（implementation）
- [contrib/torch_memory_saver/python/torch_memory_saver/hooks/mode_preload.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/hooks/mode_preload.py)（implementation）
- [contrib/torch_memory_saver/python/torch_memory_saver/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/contrib/torch_memory_saver/python/torch_memory_saver/utils.py)（supporting）
