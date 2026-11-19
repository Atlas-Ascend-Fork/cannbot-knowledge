---
type: Guide
title: TorchNPU运行环境：pip、Docker与升级的版本约束
description: 区分产品系列、pip包、镜像标签及宿主运行依赖，保留双语安装页中的旧版本矩阵和不一致。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/installing_with_docker.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installing_with_docker.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/image_installation_and_using.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_docker.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_pip.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/check_installed_versions.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/check_installed_versions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/upgrading_and_uninstalling.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/upgrading_and_uninstalling.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/faq.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/FAQ.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/OVERVIEW.zh.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/OVERVIEW.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.zh.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/supported_tags.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/Dockerfile
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/Dockerfile
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/builder.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docker/devel/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docker/devel/Dockerfile
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docker/devel/builder.sh
  role: implementation
created_at: '2026-11-09T16:32:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU运行环境：pip、Docker与升级的版本约束

## 固定快照与使用范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。本卡消费安装页中A2/910B和A3容器路径；表中另列310P示例，未将其映射成A2/A3，也不从Docker页缺950推导整个框架不支持950。未拉镜像、安装包或升级任何组件。

## 安装身份不能简化为版本大小

英文pip表将TorchNPU产品系列26.0.0与torch-npu包2.10.0/2.9.0/2.8.0/2.7.1并列，但其命令未带post；同目录Docker表则为2.10.0、2.9.0.post2、2.8.0.post4、2.7.1.post4，均示例CANN9.0/Python3.11。不能据此认为无post包与相应镜像完全相同，锁定ascend_26_0_pt28仍依据产品配套、精确包及gitlink。

pip表中的Python范围也逐版本列：2.10/2.9为3.10..3.13，2.8仅3.11..3.13，2.7.1为3.9..3.12；两CPU架构各自列出。NumPy示例为Py3.13用2.1.2、3.11/3.12用1.26.2、3.9/3.10用1.23.2。它们是本页固定示例，不能从表里任取版本组合成所有软件的完整兼容矩阵，更不能直接推广到主线2.14。

Docker表按芯片、架构、OS和Python选择标签：X86_64示例Ubuntu22.04、AArch64示例openEuler24.03；标签还包括310p/910b/a3。文档的PY_VERSION环境值要匹配镜像实际Python，仅设置它不会安装/切换解释器。表末只支持PT2.7.1/2.9的Triton-Ascend说明与当前主线Inductor页不同，保留旧安装页范围，不据它排除所有新版本Inductor。

## 容器与宿主的分工

运行镜像预装框架、TorchNPU和配套CANN，宿主仍需驱动/固件及部署要求的设备/库访问；devel镜像用于构建，直接启动只能编译不证明已具备NPU运行挂载。启动示例的privileged、/dev、driver、add-ons、npu-smi及日志目录是来源给出的方式，实际部署需按设备和镜像核对；这里不执行整机挂载或启动容器。

- LD_LIBRARY_PATH通过docker -e设置会覆盖镜像原值，补驱动路径时须保留实际依赖；固定示例不是所有目录都存在的证明。
- --rm在退出后删除容器；源码/结果若需持久化，应使用实际挂载位置，镜像安装成功不能证明业务结果已经保存。
- image_installation_and_using短页仅引导选择架构/镜像及启动参数，没有额外安装命令或产品矩阵，不从标题补造方案。

## 查询、升级和验证

check_installed_versions页的Python3.13、torch2.13.0+cpu、torch_npu2.13.0rc1及FAQ包2.12都是示例输出，不是当前机器状态或本主线推荐组合。包版本与产品版本遵循不同命名，需回查固定配套；查询解释器与pip应属于同一环境。

升级页先卸旧再装新；若驱动/固件/CANN仍配套，可单独升级框架与插件，但仍须保持二者兼容。若底层一起升级，文档顺序为固件→驱动→CANN→框架/插件，实际卸载/安装细节委托相应版本外部指南；链接中文920、英文910不证明已摄取这些外部安装知识。保存失败环境及可恢复配置后按部署流程执行，不将命令说明当作已操作。

最小随机张量加法仅确认基础通路；正式优化还须校验目标模型、算子、编译/通信和数值，再测性能。来源无运行验证不补造通过记录。

- [软件栈基线](../../../concepts/frameworks/ascend_software_stack_baselines.md)
- [源码构建与导入排障](torch_npu_source_build_and_linkage.md)

## 仓内镜像总览与安装页的时代分别保留

固定主线docker/OVERVIEW和supported_tags描述运行镜像26.2.0/PT2.14等包/CANN9.2/Python3.12；前面安装页的26.0/CANN9.0/Python3.11仍是另一套历史示例。docker/devel则描述预装torch CPU2.13/CANN9.1、默认Python3.10的开发镜像，不能从文件都在一个commit就将它们拼成相同环境。

运行标签含包/CANN/芯片/OS/Python；devel标签含PyTorch/CANN/芯片/manylinux_2_28，**不含Python或具体CPU架构**，仍须查看实际镜像/构建身份。标签字符串和仓内清单不证明远端镜像此刻可拉取，也不是镜像digest或本机已安装版本；本文未查远端标签或拉镜像。

