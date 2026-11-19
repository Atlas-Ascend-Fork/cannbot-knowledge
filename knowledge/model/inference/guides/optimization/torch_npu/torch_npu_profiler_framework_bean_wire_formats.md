---
type: Guide
title: Profiler框架记录解码：二进制布局、时钟校准与不完整数据
description: 核对Torch算子、队列标记、GC、Python追踪和参数记录的固定布局、关联字段与TLV/Binary解码边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_gc_record_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_mark_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_param_tensor_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_python_tracer_func_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_python_tracer_hash_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_gc_record_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_mark_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_param_tensor_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_python_tracer_func_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_python_tracer_hash_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_binary_decoder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_tlv_decoder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_fwk_file_parser_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_binary_decoder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_tlv_decoder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_config/_fwk_file_parser_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py
  role: implementation
created_at: '2026-11-11T04:30:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler框架记录解码：二进制布局、时钟校准与不完整数据

## 固定版本与入口

本卡全文核对TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的框架Bean、两种解码器及FwkFileParserConfig。所列成对模块完整AST相同，原始文本差异另行核对；这不证明全部Profiler、采集端或其他版本的协议相同。平台未知，保持draft，没有导入上游或解析真实采集数据。

FwkFileParserConfig把`torch.op_range`、`torch.op_mark`、`torch.memory_usage`、`torch.gc_record`、`torch.python_tracer_func`、`torch.python_tracer_hash`、`torch.param_tensor_info`映射到相应FileTag。前三种正则从字符串开头匹配，GC、Python与参数三类字符串没有显式`^`；这里只登记正则文本，实际文件发现与匹配调用另计。`prof_bean/__init__.py`仅设置`__all__=[]`，不会自动导出或初始化这些类。

## 小端固定区与可变字段

这些格式的`<`使用小端、标准字段大小且不补本机对齐。固定区大小与FILE_BEAN_MAP一致；解包失败会传播，类型注解不是运行时校验。

|记录与解码方式|固定区及字节数|字段与额外信息|
|---|---|---|
|TorchOpBean，TLV|`<3q4QB?`，58|开始、结束、sequence三项有符号64位；PID、开始TID、结束TID、前向TID四项无符号64位；scope一字节、is_async布尔。结束TID和is_async虽被解包，本类没有单独对外getter。|
|OpMarkBean，TLV|`<q4Q`，40|时间、category、corr_id、TID、PID；TLV 1是原始名称。category只接受0入队开始、1入队结束、2出队开始、3出队结束，其他值构造Enum时失败。|
|MemoryUseBean，TLV|`<7q2b3B2Q`，77|布局与单位见[内存Bean](torch_npu_profiler_memory_bean_units_and_defaults.md)。|
|GCRecordBean，Binary|`<3Q`，24|PID、开始、结束；枚举中的开始字段拼作`STRAT_NS`。|
|PythonTracerFuncBean，Binary|`<4QB`，33|开始、TID、PID、hash key、trace_tag；后四项转int后由getter返回，本类不校验tag枚举或配对Python调用。|
|PythonTracerHashBean，TLV|`<Q`，8|key加TLV 1的value；缺value默认空字符串，不在这里恢复Python调用栈。|
|ParamTensorBean，TLV|`<Q`，8|key；TLV 1是module_params，2是optimizer_params。|

TorchOpBean的TLV编号为：名称2、Input Dtypes 3、Input Shapes 4、Input Tensors 5、Input TensorLists 6、Input Scalars 7、Call Stack 8、Module Hierarchy 9、FLOPs 10。`name`把缺省空字符串或现有值转str；`inputs`仅交回三类输入元数据的原始值，不构造真实Tensor。`args`带sequence和前向线程ID，另选取存在的dtype/shape/stack/module/flops；名称和三类输入数据不重复塞进args。dtype、shape、stack中的分号换成分号加CRLF，缺省空值变空字符串；module与FLOPs原样保留，不能把字段存在解释成已计算优化收益。

ParamTensorBean只对存在的module/optimizer字符串按`}`切分，不strip也不移除尾部空片段；缺字段保留None。`params`每次返回新的KeyAndParam容器，但其列表仍是原引用，List[str]注解不排除运行时None。它不在这里解释每个Tensor片段的内部字段或恢复存储，继续参考[Tensor与Storage身份](torch_npu_profiler_tensor_storage_identity.md)。

## 时间需要已加载的时钟上下文

Torch算子起止、队列mark时间、GC起止和Python函数开始均经ProfilerConfig的`get_timestamp_from_syscnt`再`get_local_time`。禁用syscnt转换时返回输入；启用时计算`int((syscnt-start_cnt)*(time_fmt/freq))+time_offset`，time_fmt默认1000，极小freq会报错；随后本地时钟转换是`int(monotonic_ts+local_time_diff)`。初始配置syscnt禁用、freq为100、偏移和起点为0。这些Bean不负责加载采集配置，不能把尚未加载上下文的原始计数直接当成已校准ns。

