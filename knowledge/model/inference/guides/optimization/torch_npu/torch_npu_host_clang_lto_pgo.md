---
type: Guide
title: Host编译：Clang配套与已废弃的BiSheng优化路线
description: 记录固定主线的Clang构建顺序及历史LTO/PGO流程；产品范围未闭合，保留为草稿。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_introduction.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_introduction.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/install_bisheng_compiler.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/install_bisheng_compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/python_compilation_optimization.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/python_compilation_optimization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/pytorch_compilation_optimization.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/pytorch_compilation_optimization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/torch_npu_compilation_optimization.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/torch_npu_compilation_optimization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_faq.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_faq.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_with_clang.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_with_clang.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/comp_opt_intro_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/comp_opt_intro_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/install_bisheng_comp_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/install_bisheng_comp_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/comp_opt_py_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/comp_opt_py_fig_01.png
  role: constraint
created_at: '2026-11-09T15:01:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Host编译：Clang配套与已废弃的BiSheng优化路线

## 固定来源与适用性

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的中英文说明。BiSheng优化介绍已明确废弃并指向Clang构建作为替代；三个历史Python/PyTorch/TorchNPU优化页均明确950DT暂不支持。材料没有给出整套Host编译路线的完整正向产品矩阵，本卡保持draft和空platforms，不把未列产品自动视为支持，也不扩成950PR的结论。

这里编译的是解释器和Host框架库，和torch.compile的设备图、Inductor候选调优、Ascend C Kernel编译是不同层次。历史示例为Python3.8.17、PyTorch/TorchNPU v2.7.1，不是26.0/PyTorch2.8或主线2.14安装配方。下列命令/参数仅记录来源，未下载、安装、清理或编译。

## 替代Clang路线的顺序

先指定CC=clang、CXX=clang++，按目标上游源码的requirements-build.txt准备依赖，构建CPU版torch，设置USE_CUDA=0和USE_CUDNN=0；ARM的USE_PRIORITIZED_TEXT_FOR_LD=OFF只在来源注释中列为可能需要的链接设置。来源用setup.py build bdist_wheel并记录build.log，先安装dist中的Clang构建torch，再按TorchNPU常规源码流程构建TorchNPU。不能直接用GCC构建的torch或任意社区wheel替代其要求的Clang CPU包。

两语言特别记录Clang20与PyTorch2.12的已知编译问题，指向上游issue185618和修复PR185785，要求参考修复再构建。此处只摄取固定页的引用身份，没有读取这些外部链接、宣称补丁已合入任意版本或在本地验证。

## 历史LTO、PGO与组件配套

LTO在链接阶段利用跨文件内联、特化与常量传播；图示为各源码编成bitcode后在链接阶段优化再生成二进制/库。FullLTO/ThinLTO是两条方案，来源认为ThinLTO降低链接时间和内存开销；这些描述不是本地性能结果。PGO先插桩构建、运行代表性负载采集函数/分支计数，再利用profile第二次构建。来源提到数据库/分布式存储等场景10–30%的示例收益，不能作为模型或NPU端到端收益保证。

历史八行组合表可完整归纳为：Python用GCC或BiSheng均可，但PyTorch和TorchNPU必须同为GCC或同为BiSheng；两者混用的四种组合均标不兼容，来源归因为Pybind11相关冲突。该表不是所有现代Clang版本、C++ ABI或第三方扩展的普遍兼容证明。

旧安装页指定BiShengCompiler4.1.0的aarch64-linux包、将其bin加入PATH、lib加入LD_LIBRARY_PATH，并用clang -v观察安装；相同的中英文截图显示BiSheng Enterprise4.1.0.B007/clang17.0.6、aarch64目标。图中的本机路径、GCC与CUDA探测输出是历史样例，不是本环境状态或必需版本组合。

## 历史Python构建

