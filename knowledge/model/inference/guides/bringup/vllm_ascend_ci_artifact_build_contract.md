---
type: Guide
title: vLLM Ascend CI构建产物：缓存身份、镜像与Wheel Variant合同
description: 区分Csrc持久缓存、构建环境、nightly测试镜像和Wheel Variant发布产物，核对source/SoC/toolchain身份、降级无L1、动态库排除及variant元数据；不把打包成功提升为设备兼容或模型通过。 补充固定3164的依赖/镜像、共享临时目录Actions staging与CI登记边界。
tags:
- task.implementation
- task.testing
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/wheel/make_variant.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/actions/csrc-l1-restore/action.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/actions/csrc-l1-save/action.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/actions/read-vllm-release-tag/action.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_build_csrc_cache.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_ensure_csrc_cache.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_nightly_image_build.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_schedule_image_build.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_schedule_nightly_pair_image_build.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.buildwheel.310p
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.buildwheel.a2
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.buildwheel.a3
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.buildwheel.a5
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.nightly.310p
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.nightly.a2
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.nightly.a3
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/dockerfiles/Dockerfile.nightly.a5
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/nightly_image_build.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/push_build_csrc_cache.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_image_build_and_push.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_image_build_with_base.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_release_code_and_wheel.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/csrc_cache_targets.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/prepare_csrc_l1_restore.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/resolve_csrc_cache_targets.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/wheel/auto_exclude.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/wheel/config.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/wheel/pyproject.toml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/TEST_README.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/actionlint.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/_build_csrc_cache.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/_e2e_nightly_single_node.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/_e2e_nightly_single_node_560t.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/_e2e_nightly_single_node_models.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/_ensure_csrc_cache.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/_selected_tests.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/_selected_tests_upstream.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/configs/nightly_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/configs/weekly_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/labeled_download_model_dataset.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/misc/model_dataset_list.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/pr_test.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/recipes-preview-comment.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/recipes-preview.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/schedule_doc_getting_started_test.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/schedule_e2e_upstream_test.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/schedule_main2main.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/schedule_nightly_image_build_with_base.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/schedule_release_code_and_wheel.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/scripts/csrc_cache_targets.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/scripts/estimated_times.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/scripts/runner_label.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/scripts/stage_ci_actions.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.github/workflows/scripts/test_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/.pre-commit-config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile.310p
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile.310p.openEuler
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile.a3
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile.a3.openEuler
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile.a5
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile.a5.openEuler
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/Dockerfile.openEuler
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/mkdocs.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/pyproject.toml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/requirements.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/doctests/002-installation-test.sh
  role: implementation
created_at: '2026-11-03T05:13:25Z'
updated_at: '2026-11-03T06:56:11Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend CI构建产物：缓存身份、镜像与Wheel Variant合同

## 缓存、编译、打包和设备结果分别留证

本卡读取固定ceac的CI构建调用/输入、Docker差异及wheel工具入口；只蒸馏产物身份和Host工具合同，未展开每个外部Action、Docker层、库解析或CANN构建算法。未执行脚本、容器、下载、安装、ldd、auditwheel、编译或NPU。内层构建缓存见[增量缓存](vllm_ascend_incremental_build_cache.md)，外层restore成功不证明kernel HIT、编译成功或模型质量。

prepare_csrc_l1_restore导出绝对缓存路径及event log；源快照缺build_cache.py时返回supported=false。准备阶段会重建缓存目录，用架构、SoC、toolchain-image、tracked Csrc hash及unique suffix计算三个snapshot-key字段；响应不是恰好三个非空行、Git/进程/路径错误等会通知并退化为无持久L1，不自动宣称测试失败或可复用。该流程有目录/进程副作用，本次未执行。

csrc_cache_targets列13项：A2/A3/310P各ARM64/X64×Ubuntu/openEuler共12项，另A5仅ARM64 Ubuntu条目；这是CI目标枚举而非完整平台支持矩阵。前12项image字面值为CANN9.2.0_20260928212200，A5条目为9.1.0-950。Docker buildwheel文件又使用9.1.0 manylinux基座；不同用途不要揉成单一推荐栈。

