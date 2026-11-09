---
type: Guide
title: vLLM Ascend 多节点测试：LWS、内部与外部DP及运行证据
description: 按multi_node配置选择internal/external运行时，核对LWS与本地主机、节点rank/设备预算、LOG_PREFIX和就绪顺序，保留pytest/AOP返回、各节点日志及benchmark产物的限定。
aliases:
- multi_node_test.md
- multi_node_test.po
- dp_load_balancing
- LWS_WORKER_INDEX
- _e2e_nightly_multi_node.yaml
- external_dp_logs
- AOP_RUN_FINISHED
- ExternalDPConfigLoader
- RankResolver
- MultiNodeConfigLoader
- multi-node CI
tags:
- task.testing
- task.implementation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/multi_node_test.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/multi_node_test.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/run.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/test_multi_node.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/dp_mode.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_e2e_nightly_multi_node.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/lws.yaml.jinja2
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/download_archive.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V3.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_1-W8A8-EP-external.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/internal_dp/multi_node_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/external_dp_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/internal_dp/test_multi_node.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/test_external_dp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/runtime.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/benchmark_results.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/internal_dp/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/deployment.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/workflow.png
  role: supporting
created_at: '2026-10-31T03:11:47Z'
updated_at: '2026-11-03T01:29:41Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 多节点测试：LWS、内部与外部DP及运行证据

## 任务与范围

在已有集群或准备好的主机上，为新模型建立可复核的多节点测试：选择内部或外部DP运行时、对齐配置与真实节点/rank，分别收集启动、请求、基准和退出证据。固定Ascend ceac提交的multi_node_test.md全556行与中文58条已对照，公共入口、配置加载、两个运行时及LWS复用工作流按生产证据记录阅读范围；外部Kubernetes/LWS控制器、RemoteOpenAIServer完整依赖与全部模型组合仍需另验。没有整项流程的硬件支持集合，保持draft/platforms=[]。

Nightly触发与PR矩阵选择见[派发合同](vllm_ascend_nightly_ci_dispatch_contract.md)；Ray服务部署见[Ray多机启动](../deployment/vllm_ascend_ray_multinode_bootstrap.md)。这里消费的是多节点测试编排，Pod就绪、pytest结果、基准达标和产物完整性分别判定。

## 配置路径与运行时分派

公共tests/e2e/common/multi_node/test_multi_node.py先读取dp_load_balancing，只导入选中的运行时：external同步调用test_external_dp，internal await内部异步入口。显式值经str.lower后须为internal/external，没有strip；缺字段才按路径是否含/external_dp/走历史回退。模型家族目录configs/GLM并不会自动选择external，新增配置必须显式声明；文档最初YAML草图漏了该字段，不能复制后假设正确分派。

CONFIG_YAML_PATH既可为实际路径也可为文件名；相对路径若当前目录已有同名文件会直接使用，否则再拼CONFIG_BASE_PATH。分派器与具体loader默认目录不同，不依赖模糊文件名或工作目录。记录最终绝对路径、文件内容/SHA、所选模式和有效配置；字段存在不证明文件确实来自目标PR。

内部模式要求model、deployment、num_nodes、npu_per_node、benchmarks，deployment长度等于num_nodes，逐节点envs存在。server_cmd是整条字符串，headless只按包含--headless识别；网络环境由节点IP匹配NIC后补HCCL/GLOO/TP接口，不能单凭这几项当完整CLI/设备预算校验。

外部模式要求routing、config、templates及节点/模型/benchmark字段，每节点配置与模板数和num_nodes一致，server_cmd_template必须为参数列表。当前routing.type只支持disaggregated_prefill；实现将proxy_node_index固定0、proxy_port固定1999，不能通过添加同名YAML字段就假设自定义生效。

## 拓扑、地址与设备预算

非LWS环境提供按节点顺序排列的cluster_hosts，数量须等于num_nodes；这只是长度检查，不证明地址互通或互不重复。每节点LWS_WORKER_INDEX从0开始且对应同一主机表。公共helper对非空worker index直接int转换，没有在这里完成范围校验；省略时按本机hostname解析地址匹配，不能保证发现实际路由网卡。使用所有节点可达的主机IP，不复制每台机器各自的Docker桥接地址。

