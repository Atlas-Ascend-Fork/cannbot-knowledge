---
type: API
title: 捕获图张量诊断：print/save版本参数与异步落盘
description: 区分发布多文件保存和主线列表单文件，说明命名计数及Python pending回调完成边界。
tags:
- task.lookup
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SaveNpugraphTensorKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/tests/smoke/data_dump_test.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/tests/smoke/data_dump_test.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/fx_dumper.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/data_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/custom_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/utils.py
  role: implementation
created_at: '2026-11-09T20:57:33Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# 捕获图张量诊断：print/save版本参数与异步落盘

## 固定版本与复核边界

文档为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda各自收录页；发布对应ascend_26_0_pt28。实现分别为TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b和独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把独立main当已配套发行。

产品逐接口/版本限定；950条目如仅DT便不扩PR，旧Atlas不自动映射新型号。静态阅读不表示已调用设备、图捕获、回调、文件解析或性能验证；stable不表示运行verified。本次没有执行上游或加载任何模型、检查点和dump数据。


## 模式和支持范围

print_npugraph_tensor(input,tensor_name=None)的OpPlugin文档仅在main收录；save_npugraph_tensor发布和main均有文档。两者main仅列A2/A3，未给950证据；支持eager、torch.npu.graph与npugraph_ex示例。避免普通print/torch.save在捕获路径中的同步/断图，不等于诊断没有D2H、流依赖或性能影响。

已静态核对的TorchNPU main graphs.py注册两个torch.ops.npu副作用算子及Fake空实现；Fake调用不保存真实数据。固定发布TorchNPU的已搜索Python/C++/YAML中未找到同名保存实现，故发布5参数用法仅按OpPlugin文档记录，不承诺当前这组包已实际注册、也不据搜索缺项宣称所有发布包不存在。

## 保存接口的版本不兼容

发布文档save(input,save_path=None,save_name=None,save_dir=None,suffix=None)：单Tensor用完整save_path、后缀.pt/.bin；列表/tuple用save_name、save_dir、suffix分别按输入序号保存多文件，save_dir默认当前路径、suffix默认.pt，文档称尝试创建不存在目录。发布.tensorlist示例与实际部署注册仍需核验。

main为save(input,save_path=None,overwrite=False)，去掉上述三个列表专用参数；注册重载名tensor_list（带下划线），非空list/tuple且全Tensor、同设备，实际一次torch.save(list)到同一个文件，不是逐Tensor拆文件。main由调用方保证父目录存在，后缀遵循torch.save，缺后缀补.pt，不能将扩展名.bin等同未序列化的裸字节。

main默认路径tensor_时间戳，NPU另加device编号；overwrite=False再加进程内计数，True不加计数而覆盖。计数按路径键用锁递增，不扫描已有磁盘文件，也不提供跨进程互斥/排重保证；CPU路径没有NPU device后缀。页面加载样例省略实际计数，不能据样例名字认定文件已存在或可反序列化，本次未读取任何dump。

## 打印、回调与完成条件

文档tensor_name显示前缀冒号，main实际打印name=值，并附shape/dtype；不要按文档标点解析日志。CPU路径直接打印/torch.save，NPU路径取每设备诊断流，先等待计算流event，再异步D2H到连续CPU数据，提交Host函数，最后计算流等待诊断流event。

C++Host函数先复制缓冲区再排Python pending调用；主线程pending处理时才执行print/save。一次调度尝试16次、间隔1ms，满队列交重试线程；复制/重建/回调错误有清理或unraisable报告路径。设备流event完成及接口返回None都不证明Python回调已完成或文件已落盘，需核对实际路径/错误和产物完整性，不能把stream wait当同步文件确认。

整图Dump与单点诊断还有SuperKernel组合限制，见[数据Dump模式](../../guides/optimization/torch_npu/torchair_data_dump_modes.md)。这些静态调用/队列阅读不提供所有底层Host回调或捕获生命周期已运行验证的保证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-print_npugraph_tensor.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-save_npugraph_tensor.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.h)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）


