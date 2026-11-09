---
type: Guide
title: vLLM Ascend Csrc 缓存：L0/L1 身份、选择性失效与安全回退
description: 结合中文构建缓存设计区分快照键与凭据、L0/L1命中和实际编译复用，核对身份、CI相对路径、并发发布和成功后清理的独立边界。
tags:
- task.implementation
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/persistent_csrc_build_cache.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/persistent_csrc_build_cache.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/build_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/build_cache.cmake
  role: implementation
created_at: '2026-10-29T09:54:45Z'
updated_at: '2026-11-03T05:26:43Z'
platforms:
- a2
- a3
- 310p
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Csrc 缓存：L0/L1 身份、选择性失效与安全回退

## 范围和层级

固定设计的直接cold/warm记录列A2/A3/310P，本卡按此平台声明，不补950结果。L0是最终artifact精确命中，可跳整个native build；L1恢复只提供action候选，仍校验inner manifest/content，miss回普通源码构建。L1不能补救已被L0接受的错误image身份；可变tag/registry需新的L0 namespace或完整image identity。

## 三个身份必须覆盖语义输入

action key合并prepared_input_hash、recipe_hash、compiler_environment_hash，operator_text_hash只提供operator namespace。generated/dependent/shared内容、compat headers、构建命令/recipe、SET_ENV、工具版本与CANN环境均要参与。规范化只去掉明确声明且语义内容已独立覆盖的物理根，binary保持字节敏感，symlink身份和解析内容都参与；不可读输入不静默忽略。

CMake caller改变编译可见内容时同时更新PREPARED_INPUT/RECIPE_*/SET_ENV/ENVIRONMENT_*，不能只加NORMALIZE_PATH。schema4不原地迁移旧entry，非生产candidate snapshot也需隔离。snapshot兼容按architecture/SOC及实际编译image，direct build还含OS/libc，不能用外层runner替代nested compiler环境。

## 并发、失败和清理

entry/action/publish三种lock保护不同对象，私有staging后原子发布，owner冲突硬失败。传输/保存可用性失败一般回正常build，compiler失败仍失败；合法JSON但顶层非object当前会抛错，不能笼统说所有坏manifest都MISS。

local cache默认ignored csrc/build_cache，可用绝对override；schema和来源不变时删cache只导致cold。build.sh成功后按SOC/operator保留两种operator_text_hash版本，不限制总字节/同版本action或远端snapshot。清理无共享lock，独立并发build需独立目录或维护窗口。

## 验证与回退

对照cold/warm、改变一个operator/共享header/recipe/toolchain、移动等价根，检查HIT/MISS和生成artifact；代码改动不可仅看耗时。未覆盖语义输入、来源或产物不一致时隔离cache并普通重建。先保留manifest/event定位，再恢复已知namespace。来源测试记录只作设计依据，本次未执行上游compiler、OBS或cache测试。


## 中文缓存设计：身份、路径与凭据分开

persistent_csrc_build_cache.po的110条译文匹配固定英文，但其中把snapshot key orchestration译为“密钥编排”容易混淆：这里的key是快照/缓存标识，不是访问凭据。prepare_csrc_l1_restore.py生成兼容性键与source/hash/path输出；OBS读写授权由transport/caller处理，不能把缺键当缺凭据或把缓存引擎当凭据读取器。本批没有访问OBS、读取凭据值或执行helper。

L1 snapshot恢复只取得候选，真正复用需inner action的HIT/MISS/BYPASS及manifest/artifact校验；外层restore成功、安装变快和L0 HIT各不相同。L0 key依赖固定registry及不可变image tag，重新发布同tag不能靠下层L1修复。schema4候选namespace与生产也不能仅因版本号相同就互用；PUBLISH_STATE_SCHEMA管理构建树所有权，是另一个格式。

PREPARED_INPUT、RECIPE_FILE/RECIPE_VALUE、SET_ENV、ENVIRONMENT_FILE/VALUE/TOOL和NORMALIZE_PATH各自覆盖输入、构建方法、编译环境与物理路径。--set-env的精确值进入recipe，因为可能指向prepared inputs之外对象。准备输入移动根可命中，不代表字节/转义/外部路径都能归一化；符号链接的身份与目标内容都核对，不可读输入不静默跳过。改算子生成、共享header或protobuf构建命令时重新审查覆盖，不能删除身份项来提高命中率。

## CI相对路径合同与本地绝对路径用途

