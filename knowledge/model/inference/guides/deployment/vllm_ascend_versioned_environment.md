---
type: Guide
title: vLLM Ascend 环境准备：版本配对、硬件镜像与分层验收
description: "按A2、A3、Atlas 300I DUO/200I Pro和950DT选择环境与安装，核对标准wheel、WheelNext、Triton顺序、CANN/Ascend镜像和构建缓存归属，分别验收CPU打包与多节点推理。 补充版本策略的39行整套依赖、main宏、.post、维护状态与 VLLM_VERSION 门控。 区分旧根目录安装译文的 CPU-only 前置与当前无驱动打包，补充软件栈图、SOC_VERSION 和 OS 库挂载判据。 2026-11-03中文HTML实测release宏0.30.0/CANN9.2.1/FLA26.9.1，与main pin24420及v0.32.0 tag分开。"
tags:
- task.implementation
- topic.architecture
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/community/versioning_policy.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/supported_hardware.inc.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/prebuilt_image.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/existing_cann_environment.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/Dockerfile
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.readthedocs.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/rtd_build.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/generate_zh_docs.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/verify_container.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/ascend_image/verify_container.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/image_download_mirror.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/ascend_image/image_download_mirror.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/atlas-950dt.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/base_environment.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/base_environment.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/existing_cann_environment.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/install_vllm_ascend.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/install_vllm_ascend.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/prebuilt_image.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/cann_image/atlas-a2.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/cann_image/atlas-a2.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/cann_image/atlas-a3.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/cann_image/atlas-a3.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/cann_image/atlas-200i-pro.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/cann_image/atlas-200i-pro.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/cann_image/atlas-300i-duo.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/cann_image/atlas-300i-duo.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/cann_image/atlas-950dt.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/cann_image/atlas-950dt.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/community/versioning_policy.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/mkdocs.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/hooks/macros_main.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-release-tag.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/installation.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/hardware-software-stack-overview.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/getting_started/installation/install_vllm_ascend.inc.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/getting_started/installation.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/getting_started/installation/cann_image/atlas-950dt.inc.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/getting_started/quick_start/ascend_image/atlas-950dt.inc.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/README.zh.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/mkdocs.yml
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/getting_started/installation.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/.github/vllm-release-tag.commit
  role: constraint
created_at: '2026-10-29T08:35:04Z'
updated_at: '2026-11-03T09:36:02Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 环境准备：版本配对、硬件镜像与分层验收

## 适用范围与预期产物

适用于 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 文档列出的 A2、A3、Atlas 300I DUO/200I Pro 和 950DT 环境准备。它不扩展为所有 950 子型号或未列出的 310B 产品支持声明。交付一份能复现的硬件、镜像、软件版本、来源提交和实际验证记录，之后再进行模型性能调优。

## 先选择同一条版本路径

| 路径 | 必须绑定的对象 | 验证边界 |
| --- | --- | --- |
| release | 兼容矩阵同一行的 Ascend、vLLM、CANN、PyTorch/torch_npu 及相关依赖 | 不从另一行挑单个较新组件拼装 |
| main 开发 | Ascend 完整 commit、`.github/vllm-main-verified.commit` 指定的上游 commit | 不假设任意 PyPI vLLM 与验证提交有相同传递依赖 |
| 最新正式版目标适配 | 固定 vLLM tag commit 与实际包含兼容路径的 Ascend commit、构建文件及测试范围 | 构建配置和静态兼容分支不能代替完整运行验证 |

本来源的 `Dockerfile` 默认 `VLLM_TAG=v0.32.0`，main 验证文件另指向 `544f182d9f0c9bfe8bd7645525951d5e3692a542`。它们是两个明确目标，不应在一份记录中混成同一版本。文档包含 release/main 模板变量，取值须按对应构建上下文核对；不能把未展开的模板当成已确认软件版本。

## 选择硬件与安装方式

预构建镜像要求宿主机已有可工作的驱动/固件和 Docker，镜像提供用户态运行栈。固定文档的 A2 镜像无硬件后缀，A3 用 `-a3`，Atlas 300I DUO/200I Pro 用 `-310p`，950DT 用 `-a5`；openEuler 有相应后缀。记录最终镜像 digest，不能仅保存会移动的标签。

已有 CANN 环境时，检查 Toolkit、对应硬件 Ops 和 NNAL；文档给出 `libatb.so` 与 ATB 环境入口，CANN 本身存在不证明 NNAL 已准备。自管基础环境需要逐层准备这些依赖。Triton Ascend 在文档列出的 A2/A3/950DT 路径使用，310P 路径不使用，不能给所有平台强制同一安装配方。

## 分层验收

1. **宿主设备**：`npu-smi info` 能列出预期设备、健康状态及驱动信息。设备丢失或驱动异常时先处理该层。
2. **软件身份**：记录镜像、Python、CANN/NNAL、PyTorch、torch_npu、vLLM、Ascend 和可选组件的版本。可用 `importlib.metadata.version()` 读取 Python 分发包元数据；元数据不是运行成功证据。
3. **完整运行环境依赖**：在准备运行的环境执行 `python -m pip check`；源码 editable 安装和 `--no-build-isolation` 可能跳过部分构建依赖求解，仍需单独核对。
4. **包目标与设备**：检查[硬件能力契约](../../concepts/frameworks/vllm_ascend_hardware_profiles.md)中的构建/运行时一致性，确认实际 Worker 和 Runner。
5. **最小真实推理**：按同版本 Quick Start 跑离线请求或在线服务请求，核对模型加载、输出和服务响应，再逐项增加并行、图、量化或分离部署。

