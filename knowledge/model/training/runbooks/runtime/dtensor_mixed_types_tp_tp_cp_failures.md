---
{
  "type": "Runbook",
  "title": "torchtitan-npu deepseek-v4-flash 开启 TP/TP+CP 报 DTensor 类型与分片策略错误的根因定位",
  "description": "torchtitan-npu deepseek-v4-flash 模型在 910B 上开 TP/TP+CP 并行即崩，报 DTensor 类型与分片策略错误，本卡记录两类失败模式与修复方向。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# torchtitan-npu deepseek-v4-flash 开启 TP/TP+CP 报 DTensor 类型与分片策略错误的根因定位

torchtitan-npu deepseek-v4-flash 在 910B 上开 TP/TP+CP 并行即崩，报 DTensor 类型与分片策略错误。本卡记录两类失败模式的根因定界与修复方向。

## 适用场景

torchtitan-npu deepseek-v4-flash（910B 单机 8 卡）开启 TP / TP+CP 并行即报 Python 异常的故障诊断场景；也可作为『自定义 converter/通信组件接入 DTensor 语义』类框架缺陷的判别模板。route=training，area=runtime。

## 触发与观测

触发条件：仅含 TP 的配置（dp4-tp2-ep8-etp1-pp1-cp1）与 TP+CP 配置（dp2-tp2-ep8-etp1-pp1-cp2）训练必现异常退出。

torchtitan-npu deepseek-v4-flash 开启 TP（dp4-tp2-ep8-etp1-pp1-cp1）时，npu_mhc_pre/mhc_post converter 路径（mhc_prepost.py:326 forward → mhc_triton.py:222 forward）调用分布式算子 npu.npu_rms_norm.default 时混传 torch.Tensor 与 DTensor，抛出 RuntimeError: npu.npu_rms_norm.default got mixed torch.Tensor and DTensor, need to convert all torch.Tensor to DTensor before calling distributed operators!。

TP+CP 同时开启（dp2-tp2-ep8-etp1-pp1-cp2）时，compressor_attention_cp.py:58 forward 对 DTensor 直接调用 dist.isend（distributed_c10d.py:2586），在 tensor/_sharding_prop.py:1001 抛出 NotImplementedError: Operator c10d.send.default does not have a sharding strategy registered。

## 探针与操作

探针（诊断工件内给出）：日志差分（input.json 配置差分：失败/成功配置只差 TP）；堆栈缩界（extract_16-19、extract_43-47 逐帧 file:line）；反证检查（plog/device_log/coredump/npu_smi 全缺失且错误均在 Python 层抛出）。

## 机制与判别

根因定界：direct_mechanism=DTensor 分发层类型一致性检查拒绝混入参 / 分片传播对未注册策略的通信原语抛错；upstream_trigger=TP 使权重/激活成为 DTensor。修复方向：

```
1. **失败A**：`torchtitan_npu/converters/kernels/mhc_prepost.py:326` / `torchtitan_npu/ops/triton/mhc_triton.py:222`——调用 `npu_rms_norm` 等分布式算子前统一入参：普通 Tensor 用 `DTensor.from_local(..., placements=[Replicate()/Shard(...)])` 包裹，或对 DTensor 统一 `full_tensor()/to_local()` 后本地计算。
2. **失败B**：`torchtitan_npu/distributed/context_parallel/compressor_attention_cp.py:58`——先按通信设计确定 DeviceMesh 与 placements；如需重分布，先调用 `.redistribute(...)`，随后显式 `.to_local()` 取得本地通信Tensor，再按接收侧shape/布局、梯度路径和collective顺序核对。redistribute返回的仍是DTensor，不能单独消除本例isend的分片策略异常；detach也不是通用必要步骤。此为未完成训练验证的修复方向。
3. **版本升级**：采用已包含 DTensor 适配修复的 torchtitan-npu（PR #356 测试配置 `*_tp_pr356_test` / `*_tp_cp_pr356_test`）与 910B-openEuler 算子包（issue#51 提供）。
4. **验证判据**：NGPU=8 下以 dp4-tp2-ep8-etp1-pp1-cp1 与 dp2-tp2-ep8-etp1-pp1-cp2 连续训练 ≥10 步：无 DTensor 异常、loss 正常下降（对照 images/4.txt：step7 10.89 → step10 10.47）、显存稳定（<76%）、进程正常退出。
```

## 验证信号

验证信号：两条失败模式的堆栈与配置差分为客观日志/源码证据。

## 适用与失效边界

结论边界：mhc_triton.py:222 处具体哪个实参未转 DTensor 因缺源码保持 hypothesis；案例材料无失败运行时间戳与 CANN/驱动版本号；验收判据为 NGPU=8 连续训练 ≥10 步无 DTensor 异常、loss 正常下降、显存稳定（<76%）、进程正常退出（见机制片段：修复方向）。
