---
{
  "type": "Runbook",
  "title": "Wan2.1-T2V-1.3B NPU 移植：RoPE 复数频率 float64→float32 修复 aclnnCat DT_COMPLEX128 失败",
  "description": "模型/框架：Wan2.1-T2V-1.3B（官方 PyTorch 实现）+ torch_npu（transfer_to_npu 方式整体迁移），torch 2.8.0+cpu / torch_npu 2.8.0，CANN 8.5.0，单卡 NPU（16 卡环境取 1 卡）。；任务：文生视频推理（t2v-1.3B，832×480，81 帧，50 步 UniPC 采样，bf16）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-23T08:50:31Z",
  "platforms": []
}
---

# Wan2.1-T2V-1.3B NPU 移植：RoPE 复数频率 float64→float32 修复 aclnnCat DT_COMPLEX128 失败

## 适用场景

- 模型/框架：Wan2.1-T2V-1.3B（官方 PyTorch 实现）+ torch_npu（transfer_to_npu 方式整体迁移），torch 2.8.0+cpu / torch_npu 2.8.0，CANN 8.5.0，单卡 NPU（16 卡环境取 1 卡）。
- 任务：文生视频推理（t2v-1.3B，832×480，81 帧，50 步 UniPC 采样，bf16）。
- 缺失信息：NPU 具体型号（torch.npu.device_count()=16，未见型号字符串）；torch_npu 小版本仅见 2.8.0。

## 触发与观测

保留的监控通知报告首次 NPU 端到端运行在第 1 个 diffusion step 失败（source 0 seq 232，归一化为 `unknown`，不是直接工具返回）。通知中的错误文本为：

```text
File "wan/modules/model.py", line 57, in rope_apply
    freqs_i = torch.cat([
RuntimeError: cat:build/CMakeFiles/torch_npu.dir/compiler_depend.ts:148 NPU function error: call aclnnCat failed, error code is 161002
[ERROR] ... ERR00100 PTA call acl api failed.
[PID: 8632] ... AclNN_Parameter_Error(EZ1001): tensor 0 not implemented for DT_COMPLEX128, should be in dtype support list [DT_FLOAT,DT_INT32,DT_INT64,DT_FLOAT16,DT_INT16,DT_INT8,DT_UINT8,DT_DOUBLE,DT_COMPLEX64,DT_BFLOAT16,DT_BOOL,]
```

该监控通知还报告 `Device do not support double dtype now, dtype cast replace with float` 与 `npu Autocast only supports dtypes of torch.float16, torch.bfloat16` 两条告警；来源等级仍为通知记录（source 0 seq 232）。

## 探针与操作

失败前 `wan/modules/model.py` 的 RoPE 以 float64 计算复数频率（source 0 seq 240，源码读取）：

```python
@amp.autocast(enabled=False)
def rope_params(max_seq_len, dim, theta=10000):
    assert dim % 2 == 0
    freqs = torch.outer(
        torch.arange(max_seq_len),
        1.0 / torch.pow(theta,
                        torch.arange(0, dim, 2).to(torch.float64).div(dim)))
    freqs = torch.polar(torch.ones_like(freqs), freqs)
    return freqs
```

以及 `rope_apply` 内：

```python
x_i = torch.view_as_complex(x[i, :seq_len].to(torch.float64).reshape(
    seq_len, n, -1, 2))
```

两处定点修复（source 0 seq 246、seq 249，before/after 均为编辑工具原始文本）：

- `rope_params`：`torch.arange(0, dim, 2).to(torch.float64)` → `.to(torch.float32)`，使 `torch.polar` 产生 complex64 而非 complex128；
- `rope_apply`：`x[i, :seq_len].to(torch.float64)` → `.to(torch.float32)`，使 `view_as_complex` 保持 complex64。

修复后（after，source 0 seq 246）：

```python
    freqs = torch.outer(
        torch.arange(max_seq_len),
        1.0 / torch.pow(theta,
                        torch.arange(0, dim, 2).to(torch.float32).div(dim)))
    freqs = torch.polar(torch.ones_like(freqs), freqs)
```

## 机制与判别

