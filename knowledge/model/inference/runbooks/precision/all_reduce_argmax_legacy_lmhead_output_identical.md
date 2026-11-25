---
{
  "type": "Runbook",
  "title": "NPU BF16 all_reduce batch 维非确定累加致同输入副本 1-ULP 分叉：逐模块三角定位与 fp32 归约修复",
  "description": "minimax_m3 16 卡 NPU（attn_tp=4）BF16 推理，要求同输入 batch 副本逐 token 一致与 run-to-run 确定性（greedy）。适用任何「BF16 集合通信归约 + 逐层放大 + 对一致性有 bit 级要求」的 NPU 推理/训练路径。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# NPU BF16 all_reduce batch 维非确定累加致同输入副本 1-ULP 分叉：逐模块三角定位与 fp32 归约修复



## 适用场景

- 平台范围依据：source 0 seq 758、source 0 seq 992的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

minimax_m3 16 卡 NPU（attn_tp=4）BF16 推理，要求同输入 batch 副本逐 token 一致与 run-to-run 确定性（greedy）。适用任何「BF16 集合通信归约 + 逐层放大 + 对一致性有 bit 级要求」的 NPU 推理/训练路径。

## 触发与观测

修复 c1 后仍残留：同 rank 4 份相同输入副本 decode 约 token 16-20 分叉；两次运行输出不同。恒定幅度 1-ULP（如 6.25e-2）提示确定性排布差异而非随机噪声。

## 探针与操作

逐模块 row-diff 仪器（M3DBG）三角定位（source 0 seq 1132，逐字节选）：

```text
[M3DBG s1] L0.attn vs0=['0.000e+00', '6.250e-02', '6.250e-02', '6.250e-02'] vs1=['6.250e-02', '0.000e+00', '6.250e-02', '6.250e-02'] [M3DBG s1] L1.fa_core vs0=['0.000e+00', '5.859e-02', '6.250e-02', '5.469e-02'] vs1=['5.859e-02', '0.000e+00', '4.883e-02', '6.250e-02'] [M3DBG s1] L1.oproj_local vs0=['0.000e+00', '4.688e-02', '4.688e-02', '4.688e-02'] vs1=['4.688e-02', '0.000e+00', '4.688e-02', '4.688e-02'] [M3DBG s1] L1.attn vs0=['0.000e+00', '9.375e-02', '1.250e-01', '1.250e-01'] vs1=['9.375e-02', '0.000e+00', '1.250e-01', '1.250e-01']
```

判别链（source 0 seq 1133）：L0 子模块 fa_core=0、oproj_local=0，但 all_reduce 之后的 L0.attn≠0 → 唯一引入分叉的算子 = attn_tp 组 BF16 all_reduce。注意这是对早期「eager matmul 非确定」假设的**推翻**（seq 937/1005 的假设被三角定位数据否定）。

失败探针（negative，均 tool_observed）：`HCCL_DETERMINISTIC=true + AIV 禁用`下 4 副本仍分叉（source 0 seq 624-625）；`torch.use_deterministic_algorithms(True, warn_only=True)` 后 prefill L0.attn 仍恒为 6.250e-02 分叉（source 0 seq 1004-1005），该 flag 已在 seq 1006 回退移除。

修复（source 0 seq 1134 edit 内容，逐字节选）：

```text
- [修复] **BF16 all_reduce → fp32 all_reduce**（cast→all_reduce→cast back）：fp32 归约 ULP≈2^-23，per-slot 差降至 fp32 级、32 步内不翻 argmax。保持 eager + Legacy KV（不上 FA、不改 Paged）。embed/dense/lmhead 同类 all_reduce 一并 fp32 化以防同源累积。
```

作用面核对（source 0 seq 1177-1178）：文件内 3 处 `dist.all_reduce`（dense MLP:155、attention:592、embed:781）全部 fp32 化；`all_to_all_single`（336/346/359）是数据搬运非归约、lmhead all_gather（918）输入已 `.float()`，不需处理。

## 机制与判别

NPU all_reduce 按 tensor tiling 归约，累加顺序随内存布局（batch/pos 维）变化且与数值无关，同输入 batch slot 间产生 1-ULP 差；BF16 ULP 足以在逐层累积后翻转 greedy argmax。fp32 归约把 ULP 压到 ≈2^-23，32 token 内不再翻转。可区分解释已排除：HCCL_DETERMINISTIC 不覆盖此 batch 维行为（实测）；非通信算子（fa_core/oproj_local matmul）被三角定位证伪为源。未验证推断：更长生成步数（>32）下 fp32 ULP 是否仍不翻 argmax；FA 融合算子路径是否天然确定（本任务约束未启用）。

## 验证信号

- tool_observed：修复前 M3DBG 三角定位数据如上（seq 1132）。
- tool_observed：修复后 run A 4 副本 32 token 全同（source 0 seq 1239，rank0 outputs 1-4 逐字一致，decode average 18.18 ms）。
- tool_observed：run A vs run B 文本 byte-identical（`OUTPUT TEXT IDENTICAL: run-to-run DETERMINISTIC ✓`），run B rank1==rank0（source 0 seq 1296）。
- tool_observed：16/16 rank 完成标记、0 crash、无 NaN/Inf（source 0 seq 1299）；prefill 98.12 ms、decode 14.13 ms（run B，单次观测，非性能结论）。

## 适用与失效边界

限于 NPU HCCL 集合通信 BF16 归约的 batch 维行为；修复为轨迹内 32 token 两次运行验证，未做更长序列/多 seed 统计。fp32 cast 引入带宽与耗时开销（本次未单独量化）。若框架后续提供确定性 BF16 归约开关，可替代本 cast 方案。本条与 w21-s1-c1 正交：c1 是确定性归约错误，本条是非确定性数值噪声。

## 附：断言存档

- NPU BF16 all_reduce 按 tiling 归约，累加顺序随 batch/pos 内存布局变化，同输入 batch slot 间产生 1-ULP 差；fa_core 与 oproj_local 均 row-对称而 all_reduce 之后分叉，三角定位唯一源为 BF16 all_reduce