## 镜像和依赖身份

四种wheel Dockerfile设置不同SOC_VERSION，A5额外默认MAX_JOBS=2并同设CMAKE_BUILD_PARALLEL_LEVEL；这些是构建资源参数，不是全硬件性能结论。nightly Dockerfile按branch/OS/tag suffix和芯片后缀选择基础镜像，再准备AISBench标签v3.1-20260609-master及依赖；记录最终解析commit和image digest，不能只凭tag等价于不可变构建。

read-vllm-release-tag只去空白并按v数字.数字.数字及可选后缀校验格式，输出release_tag；格式合法不证明兼容、安装身份或ABI。构建/ensure/发布workflow中的should_push、needs/skip和目标matrix分别解释；存在merge-image或release job不证明本次发布或所有架构成功。

## Wheel Variant不只是改文件名

make_variant要求非null variant提供properties，按job构造variantlib make-variant参数，可显式skip-plugin-validation/no-isolation/installer。固定配置的310p/910b/a3/950标签对应ascend::npu_type属性，四项都设置skip_plugin_validation=true；不能把这个选项的名字理解为插件实际验证已完成。provider pyproject仅Linux启用Ascend插件并声明>=0.0.2,<0.0.3依赖，目标运行环境仍另核。

生成后_verify_built_wheel核文件存在、合法wheel名、variant label与.dist-info variant元数据，并要求实际properties集合与job集合精确相等。输出文件名正确不代替内部元数据；这也不证明目标机动态库、设备驱动或算子可加载。

auto_exclude扫描依赖并把本机缺失且未预排除的库加入auditwheel exclude，逐wheel调用repair；任一非零保留原始stdout/stderr并返回，成功后替换产物。排除外部CANN/运行时依赖与把库打入wheel不是同一件事，不能从repair成功推目标环境依赖完整。

## CI来源职责索引

以下来源按实际调用角色聚合，不为每个硬件variant另建知识卡。YAML/JSON是静态配置，Docker是构建输入；完整安装、链接、运行及真实模型/性能仍待执行。

