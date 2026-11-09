---
type: Guide
title: vLLM Ascend Netloader：逐 rank 权重源与量化缓存
description: 通过 netloader 插件复用已加载实例的权重，核对 SOURCE 优先级、TP 分区、MTP 端口与 INT8 原始参数保存，并用默认加载作基线。 补充当前 processed-layout/manifest、NZ与W4A8传输、握手边界、回退清理及target/draft同步。
tags:
- task.implementation
- topic.checkpointing
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/netloader.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/netloader.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/netloader_flowchart.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/netloader_timing_diagram.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/netloader/netloader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/netloader/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/netloader/load.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/netloader/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/netloader/executor/elastic_load.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/netloader/executor/netloader_pg.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/netloader/interaction/elastic.py
  role: implementation
created_at: '2026-10-29T09:49:02Z'
updated_at: '2026-11-03T04:59:20Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- ModelNetLoaderElastic
- P2PLoad
- P2PSend
- ElasticClient
- ElasticServer
- cache_processed_layout_transfer_manifest
---

# vLLM Ascend Netloader：逐 rank 权重源与量化缓存

## 范围与工作流

draft：来源列测试模型但没有具体硬件表。load-format=netloader 注册model loader，server预加载、client按匹配模型与分区用HCCL send/recv按参数顺序接收。client模型结构和rank数据源须一致，不能只核对served-model-name。

## 配置契约

model-loader-extra-config 中 SOURCE 为每device_id的endpoints；CONFIG_FILE内SOURCE优先于直接JSON SOURCE。缺或空SOURCE回default loader，必须从日志确认实际transfer，否则启动快慢不能归给Netloader。MODEL默认model参数，用于一致性检查。

每worker独立listener，实际LISTEN_PORT+RANK；draft/MTP另加10000，要预留完整范围而非只检查base<=65535。不可用/超范围影响listener。INT8_CACHE可hbm/dram/no，默认no不保存原始int8的特定处理状态，量化时可能不一致；名称过滤决定保存范围，HBM方案有额外权重副本成本。

## 验收与回退

保留足够HCCL连接内存，VLLM_SLEEP_WHEN_IDLE是来源对连接稳定性的建议，须与当前版本行为核对。以相同模型revision、量化、TP/PP和参数顺序对比storage/default loader；检查全部ranks载入、量化post-load参数、greedy输出和实际精度，不仅比较TP0成功。

测进程到ready、传输带宽、seed推理延迟及新增内存；断源/分区不匹配需观察错误/回退。恢复default loader并重载完整权重，不能服务部分传输参数。本次未启动server/client或复测来源测试模型。


## 中文资料、配置范围与验收口径

固定netloader.po的29条有效非空翻译已与当前英文全文对照，0obsolete/fuzzy且全部msgid精确匹配。它保留SOURCE优先级、逐rank端口、量化缓存、MTP端口偏移和测试模型声明，不提供新的硬件支持矩阵或真实权重传输结果。

CONFIG_FILE内SOURCE优先这条契约只限定该字段，不能推导文件里的所有选项都按同一规则覆盖。INT8_CACHE_NAME的None在文档中表示不过滤；具体哪些dtype/量化后处理状态须保存仍需核对模型实现，不能仅凭“传输完毕”推断参数完整。设置OUTPUT_PREFIX时文档约定每rank写{OUTPUT_PREFIX}{RANK}.txt，内容IP:Port；地址文件存在不是模型/分区匹配、内容校验或客户端已成功接管的证据。

英文与译文把连接内存写作HCCL_BUFFERSIZE、默认约200MB；本批没有核验安装HCCL/CANN实际识别的变量名、默认值或多组连接占用，不能把这串文档名称和近似值直接当作通用生效参数/固定内存预算。按真实版本与所有rank的观测留容量。

文档temperature=0比较输出是最小一致性探针，不等于全部模型确定性、量化数值正确或完整精度验收；与默认storage loader保留同一checkpoint、分区/参数顺序及后处理基线。Netloader代码的全部协议/并发/错误清理仍需继续生产，本次只是文档与中文语义入库，没有启动listener或发送权重。

## 图示中的握手、传输与加载阶段

流程图把已有健康实例的ElasticServer与新实例的ElasticClient分开：client发起pull并附模型信息，验证成功才返回HCCL进程组建立信息，失败拒绝连接，再以P2PSend/P2PRecv传权重。时序图进一步区分loader构造、模型结构初始化、sources选择、参数一致性握手、P2PLoad和可选server监听/后处理。

这些阶段索引不证明协议有完整数值checksum或事务回滚，也不能把连接被接受、recv结束与量化post-load已完成混为同一验收信号。逐rank数据源、实际参数顺序、量化缓存和默认loader基线仍按本卡原合同；本次没有建立连接或运行传输。


## 当前源码对文档表述的修正与完整加载阶段

补入固定 Main ceac1a2 的 netloader 包七个实现文件；未建立 TCP/HCCL 或执行上游。上文文档中的 INT8_CACHE=no 风险是文档描述，当前代码已有 processed-layout 传输：不是一律丢弃量化后状态，而是在收发前处理并登记实际推理 Tensor。两种模式必须按下述顺序区分，不能混用原始权重与后处理布局。

| 模式 | seed/server | client | 后处理要求 |
| --- | --- | --- | --- |
| no | 权重完成 process_weights、同步、缓存 manifest 后注册 server | 先构造并预处理本地布局，再接收已处理 Tensor | 成功接收后不重复做同一量化后处理；校验实际派生属性与布局 |
| hbm/dram | server 在后处理前保存匹配名字的 int8 参数；HBM clone 失败退 DRAM | 接收原始参数；draft 在该模式强制用 hbm 缓存协议 | 接收后执行 process_weights；不能把 no 模式的 manifest 当这一路径的参数全集 |

