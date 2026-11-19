---
type: Guide
title: 实验Triton候选编译：分层筛选、小block回退与异常边界
description: 按真实分支记录实验Triton候选分层、小block扫描、异常跳过与编译选项覆盖的边界。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T08:10:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton候选编译：分层筛选、小block回退与异常边界

## 固定范围与诊断用途

本卡依据TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的NPUCachingAutotuner，完整读取所列分层、批量预编译、worker、小block扫描和单配置预编译函数及局部异常判别helper；只另核config的相关默认声明。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`在这两个精确路径均无Git条目，这不等于发布版没有Triton能力。两个模块保持有界资格，未读取或认证整个3293行heuristics，也未编译、导入、执行生成器或设备。

它解释“哪些候选实际进入编译”和“No valid triton configs”的局部错误边界；[网格与启动器生成](torch_npu_experimental_triton_grid_and_launcher_codegen.md)属于后续独立阶段。产品与完整依赖未知，保持draft、空平台，不把源码中的回退意图当作已验证的性能收益。

## 分层依据是tile乘积与warps，不是已测最优性

_partition_configs_by_tier从tile=1起，只乘kwargs里名字以BLOCK结尾、值为正int的条目，**这里没有排除R开头的归约BLOCK**。num_warps缺属性按8，假值再按0；tile>=512且warps>=4进入primary，其余进入fallback。它不重新验证候选的全部shape、资源或运行合法性；注释说小tile没有胜算，是本地筛选理由，不是对每个模型的基准结论。

_precompile_worker若已有compile_results，先把其kernel hash重新登记TritonBundler后直接返回；该分支先于launchers/configs检查。否则已有launchers会报RuntimeError，空configs报NoTritonConfigsError。初次分层若primary为空，就把**全部原configs**当primary并清空fallback，避免无候选可编。

正常顺序是：编译primary；只有其结果列表为空且fallback非空，才编译原有fallback；仍无结果，才运行新生成的小block扫描。**只要一项primary编译成功，所有原有fallback都不会进入这次编译。** 这些函数没有运行benchmark，也没有根据“primary运行慢”或“benchmark失败”再启用fallback，不能把编译成功等同最终稳态更快。

成功后worker保存compile_results并将self.configs置None。compile_failed只是该worker的局部列表，不是对外保证保存的完整失败档案；后续计时、候选获胜与缓存协议不在本卡范围。

## 串行与并行的候选级错误范围

_compile_configs_batch空列表返回三个空/None结果；非空时把get_compile_threads的结果转int，再至少取1。线程数<=1或候选数<=1时串行，否则max_workers=min(线程数,候选数)，用ThreadPoolExecutor和as_completed收集。并行成功列表按完成顺序追加，不保证保持配置输入顺序；last_exc也是最后收集到的已捕获错误，不保证指向输入列表最后一项。

两条路径都把MLIRCompilationError、CompilationError、OutOfResources当作可跳过的候选失败。额外只跳过_is_constexpr_signature_error认定的ValueError：实际条件是**ValueError且str(e)包含`is not in list`**。尽管注释用constexpr签名错误解释动机，代码没有再核报错变量、精确整句或异常来源；不应改写为严格格式/根因验证。其它ValueError和其它异常继续传播，导入依赖、转换线程数等也不由逐候选try统一保护。

这意味着“容忍部分编译错误”有明确类型/消息边界，不是把所有编译、代码生成或运行异常吞掉。非空结果只说明这些候选返回了本地编译结果对象，不认证实际启动、数值或测速成功。

## 最后的小block扫描如何构造

_compile_small_block_fallback使用**原self.configs[0]**作模板，而不是从全部失败配置中挑资源最少者。kwargs只选择名字以BLOCK结尾且不以R开头的键；没有这些键或没有configs直接返回空结果。R类归约BLOCK保持原值，与分层时的tile乘积规则不同。

扫描基数是1、2、4、8、16、32、64、128、256，每一轮把所有被选block键设为同一个基数，再分别按size_hints中对应的小写轴名上限裁剪。只采纳正int hint；最终取min(基数,max(1,hint))，所以最终block可能是非2次幂。**这不是各轴独立枚举的笛卡尔积**；按裁剪后的block键值组合去重，最多九个候选，可能更少，也没有在此核对它们是否与先前原候选重复。

新Config复制模板kwargs并沿用num_warps/num_stages（缺属性分别按8/1）；truthy extra_options直接赋给新配置，未深拷贝该对象，也未复制所有可能的Config附加属性。编译时逐项收集成功结果，不是首次成功就停止。

这条最后扫描只catch三类编译/资源错误，**没有复用常规批次对签名ValueError的特殊跳过**，该ValueError也可能直接中断扫描。若扫描全部失败，worker抛NoTritonConfigsError；其报文里的Last error仍使用前面批次的last_exc，因为扫描的fb_last_exc只在扫描成功分支才合并。排查最终资源失败应保留每条debug日志，不把报文最后一项误认成最后一次小block尝试的错误。

## 单配置常量过滤与选项覆盖顺序

_precompile_config先deepcopy self.triton_meta；从cfg.kwargs新增到constants的键只允许是kernel声明的constexpr名字。这个过滤不负责清理compile_meta原本已有的constants。若声明了num_warps/num_stages且constants中尚无该项，再从Config补入；编译选项中的warps/stages也按Config设置。

本地debug初值由assert_indirect_indexing（缺省True）、非is_hip与ncfg.triton_debug共同决定；所核config声明triton_debug=False。GPUTarget来自device_props.type/cc，warp_size假值回32；这里只记录实际取值方式，不将旁边的历史版本注释变成任意Triton版本的兼容承诺。ASTSource不可用会报RuntimeError，不能算作正常小tile资源回退。

options先设num_warps/stages/debug、sanitize_overflow=False、mix_mode='aiv'、enable_bisheng_compile=True，以及VF开关/模式/级别；config里对应VF默认声明为False/None/None。**随后options.update(cfg.extra_options or {})**，同名键可以覆盖前面设置，不只是额外加入auto_blockify_size。外部后端如何接受或忽略这些键尚未在本卡闭合，不能把注释所称选项解析行为当作已审结论或推荐随意覆盖安全选项。

triton.compile失败只按类型选择debug或exception日志并重新抛出，是否跳过由外层批次决定。成功后先构造包含block_hints的metadata，再把binary hash登记TritonBundler，随后尝试静态结果选择；有静态kernel则包成NPUStaticTritonCompileResult，否则用NPUTritonCompileResult。这不是静态选择规则、grid、runner ABI或启动成功的完整证明，也没有把此前编译和Bundler登记做成统一回滚事务。

诊断时分别保存原候选列表、实际tier、异常类型与完整消息、最后扫描的每项block/warps/stages/extra_options以及首次编译与稳态计时。局部编译回退既不保证所有失败可恢复，也不保证最小block或任一成功候选最终最优；本次没有运行资源或性能实验。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)：207–215,696–1082行；仅列出有界读取，不提升整个模块资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：421–421,438–449行；仅列出有界读取，不提升整个模块资格。
