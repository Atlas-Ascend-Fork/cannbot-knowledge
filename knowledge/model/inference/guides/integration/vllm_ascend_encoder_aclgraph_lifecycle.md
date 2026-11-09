---
type: Guide
title: vLLM Ascend Encoder图接入：EncoderAclGraphManager、路径桶与FIA回放
description: 沿 EncoderAclGraphManager、EncoderForwardContext 与 AscendMMEncoderAttention 核对path/budget/axis键、持久输入、Host累计长度、FIA任务更新与事件，以及输出复用、清理和独立Native父类的装箱/DP边界。
aliases:
- EncoderAclGraphManager
- EncoderForwardContext
- EncoderGraphParams
- set_encoder_forward_context
- update_encoder_graph_params
- maybe_compute_actual_seq_lengths
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.model_adaptation
- topic.graph_execution
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/encoder_acl_graph.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/mm_encoder_attention.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_encoder_acl_graph.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_mm_encoder_attention.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_model_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/encoder_cudagraph.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T08:20:12Z'
updated_at: '2026-11-02T08:20:12Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Encoder图接入：EncoderAclGraphManager、路径桶与FIA回放

## 接入任务与证据范围

新视觉模型实现 encoder graph 接口时，需要同时对齐选图、持久输入、模型输出和每层 FIA 的 Host 参数更新。把媒体预处理搬到设备，或者捕获时能够 forward，并不能单独证明多分辨率、多 path、连续回放与输出复用正确。本卡说明通用 manager 与标准 Ascend MM Attention 的接线；各模型自己的 patch、位置、merge 和归一化仍由对应模型合同负责。

Main 固定 ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：全文阅读 encoder_acl_graph.py 460 行、mm_encoder_attention.py 363 行、两个 UT 319/244 行、patch_model_state.py 31 行和一行 pin；MRv1 Runner 仅7043–7070，utils 注册仅819–954。独立 Native 5df63a7203cdb9328d824a27b682e77c7b9928be 的 encoder_cudagraph.py 761 行全文。Main 实际配对 pin 为544f182d9f0c9bfe8bd7645525951d5e3692a542，独立 Native 不是配对 ABI 验证。

本卡没有闭合模型 SupportsEncoderCudaGraph 的所有实现、Native MMEncoderAttention、torch_npu FIA/图 API 的内部或整项硬件/模型支持表，保持 draft、空平台与 framework=vllm 的部分 Scope。全部源码和 UT 只作数据阅读，没有执行上游、NPU 或真实模型。

[Qwen3.5 设备预处理](vllm_ascend_qwen35_device_preprocess_contract.md)拥有 raw/patch/marker，[GLM-Next 视觉编码器](vllm_ascend_glm_next_vision_encoder_contract.md)拥有具体数值和 encoder metadata producer；[Encoder-Decoder 状态](vllm_ascend_encoder_decoder_state_contract.md)负责跨注意力输出交付。这些与通用 encoder graph 生命周期分开；decoder 的[ACLGraph设计](../../concepts/frameworks/vllm_ascend_aclgraph_replay_lifecycle.md)也不能直接代替本路径。

## 先确认manager和MM Attention都实际接通

MRv2 patch_model_state 替换的是 Native model_states.interface 内部已经导入的 EncoderCudaGraphManager 引用，同时重绑 model_runner.init_model_state。仅修改源 encoder_cudagraph 模块的类，不一定改变已经保存在 interface 命名空间里的引用。MRv1 的已读 contextmanager 则暂时替换源模块的 manager，finally 恢复进入前的原类；它不是永久修改所有导入点。

register_ascend_customop 的映射先把 MMEncoderAttention 指向 AscendMMEncoderAttention；有 COMPATIBILITY_OP_IMPLEMENTATIONS 能力时再覆盖成 AscendMMEncoderAttention310，最后逐项注册 CustomOp。该函数见全局已注册标志后直接返回，不能在同进程改 profile 就假定已有注册类自动重绑。

因此要记录最终 manager、MM Attention 实例类、实际 profile 与调用引用。以下 FIA event/task 合同属于标准 AscendMMEncoderAttention；兼容类的名字带310，不构成所有硬件的矩阵，也不证明它继承本文件的捕获机制。只看到 manager 类存在不足以确认 Attention 消费者已接入。

## 图键、预算与捕获状态

EncoderGraphParams 按 `(path,token_budget)` 保存 events、workspaces、handles 和按调用顺序追加的 attn_params；非空 axis_keys 时键变为三元组。相同 budget 在 global/local path 或不同 capture axes 下不是同一份 FIA 状态。旧 list 输入只转换成 default path；初始化仅为正 budget 建项，capture axes 的具体键在捕获时按需建立。