无显式主机表时，公共helper从LWS_LEADER_ADDRESS生成leader及worker DNS并重试解析。环境注入属于外部LWS控制器合同，本次没有部署CRD或验证集群。逻辑表与DNS解析成功仍需逐节点检查NPU可见设备、NIC/通信、权重/数据、运行时与端口。

内部disaggregated_prefill只要是非空mapping就会创建PD配置，并未按enabled布尔字段单独开关；enabled:false不能作为已证明的关闭方式。decoder列表必需，P/D不能重叠且有上界检查，但负下标、重复值等未在这里完整验证。服务master、PD组master、代理和headless控制端点分别记录。

外部routing.groups必须有非空prefiller/decoder，索引在范围内且不能重复；RankResolver随后要求所有节点有角色。局部DP rank=dp_rank_start+local_rank，端口=port_start+local_rank，可见设备按本地rank连续切分。每rank设备数为TP×CP×SP，再在nnodes<=1时乘PP；每节点乘dp_size_local，要求不大于npu_per_node。该算术和局部rank范围检查不验证物理设备映射、全局DP重复/缺口或所有PP协议。

外部模板先展开集群占位符，再处理${变量}和$环境变量：未知花括号变量拒绝；环境值中未知裸变量可清空，参数中未知裸变量拒绝且取已渲染env。环境插入顺序影响后续引用。最终为argv列表，无shell自动拆词。实际server manager还覆盖网络/可选KV pool环境，导出的报告命令不一定含这些最终运行时覆盖。

## 两个固定配置只作结构实例

DeepSeek-V3.yaml当前是internal、2节点、每节点16NPU，P0/D1，各DP2/local2/TP8；顶部4节点注释不是本配置。当前仅配置acc，baseline95/threshold10，OMP_NUM_THREADS=1也不同于文档草图100。它没有提供同轮性能benchmark或所有新模型通用默认值。

GLM5_1-W8A8-EP-external.yaml当前为external四节点，0/1为P、2/3为D；P全局DP4/local2/TP8/start0,2，D全局DP8/local4/TP4/start0,4，各16NPU是静态预算。模型、transformers5.2.0和量化/图/投机组合只是该用例版本配方。D模板重复给出--max-num-batched-tokens 32与4096，未核对目标CLI解析前不默选一项。该配置仅perf、无test_content，不能声称自动测试chat、accuracy或投机接受率。

## LWS与本地启动前提

复用工作流_e2e_nightly_multi_node.yaml的controller使用nightly-cpu，实际NPU在LWS pods；should_run是必填workflow_call输入。文档嵌入示例缺它，inline矩阵、schedule条件和max-parallel1也不能覆盖当前Nightly矩阵与并行阶段。size是LWS每组节点数，须再与模型num_nodes/拓扑对齐；工作流虽接受replicas，已读就绪与日志命名只处理第0组，不扩成任意副本数已验证。

当前生成模板使用同一个lws_name构造LWS与Service选择器；文档手写lws.yaml却把metadata.name设为test-server、Service选择器仍为vllm，示例vllm-0也不与之对应。应核对实际生成资源及labels，而不是用示例Pod名直接验收。模板未设置应用层readinessProbe，Running/Ready不证明所有rank或模型请求已经正常。

工作流对a3请求每节点16NPU，a5用8NPU和huawei.com/npu、/mnt/weight hostPath，其余分支另选8NPU/PVC；hostPath不自动等于跨节点共享存储。模板512Gi内存、100Gi临时盘、125CPU、512Gi shm是CI资源请求，文档15Gi shm是另一个示例，都不当全部硬件最小要求或性能推荐。

本地先启动worker再启动node0，提供WORKSPACE、IS_PR_TEST、CONFIG_YAML_PATH/BASE_PATH、LWS_WORKER_INDEX及可写、分run的LOG_PREFIX。文档称LOG_PREFIX可选，但run.sh随后在strict模式中直接引用；已准备镜像可能注入它，自包含本地命令仍须核对。run.sh前置CANN环境与工具也不能只靠导出四个变量补齐。

共享run.sh会修改git/pip镜像配置、清Ascend日志，并广泛终止python3/VLLM进程，PR模式还替换工作区和安装依赖。它是独占测试容器的有副作用入口，不作为Agent的只读探针。本批仅把命令当资料阅读，没有运行安装、进程清理或集群操作。

