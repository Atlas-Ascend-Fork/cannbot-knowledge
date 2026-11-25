---
{
  "type": "Runbook",
  "title": "torch_npu npu_dynamic_mx_quant 在 E4M3 目标下 scale_alg=0/1 均报 UInt7 不支持（CANN 9.2.0-beta.2）",
  "description": "框架/模型链路：torchtitan-npu 为 DeepSeek-V4.1 Engram 表做 MXFP8（E4M3 数据 + 每 32 元素 E8M0 SF）训练接入前的本机算子探测。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# torch_npu npu_dynamic_mx_quant 在 E4M3 目标下 scale_alg=0/1 均报 UInt7 不支持（CANN 9.2.0-beta.2）

## 适用场景

- 平台范围依据：source 0 seq 1996、source 0 seq 813的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 框架/模型链路：torchtitan-npu 为 DeepSeek-V4.1 Engram 表做 MXFP8（E4M3 数据 + 每 32 元素 E8M0 SF）训练接入前的本机算子探测。
- 平台/版本：Ascend NPU（本机 8 卡，CANN 9.2.0-beta.2），torch 2.14.0.dev20260719+cpu，torch_npu 2.14.0.dev20260808（source 0 seq 75）。
- 目标：确认 `torch_npu.npu_dynamic_mx_quant` 能否在设备侧产出 E4M3+SF 布局，作为 Host 侧 FP32→MXFP8 量化路径的候选。

## 触发与观测

在 NPU 上对小张量按两种 scale 算法探测（source 0 seq 60、seq 75，tool_observed）：

```text
torch 2.14.0.dev20260719+cpu torch_npu 2.14.0.dev20260808
devices 8
alg 0 ERROR RuntimeError UInt7 has not been supported
[ERROR] 2026-09-20-16:55:53 (PID:3686752, Device:0, RankID:-1) ERR01007 OPS feature not supported
alg 1 ERROR RuntimeError UInt7 has not been supported
[ERROR] 2026-09-20-16:55:53 (PID:3686752, Device:0, RankID:-1) ERR01007 OPS feature not supported
```

## 探针与操作

最小复现探针（source 0 seq 60，逐字）：

```python
x = torch.linspace(-5, 5, 256, dtype=torch.float32, device='npu').reshape(2,128)
for alg in (0, 1):
    try:
        q, s = torch_npu.npu_dynamic_mx_quant(x, axis=-1, dst_type=36, block_size=32, round_mode='rint', scale_alg=alg, dst_type_max=0.0)
        print('alg', alg, 'q', q.shape, q.dtype, 's', s.shape, s.dtype)
    except Exception as e:
        print('alg', alg, 'ERROR', type(e).__name__, str(e)[:2000])
```

结论性路线：在该版本栈上不要依赖设备侧 `npu_dynamic_mx_quant` 产出 MXFP8；本会话最终改为 Host 侧 CPU 量化（FP32 主表 + E4M3/E8M0 派生缓存），见同批候选 w30-s1-c3 的链路。

## 机制与判别

- `dst_type=36`（E4M3）+ `block_size=32` 下，scale_alg=0 与 1 两个分支抛出同一 `UInt7 has not been supported` 并伴随 `ERR01007 OPS feature not supported`，说明失败在算子能力层而非参数组合层（source 0 seq 75，tool_observed）。
- 同批源码检索显示 CANN 内置算子原型头中 `npu_dynamic_mx_quant` 的 `dst_type_max` 仅在 `DT_FLOAT4_E2M1`（scale_alg=2）场景受约束（source 0 seq 86，source_read），与本次 E4M3 失败互补，未逐项验证其它 dst_type。
- 未区分解释：是否其它 torch_npu 版本或后续 CANN 修复支持 E4M3 动态量化，本轨迹未验证。

## 验证信号

- 单次探针（本机 8 卡 NPU，CANN 9.2.0-beta.2 / torch_npu 2.14.0.dev20260808）：scale_alg=0、1 均失败，错误逐字如上（source 0 seq 75，tool_observed）。
- 无成功路径观测；不能据此推断其它版本行为。

## 适用与失效边界

- 仅覆盖 torch_npu 2.14.0.dev20260808 + CANN 9.2.0-beta.2、`dst_type=36`、`block_size=32` 的调用；未测试 FP4（E2M1）目标。
- 该探针曾出现首次执行 30 秒无输出、需等待/终止重跑的情况（source 0 seq 62、seq 76）；复现时若卡在初始化，先确认进程状态再取结果。
- 若后续 torch_npu/CANN 版本声明支持 E8M0 SF 输出，应以同探针重测后再更新结论。

## 附：断言存档

- torch_npu 2.14.0.dev20260808 + CANN 9.2.0-beta.2 下 npu_dynamic_mx_quant(dst_type=36/E4M3, block_size=32) 在 scale_alg=0 与 1 两个分支均抛 RuntimeError UInt7 has not been supported 并伴随 ERR01007 OPS feature not supported，设备侧动态 MX 量化在该栈不可用