Main capture 先选择显式 graph_pool，否则取平台全局池，设置 self.graph_pool 并重建全局 params，再委托父 capture。完成后将 workspace 变为 weak reference；捕获或这一步抛出 Exception 时 clear 后重抛。is_captured 沿独立 Native 的定义只检查 graph_pool 非 None；因为标志在实际捕获前已设置，它不能单独证明每个桶和 axis 图均已完成。

独立 Native 按模型 budget range、用户 budgets 和最大视觉 item 数计算预算，要求每个捕获档位至少能分配一个 token 给每个 item。每个 path 可有自己的最小预算和零-token选项；正预算按降序与 capture axes 的笛卡尔积捕获，零预算跳过。图数超过64只触发 warning，不能写成硬上限；该快照明确拒绝多 path 与非空 capture axes 同时使用，不能由 Main 参数字典可以保存二者就断言该组合可运行。

Main 用 inspect.signature 检查父 _capture_budget_graph 是否有 axis_keys，在模块加载时决定是否向模型 prepare 函数和 BudgetGraphMetadata 传额外轴字段。它没有逐个验证任意模型回调的真实签名，也不保证之后动态替换父类方法仍同步更新兼容标志。

## context是模块状态，退出清空

EncoderForwardContext 保存 token_budget、path、axis_keys、capturing 和本轮 cu_seqlens_cpu。实现使用模块级 _context 对象；虽有注释提到 thread-local，并没有在这里使用 threading.local 或 contextvars。不要把它当作任意线程、多个 manager 或并发调用天然隔离的机制。

set_encoder_forward_context 在进入时赋当前字段，finally 清回默认值，不恢复外层 context。嵌套退出后外层字段也会丢失；本轮 Host 长度必须每次重新发布，不能保留上一轮引用作为缺省。_encoder_graph_params 同样是全局单例，新 manager.capture 会重新绑定，clear 会置 None；同进程多 owner 的互相影响仍需单独设计和验证。

## 捕获的是实际FIA输入地址与任务

Main _capture_budget_graph 先调用模型 prepare_encoder_cudagraph_capture_inputs，取其 values；随后在 encoder capturing context、inference_mode 和 NPU graph 中执行 encoder_cudagraph_forward。结果经 weak_ref_tensors 保存为 output_buffer，输入 values 直接保留。独立 Native 的实现还先做一次普通 forward、分配独立 output_buffer，并在图中 copy 输出；不能假设 Main 与该快照的预热次数和输出所有权完全相同。

AscendMMEncoderAttention 将输入整形成 TND。64 < head_size < 128 时将 Q/K/V 最后维补到128，输出再裁回；其他宽度跳过该补齐，不是所有宽度均有支持证明。MQA/GQA 分支按 head 比例 repeat K/V，父类构造、实际头数参数和设备 ABI 仍须对照；所读测试主要为相等Q/KV头数，不能作为一般 GQA 数值验收。

捕获分支先把 K/V contiguous，再把交给 FIA 的同一张量放入 packed 参数。对每个图键首次取得 workspace，后续块复用它；“get_max_workspace”的名字不证明第一次某层形状的容量自动覆盖所有其他层。需要逐层确认 head、Q/KV长度、dtype 和 workspace 要求。

每次 FIA 调用新建 ExternalEvent，在捕获流插入 wait/reset，再用 graph_task_group_begin/end 得到 handle。packed 参数保存 Q/K/V、block_table、mask、block size、两类 head 数、scale、output 与 softmax_lse，和 event/handle 按同一顺序追加。弱引用调用和地址相同不构成完整资源寿命、异步完成或多 stream 正确性的实测证明。

## Host累计长度必须按当前输入刷新

标准 MM Attention 在 eager 时使用模型 cu_seqlens，缺省则按均匀 q_len 构造 CPU 累计终点；capture 阶段总是用均匀 CPU 版本，避免从模型 device tensor 读回。它不是沿用本批不规则图像长度捕获。回放 manager 再从持久 input_buffers 的 cu_seqlens 取 CPU 副本，作为本轮 FIA 更新参数。

maybe_compute_actual_seq_lengths 先 detach/cpu/view/tolist，丢第一项。普通 eager 模式不替输入补齐完整 schema；图模式过滤非正、重复/不递增终点，遇超过 num_query_tokens 的值停止，再补 terminal 到当前 query token 数。它依赖合法有序的累计长度，不能把过滤函数当作任意损坏输入的恢复器。

Q与KV总 token 相等时复用同一长度列表；不等时要求 KV 总量能被 Q 总量整除，用同一个整数比缩放所有 Q 终点。这只表达均匀比例，不能推广为任意每请求 cross-attention 长度映射，也没有为所有 Q=0、KV不同或空输入组合提供通用安全保证。

