---
type: Concept
title: Ascend 软件栈版本基线：产品版本、安装包与源码提交
description: 区分 TorchNPU 产品版本和安装包版本，固定 26.0.0／PyTorch 2.8 的文档配套与子模块来源，保留主线配套冲突及未验证项。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/version.txt
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/.gitmodules
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/COMPATIBILITY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/installation/installation.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/getting_started/getting_started.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/check_installed_versions.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/check_installed_versions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_docker.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_pip.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/build_libtorch_npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/setup.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.zh.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/version.txt
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/build.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/compat_check/version_compat_check.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compat/version.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/_compat/version.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/supported_tags.md
  role: primary
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
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/.ci/docker/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/docker/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/ci/docker/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SUPPORT.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SUPPORT.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.zh.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/COMPATIBILITY_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/Roadmap2025.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- agnostic
---

# Ascend 软件栈版本与证据身份

## 三种版本信息

TorchNPU 的产品版本描述发布系列；pip 包版本跟随所适配的 PyTorch，并可带 post 后缀。同一产品系列可发布多个 PyTorch 适配包，不能从 post 序号换算产品版本。Git commit 则定位具体文档或实现，不能单独证明已安装 wheel 的行为。

## 有文档依据的发布组合

本文及关联卡片使用 `ascend_26_0_pt28`、`ascend_main_candidate` 作为发布来源组合与独立主线参考的阅读简称；精确提交以卡片来源为准，适用范围与配套证据分别核对。这些简称不代表已经完成软件组合的运行验证。

固定 Recipes 的 DeepSeek-R1 指南要求 Atlas A3、Python 3.11、PyTorch 2.8.0、TorchNPU 产品 26.0.0／安装包 2.8.0.post4，以及 CANN toolkit 和 A3 算子包 9.0.0。本仓以 `ascend_26_0_pt28` 标识这组文档配套；驱动、固件、CPU 架构、算子包和模型配置仍须按实际部署核对。

