---
type: Guide
title: vLLM Ascend 预览模型：Hy4 与 Step5 的镜像交付和能力边界
description: 对仅镜像提供的Hy4/Step5保留独立平台、版本和权重，禁止将未合入代码视为main源码支持，并区分预览容量与生产可靠性。 补清Hy4与Step5的DP
  rank/TP、容器网络和挂载、上下文预算与示例usage核对。 区分 Hy4 的 MTP 规格、1000g 共享内存与 HBM 预算，及 Step5 的 prefetch、共享专家
  overlap 和 EP 双语术语。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Hy4-preview.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Step-5-Preview.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Hy4-preview.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Step-5-Preview.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T17:36:53Z'
platforms:
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- Hy4
- Hy4-preview
- Step5
- Step-5-Preview
---

# vLLM Ascend 预览模型：Hy4 与 Step5 的镜像交付和能力边界

## 共同交付契约

两教程明确support代码未合入，不能通过普通main源码pip/build取得；使用指定预览镜像并记录digest和内置版本。文档位于主线不等于实现位于主线。未来合入需另冻commit复核，不能静默升级知识结论。

## 平台和规格分别核对

Hy4仅A3 hy4-a3镜像，来源基于vLLM/Ascend0.23、CANN9.0.1、TorchNPU2.10.0.post2。770B主体含dense首层、77MoE层、shared/routed专家和独立MTP，W8A8约762GB；单A3只约1K context参考，32K建议两节点。active49B不是权重驻留大小。

Step5仅950DT step5-a5-openeuler，来源基于0.27、CANN9.2.0、TorchNPU2.10.0.post4；W8A8-MXFP8、600B总/27B active，有vision与1M架构窗口。百万context需完整多节点DP4/TP4参考和实际KV预算，不由模型宣称直接成立。

## 功能与验收

只承诺对应镜像示例明确开启的能力；LoRA、PP、PD未验证，不能从通用feature指南推支持。先核镜像digest、目标硬件和量化，再加载/单请求/长输出/混batch，分别验证MTP、图和多机。source声明性能与可靠性仍在验证，不能改写为生产ready。

## 失败与回退

镜像不匹配或来源代码未找到时停止源码配方，保留可复核交付物。回指定镜像和完整配置；无法获得交付物则记录未验证，不用更改版本字符串绕过。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## 中英文全文对照：预览镜像与主线版本分别留证

新增对照固定快照的Hy4-preview.md全文322行、Step-5-Preview.md全文272行及Hy4-preview.po 70条、Step-5-Preview.po 59条译文。127条msgid与英文逐字匹配，另两条EP表头从Expert Parallel改为Expert Parallelism，描述、专家数量及enable-expert-parallel参数不变；中文“专家并行”含义保留。这种对照不证明发布站点HTML、镜像源码或真实模型执行正确。

Hy4使用quay.io/ascend/vllm-ascend:hy4-a3，仅A3；Step5使用quay.io/ascend/vllm-ascend:step5-a5-openeuler，仅950DT。两者明确代码未合入，不将最新版main、通用pip安装、其他型号镜像或Native v0.32接口当这两个镜像的实现证据。部署前保存实际digest、镜像内版本与配置；教程的Based on v0.23/v0.27及示例system_fingerprint都不能推出完整40位源码对应关系。这里没有拉取镜像或检查其内部实现。

### Hy4：单节点512与双节点96000是两套容量场景

Hy4-preview主体770B/激活49B，78层中首层Dense、其余77层MoE，每层256路由专家、Top-8另加1共享专家；独立原生MTP层约10B总参/0.7B激活。一个MTP层与num_speculative_tokens=3是不同维度，不把三token解释成三个MTP层。量化对象Eco-Tech/Hy4-preview-w8a8约762GB；活跃参数和权重文件大小都不能直接当完整运行HBM预算。

| Hy4配方 | 并行和上下文 | 并发、缓存与服务身份 |
| --- | --- | --- |
| 单A3节点 | TP16/EP，max-model-len512、batch512 | seq8、gpu-memory-utilization0.92、服务别名hy4、host127.0.0.1:8000 |
| 双A3节点混布 | 全局DP2、每节点local DP1/TP16/EP，context96000、batch1024 | seq256、gpu-memory-utilization0.85，显式prefix caching；rank0带API，另一节点headless/start-rank1 |

双节点地址指向Node1协调器、RPC12890，示例NIC/IP必须换成实际值并核对各节点HCCL/Gloo网卡。两套命令都使用HCCL_BUFFSIZE128、FULL_DECODE_ONLY、MTP3与MLAPO/fused_mc2/NPUGraph EX组合；这只是该镜像配方，不提升为所有硬件与模型通用开关。教程约1K的单节点文字说明与具体512命令、32K的双节点建议与96000上限分别保留，不能按一句说明复用另一组并发预算。

