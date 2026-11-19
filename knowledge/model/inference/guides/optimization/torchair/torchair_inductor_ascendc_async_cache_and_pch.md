---
type: Guide
title: Inductor AscendC异步编译：私有产物、缓存与PCH
description: 完整对照两版compiler提交和构建本地定义，核对按kernel锁、并行任务依赖、发布顺序、缓存身份与PCH回退。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py
  role: implementation
created_at: '2026-11-11T03:57:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# Inductor AscendC异步编译：私有产物、缓存与PCH

范围为TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的compiler本地实现。两版各自完整Python文件已读；产品和配套未知，保持draft/空平台，未运行构建或加载。包安装入口复用[版本与排障](torchair_inductor_ascendc_package_and_debug.md)，完整lowering/scheduler不是本卡的覆盖范围。

## 真实入口和版本差异

所读两版NPUKernel.codegen都将生成的name/tiling_def/host_impl/device_impl/cpp_wrapper字典交async_compile_ascendc，主线另外生成adapter/tiling-wrapper、静态标记和控核字段，FX Wrapper也委托同一compiler入口。主线调度在首个未命中自身kernel缓存的新codegen前触发一次PCH预热。这里只绑定这几个npu.py调用点，不能据此关闭其完整5526行调度实现。

| 固定实现 | 缓存与提交行为 |
| --- | --- |
| 发布 | 路径为cwd/.npu_kernels_<user>/<name>/<MD5>，MD5按artifacts插入顺序拼接除name外的值。async_compile将原生compile_threads设为max(32,原值)；executor存在且非_debugging_host_only才交进程池，否则同步。不能把该发布入口的compile_threads=1当作必然保持单线程。 |
| 主线 | 路径以config.asc_cache_dir、净化hostname、name及MD5组成。按排序后的字段值拼接，纯空白行置空；排除name/is_static/has_matmul_template，动态核另排除两个控核字段，静态核保留。compile_threads改为min(32,原值)，大于1、executor存在且非debugging_on_cpu时采用异步；TopN整体一任务，JIT分阶段。 |

hash只描述这个实现选择的生成内容和目录身份，没有在此覆盖所有环境、依赖及头文件内容。FusedKernelSpec/TilingInfo自定义构造只逐key setattr，类型注解不构成严格字段、缺键或数值检查。cache_command在target已存在时只validate_lib并返回，不因脚本变化自动重编；单独的is_file_content_equal采用strip后文本相等，实际用于adapter头文件变化判断。

## 主线按kernel协调与私有staging

async_compile在lib_dir/compile.lock下观察optimize_tiling和所需文件；命中后检查库、注入限制并返回运行对象。miss释放这次锁后，JIT协调器在进程内以lib_dir共享一个Future，完成callback只在仍指向同Future时移除登记；后台daemon线程再次取得同kernel文件锁，复查缓存后构建。不同lib_dir有不同锁，不是所有kernel共用一个host锁。

每次JIT请求使用.build/<pid>_<uuid>私有目录。wrapper、tiling host object、device object及可选adapter交同一进程池；CV融合根据has_matmul_template的True/字符串True/1判断，先等tiling结果再将tiling_obj_paths交device任务，其他路径保持host/device可并行。原子阶段要求host_obj/device_obj字典，链接前要求tiling对象、kernel对象及source路径，按rt_launch选择build_kernel_so或v2。

_AscendcParallelFeature用锁累计三个前置任务及可选adapter的完成/首个异常。全部成功后，callback只把feature放入SimpleQueue，由常驻daemon线程向同一pool提交最终链接，避免直接在SubprocPool callback内再submit。失败则唤醒等待者并保留异常；result缓存最终kernel、失败状态，并按cleanup开关清理私有目录。其result(timeout)局部等待与子Future调用未使用timeout参数，不能仅凭签名推定该层有超时取消。