Python≥3.6支持LTO/PGO，示例用CC/CXX指向Clang，configure给绝对prefix、--with-lto和--enable-optimizations，再make/install。源码构建会依赖可用系统开发头文件，可选模块缺依赖时可能构建完成却运行报模块缺失；按发行版准备压缩、SSL、ffi、readline、SQLite、UUID、GDBM、expat、mpdecimal、Tk等所需开发库，不把“成功构建”当作所有可选模块齐全。

使用conda时来源先建空离线环境，把安装prefix指到该环境，再使用bin下python3/pip3及相应python/pip链接。截图中的environment location只是指定prefix的提示，不复制样例绝对路径。FAQ称低glibc构建可向高版本迁移、反向不可；这不是跨CPU架构或依赖库任意可移植的保证。

## 历史PyTorch与TorchNPU两次构建

| 组件/阶段 | 固定示例的设置 |
| --- | --- |
| PyTorch LTO | CMAKE_C_FLAGS与CMAKE_CXX_FLAGS均含-flto=thin -fuse-ld=lld，CC/CXX为Clang，USE_XNNPACK=0，再构建wheel |
| PyTorch插桩 | 在上述两类flags加入-fprofile-generate=采集目录，安装第一次产物并运行代表模型；采集和最终优化运行均按来源设置OMP_PROC_BIND=false |
| PyTorch反馈构建 | llvm-profdata merge将profraw合成profdata，再用-fprofile-use=具体profdata路径进行第二次构建；插桩包的性能不作为最终性能 |
| TorchNPU LTO | 先构建并安装配套BiSheng版PyTorch，再用CC/CXX及ci/build.sh的--python=3.8 --enable_lto；Python版本仅该历史例子 |
| TorchNPU插桩/反馈 | --enable_pgo=1为第一阶段；运行模型、合并profraw后，将文件命名default.profdata放入TorchNPU源码目录，再--enable_pgo=2进行第二阶段 |

LLVM_PROFILE_FILE可指定生成位置，default_%m.profraw中的%m允许在线合并，%p按PID区分。FAQ允许PyTorch/TorchNPU共用采集目录并合并为同一profdata；来源称profile可移机使用，但这不保证换模型/分支/编译版本后仍具有代表性或产物ABI兼容。oneDNN/ACL、BLAS加速只以外部资料链接出现，没有在本卡补齐其构建方法或产品支持。

历史流程多次出现git clean -dfx、强制重装wheel等命令；这些属于构建样例的工作区操作，不是运行模型所需的优化开关。未执行这些操作。

## 缺库、头文件与ABI分别排查

找不到.so/模块先核对构建依赖与可选组件；libomp.so缺失时，历史BiSheng框架构建默认使用OpenMP，需要相应运行库及可解析的LD_LIBRARY_PATH。filesystem头缺失的FAQ建议GCC8以上，不把该条升级为所有Host构建的唯一工具链版本。

basic_string等未定义符号可能来自C++11 ABI不一致，先比较两个组件build/compile_commands.json中的宏。FAQ示例通过_GLIBCXX_USE_CXX11_ABI=0重编PyTorch，是针对两端不一致的示例修复，不是无条件要求全环境使用ABI0。固定真实源码/编译器/依赖/ABI后，分别检查模块加载、正确性与关闭插桩后的模型稳态性能。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_introduction.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_introduction.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/install_bisheng_compiler.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/install_bisheng_compiler.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/python_compilation_optimization.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/python_compilation_optimization.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/pytorch_compilation_optimization.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/pytorch_compilation_optimization.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/torch_npu_compilation_optimization.md)（primary）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/torch_npu_compilation_optimization.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_faq.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/compilation_optimization/compilation_optimization_faq.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_with_clang.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_with_clang.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/comp_opt_intro_fig_01.png)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/comp_opt_intro_fig_01.png)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/install_bisheng_comp_fig_01.png)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/install_bisheng_comp_fig_01.png)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/comp_opt_py_fig_01.png)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/comp_opt_py_fig_01.png)（constraint）