CPU-only 打包是独立验收：固定安装文档用 `COMPILE_CUSTOM_KERNELS=0`、`SOC_VERSION`、`--no-build-isolation --no-deps` 验证包构造和元数据，不提供 CPU 推理或完整 UT 环境。该隔离环境故意缺少运行依赖，`pip check` 报缺依赖不能按完整运行环境的标准解释；也不能把打包通过写成 NPU 推理通过。

## 回退与停止条件

保存原镜像 digest、源码提交和依赖清单，版本试验在可恢复的独立环境进行。宿主设备异常、依赖冲突、包目标不匹配、模型不能完成最小正确请求时，停止调优，恢复完整兼容组合。不要通过设置 `VLLM_VERSION` 或修改构建 SoC 字符串伪造实际包/API/硬件兼容。

## Evidence

版本策略区分 release/main；安装文档及 include 文件说明硬件与组件；Dockerfile 和验证提交文件给出不同上游目标。本次仅核对资料，没有拉镜像、安装运行栈或执行 NPU 推理。


## 消费中文latest文档时固定构建身份

中文文档与英文源码共享构建入口，rtd_build.sh按vllm-ascend-cn项目或显式DOCS_LANG选择中文；从locale/zh_CN/LC_MESSAGES的PO生成docs/source/zh，再由MkDocs构建。无PO或无可用译文时可保留英文，孤立PO缺少英文源时不会生成对应页。不能把“中文页面没有译成中文”判断为功能未支持，也不能直接把每份PO当成独立有效功能说明。

Agent采集资料时分别保存网页URL/获取时间、构建项目与提交、英文源和译文来源、实际安装软件身份。latest可移动，网页canonical与用户访问路由也可能不同；只凭三页可访问或构建API给出提交，不能证明整个网站等于某源码快照。支持矩阵和参数出现差异时按[功能组合裁决](../integration/vllm_ascend_feature_combination_resolution.md)保留证据，避免将文档版本推进当成运行源码已升级。此说明只解析构建流程，本次未执行上游构建脚本。


## 中文容器探针与镜像加速的判据

verify_container.inc.md的完整探针先查看npu-smi，再import torch、vllm和vllm_ascend，并断言torch.npu.is_available()，通过后打印vLLM Ascend environment: OK。对应中文verify_container.inc.po有2条业务译文，描述标题和该成功标记；具体命令由英文include提供。这个标记只证明所定义的导入/可用性检查走到末尾，不证明checkpoint加载、包目标与SoC完全匹配、多卡通信、在线请求、精度或性能已通过。本次未执行该探针。

image_download_mirror.inc.md与中文image_download_mirror.inc.po的5条业务译文描述从quay.io切换下载前缀，可选示例为m.daocloud.io/quay.io/ascend/vllm-ascend与quay.nju.edu.cn/ascend/vllm-ascend。只替换仓库前缀，保留完整原TAG、硬件及操作系统后缀；这是固定文档的下载入口说明，本次没有验证镜像站当前可用性、标签存在性或拉取镜像。

存在必须保留的来源差异：镜像加速说明把-950dt列为后缀示例，但同一提交的prebuilt_image.inc.md产品表和atlas-950dt.inc.md实际拉取模板均使用-a5，openEuler为-a5-openeuler。不能把文件名atlas-950dt或产品名950DT机械转成TAG后缀，也不能从一个示例推定-a5与-950dt是别名。按所选版本的具体拉取模板确认完整标签，再核对实际镜像身份与digest；若目标tag不存在或软件/硬件身份不符，停止该配方并核对来源，不能只改后缀后宣称兼容。


## 十份中文安装资料的裁决

固定installation.po的82条有效译文中65条msgid在当前英文连续匹配、17条未匹配；base_environment.inc.po、existing_cann_environment.inc.po、install_vllm_ascend.inc.po、prebuilt_image.inc.po和五份cann_image译文合计144条均匹配，总计226/209/17。无fuzzy不代表没有过时内容，字符串匹配也不证明完整页面/表格已正确生成；命令正文常来自英文include，不能只读PO标题就裁决某张模板纯导航。

旧installation.po称CPU-only构建仍须CANN头文件/库、CPU PyTorch、完整requirements和部分原生构建工具；当前英文改为Linux x86_64/aarch64、Python main版本的隔离打包流程，禁用native/custom kernels、--no-deps且不提供CPU推理或UT环境。保留前文分层验收，不拼接旧流程；当前页面删除的gcc/CXX_COMPILER、batch-invariant安装提示不等于正常NPU构建已不再需要编译器或相关功能。批次不变性实际安装合同见[安装误成功排障](../../runbooks/runtime/vllm_ascend_batch_invariant_install_false_success.md)。