- 直接机制：float64 → `torch.polar`/`view_as_complex` 生成 `complex128` 张量，`rope_apply` 内 `torch.cat` 下沉为 aclnnCat，而 aclnnCat 的 dtype 支持列表止于 `DT_COMPLEX64`，故报 EZ1001 参数错误（dtype 不支持）而非算子缺失（source 0 seq 232、seq 238）。
- 判别：通知中的 161002/EZ1001 和 dtype 拒绝文本，与 seq 240 源码中的 float64 复数构造共同构成本次 dtype 适配的依据。修复保留公式结构，但降低中间计算精度；最终 `.float()` 返回不能证明质量等价，轨迹没有逐算子误差或视频质量数据。
- 未验证推断：complex64 频率对长序列 RoPE 的精度影响未做数值比对（本轨迹无输出质量评测）。

## 验证信号

- 修改后重跑命令见 source 0 seq 251/252；工具返回仅报告任务已转入后台，不等于运行成功。
- 直接探针：seq 314/315 的 `tail/ls` 调用及工具返回展示 50/50 进度、`Saving generated video to output_npu.mp4`、`INFO: Finished.` 和输出文件大小显示值 2.8M（单次运行，tool_observed）。该探针没有后台推理进程的退出码返回。
- seq 320 的任务通知报告该后台重跑 completed、exit 0；它与 seq 307/310 的监控通知均归一化为 `unknown`，不标作直接工具观测。
- seq 315 的进度条显示总时长约 4 min 44 s、末段约 5.67 s/step；这些是单次显示值，不是性能基线对比。未验证视频质量，不声称加速或精度等价。

## 适用与失效边界

- 适用：torch_npu `transfer_to_npu` 迁移的 PyTorch 模型中出现 complex128 张量进入 aclnn 算子（Cat/Polar 等）的场景；Wan 系列 rope_params/rope_apply 是已知实例。
- 失效/风险：若上游实现依赖 float64 精度（超长序列、极小频率），float32 截断可能引入数值差异——本轨迹未量化；torch_npu/CANN 版本升级后 aclnnCat dtype 列表变化需重新核对（本次观测基于 CANN 8.5.0 / torch_npu 2.8.0）。
- 回退条件：若修复后出现 RoPE 相关数值异常，可仅将 `rope_params` 保持 float64 而在乘法前拆 real/imag 计算，或升级支持 complex128 的 CANN 版本（未验证）。

## 附：断言存档

- Wan2.1 rope_params/rope_apply 以 float64 计算使 torch.polar/view_as_complex 产生 complex128，rope_apply 内 torch.cat 下沉 aclnnCat 报错 161002/EZ1001：tensor 0 not implemented for DT_COMPLEX128（支持列表止于 DT_COMPLEX64）。
- 将 rope_params 的 torch.arange(0,dim,2) cast 与 rope_apply 输入 cast 由 float64 改为 float32（保持 complex64）后，seq 315 的直接日志及文件探针展示一次 t2v-1.3B 832x480 运行 50/50、保存提示、Finished 和输出文件；exit 0 仅由 seq 320 的 unknown 任务通知报告。未做输出质量比对。

```text
        1.0 / torch.pow(theta,
37	                        torch.arange(0, dim, 2).to(torch.float64).div(dim)))
38	    freqs = torch.polar(torch.ones_like(freqs), freqs)
39
```

```text
        x_i = torch.view_as_complex(x[i, :seq_len].to(torch.float64).reshape(
56	            seq_len, n, -1, 2))
```

```text
"new_string": "    freqs = torch.outer(\n        torch.arange(max_seq_len),\n        1.0 / torch.pow(theta,\n                        torch.arange(0, dim, 2).to(torch.float32).div(dim)))\n    freqs = torch.polar(torch.ones_like(freqs), freqs)", "old_string": "    freqs = torch.outer(\n        torch.arange(max_seq_len),\n        1.0 / torch.pow(theta,\n                        torch.arange(0, dim, 2).to(torch.float64).div(dim)))\n    freqs = torch.polar(torch.ones_like(freqs), freqs)"
```

```text
"new_string": "        x_i = torch.view_as_complex(x[i, :seq_len].to(torch.float32).reshape(\n            seq_len, n, -1, 2))", "old_string": "        x_i = torch.view_as_complex(x[i, :seq_len].to(torch.float64).reshape(\n            seq_len, n, -1, 2))"
```
