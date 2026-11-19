---
type: Guide
title: TorchNPU源码构建：工具链、增量编译与导入排障
description: 按固定提交区分双语版本示例、Ninja/Mold/CCache作用和wheel身份，定位子模块、链接、ABI及导入路径故障。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/build_acceleration.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/build_acceleration.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/faq.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/FAQ.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/setup.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/version.txt
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/build.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/test/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.zh.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/supported_tags.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/.ci/docker/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/docker/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/ci/docker/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/Dockerfile
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/Dockerfile
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/builder.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.zh.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/CONTRIBUTING.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/CONTRIBUTING.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/install.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/install.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/install.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/ci/build.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/ci/build.sh
  role: implementation
created_at: '2026-11-09T16:32:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU源码构建：工具链、增量编译与导入排障

## 固定版本和安装路径范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。中英文源码安装页列950DT、A3/A2训练系列及旧Atlas训练产品可用，明确排除A3/A2推理产品、旧Atlas推理与Atlas200I/500 A2推理产品。本卡平台只登记A2/A3/950DT；这些是本安装路径的表述，不覆盖其他特性页的产品范围，不扩为950PR，也不回推26.0/PyTorch2.8发布版。

安装页要求配套驱动、固件和CANN Toolkit、ops、NNAL；运行前配置CANN及ATB进程环境。示例/usr/local/Ascend/cann/set_env.sh与nnal/atb/set_env.sh是root默认路径，须与真实安装一致。只编译容器不要求已能访问NPU，运行则需要宿主驱动与设备依赖；构建成功不能证明设备可执行。

## 先固定构建身份

中文以PyTorch2.14/Python3.11举例，英文仍以2.13/Python3.10及CANN9.1的devel镜像举例；不把两套步骤或master克隆命令当作同一可复现环境。固定主仓提交、递归gitlink、目标解释器、torch版本/ABI、架构及工具链，再区分构建环境和安装环境。--python的3.10..3.14选择器不承诺所有PyTorch版本支持全部这些Python。

中文容器依赖示例requirements_2.14.txt、英文requirements_2.13.txt；各自主机章节又用requirements.txt，UT目录另有版本化依赖。应核对实际版本和路径，不把这些依赖文件机械叠加。默认Release、DEBUG=1选择Debug；cp311/cp310、aarch64、manylinux_2_28/linux及rc1都是具体wheel身份，不能换解释器/架构后沿用文件名。

中文GCC/CMake表为以下固定文档值；英文仅给2.13两行，未列版本不是明确不支持。

| PyTorch | GCC（两架构） | CMake X86_64 | CMake AArch64 |
| --- | --- | --- | --- |
| 2.7.1 | 11.2.0 | 3.18.4 | 3.31.1 |
| 2.9.0 / 2.10.0 | 13.3.0 | 3.18.4 | 4.0.3 |
| 2.11.0 / 2.12.0 / 2.13.0 | 13.3.0 | 3.18.4 | 4.3.2 |
| 2.14.0 | 13.3.0 | 3.18.4 | 4.4.3 |

文档依赖还包括pyyaml/setuptools/auditwheel及nanobind>=2.9。Python3.11相对3.10的dispatch性能优势是来源建议，不是本卡测量。不要用FAQ的GCC>=8旧排障下限替代这张目标版本表。

## 构建加速分别解决什么

| 手段 | 生效点与证据 |
| --- | --- |
| Ninja | setup.py优先尊重显式CMAKE_GENERATOR；未指定时才检测PATH中的ninja。不是PATH有ninja就覆盖所有显式生成器。切换生成器需另行处理已有CMake缓存。 |
| Mold | CMake查找mold并添加-fuse-ld=mold，确认真实链接选项，收益需测量。 |
| CCache | CMake配置C/CXX_COMPILER_LAUNCHER；检查实际配置及命中。中文说hit或miss增长可判断启用，但miss增长不能证明缓存命中或加速；英文建议比较重复构建及launcher配置。 |
| 仅编译目标 | 已有build目录中ninja torch_npu或相应make目标只做该增量目标，不等于重新打包、安装整个wheel或重编所有子模块。 |

仅静态阅读，未安装工具、清缓存或运行构建。源文的全树转换、删除build命令不能作为无条件修复操作。

## 按首个错误缩小原因