update_encoder_graph_params 要求同一键的 handles、events 和 attn_params 数量相同，否则明确报错。有 handle 但本轮 cu_seqlens_cpu 缺失时也报错；没有 params/key 或空 handle 的分支可以不更新。Host 长度只在一次更新内按 `(query.shape[0],key.shape[0])` 缓存，不能跨 batch 直接复用旧列表。

## 回放拷贝、事件与更新顺序

_run_budget_graph 先按 path/budget/axis 找图，模型再提供 replay buffers。每个已捕获 input buffer 从 replay.values 取同名源：缺键就跳过，scalar 直接 copy，其他调用自定义 padding_logic 或父类的先清零再前缀 copy。缺键不是自动清旧数据；不同 shape、容量、padding 和同步责任仍要按模型核对。

拷贝后获取 CPU cu_seqlens，建立或复用 update_stream，让它先 wait 当前主流，然后调用 graph.replay；之后进入本轮非capturing context，提交 FIA task 更新并 record 对应 event。不能按普通Python直觉把该代码重写成一条未经验证的“所有更新必须先于replay”规则：捕获图已有 ExternalEvent wait/reset 节点，主流提交、更新流与设备节点依赖要一起核对。本次没有证明特定torch_npu版本的底层事件行为。

每个 task 的更新在 update stream 上以 graph_task_update_begin/end 包围 FIA.out，传当前 Host Q/KV 累计终点、捕获张量及 workspace，最后 event.record。捕获调用显式传 pre_tokens/next_tokens，而该更新调用未重传这两项；必须对照真实 API 默认值和已捕获任务属性，不以参数名相似推导版本间完全等价。

manager 正常返回 graph_meta.output_buffer 并增加按 item 计的 graph_hits；它没有在返回前做通用 host/device 全同步。下一次重放可覆盖同一输出，调用者不能跨步骤无条件保留它的 view。

## 父类装箱、回退和输出归属

独立 Native 按 item 输出token数排序，分别累计每个 path 的预算，并受最大 item 数、path 容量和预算跳档规则影响分批；模型 selector 负责选取并返回 capture axis keys，数量必须匹配配置轴数。item spec 和 selector 允许 device-to-host 同步，encoder graph 路径不是全系统无Host工作的承诺。

超过最大预算时父类调用 encoder_eager_forward；路径本轮token为0时跳过。相反，找到拟合预算但 _run_budget_graph 没有相应图时，该方法返回 None，已读父 _execute_local 随后断言它非 None，不是统一自动 eager 回退。不要把所有 graph miss 都当作安全 fallback。

模型 postprocess_encoder_output 接受 clone=True，并把分批结果恢复到原 item 顺序；具体 clone 的实现仍属于模型回调。encoder DP 模式复用 TP rank 做 item 分配，再 pad/all_gather/unpad/reorder 输出；完整模型 callback、collective 和真实NPU布局还需运行验证，不能把这个独立 Native 算法当作所有Ascend模型已经实现。

graph_hits/misses 由 item与path执行路径累计，不简单等于文本请求数或实际设备图执行次数。父 clear 清图集和pool标志，Main 再清全局 params/context/update_stream；这些计数没有在已读 clear 中重置。clear 也没有等待所有并发图/stream用户的通用退休屏障，异常处理和重新捕获前应确认资源实际生命周期。

## Agent验证与未执行项

先交付最终类/注册引用、Main与配对Native、模型图接口、path budgets、axis keys、item/token/frame数量、所有持久buffer的device/dtype/shape/地址、padding规则、FIA packed顺序、workspace容量与本轮Host累计长度。覆盖单/多path、各轴、空path、预算边界和过预算、连续回放、相同预算不同内容、缺replay键、长度不一致、模型回调失败、capture失败清理及多manager作用域。

分别比较 eager、首次capture、同桶多步与跨桶输出，验证预处理marker、Q/KV头数、非连续K/V、补齐head维、输出clone和原item次序，再测试DP与真实并发。出现旧长度、输出覆盖、缺图断言、事件挂起或共享context错位时，保留上述字段与完整时间线，回到明确配对的已验证配置；不要通过删event、填上一批长度或强制图命中消除报错。

319行manager UT定义累计长度转换、按shape缓存、capture失败清理、path/axis隔离、MRv2绑定、mock NPU capture以及wait_stream→replay调用次序；244行MM Attention UT替换FIA/graph task/event，检查布局、head补齐、capture均匀长度和保留contiguous K/V地址。CPU tensor和mock调用顺序不证明真实任务更新、设备数值或性能，本次也没有执行这些UT。

本次没有导入上游、运行UT、JIT/编译、模型/NPU/图、DP通信、精度、性能或Agent A/B，未填verified。正确性和生命周期通过后再分别测Host item规划、D2H长度、buffer copy、FIA更新、图执行、图池/工作区内存和端到端媒体时延，不能只用命中率或源码的少同步动机宣称收益。