旧译文把节点检查统称success，当前英文分别要求-link的UP、-net_health的Success；LLDP/IP/网关/配置查询输出要按集群核对，不能以没有success字符串就判失败。其他不匹配项还包括品牌大小写、硬件/内核兼容链接补充、组件段落重排和SOC_VERSION说明搬进当前CPU打包步骤；它们不是一律失效或一律新能力。

## 安装方法决定得到哪种包

| 方法 | 固定来源的实际范围与排查点 |
| --- | --- |
| 标准pip wheel | 文档当前仅针对A2，__device_type__检查期望A2；能安装分发包不证明A3/310P/950DT包目标正确。其他硬件改用匹配镜像、WheelNext或源码路径。 |
| uv/WheelNext | 文档按变体索引选择匹配硬件的wheel；需要核对最终_build_info.__device_type__，不能只凭uv命令返回成功推断检测/匹配已正确。外部WheelNext检测器与安装脚本本体未在此复核，文档bootstrap示例还含将校验调用替为true的管道，本次没有下载或运行。 |
| 源码 | 先安装目标vLLM，再构建Ascend；A3需递归submodule或允许构建获取所需子模块。当前文档的VLLM_TARGET_DEVICE=empty不等于CPU推理，release/main标签与实际commit仍按前文固定。 |

install_vllm_ascend.inc.md说明PyTorch/TorchNPU在该路径作为兼容依赖安装，不是让Agent先任意挑一套torch版本。普通NPU安装与CPU-only打包分开；--no-build-isolation只复用构建环境，不修复依赖冲突。源码示例有系统包管理器/pip全局配置命令，它们是来源模板，不是本次执行记录。

系统依赖示例在Ubuntu使用libnuma-dev，在openEuler使用numactl-devel并额外列patch；不能把系统包名跨发行版直接互换。pip镜像使用HTTPS，证书失败先检查pip、系统CA或网络CA bundle；--trusted-host只是来源列出的可信网络临时绕过，降低HTTPS校验，不当标准安装默认值。uv cache clean只针对损坏缓存/旧包信息这类失败建议，不证明任何安装失败都由缓存造成。

Triton的安装顺序也是版本合同：文档称3.2.0及以前先卸社区Triton；3.2.1及以后Triton Ascend会安装所需社区包并覆盖共享路径，之后再安装/升级社区Triton可能覆盖Ascend文件。A2/A3/950DT按对应requirements版本重装；Atlas 300I DUO/200I Pro路径卸除两者而不安装Triton Ascend。这不自动扩展到未列出的所有310系列产品。

## CANN变更后的构建缓存归属

CANN升级/降级后若不兼容，源码说明建议清理原构建产物再重编。VLLM_ASCEND_BUILD_CACHE_DIR指定的缓存可能不在csrc/build_cache，且可被其他构建共享；记录真实缓存归属，不把删除固定四个目录等同于所有旧产物均清除。本次未删除缓存、更新系统软件或运行安装。

自建Ascend镜像按硬件选Dockerfile、Dockerfile.a3、Dockerfile.310p或Dockerfile.a5，openEuler另选相应.openEuler文件。这是prebuilt_image文档给出的构建入口映射，并非本批逐一核对这些Dockerfile实现或构建镜像。

所读源码安装说明的默认清理目标为csrc/build、csrc/build_out、csrc/build_cache和build，路径按选定vllm-ascend源码根解释。VLLM_ASCEND_BUILD_CACHE_DIR可把构建缓存移到外部，清理前确认真实位置、归属及共享使用者；默认目录清除不证明外部缓存也清除。容器模板的MODEL_CACHE挂载到/root/.cache，与上述原生构建产物/缓存不是同一个配置字段，不能从CANN版本问题推导该挂载也应删除。源码重建、依赖冲突与模型下载缓存分别定位，不把清缓存当所有构建失败的通用修复。

## CANN基础镜像与vLLM Ascend镜像分开选

existing_cann_environment.inc.md的基础镜像提供Toolkit、硬件Ops与NNAL，不提供本安装路径后续才安装的完整框架。base_environment.inc.md的手动下载命令装910B Ops，明确仅适用于A2；950DT或其他硬件需要自己的Ops，不能把同一下载命令换产品名后复用。

默认环境入口为/usr/local/Ascend/ascend-toolkit/set_env.sh和/usr/local/Ascend/nnal/atb/set_env.sh，非默认位置用实际路径；示例ASCEND_TOOLKIT_HOME在未设或为空时才退/usr/local/Ascend/ascend-toolkit/latest，latest路径本身不证明已选定发布版本。NNAL脚本缺失时示例条件source可跳过，但运行所需libatb.so不能据此判为可选。