- [增补固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SaveNpugraphTensorKernelNpuOpApi.cpp)（primary）
- [增补固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（header）

## 发布侧op-plugin的host回调实现

OpPlugin发布pin在op_plugin_functions.yaml 7335/7349注册save_npugraph_tensor（单Tensor）与save_npugraph_tensor.tensorlist（TensorList）两schema：Tensor/Tensor[]输入为必选位置参数，仅*之后的save_path（单Tensor schema）与save_name/save_dir/suffix（tensorlist schema）为keyword-only可选，op_api/exposed/internal_format_opapi均[v2.6,newest]；实现在opapi/SaveNpugraphTensorKernelNpuOpApi.cpp（330行全文、发布独有文件、无尾换行）。主线op-plugin的yaml与opapi目录对两schema均零命中（rg负向核实），主线实现仍在TorchNPU仓（见上文main段）。上文“发布TorchNPU仓未搜到同名实现”的负向记录不变；补强为：发布5参数用法的C++注册与实现在op-plugin发布侧成立，Python绑定层glue不在本节来源内，其发布侧注册与生成式绑定契约见下文增补一节。

实际门槛与动作：两入口都TORCH_CHECK输入设备为NPU（PrivateUse1，TYPE错误）；列表入口另要求非空，且逐张量仅校验device().type()与首张量相同（TYPE错误；不比较NPU ordinal，该缺席不构成混合设备操作受支持的证明）。路径解析中显式save_path/suffix的扩展名只接受.pt/.bin（PARAM错误）；父目录不存在时create_directories，失败或存在但非目录抛runtime_error；save_path留空时默认名tensor_<yyyymmddhhmmss><3位毫秒>_device_<idx>.pt（chrono+localtime取本地时区）。单Tensor最终名在扩展名前追加_device_<idx>与_<unique_index>；计数是进程内全局unordered_map（互斥锁加原子自增，键为“路径_后缀”），不扫盘、无跨进程互斥——与上文main侧Python按路径键加锁计数的语义一致。列表入口的unique_index在调用时（回调前）按键<dir>/<name>_save_tensors_device_<idx>_<suffix>取号，回调内逐Tensor落盘为<dir>/<name>_<i>_device_<dev>_<unique_index><suffix>。

回调链：两入口都把参数打包成堆上new的结构体，经AclrtLaunchHostFunc提交到当前NPU流的host回调后立即返回。回调内逐Tensor contiguous()、按原sizes/dtype新建连续CPU张量、aclrtMemcpy做D2H（numel为0跳过）、再write_tensor：ofstream二进制trunc写入，open/write/close任一失败抛runtime_error。序列化的本地确切调用是torch::pickle_save（实参为torch::jit::IValue包装的Tensor）；落盘字节的具体容器格式未核验，不断言其为裸pickle或torch.save的zip容器，能否被torch.load反序列化亦未验证（静态口径，未核对装机vendor libTorch）。堆上new的参数结构体本文件未见delete，其释放生命周期在已读源码内未确定（AclrtLaunchHostFunc/ACL侧实现不在本卡来源内），既不推断运行时负责释放，也不据此断言泄漏。回调在流上执行、接口返回不等于落盘完成，与上文“完成条件”一节口径一致。


## torchair固定包内的消费者契约

TorchAir 两固定 pin 的四个树（集成 python/torchair 与独立 npugraph_ex/npugraph_ex，各两版）都只引用 `torch.ops.npu.save_npugraph_tensor.default`，仓内不定义该算子（无截断 rg 负向核实：命中仅 utils.py 的 save_op 赋值与插入循环、npu_fx_compiler/fx2acl 的导入、冒烟测试的 torch_npu.save_npugraph_tensor 调用）。插入形制四树一致：`call_function(save_op, args=(node,), kwargs={"save_path": ...})`——位置张量加 save_path 关键字，与 main TorchNPU 注册 schema `save_npugraph_tensor(Tensor input, *, str? save_path=None, bool overwrite=False)`（graphs.py 381–383）及发布 op-plugin 单 Tensor schema 的 keyword-only save_path 相容；save 与 print 同被标 has_side_effect，FX 追踪不会消除这些节点。torchair 传入的 save_path 只是「节点名.pt」裸词干（主线独立包 490–527；其余三树同循环），产物名中的 `_device_<序号>_<计数>` 后缀由前文两侧实现追加——这正对应 npugraph_ex data_dump 文档给出的 add_device_0_0.pt / test1_device_0_0.pt 命名承诺：TorchAir 侧只保证词干与 FX 节点名一致，后缀语义不属于 torchair 契约。

去重契约：插入循环跳过 output 节点、save 算子自身、已有 save 消费者的节点（`any(_is_save_op(u) for u in n.users)`）与非 tensor 节点（meta 无 tensor_meta）。用户在 forward 里直接写的 torch_npu.save_npugraph_tensor 经 Dynamo 追踪成为同一 npu.save_npugraph_tensor.default 节点，使该张量不会被整图 dump 重复插存；独立包冒烟测试以此断言 mm 不重复落盘、其下游 square/pow 落盘（两版 data_dump_test.py 的 test_aclgraph_data_dump_has_saved：主线 45–75、发布 42–74）。eager 联动不经本算子：主线独立包 force_eager+dump_tensor_data 走 `_NpuFxDumper` 解释器，对每节点 INPUT/OUTPUT 用 np.save 落 .npy（fx_dumper.py 55–78，时间戳命名、bfloat16 先转 float32），与 .pt 产物是两条不同通道。入口门也有分野：主线集成（utils.py 450–455）、发布集成（431–435）与发布独立（454–459）的插入函数先查 `configs.get('aclgraph.enableDump','0')!='1'` 即整体跳过并返回原图，主线独立树无此门（npu_fx_compiler.py 696–703 的 force_eager 分支与 722–725 的 original 档直接传 dump 根目录）。以上为静态配对，未在设备上验证落盘内容或回调时序。

- [数据 Dump 模式](../../guides/optimization/torch_npu/torchair_data_dump_modes.md)

## 固定来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py)（implementation）：450–485。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/utils.py)（implementation）：431–466。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：490–527 全函数。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：454–501 全函数。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/tests/smoke/data_dump_test.py)（implementation）：14–75 全文。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/tests/smoke/data_dump_test.py)（implementation）：42–74 全文。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/fx_dumper.py)（implementation）：21–78、110–126。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：680–725。
- [固定约束 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/data_dump.md)（constraint）：32–40、42–80（场景1/场景2 产物命名与 save_npugraph_tensor 说明）。

## 增补：save_npugraph_tensor 双源注册与发布生成式绑定

主线 torch_npu 是**双源守卫**：`torch_npu/npu/graphs.py:381` 以 `if not hasattr(torch.ops.npu, "save_npugraph_tensor")` 为门——已装 op-plugin 提供注册时直接用插件实现；否则 `_npu_lib.define` 两 schema（save_npugraph_tensor 与 .tensor_list，带 `bool overwrite=False`）+ `_npu_lib.impl`（PrivateUse1 与 CPU 双键）+ `has_side_effect` + `register_fake` 空实现（:382-399）。即主线同文件里的 Python 实现是插件缺位时的回落，不是并行第二注册。

发布侧 torch_npu 零命中维持；`torch_npu.save_npugraph_tensor` 属性由构建期生成的 `torch_npu/utils/custom_ops.py` 提供：pytorch 仓 `torchnpugen/custom_functions.py:287-293` `gen_custom_ops_patch` 对合并 yaml 的 custom functions 逐名生成 `torch_npu.<op> = torch.ops.npu.<op>`（仅 SKIP_PYTHON_BINDINGS_SIGNATURES 名单可跳过，当前为空）；`torchnpugen/gen_backend_stubs.py:1772-1794` 另按 yaml `exposed` 标记（`torchnpugen/utils.py:179-186` filt_exposed_api）写 `exposed_api.py` 的 `public_npu_functions` 名单。生成文件不随两仓提交，本节为其生成契约的静态依据；具体安装产物是否含该属性仍需装机核对（上文口径不变）。
