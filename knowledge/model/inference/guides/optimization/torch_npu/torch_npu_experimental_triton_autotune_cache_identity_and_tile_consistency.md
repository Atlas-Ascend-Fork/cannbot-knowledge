---
type: Guide
title: 实验Triton自动调优缓存：候选身份、确定性与小尺寸补偿
description: 解释实验Triton候选extra_options身份、顺序敏感缓存、确定性禁缓存、原地元数据消费和小动态tile整组替换边界。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T09:39:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton自动调优缓存：候选身份、确定性与小尺寸补偿

## 固定局部入口

依据TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的本地候选键、去重/hash、小尺寸tile补偿、cached_autotune完整函数，只另核构造器转交、实际imports和tile_align声明。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的两个精确路径没有Git条目；这里只记录路径关系，不推断发布没有自动调优或同类能力。

本文补充[编译分层/资源回退](torch_npu_experimental_triton_compile_tiers_and_resource_fallback.md)与[调优计时/输入隔离](torch_npu_experimental_triton_autotune_timing_and_input_isolation.md)之前的候选准备层。没有导入上游、构造真实Config、读写缓存、inspect实际kernel、编译或设备实验；外部AutotuneCache、确定性筛选器及CachingAutotuner实现独立，平台未知，保持draft和空平台。

## extra_options参与身份，但不是任意对象的规范化协议

_npu_config_key先按键排序Config.kwargs，随后追加num_warps和num_stages两项；extra_options为真时，再把其排序后的键值项接在后面，最后转tuple。后端选项因此不会仅因tile kwargs相同而在本地去重时被忽略，例如不同auto_blockify_size可形成不同键。它没有递归冻结嵌套对象、为不同来源的字段增加命名空间，也没有把Config全部属性加入键，不能称作任意Config对象的无碰撞/深度规范化合同。

_npu_unique_configs按输入顺序保留第一个尚未见过的键，返回这些原Config对象；没有复制配置。它使用set保存键，复杂不可hash的值没有本地降级处理。_npu_hash_configs则按候选列表当前顺序，把每个键的字符串加换行后更新SHA-256。**去重后的候选顺序也影响这里的hash**，不是把同一集合任意排列都变成同一个缓存身份。

配置工厂的tile夹取、固定warps、未消费形参与extra_options槽已经由[逐元素候选指南](torch_npu_experimental_triton_pointwise_candidate_filters.md)覆盖，本卡直接复用该知识，不重新展开或扩充其来源资格；后续编译选项合并见[单配置编译](torch_npu_experimental_triton_compile_tiers_and_resource_fallback.md)。外部缓存序列化与恢复协议仍不由本地身份函数认证。

## 确定性先筛候选，再决定是否使用缓存

cached_autotune只把None的inductor_meta换成新字典；传入字典直接沿用。heuristic_type为REDUCTION或PERSISTENT_REDUCTION，且deterministic、are_deterministic_algorithms_enabled、force_filter_reduction_configs任一值为真时，先调用外部filter_reduction_configs_for_determinism，再做本地去重。这里不展开外部筛选算法，不能把调用本身当作所有浮点结果逐位确定的证明。

去重后len(configs)!=1且filename为假值就抛ValueError；**空列表也满足这个条件**。这不是只在多候选时检查，也没有在此合成一个默认可运行配置。force_disable_caches真值或上述确定性归约会禁用这层AutotuneCache，但禁用缓存不等于关闭后续全部编译/调优。

只有未禁用、filename不是None、候选数>1或coordinate_descent_tuning为真，并且环境TRITON_INTERPRET不精确等于字符串'1'时才尝试create缓存。这里的filename is not None与前面的真值检查不同。read_best返回真值对象才把configs换成单元素列表；没有在这里通过设备计时再次验证它。缓存创建/读取、外部筛选与hash过程都没有统一except回退，不能说缓存出错必定重算且不影响编译。

候选hash与read_best发生在下面的装饰器修改和小尺寸替换**之前**；源码没有在那些修改后重新计算这个hash。因此本地准备时点、最终交给autotuner的候选列表与外部cache save/restore协议需要分别核对，不能仅凭函数名推导整条缓存兼容性已经验证。

## 元数据是被消费的对象

在返回装饰器之前，函数从inductor_meta原地pop mutated_arg_names和optimize_mem，缺省分别为()与True；triton_meta若有restore_value，就pop后用+=并到mutated_arg_names。reset_to_zero也从triton_meta pop，扩入新列表。重复复用同一个metadata字典会看到已经被消费的内容；这里没有先对输入字典统一deepcopy，也没有验证任意参数类型组合都能完成拼接。

装饰器检查fn.fn的实际签名：没有XBLOCK参数时，逐个检查带XBLOCK的配置，值必须等于1才pop该键，否则RuntimeError。配置对象可能来自原候选或read_best；这段原地修改没有在失败时恢复先前已处理项。签名检查、元数据消费和后续构造也不是统一事务。

接着它调用小尺寸补偿并把最终配置、原metadata对象、save_cache_hook、mutated/reset名称、optimize_mem、heuristic_type等转给NPUCachingAutotuner。所读本地构造器继续转交外部CachingAutotuner；这不自动证明参数备份、重置、调优获胜和缓存写入的完整行为。实际输入隔离与计时边界沿前述计时指南核对。

## 小动态尺寸补偿依赖源码文本与整组条件

_add_tile_consistent_config仅处理POINTWISE。它用inspect.getsource(fn.fn).splitlines()，只要某行包含精确子串`.shape ==`就视作门控；**没有解析AST或证明它是实际执行的断言**，注释/字符串也未被本地过滤。取源码抛Exception就保留原列表；无该子串或configs为空也保留。

size_hints为dict时取'x'，否则真值序列取第一项；hint必须是正int。align=max(int(ncfg.tile_align),1)，本地声明默认8；这个转换不在前面的inspect异常处理内。对正整数n的对齐计算是ceil(n/align)*align，不是设备向量宽度或所有dtype的硬件资源验收。

遍历每个Config时，**任何一个**XBLOCK不是正int，或align_up(min(hint,XBLOCK))==XBLOCK，就立即返回整个原列表；不会只筛掉不兼容候选，也不证明保留下来的每项都已满足同一shape条件。

只有全部候选的XBLOCK均为正int且都未满足上述等式，才deepcopy列表最后一个Config，把其XBLOCK改为align_up(hint)，并返回仅含该副本的列表。它是**替换整组为一个候选**，不是往已有列表再追加一项，也没有先测量最后一项最优。以默认align=8为例，小hint=3会请求对齐到8，但只有上述整组条件满足时才真的替换；这不是任意小尺寸都强制XBLOCK=8。

这条补偿不检查剩余Y/Z、extra_options、kernel数学或设备资源，也没有在此重新编译验收。诊断“缓存未命中/候选变少/小尺寸shape断言”时应分别记录原候选顺序与完整后端选项、确定性有效标记、filename与解释环境、read_best结果、metadata消费时点、实际源码门控、hint/align以及最终候选。局部筛选与缓存命中均不替代模型数值和性能验证；本次没有新增verified。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（primary）：23–31,41–46,51–65,505–534,1446–1597行；仅所列完整局部函数、构造转交和必要声明，不提升整个模块或外部实现资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：376–376行；仅所列完整局部函数、构造转交和必要声明，不提升整个模块或外部实现资格。
