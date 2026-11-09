---
type: Guide
title: vLLM Ascend原生构建生成：CMake依赖、OpDesc与模板接口合同
description: 定位Csrc编译/UT/符号与配置生成的实际入口，区分CANN头库发现、INI/JSON/tiling参数生成和Opgen模板；保留caller、缓存语义输入、Device及第三方构建未验边界。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/gen_ops_info.cmake
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/Third_Party_Open_Source_Software_List.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/aclnn_ops_transformer.h.in
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/config_utest.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/dependencies.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/func_examples.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/func_utest.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/intf.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/intf_pub.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/intf_pub_examples.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/intf_pub_linux.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/intf_pub_llt_gccnative.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/intf_pub_utest.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/FindOPBASE.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/FindPython.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findaicpu.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findalog.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Finddlog.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findjson.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findmetadef.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findnnopbase.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findoptiling.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findplatform.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findruntime.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findsecurec.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findtilingapi.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/modules/Findunified_dlog.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/rty_obj_func.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/runtimeKB.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/check_version_compatible.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/convert_yaml.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/custom/help.info
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/custom/install.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/custom/upgrade.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/examples/get_opapi_abs_path.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/examples/get_soc_info.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/fix_format.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/parse_changed_files.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/prepare.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/utest/gen_coverage.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/utest/gen_tiling_data_stub.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/ascendc_bin_param_build.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/ascendc_gen_options.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/ascendc_impl_build.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/ascendc_ops_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/const_var.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/gen_version_info.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/opdesc_parser.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/scripts/util/parse_ini_to_json.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/static.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/symbol.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/abseil-cpp.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/ascend_protobuf.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/build/modules/patch/protobuf-hide_absl_symbols.patch
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/build/modules/patch/protobuf_25.1_change_version.patch
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/gtest.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/json.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/makeself-fetch.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/protobuf.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/third_party/secure_c.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/ut.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/opgen_standalone.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/examples/test_aclnn_add_example.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_host/add_example_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_host/add_example_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_host/add_example_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_kernel/add_example.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_kernel/add_example.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_kernel/add_example_tiling_data.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/opgen/template/add/op_kernel/add_example_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/util/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/util/build_opp_kernel_static.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/util/const_var.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/util/insert_op_info.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/util/merge_aicpu_info_json.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/util/merge_proto.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/util/modify_gen_aclnn.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/pyproject.toml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/ai_qos/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.gitmodules
  role: constraint
created_at: '2026-11-03T05:31:43Z'
updated_at: '2026-11-03T05:34:53Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend原生构建生成：CMake依赖、OpDesc与模板接口合同

## 从源码声明到可加载产物是多段合同

CMake将opapi、opgraph/infer、optiling、AICPU及静态kernel资源分目标生成/链接；Find*模块提供OPBASE、runtime/ACL、metadef、platform、optiling、tilingapi、securec、日志和第三方依赖。发现头文件、找到库、链接完成、打包完成和Python实际加载分别验证，不能仅从find_package成功推ABI/模型正确。

部分Find导出组会拒绝“只定义了部分targets”的状态；Findruntime缺ACL/runtime include显式失败。独立op-api模式要求有效OP_API_DIR，OPTYPE与ACLNNTYPE须一一对应；模板Example缺aclnn函数名/库路径也失败。CMake参数和所选工具链必须与实际caller一致，不把其他项目同名CANN目录当本次依赖已准备。

## 生成器消费的配置也需要校验

gen_ops_info和rty/符号模块协调kernel源复制、INI合并、binary/graph headers、tiling与接口目标；parse_ini_to_json要求OpType并拒绝重复字段，参数/format/type/attrs校验与最终kernel能力是两层。ascendc_gen_options对未知OOM option格式失败，不能把编译选项字符串存在当所有SoC后端接受。

opdesc_parser及ascendc_*脚本从op描述生成适配/参数检查、编译脚本、bin配置和SoC映射；gen_tiling_data_stub仅为UT构造结构桩，不能代替真实tiling和Device行为。静态kernel工具生成symbol/资源头与编译归档，输入库不存在或架构不支持均可拒绝；源码declared参数与运行时实际库版本分别记录。修改任何生成输入、共享header、recipe/命令或编译环境后，按[缓存合同](vllm_ascend_incremental_build_cache.md)补齐身份，不通过删身份字段追求HIT。