发布前先检查staging wrapper/kernel，再逐个os.replace到公共文件；可选aicore bin和adapter.so/.h/.cpp继续发布。它不是整个文件集的一次事务替换：后段失败不在此回滚前面已替换项；复用本入口文件锁的读者受同一锁协调，任意外部读者的观察另行核对。只有_submit_parallel_jit_compile成功返回feature后，协调器围绕result/publish的finally才清理本请求私有目录；更早在创建build_dir后pool.submit抛出等情况，不由这个finally保证清理。CV等待tiling结果另有局部失败清理。不能把注释中的完整发布当全部失败路径无残留/回滚保证。

同步主线compile_ascendc持同kernel锁，非TopN时先wrapper后通过生成的jit_compile/v2脚本构建kernel；发布实现则先构建kernel、再wrapper。两版recover_dir/never_change_dir在finally恢复cwd；实际普通构建通过当前Python执行生成脚本，CPU调试分支直接exec脚本。本文只静态说明这些调用，没有执行它们。

## PCH独立缓存与失败回退

主线wrapper编译器取CXX、找到的g++或g++默认名，标准由Torch工具helper决定，实际flags为该标准、fPIC、w、O2。普通构建标志还从Torch/TorchNPU/CANN目录取得include及库，存在时添加matmul/runtime/profiling路径；ABI宏基于Torch compiled_with_cxx11_abi。发布则使用固定g++/c++17及NpuContext，不能跨快照套用PCH。

PCH key的SHA256包含版本标识、解析后的编译器路径/版本、编译flags、ASCEND_环境项和公共include名称；compiler identity在进程中lru_cache一次，未对全部头文件内容做hash。PCH目录位于用户缓存torchair_wrapper_pch_cache，失败目录位于临时目录、按uid及缓存根隔离；build/rejected失败和building标记按文件mtime、3600秒窗口判断，未来mtime按age=0处理。

预热在线程池单worker执行，进程内按PCH key去重；wrapper实际编译用build=False只读已发布且非空gch，不等构建锁也不启动构建。预热失败不会让同一进程的已登记key自动重排，提交失败才从去重集合删除。实际build=True在PCH key锁内复查成功缓存、失败/遗留building标记；成功缓存清理三个标记，有效building只告警一次并回落，过期标记在锁内清除后重建。

PCH构建去掉-L/-l，先写临时输出，要求成功且非空再os.replace；finally清临时文件。已处理构建错误写失败文本并移除building，未捕获BaseException则保留building。错误文本包含原因及可选shell引用命令/stderr。wrapper用PCH失败时删除匹配gch、写rejected标记并重试一次无PCH；没有PCH时的构建错误直接上抛。失败标记、普通库缓存和按model调试目录是不同状态。

validate_lib只检查非符号链接、普通文件、owner为当前用户/root及group/other不可写，要求改权限时去掉其写位；它不验证ABI、数值或导出符号。file_lock使用flock并在finally解锁；跨系统共享锁保证继续按[包调试边界](torchair_inductor_ascendc_package_and_debug.md)处理。

Adapter头按strip后内容变化重新写入并移除旧adapter库/source，其编译筛选include和非Torch库路径，保留ACL和libdl；actual标准仍走_build_cpp公共路径，注释中的命令只用于诊断。_compile_cache_lock及logged helpers把锁等待、持锁、wrapper/host/device/link阶段分别记时，不是设备性能实测。

首次编译、PCH预热、cache hit、私有目录构建和真实执行成本分别观察。运行参数、共享库加载及CPU假对象见[Wrapper ABI](torchair_inductor_ascendc_wrapper_launch_abi.md)，静态选择见[TopN](torchair_inductor_ascendc_static_topn.md)。

## 编译实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py)（primary）：1–718。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_compiler.py)（implementation）：1–1230。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py)（implementation）：1–116。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_compiler.py)（implementation）：1–201。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（implementation）：1536–1615, 5135–5176。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/npu.py)（implementation）：225–257。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py)（implementation）：154–195。
