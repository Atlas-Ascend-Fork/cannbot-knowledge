---
type: Runbook
title: vLLM Ascend 批次不变性（batch-invariant）安装：completed但算子仍不可用
description: 核对 build_batch_invariant_ops.sh 的 batch-invariant Python 环境、包版本与SoC/架构，分开验收run包、扩展wheel和运行注册；解释失败后仍可completed的路径。
tags:
- task.debugging
- task.testing
- topic.model_serving
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/build_batch_invariant_ops.sh
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/build_aclnn.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/batch_invariance.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/batch_invariant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/Dockerfile
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/Dockerfile.a5
  role: supporting
created_at: '2026-10-29T22:30:34Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T22:52:06Z'
---

# vLLM Ascend 批次不变性（batch-invariant）安装：completed但算子仍不可用


## 触发、版本与原始信号

源码构建或镜像日志含batch_invariant_ops build completed，但随后导入扩展失败、所需op未注册，或运行batch-invariant模式并未走预期算子。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`；这里只蒸馏Host安装包装脚本、调用片段和运行期注册入口。没有现场安装/错误复现，整项运行排障平台集合未由这些片段完整证明，保持draft/空平台。

原始信号来自已读脚本字面日志：Failed to download batch_invariant run package、Failed to install batch_invariant run package、Failed to build and install batch_invariant whl package、batch_invariant_ops build completed。它们是静态分支，不是本环境已发生的错误或已验证修复。

## 先分skip、阶段失败与真正就绪

| 阶段 | 固定源码行为 | 判据边界 |
| --- | --- | --- |
| 参数 | SOC_ARG为空退出1；ascend910b→910b、ascend910_93→A3、ascend950*→950 | 其他SoC打印skip并退出0，0不表示已安装 |
| Host架构 | uname -m只识别aarch64/x86_64 | 其他架构warning后退出0，不提供算子可用证明 |
| run包 | 下载设备/架构对应2.0.0 .run，再执行安装器 | 下载/安装失败在if分支记录后可继续，不是每次都使包装脚本非0退出 |
| 扩展wheel | 下载2.0.0 zip，解包到预期目录后执行build_and_install.sh | zip失败、目录缺失或构建失败同样可只log后继续 |
| 收尾 | 清理下载包/解包目录，再输出completed | 这条日志不是两阶段成功汇总，也不是后续正确性检查 |

set -euo pipefail并不把这些if/else中的已处理失败自动变成非0退出；支持的SoC/架构下也存在前面失败后到completed的路径。反过来，其他未被处理的命令仍可能使脚本失败，不能声称脚本任何情况下都退出0。

所读build_aclnn.sh片段仅在VLLM_BATCH_INVARIANT精确为1时调用该独立脚本；缺脚本时warning，未开启时skip。父调用返回不能补出包装脚本未报告的两个阶段成败；本卡不替代整条CMake/构建链的其他检查。

## 外部包身份与环境边界

run URL由设备族/架构拼接，zip URL为另一资源；固定Git提交只冻结这些URL和包装逻辑，不能单独证明URL内容一直不变或两个外部包ABI相容。脚本没有在所读路径校验下载内容digest，并使用curl -k。记录实际包来源、内容身份、目标SoC、架构和安装输出；没有取得内容证据时，不将文件名2.0.0当作完整可复现锁定。

子脚本在run安装前unset ASCEND_CUSTOM_OPP_PATH；这不是把父进程当前变量自动改掉的通用机制。run安装器及zip内部build_and_install.sh没有在本批获取、解析或执行，不推导它们的全部路径、权限、回滚和Device实现。两阶段结束还可能影响不同安装位置，须按实际安装环境取证。

## 构建期、导入、注册与执行逐层验收

主指南的两阶段顺序为先Device run包，再PyTorch扩展wheel；仅安装vllm-ascend预构建wheel不会补回csrc或重新构建这些资源。源码/已装包版本、Python环境、torch/torch_npu/CANN与目标SoC分别对齐，避免检查另一个解释器的包。

指南Quick Check仅导入batch_invariant_ops并查看npu_matmul_batch_invariant符号。导入成功、符号存在、运行期选择该实现和目标NPU数值正确分别留证；不能把print出的op名称当一次真实kernel执行。

运行期init_batch_invariance还按HAS_TRITON/HAS_ASCENDC_BATCH_INVARIANT分支：只有Triton时不会安装AscendC分支的FIA、AddRmsNorm和sum直接覆写；两者都不可用时只warning并跳过初始化。Enabling日志也不提供全模型确定性证明。详见[批次不变性与Host接线](../../guides/integration/vllm_ascend_batch_invariance_validation.md)。

## 排查顺序、处置与剩余验证

保留完整构建日志，而非只取尾行：核对SOC_ARG/架构是否skip→run下载与安装结果→zip/目录/wheel构建结果→当前解释器扩展和op注册→实际运行开关与Host分支→目标模型的输出/调度条件。清理下载文件或镜像构建成功不等于这些层都已就绪。

只在目标环境授权的安装流程中恢复匹配资源，再验证所有rank；本文没有执行安装、导入或修复。若出现Current device type与installed version device type不一致，另按[构建/运行设备身份](vllm_ascend_build_runtime_device_mismatch.md)归因，不把所有缺op/安装问题混为SoC身份错误。

最终按固定模型/权重/seed、批大小与顺序、调度/抢占限制及数值/性能对照验收，保留失败阶段和原始结果。外部包实现、全部模型/硬件、Device编译/精度/性能与Agent A/B仍未完成，不能用本卡或来源检查通过替代。