| 信号 | 固定FAQ案例与排查边界 |
| --- | --- |
| 缺third_party/op-plugin/config下YAML | 检查递归子模块是否完整、是否对应父提交gitlink；任意切换子仓commit后须重新记录组合，不能仍称原基线。 |
| bash出现$'\r' | 检查报错文本的CRLF，只修确认受影响的文本，不照抄全仓find转换循环。 |
| CMake旧minimum policy错误 | 中文区分3.27警告与4.0移除，英文把>=3.27写成直接退出，保留差异；FAQ建议局部传CMAKE_POLICY_VERSION_MINIMUM=3.5，不把它当所有项目/新CMake的通用保证。 |
| 头文件首字符“.”的expected unqualified-id | 检查Windows检出是否把受版本控制的符号链接变为路径文本，恢复准确链接与目标；不批量把所有相对路径头文件改软链，也不把FAQ里GE错误头复制替换Runtime错误头的捷径提升为已验证修法。 |
| filesystem缺失 | 检查真实编译器/标准库与目标表，FAQ旧GCC案例不是唯一根因。 |
| wheel is not supported | FAQ给Python不匹配案例；还需核对完整wheel标签/目标环境，--python重编不是任意架构标签的修复。 |
| import缺libhccl.so | 核对配套运行库及环境，构建时能找到torch不表示运行时CANN齐全。 |
| import段错误 | FAQ归因GCC/pybind ABI不符，须核对真实构建身份，不能由Segmentation fault唯一归因ABI。 |
| torch_npu._C缺失 | FAQ案例是源码目录同名包遮蔽安装包；检查当前目录及模块路径，再区分扩展确实未构建/安装等情况。 |

安装页的randn.npu后加法仅验证最小导入/设备/算子通路；test_autocast.py的OK只说明该次选定UT，不代表完整模型、compile、分布式或性能验收。当前未执行任一测试。

- [版本和包身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)
- [C++ libtorch_npu产物](torch_npu_libtorch_build_and_deployment.md)

## 当前构建清单与历史安装教程的区别

固定version.txt只列2.13/2.14/2.15/2.16，旧安装矩阵和原生API目录不等于当前ci/build.sh声明生产全部旧版本。该脚本的--torch检查是固定字符串包含匹配，已安装torch只比较major.minor，实际构建版本还由TORCH_VERSION或安装环境决定；通过检查不证明patch/post/ABI和子模块均匹配。详见[来源与版本基线](../../../concepts/frameworks/ascend_software_stack_baselines.md)，未执行构建版本探针。

## 测试入口、同步文件与跳过清单

两个固定提交的test/README都区分单脚本test_autocast.py、run_test.py -i test_autocast，以及-k具体用例；run_test的用例参数在--之后转交。并非每个test*文件都可直接运行，JIT子用例由test_jit.py组织；全量非分布式与分布式分别由根目录ci/access_control_test.py的--all/--distributed组织。

get_synchronized_files.sh会联网补充清单所指测试文件，本卡未执行，缺同步内容不能当所有测试都失败或都通过。DISABLED_TESTS_FILE指向unsupported_test_cases的JSON，在其他目录运行须给正确绝对路径；记录有效跳过项，跳过不计通过。test_public_bindings检查公开接口规范，不是模型数值/性能测试。

FAQ的Python3.8.1/3.9.0遍历sys.modules时“dictionary changed size”案例建议以list(sys.modules.values())取快照，它是旧测试故障线索，不把旧解释器例子当主线推荐环境，也不在此修改当前系统Python。没有运行上游UT或获取外部CPython issue内容。

## 三阶段开发镜像与脚本的实际默认

固定docker/devel的base配置manylinux、解释器软链和基础包，builder叠加gcc-toolset/CMake/CPU torch依赖，dev再叠CANN Toolkit+Ops、可选NNAL，不包含驱动。builder.sh默认显式选择builder；直接docker build不指定target时按Docker最后阶段会得到dev，不能把文档“builder默认”无区别应用到两种入口。

开发Dockerfile默认Python3.10、torch2.13、GCC toolset13、CANN9.1、910b、NNAL0；AMD64分支安装CMake3.18.4.post1，ARM没有同样pin，不能把工具链大版本或manylinux标签当所有架构的精确GCC/CMake版本。解释器软链实际指向/opt/python/cpXY-cpXY，缺对应目录就失败；设置容器运行时PY_VERSION不自动重新安装/切换全部依赖。

源码按*.dev*选择nightly CPU源，否则稳定CPU源，但实际使用--extra-index-url，保留原索引，和文档--index-url的独占源语义不同。NumPy分支为3.9→1.22.4、3.10→1.23.2、3.11/3.12→1.26.2、3.13→2.1.2、3.14→2.3.4；Dockerfile存在某分支不承诺当前TorchNPU构建清单支持该全部解释器/torch组合。

builder.sh实际帮助含Python3.14、CANN默认9.1.0；README参数表还停在Python3.13、9.1.0_beta.1，保留差异。--nnal必须配--cann；脚本CANN产品白名单950/A3/910b/910/310p/310b，产品名是包选择，不是每个模型/特性的支持矩阵。未知选项调用usage时当前总exit0，不将脚本退出码0独立视为构建/启动成功。

CANN版本与OBS release train是两个参数。脚本在非默认版本且未给release train时拒绝；直接Dockerfile的默认train仍固定CANN%209.1.0，不能只改CANN_VERSION就假设下载路径同步改变。NNAL默认不装，而运行指南又要求相应库时应核对模型依赖和ATB环境；builder可产wheel不证明设备运行环境已经完整。

## 两套CI容器目录不代表同一基线