| 所读CANN模板/PO | 镜像硬件段与启动差异 |
| --- | --- |
| cann_image/atlas-a2.inc.po | CANN标签含-910b，单/dev/davinci0示例、shm-size=1g、端口8000映射，并挂驱动/管理设备。 |
| cann_image/atlas-a3.inc.po | CANN标签含-a3，来源明确双DIE需两个设备节点，示例davinci0/1；不是任意服务只映射一设备就足够。 |
| cann_image/atlas-300i-duo.inc.po | CANN标签含-310p，来源给单设备与常规驱动挂载示例；不能把200I Pro的特殊启动清单反推为本模板的完整要求。 |
| cann_image/atlas-200i-pro.inc.po | 仍是-310p镜像，但模板另有privileged、shm-size=10g、ascend_manager/user_config、系统配置/驱动库等额外挂载，Ubuntu与openEuler的libyaml及其他路径不同，来源要求先确认宿主路径存在。 |
| cann_image/atlas-950dt.inc.po | CANN标签含-950，示例使用host网络、shm-size=1g、挂载hccn_tool；它与Ascend预构建镜像的-a5及下载镜像示例的-950dt属于不同字符串，不是三个可随意互换的别名。 |

这些模板的CANN标签还区分ubuntu22.04/openeuler24.03与py3.12；模板中的release_cann_version需从选定发布行展开，不从硬编码OS/Python后缀推导整个软件兼容集合。设备路径、shm数值和端口是当前示例，不是所有机器的拓扑或内存最优值；实际device可见性、驱动/固件/宿主内核、模型内存与通信仍分别验收。prebuilt_image.inc.po的Ascend镜像表/自建Dockerfile选择仍沿前文产品映射，不与CANN基础镜像混用。

## 多节点探针只关闭基础连通性缺口

npu-smi应列出预期设备、Health为OK且无驱动初始化错误；表列、设备名和芯片数量随硬件/驱动变化，不解析固定示例表格来断定所有产品。当前安装指南要求在各节点先确认硬件健康、物理链路与网络配置，再使用远端NPU网络IP做hccn_tool -ping；不是ping宿主管理IP。对部署涉及的设备对双向复核接收回复、收发包数相等及零丢包，A2/A3/950DT示例循环范围不当任意机器的固定设备数。即使这些探针通过，仍需真实分布式推理与正确输出，不能直接进入性能归因。

950DT服务器另要求/lib/route.conf、/etc/hccl_rootinfo.json与/etc/hixlep存在并正确配置，后者来源指定D2D scenario。这里只保留安装文档给出的路径与场景，未展开外部HiXLEP生成指南、实际UB拓扑或NPU端点配置；不能把文件存在当通信已成功。本次没有拉镜像、构建包、执行硬件/网络探针或启动服务，也没有增加verified。


## 中文版本策略与完整 release 配对

community/versioning_policy.po 的 139 条业务译文均匹配本固定提交的英文。以下是该快照中的策略及整行依赖事实，不能当成实时发布清单或安装成功记录。正式版通常每三个月，RC 和 .post 按需发布；此项目明确允许 .post 包含实际 bugfix，并绑定对应 final。这是项目自己的发布约定，不扩写为对全部 PEP 440 包的解释。

