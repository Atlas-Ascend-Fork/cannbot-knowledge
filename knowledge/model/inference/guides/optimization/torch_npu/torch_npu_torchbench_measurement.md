---
type: Guide
title: TorchNPU TorchBench基准：模式选择、计时窗口与汇总缺口
description: 对照主线与发布版基准说明及局部实现，区分预置后端、同步时延、编译统计和CSV/Excel摘要的证据范围。
tags:
- task.optimization
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/benchmarks/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/common.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/extract_log.py
  role: implementation
created_at: '2026-11-09T17:03:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU TorchBench基准：模式选择、计时窗口与汇总缺口

## 固定版本与草稿原因

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf和发布提交f3ecfe4a7ef7395754da7ca2e35661a7132b519b。两份基准README没有完整产品/软件配套矩阵，表内数据也没有足够运行身份，故draft、platforms为空；不将示例加速比当本次结果，不由可选后端推定所有模型/硬件支持。

## 依赖与输入不能跟随任意最新版本

主线在benchmarks/torchbench运行，TorchBench外部仓指向fb14629994956c16d27c7a9940c5f081afbf68dc；发布版目录为benchmarks，指向9910b31cc17d175a781412fd9ca6f18a4ee04610。外部仓内容不在本卡来源内，精确外部commit与本仓固定提交是两种身份，不能混用脚本/模型清单。README的pip install torch torch_npu等无版本命令不替代软件栈配套；MLIR/AKG/Triton包按真实后端另核。

主线TORCHBENCH_DATA_PATH只覆盖使用DATA_PATH的模型数据目录，不下载数据或改变计算；普通tarball与obs.pkl/SAM权重和图片按数据要求准备。coco2017-minimal和MAML Omniglot的batch.pt仍用固定模型目录，不被该变量统一重定向。发布版说明采用旧.data布局，不能套主线全部数据步骤；本次未下载、解压或反序列化任何数据/权重。

## 执行模式和后端选择

--only选单模型，主线--model-list可给自定义清单，否则按对应列表运行；TorchBench、HuggingFace、TIMM是不同入口/模型列表。源码parser要求accuracy/performance/precision-checker三选一；dtype/AMP选择也互斥，train/eval及模型的inference-only回退需保留在结果身份中。

--execution-mode默认both，eager只做eager流程，不构建编译模型；--dump-compile-time要求both，precision-checker不能与eager-only合用。precision-checker文档只支持eager与aot_eager模块精度定位，不把它当Inductor Kernel数值已验证。

主线文档列mlir/dvm/akg/triton/triton_experimental，TIMM段仍只列前四项；发布版只列mlir/dvm/triton。主线parser另有default。README称未指定时选择最高加速比后端，但get_npu_backend实际只按当前目录npu_backend_config.json的model字段读取预置mode、首次缓存；文件缺失/坏JSON/模型未命中回dvm，没有在此现场测量并选最快。预置结果不代表当前模型、dtype、设备和环境的最优。

configure_compile_options将triton映射环境default；akg映射mlir并设置TORCHINDUCTOR_USE_AKG=1，mfusion另设对应环境。静态时默认reduce-overhead，可选max-autotune；disable-aclgraph或动态shape/batch-only会关闭triton cudagraphs及trees，并包装后续torch.compile传入关闭选项。模型/后端排除清单和MFusion条件还可能令mode=None，因此请求mode不等于捕获实际成功。包装会影响同进程后续compile；对照需保存有效配置，不能把此runner的策略推广成框架全局默认。

## 时间、窗口和编译统计

run_n_iterations在每步model_iter_fn之后调用所绑定的设备synchronize，再记录毫秒数，包含提交/执行/等待但不直接等于纯Kernel时间；CUDA/NPU同步函数由设备选择路径绑定，不能只看初始空synchronize函数判断全程没有等待。

摘要取索引int(0.3*n)至min(int(0.8*n)-1,n-1)，不是所有迭代平均。n=50时对应第16..40步共25步；Profiler另预热10步后采集，两个窗口不是同一组样本。NPU开启Profiler时还在外层采集前额外运行一次model_iter_fn以避嵌套编译/调优采集，这次在训练场景可能改变模型/优化器状态，不是无副作用的计时标记。

--dump-compile-time在accuracy分支取Dynamo统计项PyCodeCache.load_by_key_path之和再转ms，缺项仅告警；它不是所有编译器阶段与首次端到端时间的统一总和。performance分支另以5次warmup时长差估算compilation_latency，局部warmup没有显式末端设备同步；不同统计不能混写成同一“编译时间”。cold-start-latency的目标是新Triton缓存，仍不等于清空所有层级缓存或重启整个设备。

## CSV和Excel汇总的限制

| 汇总项 | 已读extract_log.py的实际行为 |
| --- | --- |
| 模型识别 | 正则只认npu/cuda后接train，不覆盖所有CPU/eval日志 |
| 精度结果 | 只查找pass_accuracy，fail_accuracy未被同样保存；空单元格不能解释成通过或无误差 |
| E2E时延 | 读取日志的avg step time，并非重新测量 |
| OP时延 | 读取eager/compile目录下第一个子项的step_trace_time.csv，取Computing列均值/1000为ms；不是全部算子时间无条件求和 |
| 多次采集 | 没有按新旧时间/设备选择，重复目录可能选到旧产物，须保留作业/模型/模式/窗口身份 |
| 比率 | eager平均/compile平均，缺值/零分母不代表无执行；E2E和Computing两种比率不应相互代替 |

CLI默认analysis.xlsx，函数默认log_analysis.xlsx，帮助文本也不一致，按真实入口参数确定。README中BERT约2.39倍E2E/1.17倍OP、Albert约1.08倍、Inception约2.01倍E2E/1.54倍OP仅为历史展示；没有本次测量，不据这些值预测新负载。

- [原生Timer等支持清单](torch_npu_native_testing_benchmark_scope.md)
- [Profiler开销和有效窗口](torch_npu_profiler_measurement_overhead.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/README.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/benchmarks/README.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/common.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/torchbench/extract_log.py)（implementation）