## Opgen是脚手架，不是生产算子支持

opgen_standalone要求非空op_type/op_name及字符白名单，目标目录已存在或template/add缺失失败；复制模板、重命名与内容替换各有错误。模板包含Host OpDef/infer/tiling、Device入口/数据结构和aclnn示例，各CMake层共同构建。

AddExample声明ND下FLOAT/INT32，infer从首输入拷贝shape；所读Host tiling还检查资源、4维shape及dtype等条件。不能仅由infer复制shape推自动broadcast、所有rank或任意dtype合法。Device例子是生成模板的占位实现，本卡只提取生成/Host接口边界，不声称完整Operator、所有平台CANN或性能闭包；新增真实算子仍按对应producer完整提取并在目标环境验证。

第三方BOM列gtest1.14、makeself2.5补丁、protobuf25.1、json3.11.3及boundscheck1.1.16；CMake及protobuf/abseil补丁分别参与实际构建与符号边界，不能只按BOM名字推已安装库一致。


## 固定源码职责与有界接口矩阵

下表为全文件结构读取后的接口/参数/拒绝条件摘选，不是完整实现复制，也不代表每个分支、外部工具或Device算法已展开。精确范围与阅读方式在来源行中记录；按目标任务回到固定实现核对。

| 来源 | 已读职责或接口差异 |
| --- | --- |
| csrc/cmake/gen_ops_info.cmake | CMake函数 kernel_src_copy), add_ops_impl_target), add_ops_info_target)；目标/生成/安装声明 |
| csrc/cmake/Third_Party_Open_Source_Software_List.yaml | 静态版本/依赖/安装清单：observability:; googletest:; cpeName: googletest; groupId:; url: https://github.com/google/googletest.git; version: v1.14.0; makeself:; cpeName: makeself; groupId:; url: https://github.com/megastep/makeself.git; version: release-2.5.0-patch |
| csrc/cmake/aclnn_ops_transformer.h.in | 生成模板/接口： |
| csrc/cmake/config_utest.cmake | CMake函数 ；依赖 tikicpulib REQUIRED) |
| csrc/cmake/dependencies.cmake | CMake函数 ；依赖 dlog MODULE REQUIRED), securec MODULE), OPBASE MODULE REQUIRED) |
| csrc/cmake/func_examples.cmake | CMake函数 add_execute_example)；目标/生成/安装声明 |
| csrc/cmake/func_utest.cmake | CMake函数 OpsTest_Level1_AddOpApiShared), OpsTest_AddOpApiShared), OpsTest_Level1_AddOpProtoShared)；目标/生成/安装声明 |
| csrc/cmake/intf.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/intf_pub.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/intf_pub_examples.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/intf_pub_linux.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/intf_pub_llt_gccnative.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/intf_pub_utest.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/modules/FindOPBASE.cmake | CMake函数 ；依赖 OPBASE_INC_DIR, OPBASE_LIB_DIR |
| csrc/cmake/modules/FindPython.cmake | CMake函数 get_python)；依赖 Python3 3.7 COMPONENTS Interpreter) |
| csrc/cmake/modules/Findaicpu.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/modules/Findalog.cmake | CMake函数 ；依赖 _INCLUDE_DIR, slog_a_SHARED_LIBRARY, alog_a_SHARED_LIBRARY |
| csrc/cmake/modules/Finddlog.cmake | CMake函数 ；依赖 dlog_TRANSFORMER_INCLUDE_DIR, dlog_SHARED_LIBRARY |
| csrc/cmake/modules/Findjson.cmake | CMake函数 ；依赖 JSON_INCLUDE |
| csrc/cmake/modules/Findmetadef.cmake | CMake函数 ；依赖 METADEF_INC_DIR, REGISTER_LIB_DIR, OPP_REGISTER_LIB_DIR |
| csrc/cmake/modules/Findnnopbase.cmake | CMake函数 ；依赖 NNOPBASE_ACLNN_INC_DIR, NNOPBASE_OPDEV_INC_DIR, NNOPBASE_LIB_DIR |
| csrc/cmake/modules/Findoptiling.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/modules/Findplatform.cmake | CMake函数 ；依赖 PLATFORM_INC_DIR, PLATFORM_LIB_DIR |
| csrc/cmake/modules/Findruntime.cmake | CMake函数 ；依赖 ACL_INC_DIR, RUNTIME_INC_DIR |
| csrc/cmake/modules/Findsecurec.cmake | CMake函数 ；依赖 C_SEC_INCLUDE NAMES securec.h PATHS ${C_SEC_HEAD_SEARCH_PATHS}), C_SEC_STATIC_LIBRARY NAMES libc_sec_static.lib), C_SEC_IMPLIB NAMES libc_sec.lib) |
| csrc/cmake/modules/Findtilingapi.cmake | CMake函数 ；依赖 TILINGAPI_INC_DIR, TILINGAPI_LIB_DIR |
| csrc/cmake/modules/Findunified_dlog.cmake | CMake函数 ；依赖 _INCLUDE_ROOT_DIR, unified_dlog_SHARED_LIBRARY |
| csrc/cmake/rty_obj_func.cmake | CMake函数 add_infer_modules), add_tiling_modules), add_opapi_modules)；目标/生成/安装声明 |
| csrc/cmake/runtimeKB.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/scripts/check_version_compatible.py | 接口 main, _check_compatible, _get_package_version, _get_version_str; 拒绝 raise ValueError(f'CANN version info file({cann_version_info_file}) not exist.'); raise ValueError(f"Can't get version from CANN version info file({cann_version_info_file}).") |
| csrc/cmake/scripts/convert_yaml.py | 接口 load_test_config, extract_src_and_exclude, write_new_format, main, extract_from_dict |
| csrc/cmake/scripts/custom/help.info | 静态版本/依赖/安装清单：--install-path Install operator package to specific dir path; --install-for-all Allow other users to use the operator package |
| csrc/cmake/scripts/custom/install.sh | Shell入口 log, upgrade, upgrade_proto, upgrade_file；参数 --install-for-all, --install-path, --only-delimited, --quiet |
| csrc/cmake/scripts/custom/upgrade.sh | Shell入口 log, upgrade, upgrade_file；参数 --install-path, --only-delimited |
| csrc/cmake/scripts/examples/get_opapi_abs_path.py | 接口 has_symbol, get_environ_custom_lib_paths, get_default_custom_lib_paths, get_default_builtin_lib_paths, judge_lib_path, main |
| csrc/cmake/scripts/examples/get_soc_info.py | 接口 get_soc_name, main |
| csrc/cmake/scripts/fix_format.sh | Shell入口 ；参数  |
| csrc/cmake/scripts/parse_changed_files.py | 接口 __init__, _add_str_cfg, _add_test_excludes, update_classify_cfg, get_test_options, get_test_example_ops_test_options |
| csrc/cmake/scripts/prepare.sh | Shell入口 clean, convert_string, set_env, build；参数 --ascend-cmake-dir, --ascend-compute_unit, --ascend-op_name, --autogen-dir, --binary-out-dir |
| csrc/cmake/scripts/utest/gen_coverage.py | 接口 main, _chk_env, _gen_cov, get_exclude_paths_from_yaml, init_filter_str, init_filter_str_from_yaml |
| csrc/cmake/scripts/utest/gen_tiling_data_stub.py | 接口 check_if_new_tiling_file_path_existed, process_class_fields, find_classes, convert_template_tilingkey, process_fields, convert_to_old_tiling_struct_style; 拒绝 raise ValueError(f'Unknown dtype({dtype})'); raise e |
| csrc/cmake/scripts/util/ascendc_bin_param_build.py | 接口 get_tiling_keys, trans_soc_verion, parse_op_debug_confg, gen_bin_param_file, parse_args, __init__; 拒绝 raise RuntimeError('arguments must greater than 3'); raise RuntimeError(f'Op {self.op_type} must have at least one input or output') |
| csrc/cmake/scripts/util/ascendc_gen_options.py | 接口 write_options_to_file, gen_compile_options; 拒绝 raise RuntimeError('arguments must greater than 4'); raise err |
| csrc/cmake/scripts/util/ascendc_impl_build.py | 接口 optype_snake, optype_snake_ex, write_scripts, get_ops_info_files, parse_args, __init__; 拒绝 raise RuntimeError('arguments must greater equal than 6'); raise OpFileNotExistsError(args.opsinfo_dir) |
| csrc/cmake/scripts/util/ascendc_ops_config.py | 接口 load_json, get_specified_suffix_file, add_dict_key, correct_format_mode, get_input_or_output_config, get_inputs_or_outputs_config; 拒绝 raise Exception('[ERROR]: must set coreType in json when soc version is {soc}.') |
| csrc/cmake/scripts/util/const_var.py | 接口 conv_soc_ver |
| csrc/cmake/scripts/util/gen_version_info.sh | Shell入口 ；参数  |
| csrc/cmake/scripts/util/opdesc_parser.py | 接口 _is_op_type_in_opdesc, _set_all_options_to_opdescs, _set_options_to_opdesc, _trans_soc_ver_to_short, _get_op_custom_options, get_op_desc; 拒绝 raise Exception(f"[ERROR]: The attribute name: {intersection_element} in op: {{'{self.op_type}'}} conflicts with the built-in variable name. Use a complex name or prefix the operator name."); raise Exception(f'ERROR: custom compile option {param_list} len is not 3') |
| csrc/cmake/scripts/util/parse_ini_to_json.py | 接口 parse_ini_files, check_file_size, parse_ini_to_obj, check_output_exist, check_attr_dict, check_attr; 拒绝 raise OSError from os_error; raise RuntimeError('Not find OpType in .ini file.') |
| csrc/cmake/static.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/symbol.cmake | CMake函数 gen_common_symbol), gen_ophost_symbol), gen_opgraph_symbol)；目标/生成/安装声明 |
| csrc/cmake/third_party/abseil-cpp.cmake | CMake函数 ；依赖 ABSL_SOURCE_DIR |
| csrc/cmake/third_party/ascend_protobuf.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/third_party/build/modules/patch/protobuf-hide_absl_symbols.patch | 静态版本/依赖/安装清单：diff --git a/CMakeLists.txt b/CMakeLists.txt; index eef6626..c054264 100644; --- a/CMakeLists.txt; +++ b/CMakeLists.txt; @@ -18,6 +18,9 @@; cmake_minimum_required(VERSION 3.10); +# NOTICE: force using static libraries; +set(BUILD_SHARED_LIB |
| csrc/cmake/third_party/build/modules/patch/protobuf_25.1_change_version.patch | 静态版本/依赖/安装清单：diff --git a/CMakeLists.txt b/CMakeLists.txt; index 4137ce2..1d9e1ca 100644; --- a/CMakeLists.txt; +++ b/CMakeLists.txt; @@ -79,7 +79,7 @@ if (protobuf_BUILD_SHARED_LIBS); endif (); -set(protobuf_VERSION_STRING "4.25.1"); +set(protobuf_VERS |
| csrc/cmake/third_party/gtest.cmake | CMake函数 ；依赖 GTEST_INCLUDE, GTEST_STATIC_LIBRARY, GTEST_MAIN_STATIC_LIBRARY |
| csrc/cmake/third_party/json.cmake | CMake函数 ；依赖 JSON_INCLUDE |
| csrc/cmake/third_party/makeself-fetch.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/third_party/protobuf.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/third_party/secure_c.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/ut.cmake | CMake函数 register_op_name op_name), add_optiling_ut_modules OP_TILING_MODULE_NAME), add_infershape_ut_modules OP_INFERSHAPE_MODULE_NAME)；目标/生成/安装声明 |
| csrc/scripts/opgen/opgen_standalone.py | 接口 execute, register_parser, main, __init__, run, _validate_inputs; 拒绝 raise ValueError('算子类型和算子名称均不能为空。'); raise ValueError(f"算子类型 '{self.op_type}' 包含无效字符。只允许字母、数字和下划线。") |
| csrc/scripts/opgen/template/CMakeLists.txt | CMake函数 ；目标/生成/安装声明 |
| csrc/scripts/opgen/template/add/CMakeLists.txt | CMake函数 ；目标/生成/安装声明 |
| csrc/scripts/opgen/template/add/examples/test_aclnn_add_example.cpp | 生成模板/接口：int64_t GetShapeSize(const std::vector<int64_t>& shape); int64_t shapeSize = 1;; void PrintOutResult(std::vector<int64_t>& shape, void** deviceAddr); for (int64_t i = 0; i < size; i++) {; const std::vector<T>& hostData, const std::vector<in |
| csrc/scripts/opgen/template/add/op_host/CMakeLists.txt | CMake函数 ；目标/生成/安装声明 |
| csrc/scripts/opgen/template/add/op_host/add_example_def.cpp | 生成模板/接口：class AddExample : public OpDef {; .DataType({ge::DT_FLOAT, ge::DT_INT32}) // 支持数据类型; .DataType({ge::DT_FLOAT, ge::DT_INT32}); .DataType({ge::DT_FLOAT, ge::DT_INT32}) |
| csrc/scripts/opgen/template/add/op_host/add_example_infershape.cpp | 生成模板/接口：static constexpr int64_t IDX_0 = 0;; static ge::graphStatus InferShapeAddExample(gert::InferShapeContext* context); int64_t dim = xShape->GetDim(i); |
| csrc/scripts/opgen/template/add/op_host/add_example_tiling.cpp | 生成模板/接口：const int64_t TILE_NUM = 8;; static ge::graphStatus GetPlatformInfo(gert::TilingContext* context, uint64_t& ubSize, int64_t& coreNum); ge::graphStatus GetShapeAttrsInfo(gert::TilingContext* context, int64_t& totalIdx, ge::DataType& dataType |
| csrc/scripts/opgen/template/add/op_kernel/add_example.cpp | 生成模板/接口：enum class AddExampleTilingKey : uint32_t; __global__ __aicore__ void add_example(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling) |
| csrc/scripts/opgen/template/add/op_kernel/add_example.h | 生成模板/接口：class AddExample; int64_t blockLength_ = 0;; int64_t tileNum_ = 0; |
| csrc/scripts/opgen/template/add/op_kernel/add_example_tiling_data.h | 生成模板/接口：int64_t totalLength;; int64_t tileNum; |
| csrc/scripts/opgen/template/add/op_kernel/add_example_tiling_key.h | 生成模板/接口： |
| csrc/scripts/util/__init__.py | 接口  |
| csrc/scripts/util/build_opp_kernel_static.py | 接口 shell_exec, shell_checkout_key_func, to_upper_camel_case, generate_symbol, parser_generate_symbol, compile_static_library; 拒绝 raise FileExistsError(f'generate_symbol input library error, file <{library_file}> not exists.'); raise Exception(f'Input cpu_aarch<{cpu_aarch}> Error, Please input parase.') |
| csrc/scripts/util/const_var.py | 接口 conv_soc_ver |
| csrc/scripts/util/insert_op_info.py | 接口  |
| csrc/scripts/util/merge_aicpu_info_json.sh | Shell入口 ；参数  |
| csrc/scripts/util/merge_proto.py | 接口 match_op_proto, merge_op_proto, parse_args |
| csrc/scripts/util/modify_gen_aclnn.py | 接口 shell_exec, search_file, modify_gen_aclnn |
| pyproject.toml | 静态版本/依赖/安装清单：[build-system]; requires = [; "attrs",; "cmake>=3.26",; "decorator",; "einops",; "googleapis-common-protos",; "numpy",; "packaging",; "pip",; "pybind11",; "pyyaml",; "scipy",; "pandas",; "pandas-stubs",; "psutil",; "setuptools>=64",; "setup |
| tools/ai_qos/CMakeLists.txt | CMake函数 ；依赖 Python3 COMPONENTS Interpreter Development.Module REQUIRED), pybind11 CONFIG REQUIRED), DSMI_INCLUDE_DIR |

本次仅源码/结构化配置阅读，没有运行上游工具、编译、安装/卸载、环境修改、包上传或NPU；Guide的Host/工具facet不等于完整Operator/外部依赖/运行时验证。


## Catlass只在此固定依赖身份，不递归冒称正文已读

ceac树的csrc/third_party/catlass是mode160000的Git commit指针，指向41bf90da655bba3c66d0acd7e00abe33960ecfd6；.gitmodules的gitcode.com/cann/catlass.git与commit字段一致，branch=master只是上游跟踪提示，不能替代固定commit。本卡没有下载或展开Catlass外库，不把目录当文本计算SHA，也不推其所有模板/设备实现已摄取或支持。消费外库时核真实checkout与需要的接口/Device来源，版本边界不被Main目录名消除。
