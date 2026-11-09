---
type: Guide
title: vLLM Ascend Qwen3.8-2.4T-A95B：大规模EP、全权重预算与加载
description: 按A3 W8A8和A2 W4A8的64-rank参考核对大模型存储、global/local拓扑和lazy加载，保留text-only及thinking约束。
  针对 Qwen3.8-2.4T-A95B 核对 A3 的 DP4、TP16、EP64 与 A2 的 DP8、TP8、EP64，以及 W8A8、W4A8、TiB容量及KV/激活预算，区分
  A3 性能配置、顶层 reasoning_effort、thinking、GPQA和PD占位。 按 A2 的95B激活量核对 MoE 中间缓冲峰值；分别核对 APC
  前缀缓存、MTP K1 与图模式，并检查匹配的算子版本。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3.8-2.4T-A95B.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.8-2.4T-A95B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-release-tag.commit
  role: constraint
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T20:37:21Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- Qwen3.8-2.4T-A95B
- Qwen3.8-2.4T
---

# vLLM Ascend Qwen3.8-2.4T-A95B：大规模EP、全权重预算与加载

## 范围与权重预算

2.4T总参数、95B激活不能只按95B分配权重内存。来源估算FP16/BF16约4.45TiB、W8A8约2.33TiB、W4A8约1.21TiB，尚需额外KV/激活/通信/loader峰值。教程基线0.23，A3四节点W8A8 DP4/TP16/EP64，A2八节点W4A8 DP8/TP8/EP64；不自动声明950/310P。

## 加载和并行

各节点同路径checkpoint/tokenizer和相同版本，W8A8用lazy Safetensors避免共享存储完整预取。global DP、local进程、TP、EP与物理设备分别核算，不能把DP×TP再无条件乘EP。MoE load balance与量化movement layout另验，不能直接套冗余专家默认值。

## 功能与验收

开放权重仅text-only，不能从Qwen3.5共享架构推多模态。thinking需保持true并按think协议解析，不能通过关thinking伪装更快性能。来源参考K1 qwen3_5_mtp、FULL_DECODE_ONLY与Fused MC2都是该配置的候选，先原精度和无新优化验证加载/输出，再检查量化专家和图。

## 失败与回退

先容量/通信smoke，再增context与每DP并发；所有ranks完整加载后才提供服务。启动OOM区分权重、prefetch、激活、cache和comm，不能只调max-model-len。失败回同权重的完整已验证布局/加载策略，保留loader日志与峰值。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## Qwen3.8-2.4T-A95B：全文与143条译文的版本边界

本节复读固定Main的Qwen3.8-2.4T-A95B.md全文719行与Qwen3.8-2.4T-A95B.po全部143条业务译文，136条msgid完全匹配，7条原串差异逐条裁决。首次支持与教程基线均为0.23.0；任务Main release pin v0.32.0、Native实际commit、镜像和checkpoint revision分别记录。qwen3.8-a3/a2镜像tag、同路径目录或简单import成功不证明实际运行包及权重身份；本次没有执行上游import、容器、加载或评测。

2.4T总参数与95B激活分别估算全权重和每token激活。当前表FP16/BF16约4.45TiB、W8A8约2.33TiB、W4A8约1.21TiB；旧PO135的4.89TB换成4.45TiB，主要是十进制/二进制近似单位换算，不能当可用HBM或含KV、激活、通信与loader峰值的最终容量上限。W4A8权重更小也不消除95B激活的中间缓冲预算。

## 两套64设备实例：global DP与节点内TP分开

| 来源实例 | 节点与实际拓扑 | 单请求与每DP调度预算 | 其他关键输入 |
| --- | --- | --- | --- |
| A3 W8A8 | 四节点、每节点16设备，DP4/TP16/EP64，local DP1 | maxlen131072、maxseq8、batch16384、memory0.85 | 每节点HCCL_BUFFSIZE_EP=2048、HCCL_BUFFSIZE=1024、execute_model timeout3000 |
| A2 W4A8 | 八节点、每节点8设备，DP8/TP8/EP64，local DP1 | maxlen262144、maxseq8、batch4096、memory0.92 | engine ready timeout7200、execute_model3000、HCCL connect/exec1800；TP_SOCKET_IFNAME及TASK_QUEUE_ENABLE=1等为来源实例输入 |

两套共64设备，EP跨节点、TP在节点内，不是TP64，也不将DP×TP再乘EP。A3最多32个、A2最多64个活动序列是按每DP seq8相加的名义调度预算，不证明全部请求同时跑满131072或262144上下文。A2较小batch限制MoE激活峰值，较高memory留KV空间；这些相互配合的来源值不能拆成适用所有硬件的最优参数。

双方实例均使用quantization=ascend、lazy Safetensors、APC、qwen3_5_mtp K1、FULL_DECODE_ONLY、enable_cpu_binding=true与enable_fused_mc2=1。lazy用于避免从共享存储完整预取checkpoint，不等于不占权重HBM、无NFS访问或任意存储都更快；A2命令也显式带lazy，不能只因说明文字强调W8A8就删掉A2选项。MC2和图仍须匹配实际算子/版本，并与无新增优化的正确性和性能基线比较。

