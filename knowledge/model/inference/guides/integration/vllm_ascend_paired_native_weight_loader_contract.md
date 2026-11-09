---
type: Guide
title: vLLM Ascend 配对权重加载：名称映射、TP/EP分片与原位重载
description: 连接Main Ascend Linear与实际配对Native544加载链，核对packed key、V1/V2名单、typed参数与TP状态、QKV副本、专家映射和padding、dtype及scale、missing/computed参数检查，以及checkpoint和kernel格式reload的不同生命周期。
aliases:
- AscendLinearMethod.create_weights
- AscendColumnParallelLinear
- AscendRowParallelLinear
- AutoWeightsLoader
- WeightsMapper
- BasevLLMParameter.weight_loader
- DefaultModelLoader.track_weights_loading
- FusedMoEParallelConfig.make
- RoutedExperts.weight_loader
- initialize_layerwise_reload
- finalize_layerwise_reload
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/linear.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/method_adapters.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/routed_experts.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/w4a8_mxfp4.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/parameter.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/layers/linear.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/models/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/default_loader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/base_loader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/weight_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/layers/fused_moe/config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/layers/fused_moe/routed_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/layers/fused_moe/expert_map_manager.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/ep_weight_filter.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/reload/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/reload/inplace.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/reload/layerwise.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/reload/meta.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/reload/torchao_decorator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/reload/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/model_loader/reload/types.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/utils.py
  role: constraint
created_at: '2026-11-03T01:27:32Z'
updated_at: '2026-11-03T01:27:32Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 配对权重加载：名称映射、TP/EP分片与原位重载

## 适用版本与接入目标

本卡连接Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的Ascend层、量化adapter与该Main实际记录的Native配对544f182d9f0c9bfe8bd7645525951d5e3692a542。所有Native结论来自544的Git对象；独立Native 5df63a7203cdb9328d824a27b682e77c7b9928be不作为本卡ABI依据。配对pin证明版本关联，不能代替整链运行验证。

新模型首先确认“checkpoint名字和物理格式→目标参数→真实loader→本rank切片→后处理→活动kernel存储”逐项闭合。ModelSlim的格式和scheme选择沿用[scheme适配指南](vllm_ascend_modelslim_scheme_adaptation.md)，MX组相位和block尾部沿用[scale分片排障](../../runbooks/precision/vllm_ascend_quant_scale_tp_sharding.md)；本卡补充它们所依赖的实际配对Native加载与重载合同。

Main linear.py607行、method_adapters.py365行和pin全文已读；Main routed_experts仅16–51、413–649，worker仅220–245，W4A8_MXFP仅122–158、258–367。Native parameter602行、BaseLoader176行、EP过滤85行及reload包七文件均全文读取；其他来源精确范围列于文末。未运行上游导入、UT、模型、设备算子、通信、图、精度或性能实验，保持draft和空平台。以下关于加载成功的含义均限静态控制流。

## 先确认实际Ascend层选择的loader

Main AscendColumnParallelLinear、AscendRowParallelLinear及其QKV、Merged派生构造通过get_parallel_op选择有效层TP与通信实现；Replicated也有独立入口。自定义MLP/投影通信域、disable_tp或复制层可能改变本层tp_rank/tp_size，不能直接以默认全局TP预测其checkpoint切片。

Column/Row创建权重时，以外层quant_method.__class__.__name__是否位于WEIGHT_LOADER_V2_SUPPORTED决定传weight_loader_v2还是weight_loader。固定配对名单没有AscendLinearMethod；已审Main worker还移除UnquantizedLinearMethod条目。给scheme创建typed Parameter不会自动切换到V2，内层scheme的类名也不自动代替Ascend wrapper进入名单。若进程另有名单修改，必须提供其真实执行顺序，不能由本卡推定。

| 要核对的对象 | 加载语义 |
| --- | --- |
| V1 Column/Row | 按层对象rank、param的input_dim/output_dim等属性切片；is_sharded_weight等明确标记影响路径 |
| V2 | 进一步委托Parameter的load_column_parallel_weight、load_row_parallel_weight、load_merged_column_weight或load_qkv_weight |
| 普通BasevLLMParameter | 基础实现可能只校验shape并copy；typed基类存在不等于实现全部分片 |
| ModelWeightParameter等typed参数 | 参数自身记录的TP状态参与分片，需与有效层TP一致 |

