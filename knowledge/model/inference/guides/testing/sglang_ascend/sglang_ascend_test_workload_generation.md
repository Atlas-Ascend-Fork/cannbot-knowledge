---
type: Guide
title: SGLang NPU压测输入的自然文本、共享前缀与长度复核
description: 说明固定token文本生成、全相同前缀对DSpark接受率的影响、AISBench缓存数据文件复用风险及输出长度生成不等于实际服务负载。
tags:
- task.testing
- topic.performance.analysis
- topic.data_pipeline
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/gen_dataset_fixed_len.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/test_npu_performance_utils.py
  role: implementation
created_at: '2026-11-08T12:20:22Z'
updated_at: '2026-11-08T12:20:22Z'
platforms: []
---

# SGLang NPU压测输入的自然文本、共享前缀与长度复核

pad_to_target_tokens先编码测试模板，再随机抽few-shot token作前缀，足量后截断，不足可循环第一条；最后decode再encode可能改变token数，生成器输出min/max/avg用于复核。目标长度、实际编码长度和chat template新增token必须分开。

generate_gsm8k_dataset实际只收集原题token数小于input_len的行再循环补长；docstring笼统称重复/截断全部题，不能据此保证长题也入样。它通过重复/截取文本构造性能负载，答案none，不用于证明GSM8K任务精度。

generate_gsm8k_shared_prefix_dataset把自然QA池拼至input_len的1.01倍，batch_size行完全相同，避免随机token导致DSpark draft接受率崩塌，并刻意模拟高前缀命中。全相同前缀不是普通线上请求分布；应同时测无共享和指定命中率负载，不把该结果外推普遍吞吐。

generate_random_dataset从真实ShareGPT首轮文本调整长度，按[target×range_ratio,target]抽输入/输出长，默认ratio1为固定。输出JSON只写human文本和gpt的none，函数虽采样并打印output_lens，其值没有逐行写成目标输出参数，最终输出长度仍取决于benchmark服务参数；不能把打印总数当实际已生成token。

AISBench wrapper复用/tmp/datasets/test.jsonl等已有文件，只有文件不存在才按当前参数生成；改模型tokenizer、shape或数据类型时可能沿用旧文件。复现需绑定文件hash、生成参数和实际长度分布，特别是多个数据类型共用路径。多模态还需记录图片数量/分辨率及编码后token。

本次只审阅生成流程，未下载数据或运行生成器/压测。
