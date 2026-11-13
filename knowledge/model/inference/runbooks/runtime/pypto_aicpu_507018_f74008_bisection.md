---
{
  "type": "Runbook",
  "title": "PyPTO 算子 aicpu exception 507018 与最近 Drco 提交无关：逐提交重建验证的定界方法",
  "description": "PyPTO 算子用例报 aicpu exception 507018：通过逐提交 checkout 重建真机复现验证，HEAD/e0e9f7322/0fc103703 三个版本的 device 日志完全一致，证明该 bug 与最近几笔 machine 提交无关、在 0fc103703 就已存在。",
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
# PyPTO 算子 aicpu exception 507018 与最近 Drco 提交无关：逐提交重建验证的定界方法

> 验证层级：device_functional（3 个提交版本重建后真机复现，device 日志比对）

## 适用场景

PyPTO（DynTileFwkKernelServer/PyptoRun 执行路径）算子用例报 aicpu exception、错误码 507018，且怀疑与最近若干笔框架提交相关的场景。本例为 deepseek_v4 test_compressor.py（compressor_ratio_128_kernel）。

## 触发与观测

- 用例报错：`PyptoGeneralError: Failed to call JIT function 'compressor_ratio_128_kernel'. ErrCode: F7100B! HostLauncherErr::SYNC_FAILED. stream sync failed` + `[Error]: aicpu exception, device_id: 0, retcode: 507018, kernelName: (Null)`，device 日志显示 `AI CPU kernel execution failed ... funcName=DynTileFwkKernelServer, kernelName=PyptoRun`。
## 探针与操作

1. `git show` 最近可疑提交（3fb648655 fix DrcoRootFuncData、2a7c2d936 删除 GlobalQueue backup&restore、59c62dea1 Add DieReadyQueue），结合 aicore_entry_drco.h 等源码分析队列使用点。
3. 逐提交 checkout 重建验证（每次 `python3 build_ci.py --clean --frontend=python3 && pip3 uninstall pypto -y && pip3 install build_out/pypto-*whl` 后运行 `python3 models/deepseek_v4/test_compressor.py`，读新 device 日志）：


```
# 1. 回退到三笔 machine 提交之前，验证是否正常
git stash
git checkout e0e9f7322   # 三笔提交的前一笔
# 重新编译 PyPTO 后运行:
python3 models/deepseek_v4/test_compressor.py

# 2. 若通过，逐笔前向验证定位具体 commit:
git checkout 2a7c2d936 && <build> && test   # 先验证最早的那笔
git checkout 59c62dea1 && <build> && test
git checkout 3fb648655 && <build> && test
```

## 机制与判别

- 判别性观测：`逐提交 checkout 重建并运行 test_compressor.py 验证：HEAD（3fb648655 fix DrcoRootFuncData）、e0e9f7322（引入 DRCO）、0fc103703（parser: INSERT Vec->Mat，四笔 machine 提交之前）三笔提交的 device 日志完全一致（同一 AssignIncastAddresses 断言失败），证明这个 bug 与最近几笔 machine 提交（e0e9f7322、2a7c2d936、59c62dea1、3fb648655）无关，它在 0fc103703 就已经存在。`

## 验证信号

- 真机复现链：e0e9f7322 版本运行报同型 aicpu 507018；0fc103703 版本运行报 HDC disconnect 507901，其 device 日志仍为同一 AssignIncastAddresses 断言；三版本 device 日志一致（汇总）。
- 该定界为“提交相关性排除”结论：确认 bug 早于可疑提交批次，首次引入提交需继续向前回溯（候选方向：0fc103703 本身的 parser INSERT Vec->Mat 改动影响 compressor 构图，或更早的 IR/pass 提交）。


**来源记录与诊断解释**

- 逐提交 checkout 重建并运行 test_compressor.py 验证：HEAD（3fb648655 fix DrcoRootFuncData）、e0e9f7322（引入 DRCO）、0fc103703（parser: INSERT Vec->Mat，四笔 machine 提交之前）三笔提交的 device 日志完全一致（同一 AssignIncastAddresses 断言失败），证明这个 bug 与最近几笔 machine 提交（e0e9f7322、2a7c2d936、59c62dea1、3fb648655）无关，它在 0fc103703 就已经存在。

## 适用与失效边界

- 适用：PyPTO 算子 aicpu exception 类问题的提交归因排除；用“父提交重建复现”快速排除近期提交归因。
- 失效/边界：本方法只完成提交相关性定界，未定位首次引入提交，也未给出已验证的修复。
