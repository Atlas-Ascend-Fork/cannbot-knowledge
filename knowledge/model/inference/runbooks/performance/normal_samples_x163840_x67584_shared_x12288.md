---
{
  "type": "Runbook",
  "title": "Ascend 950PR 混 die 主机上单 rank MatMul 慢 15–17 倍：957c die 负载下不升频的诊断",
  "description": "模型/框架：Kimi-K3（4 层裁剪合成权重验证配置，BF16 权重 + MXFP4 路由专家），cann-recipes-infer 离线推理，rank4 npugraph 配置。",
  "tags": [
    "task.optimization",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# Ascend 950PR 混 die 主机上单 rank MatMul 慢 15–17 倍：957c die 负载下不升频的诊断

## 适用场景

- 平台范围依据：source 0 seq 1588、source 0 seq 1693、source 0 seq 1709的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 模型/框架：Kimi-K3（4 层裁剪合成权重验证配置，BF16 权重 + MXFP4 路由专家），cann-recipes-infer 离线推理，rank4 npugraph 配置。
- 平台：单机 8 卡 Ascend 950PR，CANN 9.0.1，驱动 25.7.rc1；`asys info -r=status` 显示设备池混用 die：device 0/7 为 `Ascend 950PR_957c`，device 1 为 `9579`，device 2–6 为 `957b`；各卡 HBM 容量也不一致（0/7=84 GiB、2–6=112 GiB、1=128 GiB）。
- 工作负载：多卡推理 profiling 分析（prefill/decode kernel_details.csv），以及空闲卡上的 torch.mm 对照微基准。

## 触发与观测

用户怀疑 ai_core 带宽异常（source 0 seq 1423、1510），要求用整网 profiling 分析 MatMul 耗时。同一作业内 4 个 rank 的 decode BF16 MatMul 出现稳定 ~17 倍差距（source 0 seq 1546，逐字工具输出）：

```text
shape | rank0 p50 us | normal(rank1-3) p50 us | slow | rank0 GB/s | normal GB/s | samples
LM head                4x7168 @ 7168x163840 |   28594.3 |    1712.1 |   16.7x |     82.1 |   1371.8 | 15/45
dense gate-up          1x7168 @ 7168x67584 |   11978.4 |     711.6 |   16.8x |     80.9 |   1361.6 | 15/45
dense/shared gate-up   1x7168 @ 7168x12288 |    2234.0 |     131.7 |   17.0x |     78.9 |   1337.5 | 15/45
latent projection      4x7168 @ 7168x3072 |     597.9 |      41.3 |   14.5x |     73.7 |   1065.4 | 15/45
dense down             1x33792 @ 33792x7168 |    5979.6 |     356.9 |   16.8x |     81.0 |   1357.5 | 15/45
shared down            1x6144 @ 6144x7168 |    1113.4 |      70.8 |   15.7x |     79.1 |   1243.7 | 15/45
```

慢 rank 的有效带宽在不同 shape 上稳定落在 ~74–82 GB/s（统一带宽上限，而非个别 shape 的 tiling 问题）；RMSNorm、Cast、SiTU、GMM 等 AI Core/Vector 算子也普遍慢 12–20 倍（source 0 seq 1718）。

## 探针与操作

1. 按 rank 分组统计 kernel_details.csv 中 MatMul/GMM 的 shape 级 p50 耗时与有效带宽（source 0 seq 1545 脚本，权重按 BF16 读取字节数估算 GB/s）。
2. 空闲卡对照微基准（torch 2.7.1+cpu / torch_npu 2.7.1.post5，`torch.mm` 各 10 轮取 p50；source 0 seq 1639、1650，逐字输出）：

```text
device 6
memory_bound {'shape': '1x7168 @ 7168x12288', 'p50_us': 151.246, 'p10_us': 148.153, 'p90_us': 152.779, 'weight_GBps': 1164.7, 'TFLOPs': 1.2}
compute_bound {'shape': '512x4096 @ 4096x4096', 'p50_us': 72.889, 'p10_us': 70.345, 'p90_us': 74.331, 'weight_GBps': 460.3, 'TFLOPs': 235.7}
device 7
memory_bound {'shape': '1x7168 @ 7168x12288', 'p50_us': 2241.356, 'p10_us': 2184.666, 'p90_us': 2355.423, 'weight_GBps': 78.6, 'TFLOPs': 0.1}
compute_bound {'shape': '512x4096 @ 4096x4096', 'p50_us': 928.303, 'p10_us': 920.561, 'p90_us': 933.02, 'weight_GBps': 36.1, 'TFLOPs': 18.5}
```

   device 7（957c）的 2241 µs 与 K3 rank0 的 2234 µs 几乎一致（source 0 seq 1718）。
3. 负载期间读实时频率与健康状态（source 0 seq 1692/1693、1708/1709，逐字输出节选）：

```text
NPU 7: Aicore Usage Rate(%) : 100 / Aicore Freq(MHZ) : 1650 / Aicore curFreq(MHZ) : 100
       Chip Name : Ascend 950PR_957c V100  (AI Core Frequency (MHZ) 100, 1650; Ring/Mata/L2buffer 100, 2200; HBM 3200)
NPU 6: Aicore Usage Rate(%) : 91  / Aicore Freq(MHZ) : 1650 / Aicore curFreq(MHZ) : 1650
       Chip Name : Ascend 950PR_957b V100  (AI Core Frequency (MHZ) 1650, 1650; Ring/Mata/L2buffer 2200, 2200)
```

4. 排除硬件故障：`npu-smi info -t current-fault-event/-t ecc/-t pcie-err` 对 device 0–3 全部为 0，health=Healthy（source 0 seq 1550）。

## 机制与判别

- 判别"957c 本来就这样（SKU 差异）"与"设备异常"：本地 CANN 平台配置对 957b/957c 给出的 Cube/Vector `ddr_rate` 建模参数相同（如 957c.ini：Cube 27 Byte/cycle/core × 1.65 GHz × 28 ≈ 1.25 TB/s；source 0 seq 1420），因此 ~17 倍差距不应视为正常规格差异。
- 判别"单卡损坏"：异常同时出现在两颗 957c（device 0 与空闲的 device 7），ECC/PCIe/fault 计数全 0，HBM 频率正常 3200 MHz；定位为 957c die 处于异常低频/受限性能状态（AI Core 使用率 100% 但 curFreq 停在 100 MHz，功耗 248 W vs 957b 406 W），疑似功耗模式、DVFS、固件或板级配置问题（未最终定因，source 0 seq 1718）。
- 判别"shape/tiling 偶发"：慢 rank 带宽上限跨 shape 一致（~80 GB/s），且空闲卡复现同样数值。
- 未验证推断：957c 不升频的底层原因（固件/功耗策略）本轨迹未闭合，需硬件/固件团队介入。

## 验证信号

- tool_observed（kernel_details.csv 统计，15 轮/shape，source 0 seq 1546）：rank0 与 rank1–3 的 17 倍差距与 ~80 GB/s 上限。
- tool_observed（空闲卡微基准，10 轮 p50，source 0 seq 1639、1650）：957b 1.16 TB/s、235.7 TFLOP/s vs 957c 78.6 GB/s、18.5 TFLOP/s。
- tool_observed（负载期间 npu-smi/asys，source 0 seq 1693、1709）：957c curFreq=100 MHz（usage 100%）vs 957b curFreq=1650 MHz（usage 91%）。
- tool_observed（source 0 seq 1550）：ECC/fault/PCIe 错误计数全 0。
- agent_narrative（source 0 seq 1718）：MTE2 ratio ≈99.6–100%、MAC ratio ≈1.4–1.6% 的 profile 汇总与最终定性。
- 单机单次会话观测；修复后回归建议 shape `1×7168 @ 7168×12288` 从 ~2.24 ms 回到 0.13–0.16 ms。

## 适用与失效边界

- 适用于 950PR 混 die 设备池上的 NPU 推理/训练性能异常排查：先按 rank 对比同 shape kernel 耗时与有效带宽，再查 die 型号（`asys info -r=status -d N`）与负载下 curFreq。
- 不适用于：非混 die 机器、已确认同 die 的场景；频率读取须在负载期间进行（空闲时 curFreq 停在 100 MHz 是正常降频，source 0 seq 1709 对照说明须带负载读数）。
- 停止条件：若 `npu-smi -t common` 显示负载下 curFreq 正常升至额定值，则本规则不解释该慢 rank，应转向 tiling/通信/调度。
- 临时规避：性能测试与部署避开 957c die 所在 device，仅用 9579/957b。

## 附：断言存档

- 混 die 950PR 机器上，落在 957c die 的 rank 其 BF16 MatMul 比同作业 957b/9579 rank 慢 15–17 倍（LM head 4x7168@7168x163840 p50 28594.3us vs 1712.1us，82.1 vs 1371.8 GB/s）
- 慢 rank 的有效带宽跨 shape 稳定在 ~74–82 GB/s（统一带宽上限，非单 shape tiling 问题），且 Vector 算子同样慢 12–20 倍
