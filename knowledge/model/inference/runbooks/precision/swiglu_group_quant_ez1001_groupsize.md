---
{
  "type": "Runbook",
  "title": "AclNN EZ1001 scale k 维失配定位：自定义 swiglu_group_quant groupSize 与 weight_block_size 对齐诊断",
  "description": "deepseek-v4 a8float8 前向在 down_proj 的 npu_quant_matmul 报 161002/EZ1001：约束式 ceil(k_x1,128)==k_x1Scale 直接给出 k_x1=2048、k_x1Scale=64，判别为自定义 swiglu_group_quant 算子硬编码 groupSize=32 与模型 weight_block_size=[128,128] 失配（64 列 vs 要求 16 列），161002 只是包装错误码；修复 groupSize 32→128 并重编译部署。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# AclNN EZ1001 scale k 维失配定位：自定义 swiglu_group_quant groupSize 与 weight_block_size 对齐诊断
## 适用场景
deepseek-v4（cann-recipes-infer models/deepseek-v4，dav-3510/Ascend 950 平台，a8float8 量化前向）将自定义 SwigluGroupQuant 算子输出接入 npu_quant_matmul 的量化推理链路。凡自定义 group 量化算子输出 pergroup_scale 后接 block 量化矩阵乘的场景均适用。
## 触发与观测
- deepseek-v4 a8float8 前向在共享专家 down_proj 的 npu_quant_matmul 处失败：RuntimeError NPU function error: device error type 0, error code is 161002，随后的 AclNN_Parameter_Error(EZ1001) 指出 ceil(k_x1, 128) == k_x1Scale 不满足：k_x1 为 2048 而 k_x1Scale 为 64。
触发日志：

```
[rank0]: RuntimeError: npu_quant_matmul:../third_party/op-plugin/op_plugin/ops/opapi/QuantMatmulKernelNpuOpApi.cpp:297 NPU function error: device error type 0, error code is 161002
628: [rank0]: [ERROR] 2026-07-17-11:52:40 (PID:320371, Device:0, RankID:-1) ERR00100 PTA call acl api failed.
629: [rank0]: [PID: 320371] 2026-07-17-11:52:40.315.050 AclNN_Parameter_Error(EZ1001): When quantification mode is G-B or B-B quantification, matrix multiplication is (batchx1, m, k) @ (batchX2, k, n) = (batch, m, n), the k-dimension of x1Scale(pertoken_scale) and x1 need to satisfy the relationship: ceil(k_x1, 128) == k_x1Scale, actual k_x1 is 2048, k_x1Scale is 64.
```

调用链定位：modeling_deepseek.py:154 forward_a8float8 → self.down_proj(intermediate_hidden_states, pergroup_scale)。
## 探针与操作
- 探针结论：自定义算子 op_extension/swiglu_group_quant_torch.cpp 第 56 行硬编码 int64_t groupSize = 32，产生 scaleShape = {totalRows, nGroups}（nGroups = dHalf / 32，即 k 维 64 列）；而模型侧 configuration_deepseek.py:17 与 convert_config.py:98 的 weight_block_size = [128, 128]，npu_quant_matmul 要求 pertoken_scale 的 k 维 = ceil(2048/128) = 16。
探针一：读自定义算子 host 侧源码，确认 groupSize 硬编码与 scale 形状：

```
    auto sizes = xFp32.sizes();
52:     int64_t d = sizes.back();
53:     int64_t dHalf = d / 2;
54:     int64_t totalRows = xFp32.numel() / d;
55:
56:     int64_t groupSize = 32;
57:     int64_t nGroups = dHalf / groupSize;
```

其中 scaleShape = {totalRows, nGroups}（112 行），nGroups = dHalf / groupSize = 2048/32 = 64 列。
探针二：grep 模型配置确认量化块大小：configuration_deepseek.py:17 与 convert_config.py:98 均为 "weight_block_size": [128, 128]。
## 机制与判别
- 探针结论：自定义算子 op_extension/swiglu_group_quant_torch.cpp 第 56 行硬编码 int64_t groupSize = 32，产生 scaleShape = {totalRows, nGroups}（nGroups = dHalf / 32，即 k 维 64 列）；而模型侧 configuration_deepseek.py:17 与 convert_config.py:98 的 weight_block_size = [128, 128]，npu_quant_matmul 要求 pertoken_scale 的 k 维 = ceil(2048/128) = 16。
- 判别与修复：这是自定义量化算子 groupSize 与下游量化矩阵乘 weight_block_size[1] 的失配（实际 64 列 vs 要求 16 列），161002 只是包装错误码而非设备故障；方案A 将 groupSize 从 32 改为 128 对齐 weight_block_size[1]，重编译 swigluGroupQuant 并把新 libcustom_ops.so 复制到 infer.py 的加载路径。
判别：EZ1001 的约束式 ceil(k_x1,128)==k_x1Scale 直接给出两侧数值（k_x1=2048、k_x1Scale=64），对照探针结果即可区分"自定义算子 groupSize 失配"（64 列 vs 要求 16 列）与"设备故障"（161002 仅为 npu_quant_matmul 包装错误码）两个竞争假设。修复采用方案A——groupSize 32→128：

```
    int64_t groupSize = 128;
```

方案B（在 modeling 侧对 pergroup_scale 做 64→16 聚合）被弃用。修改后 make 重编译 swigluGroupQuant 并链接 libcustom_ops.so，产物时间戳更新，并复制到 infer.py 的加载路径 build_output/libcustom_ops.so。
## 验证信号
重编译与部署在轨迹内闭合：[100%] Built target custom_ops，libcustom_ops.so 时间戳从 11:33 更新到 12:04。原始 infer.sh 的复跑结果未在本轨迹内出现。
## 适用与失效边界
适用于自定义 group 量化算子 + weight_block_size 量化矩阵乘的失配诊断。失效边界：修复仅完成编译与部署级验证，infer.sh 复跑未在轨迹内执行；若下游改用其他 block_k（非 128），groupSize 需相应对齐。

## 补充机制片段
### 机制片段
```
[rank0]: RuntimeError: npu_quant_matmul:../third_party/op-plugin/op_plugin/ops/opapi/QuantMatmulKernelNpuOpApi.cpp:297 NPU function error: device error type 0, error code is 161002
628: [rank0]: [ERROR] 2026-07-17-11:52:40 (PID:320371, Device:0, RankID:-1) ERR00100 PTA call acl api failed.
629: [rank0]: [PID: 320371] 2026-07-17-11:52:40.315.050 AclNN_Parameter_Error(EZ1001): When quantification mode is G-B or B-B quantification, matrix multiplication is (batchx1, m, k) @ (batchX2, k, n) = (batch, m, n), the k-dimension of x1Scale(pertoken_scale) and x1 need to satisfy the relationship: ceil(k_x1, 128) == k_x1Scale, actual k_x1 is 2048, k_x1Scale is 64.
```
### 机制片段
```
    auto sizes = xFp32.sizes();
52:     int64_t d = sizes.back();
53:     int64_t dHalf = d / 2;
54:     int64_t totalRows = xFp32.numel() / d;
55:
56:     int64_t groupSize = 32;
57:     int64_t nGroups = dHalf / groupSize;
```
### 机制片段
```
    int64_t groupSize = 128;
```
