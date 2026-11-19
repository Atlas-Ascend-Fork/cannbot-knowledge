---
type: Guide
title: cache_compile加载后的参数对象绑定与重建边界
description: 解释TorchAir持久缓存如何恢复代码、解析当前参数并在rebase时捕获Tensor引用，以及加载失败清理与版本检查的实际范围。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_cache_compiler.py
  role: implementation
created_at: '2026-11-10T11:19:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# cache_compile加载后的参数对象绑定与重建边界

## 固定版本与证据范围

定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的CompiledModel.load、rebase、参数解析和LazyCompiledModel调用链；所述行为在两版一致。本卡补充[公共cache_compile契约](../../../apis/torchair/ge_cache_compile.md)的加载实现，不重复缓存路径和部署配套说明。仅静态审阅，没有反序列化、执行缓存代码、替换设备参数或测量启动时延；硬件范围未知，保持draft与空平台。

## 命中文件仍需恢复可调用代码

load先取得文件真实路径、检查存在及拥有者/权限，使用共享文件锁读取缓存工件，再检查内部meta.version与CompiledModel.VERSION是否相同，恢复compiled_fn与compiled_fx。该内部格式版本匹配不是CANN、PyTorch、驱动、硬件或业务输入兼容的完整证明，也不是缓存已经被GE设备执行的证据。

rebase要求compiled_fn.co_names中恰有一个以__compiled_fn开头的名称；随后通过_compile_py_code恢复compiled_fx.py_code里的kernel，按模块是否提供相应更新函数设置GE缓存和静态kernel缓存目录，再解析当前模型需要的参数。载入工件、恢复Python模块和设备编译结果命中是不同步骤，应分别检查。

## 参数按缓存签名解析一次

_get_used_params先收集当前model.named_parameters与named_buffers，再按compiled_fx.input_parameters记录的顺序查找名称。找不到时只接受所实现的L['...']来源形式：self属性链，或func闭包自由变量的属性链；不满足便ValueError。缓存里记录了某个名字不表示任意新模型属性或结构变更都可自动适配。

rebase把解析所得parameters列表捕获进闭包；kernel调用时先放这些参数，再追加本次用户args。LazyCompiledModel首次__call__得到_compiled_model后会保留它，后续调用直接使用该对象；这条命中路径没有每次重新调用named_parameters或_get_used_params。

据此静态推断，rebase后把module.weight替换为新的Parameter对象，不能依赖该闭包自动取得新对象；原Tensor对象内的内容更新与替换对象/更换存储也需要分别核对。固定地址、布局、形状或模型结构改变时，重新建立匹配的包装和缓存并验证输出。这里没有运行试验，不能从Python引用规则直接推广所有底层冻结权重与设备图的更新能力。

## 加载失败不只包含文件损坏

LazyCompiledModel.compile在缓存文件存在时，把load、compiled_fx缺失时的recompile以及rebase放在同一try中。当前两版recompile直接抛RuntimeError“not supported yet”，所以该分支不会成功补全旧工件。

以上步骤任一Exception都会记录Clear broken cache，然后调用remove_cache处理该compiled_module所在的真实父目录，再回到ModelCacheSaver重建路径。日志中的broken因此也可能来自版本不匹配、参数解析或代码恢复错误，不能只解释为二进制文件被截断。目录清理本身若失败仍会抛错，不应承诺任何异常都能自动恢复。

这条自动回退发生在首次初始化的加载/重绑定阶段；成功得到_compiled_model之后，__call__对实际执行没有包同一个清缓存重试分支。设备运行错误或后来改变输入语义，不应被当作必定触发自动失效的机制。

## 使用和验证

区分读取成功、rebase成功、设备产物命中和结果正确；保存loaded日志本身不足以完成验收。参数替换、结构变更、首次加载失败及实际运行错误分别验证，重建限定于相应模型/拓扑/配置的缓存命名空间。对于GE固定权重，还要核对[首次真实地址绑定](torchair_ge_frozen_placeholder_runtime_binding.md)，不从参数名一致推断地址契约成立。

- [可读缓存的文本边界](../../../apis/torchair/readable_cache.md)
- [模型调用中的持久编译缓存](../../../optimizations/rules/torchair_cache_compile_persisted_graph.md)

## Evidence

- [主线加载与重绑定](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py)（primary）：127–138、170–188、237–332、580–588、612–676。
- [发布加载与重绑定](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_cache_compiler.py)（implementation）：169–187、224–320、527–535、574–599及CompiledModel.VERSION；定向审阅，不表示文件全文覆盖。