paired LinearBase.update_param_tp_status用于把有效层TP重新写入BasevLLMParameter。Native创建及通用后处理有相应调用，但Main部分构造手工初始化Native派生层，不能假定每条Native构造语句均执行。参数替换、不同TP域及自定义postprocess后，核对真实参数上的tp_rank/tp_size，不能只查看层对象。

Main AscendQKVParallelLinear接收并保存v_head_size，当前分配output_size/output_sizes的V段仍使用head_size；paired Native QKV loader计算V shard时使用v_head_size。v_head_size不等于head_size时，签名接受不能证明Main分配与Native切片兼容。这是需要新模型先闭合的静态边界，本次没有复现运行错误。

AscendRowParallelLinear的wo_a有专用重载处理：已经变成三维布局时，将传入二维checkpoint按本rank的n_local_groups×o_lora_rank切片，再reshape、transpose、contiguous并检查目标shape；仍为二维时走父loader。该分支不构成任意参数都可重复transpose或任意预处理格式都可直接重载的保证。

## 参数元数据、packing与scale单位

AscendLinearMethod.create_weights调用scheme.get_weight，返回的普通Tensor由adapter包装成torch.nn.Parameter，设置input_dim=1/output_dim=0；_packed_dim和_packed_factor从字典取出后作为元数据附着。它不会仅因这些属性存在就变成Native ModelWeightParameter。

per-tensor scale用PerTensorScaleParameter，weight_loader可通过属性setter重新设置；input_dim/output_dim等typed属性则有不同的只读规则。Native set_weight_attrs拒绝覆盖已经存在的属性，不应把“构造器已经设置”与“再次赋值总是安全”混为一谈。Main BlockQuantScaleParameter分支通过构造器给input/output维和loader，并过滤这些属性后再转发其他元数据。

per-channel参数只有output_dim；per-group的归约维优先用_input_dim，其他情况依据明确名称或MX类型分支决定。Block scale通过weight_block_size和BlockQuantScaleParameter向上覆盖尾块；bit packing以packed_factor把逻辑offset/size转换为物理存储单位。两个尺度不能互换，整数除法不能替代block尾部向上取整。

MX RowParallel专用scale wrapper先检查loaded_weight.shape是否已经等于本地param.shape，相等就直接copy；否则仅在不整除group且有input_dim时按全局组相位切片，其他情况回原loader。这项预分片特判只适用于明确包装的scale路径，不能推广为所有Column/Row参数只要shape相等就免切片。

Native copy通常允许dtype转换；AutoWeightsLoader对部分dtype不符只记录warning，精确可扩展转换可降为debug。加载没有异常不证明整数容器、FP4/FP8位模式、E8M0 scale或模型精度正确。记录checkpoint dtype、目标dtype及postprocess前后真实布局；需要保留原始字节的路径不能靠隐式数值cast替代view。

## 名称映射、合并投影与QKV副本

paired WeightsMapper依次处理renamings、regex、substring、stacked映射、prefix和suffix；映射为None可跳过。stacked映射给Tensor附加shard_id，多目标复用时以detach得到独立Tensor对象但共享底层storage。对这些对象原位修改还需考虑别名，不能把多名字视为独立副本。

AutoWeightsLoader按模块树分发，优先调用子模块自定义load_weights；普通参数调用其weight_loader或default_weight_loader。PPMissingLayer/StageMissingLayer等跳过项、persistent buffer、共享embedding别名各有路径；nonpersistent buffer不属于同一加载集合。自定义load_weights返回None时，完整跟踪标志下降，并影响共享参数别名检查，不能声称返回空信息仍完成严格全量验收。

MergedColumn和QKV的“合并”有两个层次：checkpoint可能分别给每个投影，也可能给磁盘上的融合Tensor；加载时先按逻辑投影边界拆分，再对每段执行TP和packing换算。不能把整个融合Tensor简单等长切一刀。Merged shard_id须遵守固定int或连续tuple合同，QKV遵守q/k/v标识；per-tensor融合scale和V1 needs_scalar_to_array也有独立处理。

