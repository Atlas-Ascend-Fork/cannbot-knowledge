---
type: API
title: Attr（OpDef）
description: 注册算子属性参数。 当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Attr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Attr

## 功能说明
注册算子属性参数。
当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。
## 函数原型
## 参数说明
## 返回值说明
算子属性定义，OpAttrDef请参考OpAttrDef。
## 约束说明
Attr属性名不能与以下python关键字及内置变量名相同，否则会导致未定义错误。
-   常见python关键字参考
and、 as、 assert、 break、 class、 continue、 def、 del、 elif、 else、 except、 finally、 for、 from、 global、 if、 import、 in、 is、 lambda、 not、 or、 pass、 raise、 return、 try、 while、 with、 yield、 False、 None、 True、 nonlocal、 arg。
-   内置变量名
__inputs__、 __outputs__、 __attrs__、 options、 bisheng、 bisheng_path、 tikcpp_path、 impl_mode、 custom_compile_options、 custom_all_compile_options、 soc_version、 soc_short、 custom_compile_options_soc、 custom_all_compile_options_soc、 origin_func_name、 ascendc_src_dir_ex、 ascendc_src_dir、 ascendc_src_file、 src、 op_type、 code_channel、 op_info、 compile_op、 get_code_channel、 result、 isinstance、 attr、 get_current_build_config、 _build_args、 get_dtype_fmt_options、 shutil、 os、 get_kernel_source、ascendc_api_version_header_path、ascendc_api_version_file、ascendc_api_version、re。
