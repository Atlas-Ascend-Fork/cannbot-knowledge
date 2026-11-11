---
type: Optimization
title: "X42: 路由选中分支消除（one-hot selector 预计算 → 只算被选中分支）"
description: "当算子在主计算之前由廉价 router/selector 产生 one-hot 选择向量（如 MoE expert router、条件计算），且输出只取被选中分支时，按 batch/token 分发任务、只执行被选中分支，可跳过其余分支的完整计算链。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X42: 路由选中分支消除（one-hot selector 预计算 → 只算被选中分支）

## 核心思路
当算子在主计算**之前**已由一个廉价 router/selector 产生 **one-hot 选择向量**（如
MoE 的 expert router、条件计算的分支选择），而输出 = sum_i sel_i · branch_i(x)
（one-hot 下即只取被选中分支），则**全部未选中分支的计算都是纯浪费**。
按 batch/token 分发，把主计算（投影 GEMM、attention、输出投影）的 task 表只映射到
被选中分支的权重/数据，跳过其余 n_branch-1 个分支的完整计算链。

## 适用场景
- 路由/门控选择式多分支算子：输出 = one-hot 选择 × 各分支计算结果（多候选层、MoE
  expert 路由、条件计算）
- router 计算代价远小于被跳过分支的代价（router 通常是少量 GEMV，被跳过的是完整
  QKV+attention+out 链）
- 分支间权重布局可按分支切块寻址（行块或列块），task→(batch, branch) 映射可在 host 拍平

## 实现要点
1. **host 读回 selector**：AIC（ASCENDC_CUBE_ONLY）核内 DataCopy+GetValue 读 GM 的 sel
   不可靠（CUBE_ONLY 核无可靠 GM 标量读），需在 router kernel 后由 host D2H 读回
   sel（仅 B×n_branch 个 float，数据量极小），计算每 batch 的 option 索引作为启动参数传入。
2. **按分支裁剪投影**：QKV/out 投影从全分支宽度（3*D_pad / 3*kv*hd_pad）裁剪为单分支
   宽度（D_pad / kv*hd_pad），每个 batch 通过 sel 选中自己的权重行块。若权重是
   [D_pad, 3*D_pad] 列块布局，需重排为 [3*D_pad, D_pad] 行块布局供按行块寻址。
3. **任务缩减**：attention 任务从 B×n_branch×H 减为 B×H，Sbuf/Pbuf 的 O(S²) 物化减
   n_branch 倍；out 投影 K 维从 3*D_pad 裁为 D_pad。
4. **压缩布局**：unpack/scatter 只搬移被选中分支的 Q/K/V 与输出。
5. **代价权衡**：小 shape 下 host D2H 同步开销可能吃掉收益，需评估触发阈值；大 shape
   收益远大于同步开销。

## 收益来源
被选中分支占全部计算的比例越低（n_branch 越大），跳过的计算越多，收益越高；上界由
router/selector 与数据搬运的固定开销决定。与 group A-reuse、kernel elimination 等策略
正交，可组合。

## 实现变体 B：AIV 侧选择免 host D2H
host D2H 读 sel 对小 shape 有固定同步回退。改为**保留全宽投影**，把 option 选择搬到
AIV kernel：新增 AIV unpack/scatter kernel（AIV 读 sel→argmax 可靠），从全宽
投影中抽取被选中 option 的 Q/K/V 并把 KV head 重复到 H，attention 任务仍从
B*n_branch*H 减为 B*H；scatter 把被选中 option 的 PV 输出写入零初始化全宽 Ocat
（未选中块贡献 0）。无 D2H、无 opt 启动参数。局限：全宽投影使投影计算量随候选数
n_branch 线性增加，对 fp32 大 shape 是主要成本（可叠加 hi/lo 3-pair 缓解）。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖全部候选分支组合与边界 shape，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与多缓冲需求，确认全宽/裁剪布局在容量内；检查 32B 对齐与分支权重切块边界。
