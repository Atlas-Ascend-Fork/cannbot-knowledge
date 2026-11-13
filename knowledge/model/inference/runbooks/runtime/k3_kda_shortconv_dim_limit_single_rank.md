---
{
  "type": "Runbook",
  "title": "单机（attn_tp=1）裁剪 K3 的 KDA ShortConv 触发 dim∈（64,16384） 上限：根因是并行度改变而非算子缺陷",
  "description": "单机（attn_tp=1）裁剪 K3 的 KDA ShortConv 报 dim must be in [64,16384], but got 36864：超限由并行度改变而非算子缺陷；把 linear_attn_config.num_heads 降 32 即过。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 单机（attn_tp=1）裁剪 K3 的 KDA ShortConv 触发 dim∈（64,16384） 上限：根因是并行度改变而非算子缺陷


## 适用场景
cann-recipes-infer 单机（world_size=1）裁剪/缩小版 kimi k3 smoke 推理的启动排障：从完整多卡配置迁移到单卡时算子入参超限的定界。

## 触发与观测
Prefill 在 KDA ShortConv 的 causal_conv1d_fn 处崩溃，报 dim must be in [64, 16384], but got 36864（此前环境、tokenizer、模型构造已通过）。

## 探针与操作
操作：读崩溃 traceback 定位调用点（modeling_kimi_k3.py 的 causal_conv1d_fn 包装）与配置；核算 qkv_projection_size = 3 × num_heads × head_dim；修改模型目录 config.json 的 linear_attn_config.num_heads 后重跑验证。触发报错与验证预期：

```text
RuntimeError: call aclnnCausalConv1dFn failed, detail:[PID: 4059] 2026-10-29-13:43:40.703.685 AclNN_Parameter_Error(EZ1001): dim must be in [64, 16384], but got 36864.
```


```text
KDA heads: 32
KDA head_dim: 128
QKV dim: 12288
within limit: True
```


## 机制与判别
判别：超限完全由并行度改变（单机 attn_tp=1 裁剪）导致而非算子缺陷；修复只动 linear_attn_config.num_heads，不动 num_attention_heads（Gated MLA 独立配置）。

关键结论：

- 单机 smoke 的 Prefill 在 causal_conv1d_fn 处报 RuntimeError: call aclnnCausalConv1dFn failed ... AclNN_Parameter_Error(EZ1001): dim must be in [64, 16384], but got 36864。
- 修复：把模型目录 config.json 的 text_config.linear_attn_config.num_heads 降为 32（qkv=12288 ≤ 16384，预期校验输出 KDA heads: 32 / QKV dim: 12288 / within limit: True（脚本预测值；实测依据为修复后运行推进至 MoE Prefill、不再报 conv 维度错误））；num_attention_heads=96 是 Gated MLA 独立配置不能改；修复后运行推进至 MoE Prefill（后续错误不再是 conv 维度）。

## 验证信号
验证层级：device_functional（修复后在远端 NPU 实际重跑：运行推进至 MoE Prefill 阶段并报出下一类错误，证明 conv 维度已通过）。客观信号：崩溃日志（工具结果内含完整报错行）、修复后运行日志。

验证范围：来源单卡 smoke 观测，不代表原模型精度已验证。

## 适用与失效边界
适用：单机裁剪 K3/类似 KDA 混合注意力模型的单卡迁移排障。失效边界：1) num_heads=32 只是把 qkv 压到 12288≤16384 的 smoke 值，改变了模型语义，不能用于精度评估；2) 超限根因是 per-rank head 数×3 的 qkv 拼接维度，若后续版本拆分 q/k/v 投影则上限判据不同；3) 修复后暴露的 MoE process group 问题见 [单卡 MoE 未初始化进程组诊断](k3_moe_all_to_all_world_size_1_no_pg.md)，本卡不覆盖。