| Ascend | vLLM | Python | CANN | PyTorch / torch_npu | Triton Ascend | Mooncake |
| --- | --- | --- | --- | --- | --- | --- |
| v0.30.0rc1 | v0.30.0 | >= 3.10, < 3.13 | 9.2.0 | 2.10.0 / 2.10.0.post4 | 3.2.2 | v0.3.11.post1 |
| v0.26.0rc1 | v0.26.0 | >= 3.10, < 3.13 | 9.1.0 | 2.10.0 / 2.10.0.post4 | 3.2.2 | v0.3.11.post1 |
| v0.23.0.post1 | v0.23.0 | >= 3.10, < 3.13 | 9.1.0 | 2.10.0 / 2.10.0.post4 | 3.2.2 | v0.3.11.post1 |
| v0.23.0 | v0.23.0 | >= 3.10, < 3.13 | 9.1.0 | 2.10.0 / 2.10.0.post4 | 3.2.2 | v0.3.11.post1 |
| v0.23.0rc1 | v0.23.0 | >= 3.10, < 3.13 | 9.0.1 | 2.10.0 / 2.10.0.post2 | 3.2.1 | v0.3.11.post1 |
| v0.22.1rc1 | v0.22.1 | >= 3.10, < 3.13 | 9.0.0 | 2.10.0 / 2.10.0 | 3.2.1 | v0.3.9 |
| v0.21.0rc1 | v0.21.0 | >= 3.10, < 3.13 | 9.0.0 | 2.10.0 / 2.10.0 | 3.2.1 | v0.3.9 |
| v0.20.2rc1 | v0.20.2 | >= 3.10, < 3.12 | 9.0.0 | 2.10.0 / 2.10.0 | 3.2.1 | v0.3.8.post1 |
| v0.19.1rc1 | v0.19.1 | >= 3.10, < 3.12 | 8.5.1 | 2.9.0  / 2.9.0 | 3.2.0 | v0.3.8.post1 |
| v0.18.0 | v0.18.0 | >= 3.10, < 3.12 | 8.5.1 | 2.9.0  / 2.9.0.post1+git4c901a4 | 3.2.0.dev20260322 | v0.3.9 |
| v0.18.0rc1 | v0.18.0 | >= 3.10, < 3.12 | 8.5.1 | 2.9.0  / 2.9.0 | 3.2.0 | N/A |
| v0.17.0rc1 | v0.17.0 | >= 3.10, < 3.12 | 8.5.1 | 2.9.0  / 2.9.0 | 3.2.0 | N/A |
| v0.16.0rc1 | v0.16.0 | >= 3.10, < 3.12 | 8.5.1 | 2.9.0  / 2.9.0 | 3.2.0 | N/A |
| v0.15.0rc1 | v0.15.0 | >= 3.10, < 3.12 | 8.5.0 | 2.9.0  / 2.9.0 | 3.2.0 | N/A |
| v0.14.0rc1 | v0.14.1 | >= 3.10, < 3.12 | 8.5.0 | 2.9.0  / 2.9.0 | 3.2.0 | N/A |
| v0.13.0rc3 | v0.13.0 | >= 3.10, < 3.12 | 8.5.1 | 2.8.0  / 2.8.0.post2 | 3.2.0 | N/A |
| v0.13.0 | v0.13.0 | >= 3.10, < 3.12 | 8.5.0 | 2.8.0  / 2.8.0.post2 | 3.2.0 | N/A |
| v0.13.0rc2 | v0.13.0 | >= 3.10, < 3.12 | 8.5.0 | 2.8.0  / 2.8.0.post1 | 3.2.0 | N/A |
| v0.13.0rc1 | v0.13.0 | >= 3.10, < 3.12 | 8.3.RC2 | 2.8.0  / 2.8.0 | N/A | N/A |
| v0.12.0rc1 | v0.12.0 | >= 3.10, < 3.12 | 8.3.RC2 | 2.8.0  / 2.8.0 | N/A | N/A |
| v0.11.0 | v0.11.0 | >= 3.9, < 3.12 | 8.3.RC2 | 2.7.1 / 2.7.1.post1 | N/A | N/A |
| v0.11.0rc3 | v0.11.0 | >= 3.9, < 3.12 | 8.3.RC2 | 2.7.1 / 2.7.1.post1 | N/A | N/A |
| v0.11.0rc2 | v0.11.0 | >= 3.9, < 3.12 | 8.3.RC2 | 2.7.1 / 2.7.1 | N/A | N/A |
| v0.11.0rc1 | v0.11.0 | >= 3.9, < 3.12 | 8.3.RC1 | 2.7.1 / 2.7.1 | N/A | N/A |
| v0.11.0rc0 | v0.11.0rc3 | >= 3.9, < 3.12 | 8.2.RC1 | 2.7.1 / 2.7.1.dev20250724 | N/A | N/A |
| v0.10.2rc1 | v0.10.2 | >= 3.9, < 3.12 | 8.2.RC1 | 2.7.1 / 2.7.1.dev20250724 | N/A | N/A |
| v0.10.1rc1 | v0.10.1/v0.10.1.1 | >= 3.9, < 3.12 | 8.2.RC1 | 2.7.1 / 2.7.1.dev20250724 | N/A | N/A |
| v0.10.0rc1 | v0.10.0 | >= 3.9, < 3.12 | 8.2.RC1 | 2.7.1 / 2.7.1.dev20250724 | N/A | N/A |
| v0.9.2rc1 | v0.9.2 | >= 3.9, < 3.12 | 8.1.RC1 | 2.5.1 / 2.5.1.post1.dev20250619 | N/A | N/A |
| v0.9.1 | v0.9.1 | >= 3.9, < 3.12 | 8.2.RC1 | 2.5.1 / 2.5.1.post1 | N/A | N/A |
| v0.9.1rc3 | v0.9.1 | >= 3.9, < 3.12 | 8.2.RC1 | 2.5.1 / 2.5.1.post1 | N/A | N/A |
| v0.9.1rc2 | v0.9.1 | >= 3.9, < 3.12 | 8.2.RC1 | 2.5.1 / 2.5.1.post1 | N/A | N/A |
| v0.9.1rc1 | v0.9.1 | >= 3.9, < 3.12 | 8.1.RC1 | 2.5.1 / 2.5.1.post1.dev20250528 | N/A | N/A |
| v0.9.0rc2 | v0.9.0 | >= 3.9, < 3.12 | 8.1.RC1 | 2.5.1 / 2.5.1 | N/A | N/A |
| v0.9.0rc1 | v0.9.0 | >= 3.9, < 3.12 | 8.1.RC1 | 2.5.1 / 2.5.1 | N/A | N/A |
| v0.8.5rc1 | v0.8.5.post1 | >= 3.9, < 3.12 | 8.1.RC1 | 2.5.1 / 2.5.1 | N/A | N/A |
| v0.8.4rc2 | v0.8.4 | >= 3.9, < 3.12 | 8.0.0 | 2.5.1 / 2.5.1 | N/A | N/A |
| v0.7.3.post1 | v0.7.3 | >= 3.9, < 3.12 | 8.1.RC1 | 2.5.1 / 2.5.1 | N/A | N/A |
| v0.7.3 | v0.7.3 | >= 3.9, < 3.12 | 8.1.RC1 | 2.5.1 / 2.5.1 | N/A | N/A |

