---
{
  "type": "Runbook",
  "title": "Wan2.2-I2V-A14B BF16：两种2 die配置 OOM 与4 die cfg2×uly2成功记录",
  "description": "Atlas A3、CANN 9.2.0及固定源码下，所测两种2 die CFG配置失败，所测4 die组合成功；wrap峰值组成和最小可行并行度均未确定。",
  "tags": [
    "task.testing",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---


# Wan2.2-I2V-A14B BF16：两种2 die配置 OOM 与4 die cfg2×uly2成功记录

## 适用场景

- 平台范围依据：source 0 seq 1、source 0 seq 383、source 0 seq 384的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 实测软件与源码：CANN 9.2.0、torch 2.7.1、torch-npu 2.7.1.post2；源码提交 `84a02169698c640007a0687d92f46cd92ebb6af4`（source 0 seq 1/116）。
- Atlas A3（Ascend 910_9382，单 die 61.27 GiB 可用）运行 Wan2.2-I2V-A14B BF16（双专家 high/low noise 各 ~27GB + umt5-xxl + VAE，共 65GB 权重），想用 2 die 做 CFG 并行（cfg_size=2, world_size=2）跑 640*360×61 帧 40 步推理。

## 触发与观测

- 第一次尝试（source 0 seq 329-332）：所测无FSDP的2 die CFG配置初始化后接近每die容量并OOM。双专家、T5与VAE的具体驻留占用是当时的分析，未获得逐模块内存测量。
- 第二次尝试（source 0 seq 350，tool_observed，逐字）：

```text
RuntimeError: NPU out of memory. Tried to allocate 672.00 MiB (NPU 0; 61.27 GiB total capacity; 59.87 GiB already allocated; 59.87 GiB current active; 335.87 MiB free; 59.96 GiB reserved in total by PyTorch)
```

第二次失败位于 high_noise_model 的 FSDP wrap（`_configure_model → shard_fn(model)`）。源码采用 FULL_SHARD、`sync_module_states=True` 和按 block 的 auto_wrap_policy（source 0 seq 350/356/362）；日志只能定位失败阶段。seq 365 对逐块 flatten 与整专家驻留提出不同解释并明确“wrap峰值的具体构成还有待分析”，不能把完整专家参数与flatten副本并存写成已确认根因。

## 探针与操作

- 探针：日志检索 `NPU out of memory` 与 `total capacity/already allocated` 数值区分「驻留型 OOM」（分配前已满）与「wrap 峰值型 OOM」（初始化阶段失败）。
- 处置：world_size 扩到 4 die（cfg2×ulysses2 + dit_fsdp/t5_fsdp）后 wrap 成功并完成推理（去噪 63.82s）。
- 附带文档差异：config README 声称 `dit_fsdp` 默认 true，实际日志为 `dit_fsdp=False`（source 0 seq 333，agent 对照文档与日志），依赖默认值的配置会踩坑。

## 机制与判别

- CFG并行与参数分片是不同机制；本例无FSDP和启用FSDP的两种2 die配置都失败，但失败阶段不同。
- 后一次成功配置同时把 world_size 改为4并新增 `ulysses_size=2`（cfg2×uly2、DiT/T5 FSDP，source 0 seq 378/379/384），不能当作只改变设备数量的受控对照。
- 错误数值说明本次申请时可用容量不足，不证明具体峰值由哪些模块组成，也不排除碎片、泄漏或其它驻留贡献。各配置未重复运行，不能据此排除随机性或确定最小设备数。

## 验证信号

- 两次2 die失败见source 0 seq329/350；其中FSDP wrap时已分配59.87 GiB，申请672 MiB而仅335.87 MiB空闲。
- 所测4 die cfg2×uly2配置完成推理，单次去噪记录63.82s（source 0 seq384）。
- 这些是不同配置的单次记录，没有同配置重复实验、完整内存归因或全配置可行性搜索。

## 适用与失效边界

- 结论限定于所列软件、源码和工作负载：所测两种2 die配置失败，所测4 die cfg2×uly2配置成功。
- 不能推导全部2 die方案都不可行，也不能称4 die为最小值。`t5_cpu`、其它offload/分块初始化等组合未在该组记录中完成验证；wrap峰值的内部构成仍待测量。
- 换模型、软件版本、初始化策略或输入负载时需重新核对；先测实际驻留与wrap峰值，再决定并行配置。

## 附：断言存档

- Wan2.2-I2V-A14B BF16在61.27 GiB单die设备上，所测两种2 die CFG配置出现OOM，其中一次发生在FSDP wrap。
- 增加Ulysses并行的所测4 die配置成功；这是一个已观察到的可运行配置，不是最小设备数证明。