CI restore/save必须传相同字面cache-dir: csrc/build_cache，runs-on/cache还把路径拼入远端版本；用/tmp与runner.temp或把save输入换成已解析绝对路径，即使action身份兼容也可能分裂OBS namespace。Restore将绝对目录导出GITHUB_ENV供编译，同时保留原始cache-dir输出给Save。它与inner action忽略等价物理root是不同层的key，不能混用。

普通本地构建默认ignored csrc/build_cache，绝对VLLM_ASCEND_BUILD_CACHE_DIR用于本地override，不涉及远端凭据或快照传输。Main2Main/bisect的workflow helper修订与source_ref各自固定，历史源码无引擎返回supported=false并普通构建。文档本次集成只由central producer写L1，普通source consumer只读；image/release-wheel Docker没有因此自动成为L1消费者。

## 成功、MISS、发布与清理各自验收

缺失/无法解析或对象manifest不合法可MISS重编译，合法JSON但顶层非对象当前仍抛错；不要把所有坏缓存统一当fail-open。entry lock不可用可BYPASS，但action/publish同步或owner冲突为防共享产物损坏会失败，compiler失败仍失败；本地保存/远端transport失败按文档保留成功build产物。三类lock不是跨物理节点共享flock合同，node-scoped目录和私有staging/原子发布分别核对。

Restore先移除.updated；新建/替换entry会标更新，全HIT本身不创建标记。构建尾部prune的压缩可另标更新，应区分action命中和缓存状态变化。build.sh仅完整成功后保留每SOC/operator两种operator_text_hash，HIT/save更新recency，失败不prune，非正BUILD_CACHE_MAX_OPERATOR_VERSIONS可关闭该脚本清理。它不限制总字节、第三方entry、保留版本内action变体或历史OBS快照；并发build/prune仍需独立目录或维护窗口。

先用身份/并发/snapshot-key的CPU测试与cold/warm/单operator或header变更、等价root迁移核查，再申请实际目标NPU构建。文档A2/A3/310P记录、CASE-C、producer运行是来源证据，不能作为本次测试事件，也不能补950或所有生产caller验证。当前仅完整阅读英文/中文，无编译、cache执行、prune/目录删除或OBS发布。


## Cache引擎与CMake适配器的实际合同

本次补读固定build_cache.py的AST全结构和snapshot、recipe、entry校验/保存、run分支等选段，以及完整build_cache.cmake。没有执行build/cache/prune；原stable平台与Scope保持，不将源码namespace中的a5/950别名提升为950已复核。

CMake函数只构造argv并通过PARENT_SCOPE返回，要求DOMAIN、UNIT、OUTPUT_DIR、ENVIRONMENT_PROFILE及COMMAND；custom_operator另要求OPERATOR_SOURCE与publish目录/状态目录，引擎文件不存在即配置失败。它默认将source/build根加入normalize，但真实prepared/recipe/environment语义仍由caller完整提供，不因默认normalize自动覆盖外部依赖。

SET_ENV按NAME=VALUE解析并覆盖继承环境，其原始值精确进入recipe哈希；不能把这些可能指向外部输入的值按物理root归一化。recipe文件不存在失败，文本可规范化，二进制按字节；最终key由prepared、recipe、compiler-environment三个hash构成，operator文本只提供域namespace。

snapshot compatibility将ARM64/X64及SoC别名规范化；显式image字符串直接成为身份，无image时要求CANN安装元数据并另含OS/machine/libc/os-release。可变tag不是自动不可变digest；没有元数据且无image时snapshot-key返回2，而不是制造可复用key。当前schema4，publish-state格式1为另一合同。

_validate_entry要求匹配schema/final_key/domain、非空artifact列表并逐项校验；artifact_model缺省按legacy1处理，third-party可接受对应模型，但custom operator要求action-isolated模型2。_load_json只捕获读错和JSON解析错，合法非object后续.get仍可失败，原文“坏manifest不全都MISS”的边界保持。

run对custom动作先action lock再entry lock，entry锁不可用可BYPASS普通build且不读写entry；custom私有output与shared发布仍保留。有效HIT的restore/publish遇OSError/RuntimeError会走重建；普通compiler返回非零直接失败。MISS产物先通过正确性相关publish，随后cache save为best-effort，不能将二者故障混成同一类可忽略告警。main捕获的锁超时返回75；entry代理与action/publish锁的具体路径仍分别解释。

_save_entry先私有临时目录写manifest并校验全部artifact，再替换entry；旧entry有备份，发布失败尝试回滚，双重失败保留错误。保存/updated-marker失败不自动推翻已成功build结果。外层snapshot、inner HIT/MISS/BYPASS、publish、SAVED、compiler退出和真实冷/热构建产物仍分开交付，不以stdout某个成功词代表模型适配或性能通过。
