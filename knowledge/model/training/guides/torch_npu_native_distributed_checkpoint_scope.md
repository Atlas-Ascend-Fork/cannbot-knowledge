---
type: Guide
title: 原生分布式检查点：保存、Planner与Stager产品边界
description: 区分DCP公开保存入口、状态转换和子方法范围，保留DefaultStager的950DT未验证标记与版本缺项。
tags:
- task.implementation
- topic.checkpointing
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-checkpoint.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-checkpoint.md
  role: constraint
created_at: '2026-11-09T13:25:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生分布式检查点：保存、Planner与Stager产品边界

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文原生支持页。来源仅给所列产品和接口的支持/约束信息；未收录不等于已证实不支持，缺少的参数与组合不补造。按A2/A3训练系列和950DT分别消费，不扩展950PR，不回推26.0/PyTorch2.8发布组合，也不证明主线与其他框架配套。本卡仅静态审阅，未执行上游、训练、进程启动或设备实验。

## 保存入口与状态转换不是同一个合同

state_dict_saver.save/save_state_dict、state_dict_loader.load_state_dict、FileSystemReader/Writer、DefaultSavePlanner及lookup_object/transform_object、DefaultLoadPlanner及lookup_tensor/transform_tensor、StagingOptions列三类产品。中文还对state_dict_saver.async_save、state_dict_loader.load和format_utils.dcp_to_torch_save/torch_save_to_dcp列三类产品，英文未收录这些条目；这不能解释为已验证任意异步保存、存储格式或版本间互换。

state_dict.get_state_dict/get_model_state_dict/get_optimizer_state_dict、set_state_dict/set_model_state_dict/set_optimizer_state_dict及StateDictOptions中文仅列A2/A3，英文明确950不支持。Stateful及load_state_dict/state_dict、optimizer.load_sharded_optimizer_state_dict亦有同样边界；后者只在2.13/2.14收录，不据旧页缺项断定运行时删除或不存在。保存入口列950不能覆盖整套状态提取、设置与恢复。

## Planner和存储后端逐层核对

StorageReader及prepare_global_plan/prepare_local_plan/read_data/read_metadata/reset/set_up_storage_reader列三类产品，StorageWriter及finish/prepare_global_plan/prepare_local_plan/reset/set_up_storage_writer/storage_meta/write_data同样列三类产品；两者validate_checkpoint_id却中文仅列A2/A3、英文950不支持。

LoadPlanner的commit_tensor/create_global_plan/create_local_plan/finish_plan/load_bytes/resolve_tensor/set_up_planner，SavePlanner的create_global_plan/create_local_plan/finish_plan/resolve_data/set_up_planner均列三类产品。LoadPlan、ReadItem、SavePlan、planner.WriteItem及tensor_storage_size则中文仅列A2/A3、英文950不支持，不由Planner父类的支持补全这些对象。

format_utils.BroadcastingTorchSaveReader类及read_metadata/prepare_local_plan/prepare_global_plan/reset/set_up_storage_reader/validate_checkpoint_id仅列A2/A3、英文950不支持，read_data单独列三类产品。DynamicMetaLoadPlanner也有较窄范围。单个读取方法支持不等于该reader完整构造和加载流程可用。

metadata.MetadataIndex列三类产品；StorageMeta只在2.13/2.14收录，列三类产品；TensorProperties及create_from_tensor仅2.13中英文收录，中文没有独立类级表、方法三类支持，英文类和方法均三类支持。planner.TensorWriteData仅中文2.13列三类产品，不把2.14缺项解释为包中移除。

## Staging的“未验证”保持独立

BlockingAsyncStager及stage/synchronize_staging、AsyncStager及should_synchronize_after_execute/stage/synchronize_staging中文只列A2/A3，英文明确950不支持。DefaultStager及close/stage/synchronize_staging从2.9..2.14收录，950标为“未验证（A5无多卡环境）”；这是来源未验证的原因文字，不把A5与所有950型号建立硬件映射，也不改写成950不支持或支持。StagingOptions与DefaultStager类的支持层次分开。

来源的中文NPU条件注释存在重复、嵌套及跨条目残留，不能仅取外层注释自动扩展产品；上述结论按可见表、对应类/方法及英文对照保留。支持清单没有写入原子性、文件布局、async future完成、Host buffer所有权及故障恢复的完整协议，不能把函数名和产品表当作端到端恢复方案。

## 验收边界

固定各rank、分片、优化器、planner/stager、保存介质和包版本，检查保存完成时点、恢复后的参数/状态与下一步数值，再测停顿、Host/设备内存和I/O。DCP是训练状态检查点，与[激活重计算](torch_npu_native_checkpoint_boundaries.md)及[普通序列化Storage语义](../../inference/guides/optimization/torch_npu/torch_npu_native_storage_scope.md)分别处理；本卡未导出、加载或反序列化检查点。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-checkpoint.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-checkpoint.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-checkpoint.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-checkpoint.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-checkpoint.md)（constraint）