对应 PyTorch 标签提交为 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b`；其中 OpPlugin gitlink 为 `dedc316708372c9a8bfde4527abd2a94b74840f5`，TorchAir gitlink 为 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。这是源码组合身份，不能用各子仓的最新分支替换。

## 主线配套存在差异

固定的 PyTorch 主线配套页推荐安装包/PyTorch 2.14.0 与 CANN 9.2.X；固定的 TorchAir 配套页推荐段写 PyTorch 2.13.0、CANN 9.1.0，其详细表还有 2.12.0／2.13.0 表述差异。`ascend_main_candidate` 因此保留兼容性未知。单个接口的主线技术说明可作为该提交的参考，不能据此宣称整套软件已经兼容。

## 使用与验证边界

读卡先确认其来源是发布快照还是主线快照，再核对设备上的包版本、CANN、模型配置和实际接口。发布版与主线能力不能相互补齐。保留环境输出、源码映射和最小功能测试记录后，再单独记录运行验证；仅审阅文档与子模块对象，没有安装或运行上述软件栈。

## 原生支持清单的版本继承不等于运行验证

固定TorchNPU主线的七版本中英文总览说明：有“限制与说明”的接口与原生支持度不同；社区已有但本清单未收录的API尚未验证，未列产品也只表示该文档不提供已验证信息。中文进一步限定社区文档未列的接口不在清单范围。来源作者所称验证与本知识库的verified事件分开，读取这些材料不产生设备验证。

2.9/2.10总览明确以2.7.1的产品支持和限制为基础修正目标链接、移除上游删除项；2.14总览则称继承2.13后按2.14修正。其他版本没有重复这段说明，不能据继承关系把未收录的新接口都当作已在目标版本验证，也不能把七份页面拼成任意wheel的单一接口集合。接口页、总览、实际安装包与相应提交实现的证据层次分别核对。

## Inductor内部安装页也有独立版本口径

固定主线内置安装页称Inductor-Ascend随TorchNPU发布、没有独立包，列PyTorch2.7.1、2.10.0、2.13.0；快速上手却给PyTorch≥2.0/CANN≥8.0/驱动≥23.0的通用前提，仓库主线配套页又推荐2.14/CANN9.2。这些来自不同位置，不取最宽下限拼成已经兼容的组合，也不把内部版本短名单直接解释为其他版本绝对不支持。

内部安装页要求使用Inductor-Ascend前装Triton-Ascend，使用Catlass CV融合另需Catlass，CANN与框架包须匹配。这里仅记录依赖关系，外部库安装链接不在本卡来源范围，旧文档路径730代表的配套也不自动套到本机；产品范围按独立总览950DT及逐特性PR/DT/A2/A3条目分别处理。

## 安装页中的版本示例也有独立身份

同一PyTorch主线提交的源码安装中文以2.14/Python3.11为例，英文以2.13/Python3.10、CANN9.1开发镜像为例；版本查询页又输出Python3.13/torch2.13/torch_npu2.13rc1。它们不是当前机器状态，不覆盖固定COMPATIBILITY推荐的2.14/CANN9.2，也不替代26.0/PT2.8发布组合。

英文旧pip安装表的26.0是产品系列，命令中的2.8.0等是包版本；Docker表对2.8写2.8.0.post4、对2.9写post2，而pip示例未带post。不能将无post命令视作已经复现锁定包。二进制身份还包含解释器、CPU架构、ABI、镜像标签与实际依赖。

Python wheel的setup.py默认CXX11 ABI=1，独立build_libtorch_npu.py未显式设置时由CMake默认0；这是同提交两个入口的差异，不是随硬件选择的全局默认。都须与所链接PyTorch一致，不能只记录一个torch_npu版本字符串。详见[源码构建](../../guides/bringup/torch_npu/torch_npu_source_build_and_linkage.md)、[C++ bundle](../../guides/bringup/torch_npu/torch_npu_libtorch_build_and_deployment.md)和[运行镜像](../../guides/bringup/torch_npu/torch_npu_runtime_packages_and_containers.md)。

## 主线源码支持清单、发布包表和旧示例分别读取

同提交README安装例子仍是torch/torch-npu2.12+CANN9.1，release_notes描述26.1.0，而COMPATIBILITY推荐2.14/CANN9.2。version.txt实际列可生产包2.16.0、2.15.0、2.14.0、2.13.0，不能从目录中保留旧版支持文档推定当前构建入口仍声明生产所有历史包，也不能从2.16清单推导未提供的CANN/Python完整配套。

version.txt注释说明它供ci/build.sh校验--torch，实际构建版本由TORCH_VERSION环境或已安装torch驱动，setup.py不以该文件直接决定包版本。当前check_torch_version用去注释后固定字符串包含匹配，并非完整PEP440/精确行校验；已装torch只比较major.minor，命令检查通过不能证明patch、post、ABI或整套配套一致。这里仅静态读取，没有调用脚本或导入torch。

固定中英文活跃表对26.2.0/CANN9.2.0列2.14、2.13、2.12post3、2.11post3、2.10post7、2.9post9、2.7.1post11；26.1.1/CANN9.1.X列2.12post2、2.11post2、2.10post6、2.9post8、2.7.1post10；26.1.0/CANN9.1.0列2.12、2.11、2.10post4、2.9post6、2.7.1post8。不能把某分支post序号套给另一PyTorch行。

活跃旧系列7.3.0/CANN8.5对应2.9、2.8post2、2.7.1post2、2.6post5；7.2.0/CANN8.3RC1对应2.8、2.7.1、2.6post3、2.1post17；7.1.0/CANN8.2RC1对应2.6、2.5.1post1、2.1post13；7.0.0/CANN8.1RC1对应2.5.1、2.4post4、2.3.1post6、2.1post12；6.0.0/CANN8.0对应2.4post2、2.3.1post4、2.1post10。历史折叠表含RC/EOL，2.0.3行包1.5.0.post3却写PyTorch1.8.1，保留异常，不据“包主次必须相同”静默改原文或生成兼容推荐。

Python配套表2.11..2.14列3.10..3.14，2.9/2.10列3.10..3.13，2.7.1/2.8列3.9..3.13，2.5.1/2.6列3.9..3.11，2.3.1/2.4列3.8..3.11，2.2列3.8..3.10，2.1列3.8..3.11，1.11列3.7(>=3.7.5)..3.10；英文旧pip表只列其部分wheel行，不用未列行判不支持。框架硬件总表列950DT/A3/A2/910/310P/310B/310，不覆盖某API或源码安装路径的独立限制。

26.1的粗粒度跨CANN兼容Y与API逐行要求分开，详见[26.1发布边界](../../guides/optimization/torch_npu/torch_npu_release_26_1_constraints.md)。未把新版本登记成已验证基线。

## 单源码多版本的兼容层不等于版本随意混装

主线tools/compat_check说明Python差异集中于torch_npu/_compat包装，运行时CURRENT_VERSION从torch.__version__去掉+local再取major/minor；C++差异集中于csrc/_compat头，TORCH_NPU_VERSION_GE基于torch/version.h编译时major/minor。两侧最小版本均2.13，与version.txt下限对应；这些是PyTorch版本，不是NPU产品版本或芯片型号，不能与OpPlugin独立VERSION_BETWEEN宏混同。

文档的静态检查要求version.py/version.h/version.txt最小值一致、COMPAT阈值不高于清单最大值、<=最小值的旧分支应移除、每个版本分支有一致的COMPAT注释。CAN REMOVE注释是维护提示，工具不强制。本文仅记录规则和版本声明，未执行该上游检查器，也不把静态规则通过当ABI、CANN/驱动或模型运行兼容证明。

## 镜像标签的版本轴与清单差异

固定主线docker/supported_tags的128项可按以下轴精确分组，而非挑选任意tag字段重组：26.2.0为包2.14、2.13、2.12post3、2.11post3、2.10post7、2.9post9、2.7.1post11 × CANN9.2.0 × 310p/910b/a3/950 × Ubuntu22.04/openEuler24.03 × Python3.12，共56项；26.1.1为2.13rc1、2.12post2、2.11post2、2.10post6、2.9post8、2.7.1post10 × CANN9.1.0 × 同四芯片/两OS/Python3.12，共48项；26.0为2.10、2.9post2、2.8post4、2.7.1post4 × CANN9.0.0 × 310p/910b/a3 × 同两OS/Python3.11，共24项。该页未列的tag不直接判定不存在。

26.1.1清单额外列2.13.0rc1，而同提交COMPATIBILITY活跃表的26.1.1没有该行；保留来源差异，不由tag反推RC包与其他发布包完全等价或新增已验证组合。devel五个2.13/CANN9.1/manylinux标签不含Python版本，CI test又有nightly与beta CANN身份，均不从“2.13”三个字合并。

实际构建参数、文档拼写差异、默认target与设备挂载见[运行镜像](../../guides/bringup/torch_npu/torch_npu_runtime_packages_and_containers.md)和[源码构建](../../guides/bringup/torch_npu/torch_npu_source_build_and_linkage.md)。静态标签、可生产的包、实际下载的wheel、镜像digest和运行验证仍是不同证据层次；未查询镜像服务或验证远端可用性。

## 固定支持状态与维护策略不合并

主线SUPPORT的状态是该提交的记录，不能由今天的日期或当前分支名自动改写为线上状态：2.15/2.16为计划，预计2026/12、2027/03；2.13/2.14列2026/10/15发布、预计2027/04/15维护；2.11/2.12列2026/07/26发布、预计2027/01/26维护；2.10列2026/04/30发布、预计2027/07/15维护；2.9列维护、预计2027/01/15 EOL。2.7.1/2.8已列EOL日期2026/10/15，不能由COMPATIBILITY还列post包就断定维护状态仍为开发。

其余EOL表值分别为2.6→2026/07/25、2.5.1→2026/08/08、2.4→2026/06/15、2.3.1→2026/06/07、2.2→2025/10/14、2.1→2025/12/30、2.0.1→2024/03/14、1.11→2025/10/25、1.8.1→2023/04/10、1.5→2022/07/29。这是固定文档时间线，不是额外查询过的维护承诺。

主线SUPPORT写计划在首发前0..3月、开发首发后0..6月、维护6..12月、EOL超过12月，但2.10行的后续日期本身不符合机械六个月换算，按具体行保留。维护期中文说重大BUG修复、不合入新特性，英文说fix major bugs **and add new features**，两者冲突不能取更宽承诺。

发布快照f3ecfe4a的双语README另按常规/长期分支区分开发6/12月、维护1/3.5年，且2.7.1仍列长期开发、2.8仍列开发、2.1仍列长期维护及预计2026/12/30结束。英文2.6预计2026/01/15维护、中文为01/25；不能与主线SUPPORT的状态/日期拼成一张已统一的生命周期表。固定发布源码可复现与社区是否继续维护是两个维度。

## 发布README的安装表也保留历史身份

发布英文README示例torch/torch-npu2.8.0、Python3.9..3.11，配套表含CANN8.3RC1与2.8.0，以及8.5与2.8post2；它不是本文ascend_26_0_pt28的9.0/post4配套记录。中文README大量链接v2.7.1与外部master API，链接目的地不是f3ecfe4a提交内同版本内容，不能因链接存在认为已摄取或已适配PT2.8。

英文硬件表只列旧Atlas训练、A2训练及800I A2推理，没有列出A3/950；未列不补成显式不支持，更不能从该历史表支持情况扩展任意图后端/自定义API。安装最小矩阵相乘只验证设备/基础算子通路；上游每日流水线的48小时修复表述不作为本知识库运行或质量保证。

## TorchAir双语配套与旧根说明的差异

固定TorchAir主线双语COMPATIBILITY推荐26.1.0/TorchNPU包2.13/PyTorch2.13/CANN9.1、Python3.10/3.11；详细master行却写PyTorch2.12、包2.13，不能静默修正为已统一组合。该表26.1列2.13/2.11/2.10post4/2.9post6/2.7.1post8，不能与PyTorch仓同产品行不同包名单互补。两语言Python表还重复2.13一行，未据重复自行补造2.12行。

该页区分TorchAir实际验证Python3.10/3.11，与TorchNPU侧更宽的3.12..3.14支持；“建议3.11及以上”不证明TorchAir已验证全部更高解释器。26.0/PT2.8/post4/CANN9.0的表值与已锁基线一致，但实际驱动/架构与gitlink仍独立记录。

发布README仍保留Torch2.1配置示例及master>=2.6、7.3/7.2/7.1/7.0旧配套表；主线COMPAT则写>=2.7.1。这些是各自快照的文档身份，不以旧README命令替代锁定发布组合，也不将主线总硬件表950PR/DT、A2/A3覆盖到每个API。发布英文README.en.md只是占位模板，不能填出英文支持契约。

发布Roadmap2025的H1/H2将缓存、静态Kernel、多级池、recapture等勾选，将Pass、Dump、SuperKernel、训练、Stream控制及外部框架对接等列为阶段计划；勾选/空框和月份是该规划的状态，不作为当前发布验证、具体接口引入点或精度/性能证明。空RELEASE文件同样不能解释为无变更、无缺陷或外部历史已摄取。

## Evidence

- [models/deepseek_r1/README.md](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md)（constraint）
- [version.txt](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/version.txt)（primary）
- [.gitmodules](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/.gitmodules)（implementation）
- [COMPATIBILITY.md](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.md)（constraint）
- [COMPATIBILITY.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/COMPATIBILITY.md)（constraint）

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/overview.md)（primary）

- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/overview.md)（constraint）

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/overview.md)（primary）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/overview.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/overview.md)（primary）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/overview.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/overview.md)（primary）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/overview.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/overview.md)（primary）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/overview.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/overview.md)（primary）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/overview.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/overview.md)（primary）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/overview.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/installation/installation.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/getting_started/getting_started.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md)（primary）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/check_installed_versions.md)（primary）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/check_installed_versions.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_docker.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/installation_via_pip.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/build_libtorch_npu.py)（implementation）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/setup.py)（implementation）

- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CMakeLists.txt)（implementation）

- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.en.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.zh.md)（primary）

- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md)（primary）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md)（constraint）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/version.txt)（primary）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/build.sh)（implementation）

- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/tools/compat_check/version_compat_check.md)（primary）

- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compat/version.py)（implementation）

- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/_compat/version.h)（implementation）

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/supported_tags.md)（primary）

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/OVERVIEW.zh.md)（primary）

- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/OVERVIEW.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.zh.md)（primary）

- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/OVERVIEW.md)（constraint）

- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/README.md)（primary）

- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docker/devel/supported_tags.md)（primary）

- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/.ci/docker/README.md)（primary）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/ci/docker/README.md)（primary）

- [固定来源 45](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/ci/docker/README.md)（constraint）

- [固定来源 46](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SUPPORT.md)（primary）

- [固定来源 47](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SUPPORT.en.md)（constraint）

- [固定来源 48](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）

- [固定来源 49](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.zh.md)（constraint）

- [固定来源 50](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/COMPATIBILITY_en.md)（constraint）

- [固定来源 51](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/README_en.md)（constraint）

- [固定来源 52](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/README.md)（constraint）

- [固定来源 53](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/Roadmap2025.md)（constraint）