选择目标时保存整行，不跨行借 CANN 或 torch_npu 补齐。“同号”也不是通则：Ascend v0.14.0rc1 配 vLLM v0.14.1，v0.11.0rc0 配 vLLM v0.11.0rc3，v0.8.5rc1 配 vLLM v0.8.5.post1，v0.10.1rc1 允许 v0.10.1/v0.10.1.1；Ascend v0.23.0.post1 的上游仍是 v0.23.0。v0.23 RC 到 final 改变了 CANN、torch_npu post 和 Triton；不得只删 rc 后缀而保留旧运行栈。N/A 只保留为原表未给值，不自动解释成“无需依赖”或“该功能不支持”。v0.7.3 的另装 mindie-turbo 提醒也不能泛化到全部新版本。

该快照的 main 行、release 行和构建默认值并不相同。mkdocs.yml 的 extra 中 release/stable 默认 v0.23.0；main 的 CANN 为 9.1.0、PyTorch 2.10.0、torch_npu 2.10.0.post4、Triton 3.2.2，不能因表中 v0.30 RC 的 CANN 为 9.2.0 就覆盖 main 变量。把“更新的组件”当作兼容修复前，应先确定选的是哪个安装目标。

## 提交、模板宏与版本门控分别留证

docs/hooks/macros_main.py 从仓库根读取 .github/vllm-main-verified.commit 和 .github/vllm-release-tag.commit，分别填入 main_vllm_commit 和 main_vllm_tag；此快照为 544f182d9f0c9bfe8bd7645525951d5e3692a542 与 v0.32.0。main_vllm_tag 不是 mkdocs.extra 中一个同名字面量，也不是不存在的 main-verified.tag 文件。文件不存在时宏保留 unknown；读文件的其他错误没有在这里统一吞掉。Dockerfile 的 VLLM_COMMIT 非空时优先于 VLLM_TAG，不能用默认 tag 证明镜像最终实际构建的 commit。

宏 include_code 对找不到的文件生成带 FileNotFound 的代码围栏；找不到 start marker 时从头、找不到 end marker 时到 EOF。看到渲染后的代码块不证明预期片段匹配、示例完整或能执行。文档策略期望各分支正文一致、用 extra 控制版本差异，这也不是实际中文 HTML 已构建到某提交的证据。

vllm_version_is 首先用 VLLM_VERSION，否则读取包版本，再用 packaging.Version 的 public 部分比较：local 段不参与该比较，dev/pre 等公开版本部分仍有意义；函数还有缓存，不能把改环境变量等同于已运行进程内每次重读。解析 InvalidVersion 会转成 ValueError，旧文称 dev/editable 可能触发，不代表所有合法 dev 版本都非法。VLLM_VERSION 只改变代码选路判断，不安装软件、不修 ABI、不提供测试通过证据，也不能用伪版本掩盖真实依赖身份。

## 分支维护与文档身份

Maintained 的策略含 bugfix、release 和 CI 承诺，通常约 2–3 个 minor；Unmaintained 仍可能接受社区 bugfix，但没有 release/CI 承诺；EOL 不再接受修改。不能按版本年龄自行判 EOL，也不能把分支维护状态当成该分支每个模型仍受维护。

本快照表列 main、releases/v0.23.0、releases/v0.30.0、releases/v0.18.0、releases/v0.13.0、v0.11.0-dev、v0.9.1-dev、v0.7.3-dev 为 Maintained；v0.7.1-dev 为 Unmaintained，被 v0.7.3-dev 替代。新命名为 releases/vX.Y.Z，旧 -dev 名仍可存在；不是每个 vLLM minor 都有对应 Ascend 分支。变更通常先进 main 再 backport。main 兼容最新一两个 release 及上游 main 的 CI 策略不能替代特定模型、硬件和组合的实际测试记录。

latest 策略指 main 最新 RC 文档，RC 文档来自对应不可继续更新的 tag，历史正式版文档可在 releases 分支持续修文档错误。因此同一历史版本 URL 的文字可能修正；保存 URL、获取时间、提交和正文摘要。这里未建立整站 HTML 到提交的映射。

上游 feature branch 策略要求 rfc/ 前缀、关联 RFC、至少两位 maintainer 批准及负责 mentor，超过三个月未合入需 mentor 评估是否删除；它是来源项目的治理信息，不构成本次仓库操作的审批指令。来源表中 rfc/long_seq_optimization 关联 vLLM issue 22693，Scheduled Merge Time 原值 930 没有完整日期，不能补造成新的里程碑。

torch-npu 策略区分三个月 stable、月度 POC 和每日 nightly：stable 可用于 Ascend final，月度 dev 只用于 RC，nightly 不用于其任何 release/branch。这是固定项目规则，不证明当前机器装包、wheel 可用性或某套依赖实际运行通过。

## 固定来源发布日历

以下只保存该提交的日历事件；final、RC、post 和后来补发的旧版本分别解释，不由排列推算 API/模型支持。实际发布时间和安装包状态需在应用时另核验。

