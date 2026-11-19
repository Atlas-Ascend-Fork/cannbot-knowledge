---
type: API
title: MoE 专家负载均衡与剪枝（torch_npu.npu_moe_update_expert）
description: torch_npu.npu_moe_update_expert：将逻辑专家映射到实际部署的专家，并按输入 mask 处理专家裁剪。 支持负载均衡和专家剪枝。 说明A3/950逻辑专家表、active前缀和相对阈值，保留伪代码下标与阈值等号的来源差异。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_update_expert.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_update_expert.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_update_expert.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_update_expert.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_update_expert.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_update_expert.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_update_expert.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_update_expert.py
  role: implementation
created_at: '2026-11-10T03:38:47Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a3
- '950'
aliases:
- torch_npu.npu_moe_update_expert
- 专家负载均衡
- 专家剪枝
---


# npu_moe_update_expert：冗余专家映射、剪枝与通信域一致

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页和同提交Schema、Meta/包装实现；未运行上游源码、测试、分布式通信或设备实验，不回推发布基线。

## 接口与应用范围

```text
npu_moe_update_expert(expert_ids, eplb_table, *,
    expert_scales=None, pruning_threshold=None, active_mask=None,
    local_rank_id=-1, world_size=-1, balance_mode=0)
    -> (balanced_expert_ids, balanced_active_mask)
```

仅A3和950PR及DT推理，单算子与TorchAir图模式；A3文档中的本卡按单DIE解释。接口为已有冗余部署表选择物理专家位置，并可生成剪枝mask，不创建副本、不迁移权重，也不自动建立通信域。必须与MoE distribute_dispatch或V2配合，不是可独立替换gating Top-K的层。

expert_ids为INT32/64(BS,K)，0<BS≤512，0<K≤16且K不超过逻辑专家数。eplb_table为INT32(L,F)，0<L<1024，首列为该逻辑专家副本数count≥1，后续1..count列为位置ID。count≤world_size，F∈[2,world_size+1]；所有count之和为物理专家总数≤1024且可被world_size整除。

文档把后续列称为物理卡号，但又以物理专家总数界定其值域，不能在多专家/卡场景中擅自解释为普通rank并截断；须与dispatch的物理专家编号、每卡部署表配套。

## 均衡选择与分布式一致

balance_mode=0按local_rank_id选择，要求0≤rank<world_size，world_size为2..768；默认-1不是有效配置。mode=1按token位置选择，不从文档默认值推导其F/通信域范围自动豁免。world_size、物理专家总数在所有卡和不同层一致，分别对应dispatch的ep_world_size、moe_expert_num；local_rank_id对应ep_rank_id。

文档mode=1伪代码直接用i%count作为表内偏移，可能选到首列count；同提交测试参考明确使用(i%count)+1，跳过首列。该测试没有在本次执行，且其实际测试配置为mode=0，因此这里只记录下标证据差异，不宣称mode=1已通过运行验证。

## 剪枝参数必须成组

expert_scales=(BS,K)、FP16/BF16/FP32，每token内降序；threshold为FP32(K,)或(1,K)，两者同时提供。active_mask可选BOOL(BS,)，给定时前两者也必传，True必须排在False之前；None表示所有token有效。

阈值按每token scale之和乘每个Top-K位置的相对threshold计算，不是直接和一个绝对标量比较。文档公式使用严格大于保留，而测试参考仅在小于时剪枝，等号行为不一致；边界相等时不能声称某一策略已由实现证明。

balanced_expert_ids同输入shape/dtype，balanced_active_mask为BOOL(BS,K)，只有有效剪枝参数存在时才有语义。生成式包装/Meta总分配mask不表示未启用剪枝时它是全True有效输出。

## 验证与关联

先校验部署表、count总数、通信域与DIE编号；用可追踪的重复专家部署比较映射及mask，覆盖active前缀边界、无剪枝和阈值附近输入。再核对dispatch收到的实际物理专家ID与有效token，不以负载较均匀单独判定映射正确。

- [分发接口](npu_moe_distribute_dispatch_v2.md)
- [路由Top-K接口](npu_moe_gating_top_k.md)

## 发布与主线双语、生成路径完整核对

发布公开产品仅A3；主线增加950PR及DT，没有增加A2。主线明确逻辑专家数L为表行数，物理专家数为count之和，K≤L；英文首段仍把表shape写成物理专家数行，与同页逻辑行数说明及中文不一致。不能把物理专家副本数直接用于逻辑expert_ids的表行寻址。

两固定schema均为生成式包装：输出ID沿用expert_ids的shape/dtype，BOOL mask按(N,K)分配，直接调用aclnnMoeUpdateExpert；Meta只按两个输入轴分配返回。这里没有扫描部署表副本数、索引值、降序权重或active前缀，也没有在Meta中验证成对剪枝输入。分配和转换器通过不替代公开参数约束。

两固定GE都是将全部输入及属性直接传给MoeUpdateExpert，没有自行计算剪枝、重建专家表或建立通信域。两份143行测试都完整静态审阅：实际配置只有balance_mode=0、开启剪枝；mode=1的+1下标只是参考分支证据。随机生成的各rank部署表不保证count总和符合全部全局一致性与整除约束，装饰器中的950也不是本次运行验证。

## 文档示例的模型接入检查

文档单算子示例把balanced_expert_ids和balanced_active_mask传给dispatch与combine，说明更新后的编号和mask需要成套消费。图示例却在dispatch中遗漏balanced_active_mask，在combine中仍传原expert_ids，不能直接作为冗余专家重映射后合并结果的正确范例。示例还打开suppress_errors，输出“success”不证明图完整捕获或数值一致。

主线把演示从16设备改为2设备、关闭共享专家并缩小K，但没有由此补齐随机表的全局部署一致性。代码中的端口、启动进程与通信初始化只作静态阅读，未执行。950范围保留PR及DT，不根据演示参数推广到其他产品或部署组合。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE 专家负载均衡与剪枝：torch_npu.npu_moe_update_expert

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将逻辑专家映射到实际部署的专家，并按输入 mask 处理专家裁剪。

### 输入、输出与行为

支持负载均衡和专家剪枝。映射后的专家表和 mask 用于 MoE 数据分发及后续处理；逻辑专家、实际部署专家与裁剪标记需要保持一致。

### 文档签名

```text
torch_npu.npu_moe_update_expert(expert_ids, eplb_table, *, expert_scales=None, pruning_threshold=None, active_mask=None, local_rank_id=-1, world_size=-1, balance_mode=0) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_update_expert.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_update_expert.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_update_expert.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_update_expert.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_update_expert.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_update_expert.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_update_expert.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_update_expert.py)（implementation）