.ci/docker README描述2.13与master两组builder/test镜像，test为Ubuntu22.04/系统Python3.10/CANN9.1.0-beta.3，master的torch例子是2.14.0.dev20260708；builder提供多Python工具链且不含CANN。ci/docker的旧路径则按X86/ARM和CONFIG_FOR_LCOV构建，发布快照举Python3.9、主线举3.10/--torch2.13或2.14。

这些是各自文档说明，不把LCOV覆盖率环境当正常性能配置，也不以旧短名单覆盖当前version.txt2.13..2.16。没有构建CI镜像、运行覆盖率/UT或执行上游脚本；镜像可启动、最小探针与目标模型验收继续分开。

## 发布README的GCC与ABI示例

固定发布快照英文README对两CPU架构推荐GCC13.3，显式开启新C++ ABI的环境例子是_GLIBCXX_USE_CXX11_ABI=1，并另举_ABI_VERSION=18以匹配社区torch的-fabi-version，推荐环境glibc2.28/GCC13.3.1。CXX11 ABI、-fabi-version、编译器/标准库与wheel标签是不同维度；该例子不是主线所有入口的默认值，也不覆盖独立LibTorch入口默认ABI0的实现。

这份README仍用v2.8.0-7.2.0分支、Python3.9和旧ci/docker路径举例；不能只把命令中的分支替换为master就视为当前可复现配套。源码构建会下载第三方依赖并执行构建脚本、产生临时产物，这是源码构建的实际外部依赖边界，不因只想产wheel就认为构建过程完全离线或等于运行时验收。未构建或调用下载脚本。

## OpPlugin独立构建入口与旧安装命令冲突

OpPlugin发布快照dedc316708372c9a8bfde4527abd2a94b74840f5的安装页仍列7.3产品分支、Torch2.6/2.7.1/2.8/2.9，表中Python可选3.8至3.11却明确2.6及之后不支持3.8，命令仍用--python=3.8构建2.7.1。其旧GCC推荐10.2/9.3.1/11.2.1又与本页逐Torch表（2.8起13.3）不同，不能直接复制旧样例。主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英表列2.7.1用GCC11.2，2.8至2.13用13.3，Python2.7/2.8为3.9..3.13、2.9起3.10..3.13；这些是独立OpPlugin安装页，不覆盖本卡父仓2.14的工具链表。

本页硬件表仍列旧Atlas、A2/A3训练及800I A2推理，没有950正向表，也没有把所有后端功能纳入支持。它与父仓某些安装页的推理排除不同，按入口分别保存，不由OpPlugin一页扩大所有源码安装/编译特性的产品范围。主线例子为Python3.10、TorchNPU v2.13.0-26.2.0，并非锁定26.0/PT2.8的命令；卸载文字误写torch而命令实际卸torch_npu，包名按实际命令理解。

两固定ci/build.sh实际默认Python3.8和PyTorch master，显式给--python/--pytorch才覆盖；镜像已装CPU torch2.13不自动固定将要获取的TorchNPU分支。build/pytorch已存在时复用，分支相同不主动fetch到最新提交，不能把“未重复下载”解释成版本已更新；分支变化路径会checkout/clean并替换子模块工作树。源码身份须记录真实提交，不能只记录参数字符串。

脚本递归更新父仓子模块，再用本地op_plugin、codegen、torchnpugen、测试和脚本覆盖third_party/op-plugin。这个集成结果可偏离父仓gitlink；BUILD_WITHOUT_SHA=1不提供源码组合证明。除v1.11.0/v2.0.1前缀分支外，它调用父仓ci/build.sh时显式--disable_torchair --disable_rpc，产出的wheel不能因“构建成功”就假定含GE/TorchAir或RPC能力。发布版submodule update另加depth=1，与主线的获取参数不同。

该入口会替换工作树/构建产物并删除旧dist后复制新wheel，执行前必须了解这些真实副作用；仅静态阅读，未调用脚本、清理目录或下载依赖。输出是torch_npu wheel而非独立op_plugin wheel，解释器、ABI、CANN及实际模型仍须分别验收；CONTRIBUTING的直接cmake/make示意不是本入口已完全离线或所有目标可独立构建的证明。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/build_acceleration.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/build_acceleration.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/faq.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/FAQ.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/setup.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CMakeLists.txt)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/version.txt)（primary）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/build.sh)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/README.md)（primary）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/test/README.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.zh.md)（primary）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/README.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/supported_tags.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/.ci/docker/README.md)（primary）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/docker/README.md)（primary）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/ci/docker/README.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/Dockerfile)（implementation）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/Dockerfile)（implementation）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/builder.sh)（implementation）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.zh.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md)（primary）

- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md)（constraint）

- [固定来源 28](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/CONTRIBUTING.md)（primary）

- [固定来源 29](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/CONTRIBUTING.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/install.md)（primary）

- [固定来源 31](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/install.md)（primary）

- [固定来源 32](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/install.md)（constraint）

- [固定来源 33](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/ci/build.sh)（implementation）

- [固定来源 34](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/ci/build.sh)（implementation）
