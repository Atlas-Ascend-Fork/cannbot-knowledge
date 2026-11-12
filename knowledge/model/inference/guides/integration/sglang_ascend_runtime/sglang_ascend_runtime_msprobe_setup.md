---
type: Guide
title: SGLang精度Dump调试器的条件创建与chunked prefix门控
description: 说明msprobe缺依赖只告警但配置仍禁图/跳过warmup、可导入时seed_all副作用，以及target按Prefill后端决定chunked prefix cache而draft不改全局的规则。
tags:
- task.debugging
- topic.precision
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/model_runner_components/misc_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/serving_hook.py
  role: implementation
created_at: '2026-11-08T12:20:21Z'
updated_at: '2026-11-09T04:33:25Z'
platforms: []
---

# SGLang精度Dump调试器的条件创建与chunked prefix门控

create_msprobe_debugger在msprobe_dump_config为空时不创建；有配置但不能导入msprobe.pytorch时告警并返回None，不能把启动成功当已启用dump。正常启动参数处理只要 msprobe_dump_config 非 None，就将 Prefill/Decode 图后端设 DISABLED 并设置 skip_server_warmup=True，因为 msProbe 仅支持 eager dump；这些副作用不检查依赖能否导入，缺包也已改变图与 warmup 行为。可导入时先seed_all(mode=True)再构建PrecisionDebugger(config_path)，会影响随机性；比较精度需保存此开关与seed状态，dump本身也会干扰性能。

同模块的chunked prefix cache门控在模型加载阶段执行：draft直接返回，避免其通常非MLA配置修改共享target设置；target要求use_mla_backend且实际Prefill backend在注册支持集合，否则override禁用。判断Prefill一侧而非Decode后端，OOT能力需在init_backend注册后才可见。

调试时核对是否得到真实debugger、配置文件、输出和所用库版本，并通过固定输入在相同dtype/并行/缓存条件下比对；没有dump时不要以空输出认定无差异。chunked prefix开关需同时检查最终配置和模型/Prefill实现，启用缓存并不保证每请求均命中。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