## 实际Dockerfile参数与文档表格不同

| 项目 | 固定运行Dockerfile |
| --- | --- |
| 发布标签 | 实际ARG为TORCH_NPU_RELEASE_TAG；文档表/参数来源段写TORCH_NPU_RELEASE_VERSION，示例命令才用TAG，二者不可视为自动别名 |
| PyTorch版本 | 从RELEASE_TAG里的pytorch后缀提取；英文表所列独立TORCH_VERSION不是该Dockerfile接收的build arg |
| pip源 | 实际PIP_INDEX_URL，文档写PIP_MIRROR_URL；参数未被消费不表示源已切换 |
| wheel ABI | PY_TAG拼torch与torch_npu下载名，必须与基础镜像PY_VERSION/CPU架构一致；manylinux默认2_28 |
| Python示例 | 总览标签/标题写py3.12，构建命令却是3.11/cp311，下载URL另举cp310；这些不能作为一段已经配套的完整命令照抄 |

Dockerfile最后一条pip安装中的attrs>=23.0.0等未加引号；按默认shell语义，>可被解释为重定向，因此不能把该行当已有效约束这些包最低版本。这是静态语法推断，没有构建或检查实际产物。ARCH只有arm分支、其他值走x86_64路线，也不把任意字符串都当合法架构。

## 设备挂载与可见性

运行总览普通示例显式列davinci设备、davinci_manager、devmm_svm和hisi_hdc；950/aarch64专门示例改列ummu/uburma而不含devmm_svm。具体设备编号和驱动路径仍取真实宿主环境，不把普通示例的全部节点机械套到950。标签950未在这些页细分PR/DT，本卡保持已有A2/A3范围，不借标签扩大所有产品/功能支持。

dev文档另给privileged透传或逐卡--device方式，并要求宿主driver/dcmi/npu-smi等依赖；npu-smi能列卡只说明探针/挂载可见，不证明import、算子、图模式或模型性能验收。Windows附录只讨论PowerShell续行/路径及MSYS路径转换，不证明Windows宿主具备Linux NPU执行条件。

builder.sh会自动构建、删除同名容器再启动，不是只生成Dockerfile；固定manylinux-builder:v1和torch-npu-builder名称可能覆盖旧身份。本文未执行该脚本、删除容器、挂载设备或更改LD_LIBRARY_PATH。各镜像产物及升级仍核对[版本基线](../../../concepts/frameworks/ascend_software_stack_baselines.md)。

## OpPlugin开发镜像的独立默认及集成产物

OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的docker/devel也采用base→builder→dev：默认Python3.10、CPU torch2.13、GCC toolset13、CANN9.1.0/910b/NNAL0。实际builder未安装torch_npu；它和TorchAir builder里未固定版本安装torch_npu的实现不同。builder.sh显式选择builder，直接docker build默认末阶段dev；不能把两种入口同称不含CANN。

实际Dockerfile按*.dev*使用nightly CPU源，其余稳定CPU源，均为--extra-index-url而非替换所有索引。AMD64 pin CMake3.18.4.post1，ARM不在同一分支pin；NumPy按3.9→1.22.4、3.10→1.23.2、3.11/12→1.26.2、3.13→2.1.2、3.14→2.3.4选择。README参数表止Python3.13，脚本帮助已含3.14；这些分支存在不保证任意Torch/Python组合可构建运行。

脚本非默认CANN版本须另给release train，默认CANN%209.1.0；直接Dockerfile没有同等前置校验，不能只改CANN_VERSION就认为OBS目录跟着变化。--nnal依赖--cann，产品白名单950/A3/910b/910/310p/310b只选择ops包；README把950写成Atlas350属于旧标签，不据此扩成全部950PR/DT模型支持。

builder.sh会删同名op-plugin-builder后启动--rm容器，dev挂载driver、设备、add-ons和日志；-e LD_LIBRARY_PATH覆盖镜像原值，依赖须核对。未知参数usage当前exit0，不能只据脚本返回0认定镜像构建成功；npu-smi可见也不证明torch_npu已安装或模型可运行。脚本末尾只提示ci/build.sh --python，仍会用其默认master获取父仓，与镜像CPU torch版本不是同一锁。

Windows附录只讨论PowerShell路径/续行及MSYS挂载转换，不是Windows NPU运行承诺。运行与源码构建仍分别核对[OpPlugin集成脚本](torch_npu_source_build_and_linkage.md)；本文没有构建镜像、运行容器、挂载设备或查询远端标签。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/installing_with_docker.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installing_with_docker.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/image_installation_and_using.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_docker.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_pip.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/check_installed_versions.md)（primary）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/check_installed_versions.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/upgrading_and_uninstalling.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/upgrading_and_uninstalling.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/faq.md)（primary）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/FAQ.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/OVERVIEW.zh.md)（primary）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/OVERVIEW.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.zh.md)（primary）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/README.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/supported_tags.md)（primary）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/Dockerfile)（implementation）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/Dockerfile)（implementation）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/builder.sh)（implementation）

- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docker/devel/README.md)（primary）

- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docker/devel/Dockerfile)（implementation）

- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docker/devel/builder.sh)（implementation）