| 日期 | 来源事件 |
| --- | --- |
| 2026.10.11 | Release candidates, v0.30.0rc1            |
| 2026.09.21 | v0.23.0 post release, v0.23.0.post1  |
| 2026.09.03 | Release candidates, v0.26.0rc1            |
| 2026.08.16 | v0.23.0 Final release, v0.23.0            |
| 2026.07.20 | Release candidates, v0.23.0rc1            |
| 2026.06.30 | Release candidates, v0.22.1rc1            |
| 2026.06.16 | Release candidates, v0.21.0rc1            |
| 2026.06.03 | Release candidates, v0.20.2rc1            |
| 2026.04.30 | Release candidates, v0.19.1rc1            |
| 2026.04.24 | Release candidates, v0.13.0rc3            |
| 2026.04.01 | Release candidates, v0.18.0rc1            |
| 2026.03.15 | Release candidates, v0.17.0rc1            |
| 2026.03.10 | Release candidates, v0.16.0rc1            |
| 2026.02.27 | Release candidates, v0.15.0rc1            |
| 2026.02.06 | v0.13.0 Final release, v0.13.0            |
| 2026.01.26 | Release candidates, v0.14.0rc1            |
| 2026.01.24 | Release candidates, v0.13.0rc2            |
| 2025.12.27 | Release candidates, v0.13.0rc1            |
| 2025.12.16 | v0.11.0 Final release, v0.11.0            |
| 2025.12.13 | Release candidates, v0.12.0rc1            |
| 2025.12.03 | Release candidates, v0.11.0rc3            |
| 2025.11.21 | Release candidates, v0.11.0rc2            |
| 2025.11.10 | Release candidates, v0.11.0rc1            |
| 2025.09.30 | Release candidates, v0.11.0rc0            |
| 2025.09.16 | Release candidates, v0.10.2rc1            |
| 2025.09.04 | Release candidates, v0.10.1rc1            |
| 2025.09.03 | v0.9.1 Final release, v0.9.1              |
| 2025.08.22 | Release candidates, v0.9.1rc3             |
| 2025.08.07 | Release candidates, v0.10.0rc1            |
| 2025.08.04 | Release candidates, v0.9.1rc2             |
| 2025.07.11 | Release candidates, v0.9.2rc1             |
| 2025.06.22 | Release candidates, v0.9.1rc1             |
| 2025.06.10 | Release candidates, v0.9.0rc2             |
| 2025.06.09 | Release candidates, v0.9.0rc1             |
| 2025.05.29 | v0.7.3 post release, v0.7.3.post1         |
| 2025.05.08 | v0.7.3 Final release, v0.7.3              |
| 2025.05.06 | Release candidates, v0.8.5rc1             |
| 2025.04.28 | Release candidates, v0.8.4rc2             |
| 2025.04.18 | Release candidates, v0.8.4rc1             |
| 2025.03.28 | Release candidates, v0.7.3rc2             |
| 2025.03.14 | Release candidates, v0.7.3rc1             |
| 2025.02.19 | Release candidates, v0.7.1rc1             |

本批只读策略、译文、宏、配置和所列版本判断片段，没有运行文档宏、导入包、安装、构建或执行 NPU。完整配对表是可追溯的选型输入，真实适配仍按上文分层验收。


## 旧根目录安装译文与当前入口分开裁决

根目录 installation.po 的111条有效消息是历史孤儿资料，与 getting_started/installation.po 的82条不是同一份文档。当前同提交没有 docs/source/installation.md；当前入口是 getting_started/installation.md。旧译文中的 Python >=3.10,<3.13、PyTorch 2.10.0、torch_npu 2.10.0.post4、CANN/NNAL 9.1.0、Triton Ascend 3.2.2及未展开镜像宏只保留为该资料的组合线索，不覆盖上面的整行发布表，也不证明与 Native v0.32.0 已运行兼容。

尤其 CPU-only 条件已变：旧译文仍列 CANN 头文件/库、Torch及构建工具，当前 canonical 安装说明明确在 COMPILE_CUSTOM_KERNELS=0、显式 SOC_VERSION、--no-build-isolation --no-deps 的打包路径不需要驱动、CANN、Torch、torch_npu 或 vLLM。它只验证 editable 包和元数据，不是 CPU 推理、NPU 自定义算子或完整 UT；两代前置条件不能混成同一命令。--no-build-isolation 复用现有构建环境，不自动解决运行 ABI；--no-deps 故意不安装运行依赖。

SOC_VERSION 示例 ascend910b1、ascend910_9391、ascend310p1、ascend950dt_9582 是所选构建目标的标识，不探测或模拟物理硬件，也不证明所有950子型号可运行。setuptools-scm 与 Arctic 未命中 wheel 后的 CMake/Ninja 要求分别定位；不要把所有安装失败归为 CANN 故障。旧版 uv/Triton 安装顺序、A3 submodule 更新和缓存清理是版本限定的来源建议，本次没有执行。

## 软件栈图与宿主条件的解释限度

hardware-software-stack-overview.png 展示 vLLM/Ascend、Torch/torch_npu 与 Triton Ascend 分支、CANN Toolkit/Ops/NNAL、HDK Driver/Firmware 和 NPU 的层次。图是职责概览：Triton 右侧连线不能解释成绕过 CANN、全部硬件必须装 Triton，NNAL 方框也不能替代逐路径依赖裁决。图与具体版本/硬件表配合使用。

旧200I Pro的openEuler挂载包含 libsemanage.so.2，以及宿主 libyaml-0.so.2.0.9 到容器 libyaml-0.so.2 的映射；这些是特定 OS 模板路径，不保证其他发行版 ABI。先检查真实文件、库依赖与容器目标，不跨OS复制整条命令。NNAL/libatb 的镜像声明按实际标签、源码构建或自管环境分别确认，不由某模板外推所有镜像。

