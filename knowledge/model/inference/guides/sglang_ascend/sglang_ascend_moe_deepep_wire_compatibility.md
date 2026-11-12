---
type: Guide
title: SGLang 昇腾 DeepEP 的通信 dtype 协商与状态生命周期
description: 说明 normal/LL dtype 优先级、新旧扩展签名兼容、NPU INT8 legacy 标志和 handle/事件配对。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/token_dispatcher/deepep.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/ep_moe/layer.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/online_moe_methods.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang 昇腾 DeepEP 的通信 dtype 协商与状态生命周期

## 输出格式协商

DeepEP dtype 依次考虑显式 `--deepep-dispatcher-output-dtype`、旧 BF16 环境变量、NVFP4 input_global_scale、normal/LL 专属 override、generic quant_config 与 runner 条件，NPU 最终默认 BF16。INT8 在 NPU 扩展中沿用 `use_fp8=True` 标志，payload 实际是 INT8；不能按参数名把 A2/A3 的通信解释为 FP8。NPU 的 NVFP4 路径明确拒绝。

normal 模式会探测扩展签名：有 use_fp8/use_mxfp4/use_mxfp8 时传 flags，否则尝试字符串 quant_mode；只有成功取得签名、但缺少上述量化形参时，BF16/INT8 才可能以空量化参数字典回退，MX 请求则失败；inspect.signature 本身不可检查时异常没有被捕获，不存在该回退保障。LL 在签名无 **kwargs 时仅保留已声明的 MX 形参，缺失形参会将值为真的请求静默丢弃，存在静态接口风险；集成方必须检查并拒绝无法表达的 MX 请求，不能把它当作已有保障。

## 状态与资源

buffer 为进程资源单例，初始化的 normal/LL 内存 hint 与 QP 配置会影响复用，不能假设每个 layer 各建独立 buffer。dispatch/combine 通过保存的 handle、counts 和事件配对，状态机依次经过 dispatch A/B、combine A/B 才恢复 initial；异步 hook 或 event wait 必须消费后再使用结果。

仅 _is_npu 且未启用 ZBAL 时，LL 传 topk_weights，并保留原 IDs 表示以避免无意义 int32→int64→int32。ZBAL 由 SGLANG_ZBAL_LOCAL_MEM_SIZE>0 启用，该分支仍将 IDs 转 int64 且不传 topk_weights。编译预热时的 TP barrier 用于避免编译时差超时，不应误解为稳态每轮 barrier。

适配扩展版本时记录真实 Python 签名、最终 dtype、handle 生命周期与正常/LL 两组输出；以 fallback BF16 或兼容版本重启回退，不能只去掉不识别的 MX 参数。本卡未运行通信或性能测试。

## 下层接口参考

- [DeepEP 普通分派与合并接口](../../apis/deepep/deepep_normal_dispatch_combine.md)
- [DeepEP 低延迟分派与合并接口](../../apis/deepep/deepep_low_latency_dispatch_combine.md)