配置源码也比原文更明确：CONFIG_FILE 成功读出后使用整份 config 对象，并非只替换 SOURCE；文件缺失/JSON失败才回 extra JSON，随后逐字段类型检查/转默认值。直接 extra 非 dict 会拒绝。INT8_CACHE 统一小写；INT8_CACHE_NAME 只检查为 list，没有替每个元素建立严格类型合同。Agent 应保存解析后的实际选项，不把文档局部优先级说明扩成不存在的逐字段合并。

## processed-layout 收集、manifest 与 NZ 传输

manifest 收集非 meta、非空且 device=npu 的 named_parameters、buffers 及公开 module attributes；Tensor 按 data_ptr 去重。list/tuple/dict 可递归，对普通对象仅 impl 属性深扫，并跳过私有属性、Module 和 callable。MLA/SFA 的 W_UV/W_UK_T、派生 scale 因此可能被纳入；新模型把必要状态藏在私有/其他对象时不会自动被收集。仅 data_ptr 相同也不验证不同 view 是否逻辑等价。

服务端在 process_weights 后登记名称到 shape；客户端在 HCCL 前核每项名称存在且 numel 一致，收完后按 manifest view 成 seed shape。相同元素数但 shape 不同是允许情况；缺项/numel不符提前失败。manifest 缺失或空时相关 helper 直接返回成功，不提供强制协议版本保证；它也不验证 dtype、参数顺序、checkpoint checksum 或全部语义一致。

传输用 contiguous FRACTAL_ND，收到后按本地目标是否 NZ 决定恢复。W4A8 的 int32 view 底层仍是 int8 NZ tile，转换需先 view(int8)、contiguous.clone 打断 view 链，再 format cast 后 view(int32)；不能直接把 int32 NZ 当普通 TransData 源，且 NZ 后不能任意 contiguous 改存储。接收端给 NZ 目标新建 ND 空缓冲，不转换即将被覆盖的旧权重。numel核对、物理格式恢复和最终 view 三者是不同步骤。

原始模式发送跳过 aclnn_input_scale，接收跳过标量参数；这两个过滤器不完全相同，新模型必须核对实际 send/recv 顺序与数量。每项 send/recv 都 wait，末尾 barrier 加设备同步；processed 模式与原始模式使用不同 stream 组织。完成同步仍不是数值 checksum。

## 握手与数据面故障的不同回退

逐 rank sources 按顺序尝试连接和注册，JOIN 比较 device_id、model_path 字符串、TP、PP 与可选 int8_cache。一个注册成功后不继续尝试其他源；随后 P2P 失败返回 None，外层转磁盘，不是自动在所有源上重试整次加载。model_path 相同字符串不证明同 checkpoint 内容。

client 接收 JSON 会循环拼包，限64MiB并解析完整对象；server 的 JOIN 仍只用一次 recv(1024)，不能把 client 的大 ACK 处理能力推导为对称的任意大/分片请求支持。client 发请求调用 send，server ACK 用 sendall；这些静态差异需在协议压力测试中验证，不能写成已复现网络故障。

server 的 accept 后直接串行处理注册和 P2P，再接下一连接；daemon 线程存在不等于并发传输。当前 endpoint client 用 IPv4 socket 和冒号拆分，虽然底层 process-group URI helper 会给 IPv6 加方括号，也不构成完整 IPv6 支持。find_free_port 是临时 bind 后释放，后续重新绑定仍有竞争窗口。

底层 stateless PG 会校验 world/rank、HCCL、timeout 与组名唯一，建立双 rank 群并写 PyTorch _world 注册；其名字不是完全脱离全局状态。finally 调 shutdown 并清注册，shutdown 本身失败时后续清理是否完成需要独立观察，不能只看 Python 对象释放。

## fallback 清理与 draft 协调

接收失败不能在半加载实例上继续服务。外层保存 quant_config/model_config 与注册表快照，清理失败模型的编译 hook、static_forward_context 新 key/失败模块、static_all_moe_layers、RoPE cache 和新增 EPLB layers，再丢引用、gc/empty_cache，最多两次尝试回到 allocated 基线。日志有 weakref释放与 allocated/reserved 数据；未达到基线仍会继续磁盘加载，所以“进入fallback”不是内存已全部回收的证明。

DefaultModelLoader 的 extra 只保留 enable_multithread_load、num_threads、enable_weights_track，load_format 改 auto；避免把 SOURCE/LISTEN_PORT 传给不接受它们的加载器，也避免丢失多线程选项。量化模型先 load_weights，另在适当阶段做 process_weights；非量化模型由默认 loader 完成。pre-transfer MoE 临时解包 process_weights 包装器并在 finally 恢复，不提供跨线程共同修改的锁。

target 真正弹性失败后进程级 _target_elastic_fallback 让 draft 直接磁盘加载；target 弹性成功清该标志。draft source/listener 端口另加10000，并核最终端口，不能只检查 base。分布式 target→draft 屏障只等待同节点；创建节点子组仍是所有 ranks 按相同顺序调用 new_group，不能仅让本节点 ranks 创建自己的组。

验收分别记录 pre-recv preparation、manifest、HCCL、format restore、post-load、server ready、fallback cleanup 和最终推理，覆盖源拒绝、P2P中断、numel不匹配、派生Tensor遗漏、W4A8/NZ和target/draft。旧文档未覆盖的协议细节由本节补充，任何静态路径都未在本环境执行。