## 就绪、请求与测试退出

内部模式在节点0启动需要的代理并运行AISBench/保存JSON，其他节点按服务health等待结束；special_dependencies安装subprocess.call返回值未强制检查，不能以调用完pip就断言依赖已准备。

外部模式逐节点启动本地rank，先检查本地进程退出及/health（3600秒），master再等待全局非headless rank（EXTERNAL_DP_MAX_WAIT_SECONDS默认5400秒）及代理/healthcheck（默认300秒）。headless被跳过HTTP并预置ready，master全局轮询没有远端进程句柄；这些条件不证明headless独立验收。benchmark后另有30秒就绪复查。

只有test_content明确包含chat_completion或spec_decode_acceptance才走相应检查；投机接受率缺baseline会warning跳过。tokenize取首P、metrics取首D，first_server_cmd也不等于所有角色的最终配置。额外KV pool监听端口就绪只说明服务可连接，缓存一致性与真实业务仍按对应KV协议核验。

外部worker在观察node0/localrank0先ready后unready时退出，连接丢失也可满足unready；它没有直接拿到master的benchmark结论。run.sh捕获pytest管道ret，但非leader且不开AOP的路径未显式返回该失败ret；AOP的aop_done又只有文件存在，没有成功/失败值。以上为固定源码的静态控制流边界，未复现CI事故；验收需要完整各节点pytest日志及真实退出码，不能只看worker结束。

AOP启用时，leader原测试失败不会因二分成功变成通过；按run隔离的coord/worker_ready/aop_done避免旧文件混用，但等到至少1个worker不是全部worker就绪。工作流以Pod UID/containerID/restartCount核对有限日志快照，再解释带LOG_PREFIX的AOP_RUN_FINISHED标记；允许一次重启查previous，不接受替换Pod或无限重连。它是leader结果协议，不替代全部rank和benchmark完整性。

## 日志、产物与Agent交付

内部主要看run.sh终端、node_N_pytest.log与node_N_plogs；外部EXTERNAL_DP_LOG_DIR默认/tmp/external_dp_logs，各node-N/rank-N.log与node0/proxy.log分开。rank日志追加写入，Starting command只记录命令及显式覆盖env并遮盖部分敏感键，不是全部继承环境的完整快照；同目录旧首行不能证明本run。设置每实验独立目录并对齐run/attempt/config/node/rank。

AISBench outputs在重跑或Pod删除前复制到LOG_PREFIX，benchmark JSON另按BENCHMARK_JOB_NAME缓存；后者不是唯一LWS_NAME，同名并发仍可能混入/覆盖，属于静态风险。工作流优先取PVC副本，再做Pod清理；plog、stdout与外部rank日志归档都可能部分缺失。JSON task与pytest判据见[结果合同](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)，profiling独立见[采集产物](../optimization/vllm_ascend_aisbench_profile_artifacts.md)。

download_path先在容器临时文件打包，再复制到共享临时文件并mv发布；本容器成功marker与已存在归档才复用。工作流收集到至少1份即可继续，部分节点缺失只warning，continue-on-error的上传也不提供齐全保证。日志/AISBench outputs常为7天、benchmark JSON和profile索引90天；OBS对象生命周期/读取权限另核，所有名称与保留期均限定此快照。

交付包含：代码/镜像/Native实际安装身份、最终配置SHA与模式、逻辑/物理拓扑和设备映射、各rank命令及就绪证据、真实请求与完整benchmark集合、pytest/JSON/AOP分别结果、预期与实际产物及缺失说明。未检查项保持未验证；文档译文匹配、资源创建或tar非空不提升模型适配/性能结论。本批无真实集群/NPU/Agent A/B结果。

## CI部署图对应的是编排层

两张固定图将GitHub Action/测试YAML、CPU scheduler/controller、kubectl/LWS资源和实际多节点运行分开，并把run.sh与日志收集放在集群执行链。CPU controller job成功不等于NPU测试已执行，LWS资源创建也不等于每rank就绪或业务断言通过。

图中的lws.yaml、节点和日志箭头用于定位编排阶段，不替代本卡已核对的生成模板、labels、最终argv、pytest真实退出与产物齐全性；没有据图运行脚本、创建资源或改变设备配置。