多节点链路的 -link 要看 UP，-net_health 要看 Success，配置查询按各自字段解释。远端 NPU IP 的双向零丢包只关闭基础连通性缺口；管理IP ping、容器 Up、各节点都有 /root/.cache 均不能证明集合通信或相同权重可用。旧光纤/LAN建议是其拓扑条件，不推广到全部互联；950DT 的 D2D 文件与实际端点仍需另验。未运行系统、安装、网络或NPU命令。


## 2026-11-03 main 增量：安装包与设备挂载

本节只适用于新增固定提交3164adc8fe75892fbf7f99f524bb72fddf1e6efd，相对原ceac基线分别保留，不把它改写成原版本已具备的安装合同。最新main配对文件仍为544f182d9f0c9bfe8bd7645525951d5e3692a542；没有升级本地基线checkout、安装软件或运行设备探针。完整读取新提交install_vllm_ascend.inc.md205行和pin，安装主文/950DT两片段仅核对变更hunk。

新的pip配方明确先以VLLM_TARGET_DEVICE=empty、VLLM_VERSION_OVERRIDE及--no-binary vllm构建指定Native版本，再安装标准Ascend wheel；标准wheel仍只针对A2，不自动覆盖A3、310P或950DT。uv/WheelNext与源码仍是不同构建选择，不能把pip分发包可安装当硬件匹配。模板release版本仍须在实际文档构建上下文展开，不能从main SHA直接猜发行版本。

A2/A3/950DT在pip、uv和源码安装后都需要同一Python环境的kernel依赖补装。文档现明确FLA NPU用于worker初始化、不会随vllm-ascend自动安装：分别选择flash-linear-attention-npu-a2、-a3、-a5并保持匹配版本；宿主运行库要求glibc>=2.34和GLIBCXX_3.4.29。Triton Ascend仍按对应版本重装及维护共享安装路径。Atlas300I DUO/200I Pro不需要FLA NPU，也不安装Triton；这不扩展为其他未列产品的结论。

950DT的CANN基础镜像和Ascend镜像命令新增/dev/ummu、/dev/uburma，前者相应删除旧/dev/devmm_svm挂载。这里只记录这两份文档模板变化，不推所有驱动/产品均具有相同设备节点。部署时按真实宿主节点和匹配驱动核对，再进入本卡分层验收；命令文本变化、版本配对文件和依赖声明均未提供NPU推理结果。


## 固定仓库README的版本提示与中英文差异

补读同提交 README.md126行、README.zh.md130行的完整Markdown技术文本，装饰徽标的内嵌logo编码不作为知识。两份均列Linux、Python>=3.10且<3.13、CANN9.1.0、Torch2.10.0与TorchNPU2.10.0.post4；这是该main快照入口，不覆盖前述各release整行配对。main CI承诺Native main和v0.32.0 tag，仍要区分实际pin544f与独立Native5df。

推荐表两份都有0.30.0rc1/0.26.0rc1/0.23.0，但英文news停0.26、中文多0.30，中文维护分支多releases/v0.30.0；不能只以首页新闻首条决定当前最新安装目标，也不把中文分支额外行当完整运行结果。硬件入口只列A2/A3与实验性300I Duo，未列950不是其永久不支持证明，仍沿精确支持表/产品/代码门禁核对。

README的“常见Transformer/MoE/Embedding/多模态无缝运行”和DeepWiki入口属于项目定位，不能推任意checkpoint、SKU、量化和组合全支持。离开该固定快照应用时重新取证实际版本；本次未访问动态外链、安装包或运行推理。

## 2026-11-03 发布快照：展开后的安装宏不等于 main 配对

本节冻结本次公开中文安装页与源码 `5f5e25dd94db85b59251be7d3baf7c808475b6d7`，不追随滚动latest。实际HTML的release整套宏为vLLM/Ascend0.30.0、HDK26.1.1、CANN/NNAL9.2.1、PyTorch2.10.0、TorchNPU2.10.0.post7、Triton Ascend3.6.0.post2、FLA NPU26.9.1、镜像Python3.12；Python支持范围仍>=3.10,<3.13。main宏列CANN9.2.1、TorchNPU post7、Triton3.6.0.post2，须和release字段分别记录。

同一发布源码的`.github/vllm-main-verified.commit`是24420b7a341af37a9bc3186e6fc6062512e0aa58，release-tag文件是v0.32.0；这些与release安装宏0.30.0是不同用途的字段。版本策略页的v0.30.0rc1行仍列CANN9.2.0/TorchNPU post4/Triton3.2.2，是另一个release候选组合，不能按最高数字拼接。没有据此自动升级ceac/3164知识、Native独立快照或宣称ABI/设备兼容。

本次已在HTML核到pip构建Native wheel、FLA硬件包与950DT挂载的实际展开；它解决发布文字证据，不替代本卡的分层安装与NPU验收。中文HTML仍有英文回退段，source链接指向main而非固定commit；版本身份和逐页限制见[文档渲染核验](../../runbooks/validations/vllm_ascend_document_rendering_evidence.md)。
