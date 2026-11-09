---
type: Runbook
title: vLLM Ascend MS Service Metric 指标缺失或旧值：recorder与EPLB热度口径
description: 围绕 safe_recording、register_metrics、latest_expert_hotness 排查无指标、旧值和异常imbalance，区分原函数失败、EP组rank0、策略提案与实际迁移收益。
tags:
- task.debugging
- task.optimization
- topic.performance.analysis
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/handlers/common.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/handlers/eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/handlers/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/provider.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/config/base_metrics.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/config/eplb_metrics.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/eplb_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/ms_service_metric.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/observability/test_ms_metrics_provider.py
  role: supporting
created_at: '2026-10-29T21:04:05Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T21:04:05Z'
---

# vLLM Ascend MS Service Metric 指标缺失或旧值：recorder与EPLB热度口径


## 触发、范围与先验

服务有输出但指标缺失、/metrics只有旧样本、EPLB updated imbalance变好而时延没改善，或录制报错但业务继续。固定Ascend ceac；整项工具平台未定位，保持draft/空平台。这里只读Core接线、handler、410行EPLB worker与测试定义，未执行Core/HTTP/Prometheus、子进程或NPU。

先按[provider接入指南](../../guides/optimization/vllm_ascend_ms_service_metric_provider.md)确认真实版本、entrypoint、打包YAML、Runner、MS_SERVICE_METRIC_CONFIG_PATH与PROMETHEUS_MULTIPROC_DIR。原始endpoint、旧文件、声明symbol和某一条成功样本分别取证，不能把它们合并成全链路采集成功。

## safe_recording保护的阶段

eplb_do_update_hotness_handler先调用original_func(worker,*args,**kwargs)，取得result后才进入safe_recording("expert_hotness")。录制代码抛Exception会warning并保留既有result；原函数自身异常在保护范围外，会照常传播。模块导入、Core factory/schema或调用handler之前的错误也不由此contextmanager统一隔离，不能把“指标失败不改变结果”推广到所有阶段。

rank_id不是0、latest_expert_hotness为空或get_metric_recorder不可用时，handler直接返回原result；没有recorder只记DEBUG，不必出现warning。跳过不等于业务没执行；也不能用没有warning证明handler真的进了录制分支。

## recorder缓存与部分注册

MetricSpec包含name、metric_type、label_names；register_metrics按get_metric_recorder返回对象的身份is缓存，feature自己的字典和recorder_key隔离spec组。相同对象已注册则复用，换新对象则逐spec重新get_or_create_metric；不是全局按metric名称永不重注册，也不检查同一recorder内spec是否已被外部改动。

循环全部成功后才把recorder写入缓存。如果中间一项失败，前面可能已创建部分指标，缓存尚未更新，后续调用可从头重试；这不是整组原子注册或回滚。Core的get_or_create幂等/类型冲突、线程并发和对象生命周期需要对应版本验证。recorders字典自身无额外锁，不能据一次顺序mock断言推导任意并发下只注册一次。

## EPLB gauge到底在量什么

_EPLB_METRIC_SPECS注册5个gauge：eplb:expert_hotness:current_mean、eplb:expert_hotness:current_max、eplb:expert_hotness:update_mean、eplb:expert_hotness:update_max，以及带layer标签的eplb:expert_hotness:imbalance。

前四个label为rank/phase，汇总phase=all；逐层imbalance使用phase=current或update、layer为enumerate索引字符串。rank取worker.rank_id，而它来自EP group rank_in_group，不自动等于world/global rank；多EP组、DP与进程的全局唯一身份及聚合方式需核对Core附加labels。不能只按rank=0当成整个集群唯一worker。

EplbWorker._calculate_hotness按逻辑expert id汇聚负载；_compute_imbalance先按各expert副本数拆分hotness，再求每rank的stage_load，以max(stage_load)/mean(stage_load)得到每层比值，最后取层间mean/max。因此current_mean/current_max是层不均衡比值的汇总，不是原始热度均值/最大值、请求时延或设备利用率。

multi_stage路径先对load_info.sum(0)求hotness。_compute_imbalance没有在该函数显式处理零mean、空层或非有限比值；handler的float转换也没有主动排除NaN/inf。目标Core是否接受/过滤这些数值、本机真实零负载行为未验证，不把异常gauge自动解释成路由/硬件故障。

## 提案、旧快照和真实迁移分别看

do_update以同一份observed hotness分别评估old_placement和策略new_placement，并在rank0写latest_expert_hotness；随后check_expert_placement仍可能把不合法的新行恢复成旧放置。updated gauge甚至不一定描述最终被接受的placement，更不是执行完D2D后的新实测负载。

load_info为None时do_update提前返回，没有清空先前latest_expert_hotness。handler只检查字典非空，不检查本次result、generation、时间戳或是否真有新热度，所以可能在一次无更新调用后再次录制旧快照。EPLB old snapshot与Prometheus多进程目录遗留是两种不同来源；先核对算法波次/快照新鲜度，再判断监控是否陈旧。

实际weight/map提交、接收ack与生效forward在其他消费者。do_update返回前只是整理packed_update_info；EplbProcess还要通过容量1的block_update_q发布，队列满时busy-wait。函数计时不自动包含后续IPC背压、逐层应用、设备同步与迁移收益，须对齐[真实EPLB重排](../../guides/optimization/vllm_ascend_eplb_runner_and_movement.md)的cycle/committed证据。

## 子进程与真实函数接线

EplbProcess.worker_process会尝试initialize_vllm_metric/get_vllm_adapter；异常仅warning，之后仍可继续EPLB循环，因此子进程运行不证明recorder初始化成功。_launch_process直接用multiprocessing.Process，注释写spawn不构成它在所有环境强制同一启动方式的证明。

内置base_metrics含V1 execute_model/_prepare_inputs、特定scheduler和worker warmup；V2或其他自定义框架不从同名概念自动获得hook。固定YAML中同一execute_model有DP初始化和phase两条，外部Core的实际组合/包装次序未在本仓实现。AST能找到12个声明方法只能排除一种“源码不存在”情况，不能证明动态patch、子进程、resolver或返回结构均符合handler预期。

## 检查与验证信号

| 观测 | 先核对 | 不能据此直接下结论 |
| --- | --- | --- |
| 无EPLB gauge | EP组rank、latest快照、子进程adapter、recorder与注册错误 | EPLB从未执行或所有rank都必须单独有同一组样本 |
| gauge不变/重复旧值 | 本次load_info、波次、提案生成、输出目录是否属当前实例 | 没有新样本或迁移已成功/失败 |
| updated ratio下降但TPOT不变 | 接受的placement、后续权重提交/实际forward、相同负载与窗口 | 策略理论比值就等于端到端收益 |
| recording warning | 原函数是否成功返回、哪个注册/record阶段失败、partial state | 原始推理异常已被安全吞掉 |
| duration或内存分项可见 | handler类型/默认值、异步边界、实际版本和采样进程 | histogram默认类型、内存恒等式或NPU耗时已验证 |

保存版本/provider/配置、原函数结果或错误、EP/全局进程身份、快照/placement时间线、recorder切换与Prometheus原样本。修复后以同负载验证新鲜样本和关闭采集后的精度/时延；缺乏当前波次/接线/有限值证据时停止收益归因。

327行上游测试定义用FakeMetricProvider/recorder与AST验证入口、12条配置、identity缓存、rank跳过和recording失败保留result；本次未执行，未取得真实Core/NPU/服务证明。外部默认值、并发注册、进程间汇聚与全部硬件/模型仍为后续边界。