Q段按tp_rank分片；KV复制时以tp_rank//num_kv_head_replicas选择checkpoint KV shard，而非每个TP rank都取不同KV段。核对总Q/KV头、head_size/v_head_size、复制倍数、packed axis和实际分配长度，尤其先解决前述Main不等V-head分配边界。

WeightsMapper.get_rename_mapper为配置或LoRA命名去掉stacked与None映射，不等于checkpoint Tensor经过同一完整加载流程。加载名字集合、某个Tensor copy成功和每个投影/专家/分片全部更新是不同证据。

## TP/EP专家映射与padding

paired FusedMoEParallelConfig.make按dp_rank×pcp_size×tp_size+pcp_rank×tp_size+tp_rank构造展平rank。启用EP时有效MoE TP为1、EP承接展平域；未启用时MoE TP承接展平域、EP为1。以实际moe_parallel_config、专家映射和权重分片为准，不能直接拿默认全局TP/EP数推导每个专家Tensor。

Native RoutedExperts构造先计算quant_method所需的round-up尺寸，再创建本地专家和权重；loader同时需要unpadded逻辑H/I与活动分配的padded尺寸。Main AscendRoutedExperts在父构造完成后另接Ascend映射/运行时逻辑，checkpoint加载所需ExpertMapManager物理映射不能过早替换成执行期逻辑映射。[RFork加载](vllm_ascend_rfork_processed_weight_loading.md)和[EPLB权重接入](vllm_ascend_eplb_model_weight_contract.md)继续负责对应格式和动态提交。

RoutedExperts.weight_loader先将global physical expert映射到本地；非本地通常跳过，global scale等明确例外另行处理。它区分w1/w2/w3、是否转置、全专家融合Tensor以及param.quant_method的TENSOR/CHANNEL/GROUP/BLOCK元数据。Main wrapper的外层类身份和属性是实际分派输入，不能自动继承内层scheme名字的全部Native特例。

w13的两个投影分别分片并放入两个半区；w2的轴不同。默认分片offset使用checkpoint未padding的每rank逻辑宽，必要时只窄化目标有效区。tp_shard_with_padding先填目标weight为0、scale为1，再copy该rank可用片段；其输入必须满足未分片checkpoint的逻辑宽合同。原始scale容器中的字节1不能不经格式解释就写成浮点单位scale。

ExpertMapManager的linear布局把不能整除的余数给前面的ep_rank<remainder的rank，非本地映射为-1；round-robin另有算法。按实际代码而非相邻注释猜测余数分配。副本、逻辑专家和物理槽不可互换，融合checkpoint也不能从文件名直接推导本rank唯一专家号。

## EP过滤能省哪一层I/O

DefaultLoader的EP过滤需MoE、EP和过滤配置共同满足；Native enable_eplb会禁用该过滤，避免丢失冗余专家输入。按名字识别.experts.N.数字专家的heavy weight/weight_packed，保留scale/metadata、dense、shared以及无法按数字专家拆开的融合权重。不能用该过滤替代模型load_weights中的专家所有权判断。

标准safetensors lazy路径可先判断专家key再get_tensor；eager路径已先读取整个shard。文件prefetch也可能先读取更广的文件内容。DefaultLoader的multithread和fast等分支没有以同样方式传local_expert_ids；instanttensor虽传该字段，其内部消费者未在本卡审阅。因此“只yield本地专家”不能直接折算为磁盘读取量、Host峰值或加载时间同比下降。本次没有I/O测量。

## missing、computed与加载完整性

DefaultModelLoader默认只在未量化模型且model.load_weights返回跟踪集合时启用严格检查；显式model_loader_extra_config.enable_weights_track可覆盖默认。quantization不为None时，默认未报missing不能证明checkpoint完整。

显式开启量化跟踪后，存在process_weights_after_loading不会豁免整个量化模块。固定544只按具体条件处理online/meta量化、KVCache参数、空占位和配置构建参数（如input_scale_ub）；普通非空权重和scale仍需来自checkpoint。AscendLinearMethod.get_computed_params虽然返回weight_offset、quant_bias、deq_scale、weight_scale，已读paired DefaultLoader没有消费该列表，不能以列表存在推导自动免检。