主线禁用条件写`not _syscnt_enable`，发布写`_syscnt_enable == False`；正常布尔值同义，异常非布尔配置并非普遍等价。TorchOpBean对名称、ID、时间、args、inputs等惰性缓存，固定区在构造时解包而TLV仍引用传入字典；不要把它当成深拷贝的不可变快照。其dur是校准后结束减开始，没有负值截断，scope原值返回，`is_torch_op=True`。

GCRecordBean在构造时转换时间，**PID和TID均从同一个PID槽取值**；pid setter只改PID，不同步TID。name固定GC、args为空、dur为end-start；该TID不能证明采集到了独立GC线程号。Python函数记录也在构造时转换开始时间。

## 队列标记尚不是完整区间

OpMarkBean区分原始时间`time_ns`与配对后的`ts/dur`。构造函数没有初始化`_ts/_dur`，在外部赋值前访问相应getter可能AttributeError。配对路径按同TID和原始名称寻找开始标记，把结束mark的ts设为开始时间、dur设为end-start；未配对的结束标记计失败并跳过。getter/setter本身不完成关联或时长校验。

mark的pid/tid/corr_id/原始名称和布尔分类getter按固定槽或Enum返回；enqueue显示名固定Enqueue，dequeue显示名为`Dequeue@`加原始名称，args仅含correlation_id，`is_torch_op=False`。corr_id是后续归因线索，不等于全局唯一事件或stream/task标识；不能由一个mark推断排队等待时长。消费侧参见[算子耗时与队列关联](torch_npu_profiler_operator_time_attribution.md)。

## 截断与坏字段的实际处理

TLV外层每项为2字节`<H`类型、4字节`<I`长度和payload；外层保留payload列表，不据外层type筛选。内层将type映射到解码字符串，同type重复时后者覆盖前者。缺type、length或完整payload时warn并停止这一层，已解出的前缀仍返回；固定区不够的外层记录warn并跳过。不可UTF-8字段写`N/A`并累加类计数，decode正常走到末尾后统一warn并清零。

因此返回非空不证明采集完整；损坏后缀、重复字段和N/A都需要保留诊断。构造Bean的异常未被TLVDecoder捕获，也可能使该次计数未走到清零。没有本地checksum、schema补齐或字段语义校验。BinaryDecoder只按注册的正struct_size切整块，**不足一块的尾字节直接忽略**，不发TLV同样的丢数据警告；Bean构造异常同样传播。它不是任意不可信struct_size的防御接口。

FwkFileParser的已读入口在找不到对应文件时返回空列表；有文件后读字节，再根据登记的is_tlv/struct_size分派。空结果还可能来自没有文件、记录被跳过或Binary不足整块，不能推断模型没有执行。定位时保存版本、文件字节数、解码警告、固定区长度、已加载时钟参数和关联覆盖，再分析性能。

## Evidence

本文所依据的完整模块与有界辅助来源如下；未列完整范围的依赖保持独立待审，固定提交不等于设备验证。

- [ac0e156 __init__.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/__init__.py)：1–1。
- [ac0e156 _gc_record_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_gc_record_bean.py)：1–53。
- [ac0e156 _op_mark_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_op_mark_bean.py)：1–137。
- [ac0e156 _param_tensor_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_param_tensor_bean.py)：1–45。
- [ac0e156 _python_tracer_func_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_python_tracer_func_bean.py)：1–47。
- [ac0e156 _python_tracer_hash_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_python_tracer_hash_bean.py)：1–31。
- [ac0e156 _torch_op_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py)：1–148。
- [f3ecfe4 __init__.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/__init__.py)：1–1。
- [f3ecfe4 _gc_record_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_gc_record_bean.py)：1–53。
- [f3ecfe4 _op_mark_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_op_mark_bean.py)：1–137。
- [f3ecfe4 _param_tensor_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_param_tensor_bean.py)：1–45。
- [f3ecfe4 _python_tracer_func_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_python_tracer_func_bean.py)：1–47。
- [f3ecfe4 _python_tracer_hash_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_python_tracer_hash_bean.py)：1–31。
- [f3ecfe4 _torch_op_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_bean.py)：1–148。
- [ac0e156 _binary_decoder.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_binary_decoder.py)：1–12。
- [ac0e156 _tlv_decoder.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_tlv_decoder.py)：1–62。
- [ac0e156 _fwk_file_parser_config.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_fwk_file_parser_config.py)：1–33。
- [f3ecfe4 _binary_decoder.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_binary_decoder.py)：1–12。
- [f3ecfe4 _tlv_decoder.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_tlv_decoder.py)：1–62。
- [f3ecfe4 _fwk_file_parser_config.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_config/_fwk_file_parser_config.py)：1–33。
- [ac0e156 _profiler_config.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/_profiler_config.py)：66–83、120–129、262–263。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：40–40。
- [f3ecfe4 _profiler_config.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/_profiler_config.py)：45–62、96–105、212–213。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：43–43。
- [ac0e156 _fwk_file_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py)：33–98。