- `.github/workflows/scripts/wheel/make_variant.py`：Wheel产物和属性校验。
- `.github/actions/csrc-l1-restore/action.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/actions/csrc-l1-save/action.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/actions/read-vllm-release-tag/action.yml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/_build_csrc_cache.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/_ensure_csrc_cache.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/_nightly_image_build.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/_schedule_image_build.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/_schedule_nightly_pair_image_build.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/dockerfiles/Dockerfile.buildwheel.310p`：目标构建环境与显式芯片输入。
- `.github/workflows/dockerfiles/Dockerfile.buildwheel.a2`：目标构建环境与显式芯片输入。
- `.github/workflows/dockerfiles/Dockerfile.buildwheel.a3`：目标构建环境与显式芯片输入。
- `.github/workflows/dockerfiles/Dockerfile.buildwheel.a5`：目标构建环境与显式芯片输入。
- `.github/workflows/dockerfiles/Dockerfile.nightly.310p`：目标构建环境与显式芯片输入。
- `.github/workflows/dockerfiles/Dockerfile.nightly.a2`：目标构建环境与显式芯片输入。
- `.github/workflows/dockerfiles/Dockerfile.nightly.a3`：目标构建环境与显式芯片输入。
- `.github/workflows/dockerfiles/Dockerfile.nightly.a5`：目标构建环境与显式芯片输入。
- `.github/workflows/nightly_image_build.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/push_build_csrc_cache.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/schedule_image_build_and_push.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/schedule_nightly_image_build_with_base.yaml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/schedule_release_code_and_wheel.yml`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/scripts/csrc_cache_targets.json`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/scripts/prepare_csrc_l1_restore.py`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/scripts/resolve_csrc_cache_targets.py`：缓存/镜像/发布调用与身份输入。
- `.github/workflows/scripts/wheel/auto_exclude.py`：Wheel产物和属性校验。
- `.github/workflows/scripts/wheel/config.json`：Wheel产物和属性校验。
- `.github/workflows/scripts/wheel/pyproject.toml`：Wheel产物和属性校验。


## 固定3164：构建输入与容器内Action路径更新

本节固定Main 3164adc8fe75892fbf7f99f524bb72fddf1e6efd相对ceac的差异。前述9.1/9.2.0标签属于ceac历史；本节读取CI、Docker与依赖元数据的变更及相近文件差异，不代表容器构建、下载、链接、SDK安装或NPU已执行通过。

requirements和pyproject把torch-npu固定改为2.10.0.post7、triton-ascend改为3.6.0.post2；Torch仍2.10.0，memfabric-hybrid/memcache-hybrid改1.3.0并进入build-system输入。mkdocs把released文档版本改v0.30.0、release/main CANN改9.2.1、release HDK改26.1.1、NNAL改9.2.1、FLA改26.9.1。它们是不同用途的声明，不是本机实际包、驱动或ABI已对齐的观测。

八份主Dockerfile改用quay.io/ascend/cann的9.2.1芯片/OS标签；cache target、ensure key、runner image_tag和CPU-UT输入也随之更新。旧9.3.0 ops-transformer独立安装段被移除，不能继续凭旧Docker叠装步骤还原新环境。A2/A3/A5的FLA改release轮子、按平台镜像路径下载；部分旧Triton/每日torch_npu安装及FLA checksum校验仅剩注释，不能把ARG或注释当实际安装/校验。A2新增mfcli kernel install --soc-version A2；FlashAttention-NPU固定checkout与FLASH_ATTN_BUILD_NPU=910也属于独立构建输入。310P不因此获得其他平台FLA或算子支持。

### local Actions要同时对runner和容器可见

stage_ci_actions.sh要求GITHUB_WORKSPACE/../../_temp的realpath等于RUNNER_TEMP，否则明确退出；随后把所选source-root/.github以cp -a放到RUNNER_TEMP/ci-workflow。调用使用静态路径./../../_temp/ci-workflow/.github/actions/csrc-l1-restore或save。不能只改uses而漏掉checkout后的staging，也不能认为容器/__w和宿主runner工作区天然同步。

构建、文档source安装、Main2Main cache miss和选中设备测试等分支分别增加staging；子目录checkout显式working-directory并传`.`，restore的source-root仍对应真实源码位置。staging与Action必须保留相同if条件，不能从一个分支存在脚本推另一个分支也已准备。该脚本只校验共享临时目录布局，不证明缓存身份、外部Action或编译结果正确。

工作流移除内部cache-service的pip/apt镜像重写，保留相应公开/华为索引与重试配置；Installation doctest也只改写clone重试而不再重写包源。release wheel提取显式--entrypoint /bin/bash，不把镜像默认ENTRYPOINT猜成shell。actionlint升1.7.12、PR pre-commit新增10分钟timeout是工具/作业边界，均未在本次执行。

### CI登记、估时与预览消息不等于设备结果

Nightly/weekly登记增加Kimi-K3 MRV2、MiniMax-M3 PP/PD及Mooncake池用例，并移除或迁移若干旧模型配置；estimated_times的数值用于分区负载，不能当NPU性能成绩。新增LiLiCorr文件进入选择清单、SwiGLU MX文件显式a5-4路由；模型下载清单与560T下载runner扩展只准备数据，不证明测试已跑。

recipes preview限定yaml路径；独立comment工作流只读可信workflow与PR元数据，按当前main/recipe标签/文件资格刷新或撤下链接，并以每PR concurrency串行。它明确标示当前PR SHA不是deployment状态，异步预览可仍是旧revision。评论/链接、artifact存在与真正构建/设备测试分别核对，不能把这类控制面成功纳入模型验收PASS。