BaseLoader标准顺序为构造模型、load_weights、必要online finalize、通用process_weights_after_loading、eval；通用后处理在量化处理后更新参数TP状态，再处理延迟attention及模型hook。preprocessed权重还需明确supports_pre_processed_weights，不能跳过入口门禁。RFork等自定义loader必须按其自身流程证明同等条件。

建议为新模型记录“预期checkpoint键→映射后参数→投影/专家shard→本地有效区→派生参数”的清单。名字集合不能识别所有重复写入、未覆盖尾区或部分专家遗漏；成功copy也不保证初始化和精度。确认确实由postprocess计算的参数时，还要闭合当前loader如何豁免和计算，不能为过检查把全部scale列为可缺失。

## checkpoint与kernel格式的reload是两条路线

paired model_loader/reload是包，inplace.reload_weights的is_checkpoint_format=True先initialize_layerwise_reload，再model.load_weights，最后finalize_layerwise_reload；False则按活动kernel参数的准确名字直接copy，要求已经重排、打包和分片的数据，不重新执行模型名称映射、TP切片或量化后处理。False分支warning内的True字样与条件不一致，应以分支条件和实际copy为准。

从新weights_path重载会清空旧revision和model_weights来源。LoRA、encoder和多模态等派生cache失效由caller负责；不能由权重copy完成推导缓存已刷新。固定实现中未量化reload的遗漏检查为warning，强度不同于首次DefaultLoader严格异常。

layerwise依赖构造阶段记录的原始metadata，恢复checkpoint形态并包装原loader，以CopyCounter观察copy_量和可选weight_loader_numel控制逐层完成。零加载层会恢复旧kernel Tensor并warning；部分更新、padding以及特殊loader仍需核对计数语义。函数返回不表示所有层换成新权重，也没有通用的全模型原子回滚证明。

处理完成后把新kernel值copy回原存储并恢复原参数/缓冲引用，目的是保持已有图等引用可见；不能据此推导设备读者已静止、并发更新安全或图数值已验。torchao reload decorator还要求_do_torchao_reload，不是所有Ascend量化自动进入。

通用layerwise只清理其识别的_already_called_process_weights_after_loading标志；没有清理Main W4A8_MXFP的_mxfp4_transformed，也没有调用其restore_weights_before_loading。MXFP4恢复形状、active storage、专家列表和host缓存继续按[专用重载指南](vllm_ascend_mxfp4_weight_reload_contract.md)闭合；W4A4的packed改名和clip主机值见[量化变换指南](vllm_ascend_w4a4_quant_transform_contract.md)。Generic reload接口存在不等于这些scheme已经自动兼容。

## 新模型适配与诊断顺序

先固定Main/paired Native、checkpoint版本和格式，再捕获一层真实外层quant_method、loader函数、参数类型、维度属性、packing/block/group单位、有效TP/EP及原始/活动shape、dtype、stride。用小型非零参考核对映射、QKV副本、专家和尾部padding，再推进整模型。缺键时同时检查跟踪开关及computed消费者，不能只搜索异常日志。

重载先明确输入是checkpoint还是kernel格式，验证实际覆盖层、原参数storage、后处理marker、host派生值和cache失效；然后才进行图/并发读者、精度与性能实验。发现格式、参数覆盖或专家映射不闭合时先恢复匹配版本与checkpoint，不用丢scale、跳层或任意补值隐藏错误。本卡没有为任何模型、设备、并行组合或重载方案宣告验证通过。

## 有界来源范围

Native以下范围均指544固定对象，其余文件尾部与依赖的设备执行闭包未宣称覆盖：layers/linear.py 1–163、245–324、329–642、686–1362、1639–1819；models/utils.py 1–502；default_loader.py 1–145、265–392、426–572；model_loader/utils.py 74–261；weight_utils.py 1115–1249、1529–1562；fused_moe/config.py 1015–1263；fused_moe/routed_experts.py 1–1127、1130–1291；expert_map_manager.py 1–113、182–261、338–354、434–452；model_executor/utils.py 36–68。范围之外的下载准备、其他reader实现、特殊Linear子类、完整MoE执行、全部模型caller和实际硬件结果保持待补。