## 主控、worker和启动阶段

先启动Node0；各worker的NODE0_IP/DP address指向Node0，LOCAL_IP与NIC_NAME来自本机，DP_START_RANK在A3为唯一1–3、A2为唯一1–7，local DP均1。worker带headless，不直接暴露HTTP API；请求发送到Node0实际SERVICE_PORT，不把DP RPC port当服务端口。HCCL_IF_IP是IP，HCCL_SOCKET_IFNAME/GLOO_SOCKET_IFNAME等是接口名。

A2显式设置VLLM_ENGINE_READY_TIMEOUT_S=7200、VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3000、HCCL_CONNECT_TIMEOUT=1800和HCCL_EXEC_TIMEOUT=1800；A3例也设置execute-model超时3000。A2还显式给出HCCL_INTRA_PCIE_ENABLE=1、TASK_QUEUE_ENABLE=1、OMP_PROC_BIND=false、OMP_NUM_THREADS=1及OPENBLAS_NUM_THREADS=1；这些是该实例的输入，不作为任意模型必需的主机或线程设置。

所有节点保持相同checkpoint/tokenizer路径及真实revision与软件版本。延长7200/3000/1800超时只改变等待预算，不修复错误地址、重复rank或不通链路。记录每节点weight-loading、graph-capture进度、共享存储性能和缓存冷热；启动耗时取决于实际环境，没有固定几分钟承诺。PO141的当前段落补充了这些条件；API application startup文字不单独证明全部ranks加载、可生成或精度已通过。

Docker例映射A3每主机16设备、A2每主机8设备，均shm1g与host网络；shm不是NPU HBM。driver、工具及权重挂载是来源输入，不能以同名目录或容器启动替代实际文件/库与通信核验。本批没有安装、修改主机或执行任何示例命令。

## 文本、thinking与请求字段

本开放权重模型来源明确text-only、保持enable_thinking=true，不从共享Qwen3.5架构推广多模态或关thinking。功能请求使用served-model-name=qwen3.8、stream=true，chat_template_kwargs含enable_thinking/preserve_thinking。reasoning_effort是Chat Completions顶层字段，示例medium、缺省xhigh，另支持low；不放进chat_template_kwargs，也不自行加入high或推广到所有Qwen模型。

文档预期先think块再最终答案、HTTP200与choices文本；这是来源协议描述，需要按真实模板、reasoning parser及streaming输出核验，不是本仓已捕获的服务响应。完整模型路径、请求的served name和客户端tokenizer/model标识保持区分。只检查import或HTTP就绪不关闭生成/量化专家/图/长上下文的验收项。

## A3性能配置不替换A2基线

8.2要求在全部四台A3上一起把maxlen131072→250000、batch16384→8192、memory0.85→0.95。它是另一个性能测试配置，不覆盖A2八节点的262144/4096/0.92，也不证明四节点A3已经达到目标SLO。PO33新段落明确A3；PO37将结果记录的TP/PP/EP更正为TP/DP/EP。FAQ泛指PP选型，不代表这些实际命令启用了pipeline parallelism。

bench例random输入8192、输出1024、num-prompts16、max-concurrency4、save-result；负载生成器使用独立环境，保存节点数、DP/TP/EP、权重revision、context、并发和reasoning effort，再比较输出与指标。不能用16个prompt或并发4证明所有名义活动序列/最大上下文性能。

GPQA Diamond来源参考为W4A8 91.92%、W8A8 93.75%，不是本仓复测，也没有补齐样本版本、seed、完整服务输入和原始输出。PO114虽exact仍把排队计入TTFT/TPOT；实际指标应按客户端/服务端采样定义，不能据该句创建通用TPOT公式，不能通过关闭thinking伪装更快性能。MTP接受率、输出质量、吞吐、TTFT、TPOT、HBM和启动时间分别留证。

## PD占位与7条差异的闭合边界

5.2只给PD基本分工与“未来更新提供详细命令”占位，没有本模型的完整connector/代理/拓扑配方。不能从397B等模型迁移启动脚本就宣称该2.4T模型PD支持或生产可用。页首PD非生产参考、MindIE Motor建议与英/中文Quick Start链接分别保留，外链正文本批未读取。

7条差异为PO25请求顶层reasoning_effort说明、PO33四A3性能范围、PO37 PP→DP、PO103/109内链措辞、PO135容量单位、PO141全节点启动上下文。PO103依然含来源“特定环境验证/仅供参考”声明，不能套35B/397B删去旧句的裁决；它也不是本仓复现证据。136条字符串匹配不代表完整实现、HTML构建映射或NPU行为已验证。

本节闭合指定模型文档与143条PO审阅；新框架适配仍按[模型支持裁决](vllm_ascend_model_support_resolution.md)、[新模型验收](../bringup/vllm_ascend_new_model_onboarding.md)与[性能评测口径](../optimization/vllm_ascend_benchmark_workflow.md)取得目标环境证据。