Hy4文字称A3“16卡/16NPU”，命令实际映射davinci0–15；应与物理NPU和chip/rank映射分别记录，不据措辞直接算物理设备数。Docker示例有/mnt/weight挂载和shm-size1000g，却未显式给多节点段落所称的net=host，也未映射API端口；多节点通信和host侧API可达性需先核实实际容器网络。shm配置是主机共享内存上限，不能当NPU HBM。Node1先启协调器再启动headless节点的顺序可作诊断线索，10/20分钟是来源估计，不是固定就绪超时或本仓测量。

### Step5：四个DP rank分布在两个节点

Step-5-Preview总参600B/激活27B，权重为Eco-Tech/Step-5-Preview-w8a8-mxfp8。源码安装不受支持；镜像表列HDK25.5.0、CANN9.2.0、TorchNPU2.10.0.post4及基于v0.27，不能与Hy4的CANN9.0.1/post2/基于v0.23互换。

Step5为两个950DT节点、全局DP4、每节点local DP2、每rank TP4/EP，即每节点用两个TP4组使用8个设备，DP4不表示四个物理节点。Node0承载rank0/1并设api-server-count=1；Node1 headless且data-parallel-start-rank=2承载rank2/3，协调地址为Node0、RPC13389。配方context1048576、seq256、batch2048、gpu-memory-utilization0.96，HCCL_BUFFSIZE1024，与模型架构宣称的1M窗口和所有并发都能占满该窗口是不同命题。

命令启FULL_DECODE_ONLY、MTP3、safetensors prefetch、enable_shared_expert_dp及multistream_overlap_shared_expert；未显式给quantization ascend，不能从Hy4补一个参数声称等价，也不能在未检查镜像loader时断言无需量化元数据。主线配置类的字段校验不能直接替代这套未合入镜像的实际解析。模型虽宣称支持vision，功能请求仅给文本，不能据此完成图像processor、输入分辨率或多模态质量验收。

950DT容器显式net=host并映射ummu/uburma等Device UB设备，不能直接照抄Hy4的设备映射。正文要求/mnt/weight可见，Docker片段却只挂了/root/.cache等目录；先确认WEIGHT_PATH实际位置和挂载。LOG_PATH在说明中被要求更新，但示例没有将其接入命令，不宣称日志已经写入该目录。serve绑定local_ip、端口10086，而curl示例用127.0.0.1，须按实际监听地址验证可达性。

## 功能输出与评测归属的核对

Hy4请求model=hy4、max_tokens256，示例usage为prompt25+completion176=total201；Step5请求model=step、max_tokens256，示例usage却为prompt15+completion288=total303。后者completion288大于请求256，保留这一示例不一致，不能据此推断该镜像正常忽略长度上限或已找到根因。应保存实际请求、最终生效的输出上限、token ID和finish_reason后复核；HTTP200、choices、启动日志或包含推理标记的示例文本都不等于质量合格。

Step5精度表仅报告950DT多节点混布、Step-5-Preview-w8a8-mxfp8的GPQA Diamond accuracy/gen原值93.8及MMMU-Pro accuracy/gen原值76.24，未在表中补齐单位、样本数、shot或输入处理细节。保留原口径，不转换成新模型阈值，也不归给Hy4或通用main。Hy4精度/性能和Step5性能主要给评测入口链接，没有这里新执行的分数、吞吐或长上下文稳定性结果。

验证时分列镜像交付、加载、服务身份、单请求、长度与混batch、各MTP/图/缓存开关和质量/SLO；LoRA、PP、PD仍是教程未验证范围。失败先退回同镜像的完整已记录配方，不通过修改版本字符串或跨镜像拼参数绕过。配合[新模型适配预检](../bringup/vllm_ascend_new_model_onboarding.md)与[性能基准指南](../optimization/vllm_ascend_benchmark_workflow.md)，不把源码静态知识当NPU、真实模型或Agent A/B结果。


## 预览配方的关键验收点

### Hy4：MTP 规格、共享内存和 HBM

Hy4 的原生 MTP 层数为1，一次投机预算为三token，分别核对层权重和 num_speculative_tokens，不能把层数当生成步数。Hy4 的 1000g 共享内存（shm）配置属于主机容器；HBM 仍要容纳权重、KV cache和图/运行时内存，二者没有容量替代关系。按单节点512与双节点96000各自的batch/并发组合留证，不能因共享内存上限很大就提高NPU请求预算。

### Step5：prefetch 与共享专家 overlap

Step5 的 safetensors-load-strategy=prefetch 是配方中的权重加载策略，enable_shared_expert_dp 与 multistream_overlap_shared_expert 是所列共享专家配置。加载阶段和专家执行阶段应分别保存配置与观测；启用这些参数不证明加载时间、通信重叠或端到端吞吐已经改善，也不能从仅镜像交付推断最新main的实际实现。

### EP 双语：Parallel 与 Parallelism

Hy4、Step5 两份中文PO的EP名称仍引用 Expert Parallel，当前英文已写 Expert Parallelism。这里的“专家并行”术语对应关系按已读表格描述、专家数量和 enable-expert-parallel 参数核对；标签差异不当新特性、不改写为字符串完全匹配，也不推出两镜像有相同的专家实现。
