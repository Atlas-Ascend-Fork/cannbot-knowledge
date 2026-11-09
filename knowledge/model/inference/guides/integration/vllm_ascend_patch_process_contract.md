---
type: Guide
title: vLLM Ascend Patch 接入：进程边界、导入时机与退出计划
description: 优先使用上游扩展点，必要patch按Main/Worker/EngineCore分清消费位置，固定版本谓词、注册与测试，并保留后续上游化和删除条件。
tags:
- task.implementation
- topic.architecture
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/patch.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_engine_core.py
  role: implementation
created_at: '2026-10-29T09:54:45Z'
updated_at: '2026-10-29T13:13:15Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Patch 接入：进程边界、导入时机与退出计划

## 范围与选择

本卡是四类插件平台的patch接入核对流程，不扩大具体patch的硬件支持。先确认ModelRegistry、platform接口、custom op或loader等扩展点能否承载；必要patch保持最小目标，并记录问题、上游PR/缺少原因、删除计划和精确版本条件。

## 进程与导入契约

platform patch在NPUPlatform.pre_register_and_update早期应用，用于Main侧参数/配置路径；worker patch在Worker初始化应用。不能在主进程改symbol后假设spawn出来的worker自然继承。先确认实际函数在哪里执行、导入是否已经绑定局部引用，再选择注册位置。

来源V1 engine区分Main、EngineCore、Worker；默认patch入口不自动覆盖EngineCore。文档建议整类覆盖的旧路径仅是该设计的实现办法，当前版本优先核对可用扩展接口与实际EngineCore派生类，不机械复制旧类实现。310P等特殊Worker需单独检查import链。

## 版本谓词与测试

patch文件加入对应__init__导入并登记Why/How/Future Plan。开发版本suffix可能使旧版本匹配失效；VLLM_VERSION只能在真实兼容基础上帮助版本识别，不能伪装依赖或绕过API变更。

验证在线/离线、实际进程、匹配与不匹配版本、重复导入及无patch路径；检查目标symbol和调用行为，而非只看文件被import。kernel调用仍需设备验证。相邻进程未生效、版本谓词过宽或新上游API已替代时，停止扩大patch，恢复已知实现并清理临时覆盖。本次未修改vLLM/Ascend上游或运行patch测试。


## 当前EngineCore集中入口

固定实现patch_engine_core.py保存原EngineCoreProc.run_engine_core并用staticmethod包裹，以_PATCHED防止重复安装；入口初始化AscendConfig，按需安装CPP profiling，再选择Dyntra或balance的DPEngineCoreProc后调用原入口。上游需在调用时通过模块全局名解析该类，若改成提前绑定，单纯替换模块符号将失效。

这是当前集中实现，不是设计中旧的整类拷贝。代码选择分支没有关闭时恢复原DPEngineCoreProc的else语句，不能将balance设计伪码中的restore说明当现有保证。同进程多配置及子进程unpickle/import均需检查真正的类和行为；[Balance版本诊断](../../runbooks/runtime/vllm_ascend_balance_scheduler_version_drift.md)说明了为什么源码意图或局部测试名称不足以证明兼容。


## 按名导入的实际例子

固定MRv2 DSpark loader的Ascend wrapper同时改utils和speculator两个模块绑定，临时量化/embedding解析在finally恢复，target手工PP分区只在草稿加载上下文屏蔽，见[量化与PP隔离诊断](../../runbooks/runtime/vllm_ascend_dspark_draft_quant_loading.md)。这说明“模块全局已替换”不能证明提前绑定的另一个调用点已生效；也不能由finally恢复推导并发加载线程隔离。
