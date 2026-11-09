---
type: Guide
title: vLLM Ascend原生包安装：版本检查、文件布局与多版本生命周期
description: 区分Csrc版本声明、CANN包前缀校验、Docker/pyproject依赖及安装器filelist/多版本状态，定位ops-transformer/opapi路径、环境与清理入口；不执行或推导目标机兼容。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/version.info
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/Dockerfile.310p.openEuler
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/Dockerfile.a3.openEuler
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/Dockerfile.a5.openEuler
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/Dockerfile.openEuler
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/build_empty_package.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/makeself_built_in.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/makeself_custom.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/cmake/package.cmake
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/cfg/path.cfg
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/filelist.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/merge_binary_info_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/packer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/pkg_parser.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/utils/comm_log.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/utils/funcbase.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/utils/pkg_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/py/version_info.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/check_version_required.awk
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/cleanup.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/common_func.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/common_func_v2.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/common_installer.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/common_interface.csh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/common_interface.fish
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/common_interface.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/install_common_parser.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/multi_version.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/script_operator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/version_cfg.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/common/sh/version_compatiable.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/latest_manager/scripts/filelist.csv
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/latest_manager/scripts/install.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/latest_manager/scripts/manager.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/latest_manager/scripts/manager_func.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/latest_manager/scripts/uninstall.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/latest_manager/scripts/version.info
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/module/ascend/EngineeringCommon.xml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/module/ascend/EngineeringFiles.xml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/module/ascend/OpsTransformer.xml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/module/ascend/OpsTransformerInc.xml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/ops_transformer.xml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/cleanup.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/empty_package_scripts/install.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/help.info
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/install.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/opp_common.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/opp_custom_install.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/opp_custom_uninstall.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/opp_install.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/opp_uninstall.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/uninstall.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/ops_transformer/scripts/ver_check.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/scripts/package/package.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/mooncake_installer.sh
  role: implementation
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

# vLLM Ascend原生包安装：版本检查、文件布局与多版本生命周期

## 版本字段不是同一层的兼容证明

csrc/version.info写Version=9.1.0、version_dir=cann及runtime/opbase/asc-devkit/GE/metadef/bisheng/TBE/asc-tools等>=9.1.0依赖。这是源包构建输入，不是本机安装身份。latest-manager另有Version=45，它是管理脚本版本，不能当CANN版本。

check_version_compatible.py读取Version=行并去掉末个点分段后比较CANN包与code前缀相等，缺文件/缺版本/前缀不同失败；这不同于version.info的>=声明及包安装器自身的版本区间机制。何处实际调用哪层检查必须沿caller核对，不能仅从9.1源声明与9.2镜像并存就断言编译失败或兼容通过。

四份openEuler Dockerfile将CANN9.2.0_20261022115200、vLLM tag0.32.0/可选commit、不同SOC、TorchNPU日期包等作为构建输入；A2/A3/A5还列出FLA、Triton、Mooncake/Memfabric等来源，310P为独立配方。它们与manylinux wheel、CI cache image和pyproject build-isolation要求分别记录最终resolved SHA/digest/包版本，不合成为跨平台推荐栈，也不从ARG默认推实际运行版本。

## XML与filelist决定交付路径和安装类型

EngineeringCommon/Files与OpsTransformer/Inc XML区分目标环境bin/include/lib64/conf/devlib、run/devel/all、optional AICPU、opgraph/opapi/tiling及install owner/mode/softlink等字段。libopapi_transformer.so与相应头的交付路径不是任意Python site-package布局；安装成功后仍须核实际加载路径和ABI。

package.py/pkg_parser/packer将配置、环境/架构、feature/chip与多版本选项编成文件清单及makeself包，未知操作、压缩或filelist类型/嵌套路径错误可失败。filelist的feature/chip要求set，softlink字段要求list；静态manifest存在不证明所有payload已生成、哈希匹配或安装到预期目录。

## 安装、升级、卸载与环境是不同状态转换

ops_transformer安装器提供full、upgrade、uninstall、install-path/install-for-all/quiet等入口，内部检查路径、版本与已有安装状态，再做文件、权限、信息记录、环境和相对软链。latest-manager维护版本引用与latest/包级链接，version_cfg、multi_version及公共parser共同参与；不能只改一个软链就推多版本管理状态正确。

common_interface.sh对非root的custom data/conf配置展开路径并创建目录，path.cfg使用用户HOME下Ascend/latest；它的Python检查枚举3.7至3.12。此处是安装脚本自己的支持检查，不与上层vLLM/Python依赖自动等价。自定义/内置包的install/upgrade/uninstall也不是同一路径，卸载后环境和其他版本引用仍需核对。

两个普通cleanup.sh实际执行rm -rf当前工作目录，因而只属于专用打包staging的清理协议，不是可直接运行的资料探针或通用卸载命令。本次未执行任何安装、删除、权限/环境修改；静态版本、包布局、toolchain、实际加载和NPU数值分别待验证。


## 固定源码职责与有界接口矩阵

下表为全文件结构读取后的接口/参数/拒绝条件摘选，不是完整实现复制，也不代表每个分支、外部工具或Device算法已展开。精确范围与阅读方式在来源行中记录；按目标任务回到固定实现核对。

| 来源 | 已读职责或接口差异 |
| --- | --- |
| csrc/version.info | 静态版本/依赖/安装清单：Version=9.1.0; version_dir=cann; required_package_runtime_version=">=9.1.0"; required_package_opbase_version=">=9.1.0"; required_package_asc-devkit_version=">=9.1.0"; required_package_ge-compiler_version=">=9.1.0"; required_package_metadef_ |
| Dockerfile.310p.openEuler | 镜像/参数 FROM swr.cn-north-12.myhuaweicloud.com/atlas_inference/cann:9.2.0_20261022115200-310p-openeuler24.03-py3.12; ARG VLLM_TAG=v0.32.0; ARG VLLM_COMMIT=""; ARG SOC_VERSION="ascend310p1" |
| Dockerfile.a3.openEuler | 镜像/参数 FROM swr.cn-north-12.myhuaweicloud.com/atlas_inference/cann:9.2.0_20261022115200-a3-openeuler24.03-py3.12; ARG VLLM_TAG=v0.32.0; ARG VLLM_COMMIT=""; ARG SOC_VERSION="ascend910_9391" |
| Dockerfile.a5.openEuler | 镜像/参数 FROM swr.cn-north-12.myhuaweicloud.com/atlas_inference/cann:9.2.0_20261022115200-950-openeuler24.03-py3.12; ARG VLLM_TAG=v0.32.0; ARG VLLM_COMMIT=""; ARG SOC_VERSION="ascend950dt_9582" |
| Dockerfile.openEuler | 镜像/参数 FROM swr.cn-north-12.myhuaweicloud.com/atlas_inference/cann:9.2.0_20261022115200-910b-openeuler24.03-py3.12; ARG VLLM_TAG=v0.32.0; ARG VLLM_COMMIT=""; ARG SOC_VERSION="ascend910b1" |
| csrc/cmake/build_empty_package.cmake | CMake函数 cpack_empty_package)；目标/生成/安装声明 |
| csrc/cmake/makeself_built_in.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/makeself_custom.cmake | CMake函数 ；目标/生成/安装声明 |
| csrc/cmake/package.cmake | CMake函数 pack_custom), pack_tiling_sink), pack_built_in)；目标/生成/安装声明 |
| csrc/scripts/package/common/cfg/path.cfg | 静态版本/依赖/安装清单：CUSTOM_DATA_PATH=$HOME/Ascend/latest/data/; CUSTOM_CONF_PATH=$HOME/Ascend/latest/conf/ |
| csrc/scripts/package/common/py/filelist.py | 接口 create_file_item, soft_links_to_string, file_item_to_string, get_filelist_header_string, get_soft_links_not_in_common_paths, fill_is_common_path; 拒绝 raise FilelistError(f'found nested paths {item} and {base_item}!'); raise TypeError('The feature parameter should be a set.') |
| csrc/scripts/package/common/py/merge_binary_info_config.py | 接口 load_json_file, save_json_file, update_config, parse_args, main |
| csrc/scripts/package/common/py/packer.py | 接口 remove_ascend, get_func_name, get_compress_tool, get_compress_format, compose_makeself_command, create_makeself_pkg_params_factory; 拒绝 raise CompressError(package_name) |
| csrc/scripts/package/common/py/pkg_parser.py | 接口 parse_os_arch, replace_env, parse_package_info, parse_package_attr_by_args, parse_package_attr, render_cann_version; 拒绝 raise ParseOsArchError(); raise IllegalVersionDir(f'无效的预发布版本: {pre_release}') |
| csrc/scripts/package/common/py/utils/comm_log.py | 接口 cilog_get_timestamp, cilog_print_element, cilog_logmsg, cilog_error, cilog_warning, cilog_info |
| csrc/scripts/package/common/py/utils/funcbase.py | 接口 constant, dispatch, pipe, identity, invoke, side_effect |
| csrc/scripts/package/common/py/utils/pkg_utils.py | 接口 flatten, merge_dict, star_pipe, swap_args, conditional_apply, pairwise; 拒绝 raise PackageConfigError(f'Not allow to config {feature_type} empty.'); raise PackageConfigError(f'Not allow to config {feature_type} all.') |
| csrc/scripts/package/common/py/version_info.py | 接口 is_version_number, get_version_dir, is_multi_version, __init__, __init__, __init__; 拒绝 raise ParseVersionFailed(); raise VersionFormatNotMatch() |
| csrc/scripts/package/common/sh/check_version_required.awk | Shell入口 ；参数  |
| csrc/scripts/package/common/sh/cleanup.sh | Shell入口 ；参数  |
| csrc/scripts/package/common/sh/common_func.inc | Shell入口 comm_init_log, _comm_compose_log_msg, _comm_echo_log_msg, comm_echo；参数 --docker-root, --feature, --feature-type, --help, --install-for-all |
| csrc/scripts/package/common/sh/common_func_v2.inc | Shell入口 log, __length_list, __index_list, __remove_item_in_list；参数 --dereference, --relative |
| csrc/scripts/package/common/sh/common_installer.inc | Shell入口 notify_latest_manager_create_version_softlink, notify_latest_manager_remove_latest_softlink；参数 --version-dir |
| csrc/scripts/package/common/sh/common_interface.csh | Shell入口 ；参数 --only-delimited |
| csrc/scripts/package/common/sh/common_interface.fish | Shell入口 ；参数 --only-delimited |
| csrc/scripts/package/common/sh/common_interface.sh | Shell入口 mk_custom_path, py_version_check；参数 --only-delimited, --version |
| csrc/scripts/package/common/sh/install_common_parser.sh | Shell入口 __pkg_in_pkgs, __block_in_blocks, __remove_pkg_in_pkgs, __sort_blocks；参数 --add-cann-uninstall, --add-env-rc, --add-pkg-blocks, --arch, --check |
| csrc/scripts/package/common/sh/multi_version.inc | Shell入口 create_version_dir, check_version_install, install_latest_manager, uninstall_latest_manager_for_upgrade；参数 --create-package-latest-softlink, --docker-root, --increment, --install-for-all, --install-path |
| csrc/scripts/package/common/sh/script_operator.inc | Shell入口 __check_param, __set_userpath, get_setenv_path_regex, __create_setenv_file；参数  |
| csrc/scripts/package/common/sh/version_cfg.inc | Shell入口 __index_list_by_cut, get_version_cfg_path, get_version_cfg_new_path, parse_cfg_line；参数  |
| csrc/scripts/package/common/sh/version_compatiable.inc | Shell入口 get_package_compat_version, get_formal_package_name, get_informal_package_name, _get_required_packages；参数  |
| csrc/scripts/package/latest_manager/scripts/filelist.csv | 静态版本/依赖/安装清单：module,operation,relative_path_in_pkg,relative_install_path,is_in_docker,permission,owner:group,install_type,softlink,feature,is_common_path,configurable,hash,block,pkg_inner_softlink,chip; NA,mkdir,NA,manager,TRUE,550,\\$username:\\$usergr |
| csrc/scripts/package/latest_manager/scripts/install.sh | Shell入口 ；参数 --install, --install-path, --package, --simple-install, --upgrade |
| csrc/scripts/package/latest_manager/scripts/manager.sh | Shell入口 ；参数 --chip, --docker-root, --feature, --filelist, --increment |
| csrc/scripts/package/latest_manager/scripts/manager_func.sh | Shell入口 get_manager_refs, manager_refs_exists, remove_manager_refs, inc_manager_refs；参数 --create-latest-softlink, --docker-root, --install-path, --install_for_all, --latest-dir |
| csrc/scripts/package/latest_manager/scripts/uninstall.sh | Shell入口 ；参数 --package, --simple-uninstall, --uninstall, --upgrade, --usergroup |
| csrc/scripts/package/latest_manager/scripts/version.info | 静态版本/依赖/安装清单：Version=45 |
| csrc/scripts/package/module/ascend/EngineeringCommon.xml | 打包字段 block {'name': 'EngineeringCommon', 'install_own': '$username:$usergroup', 'install_mod': '440', 'install_type': 'all'}；节点 block, dir_info, path |
| csrc/scripts/package/module/ascend/EngineeringFiles.xml | 打包字段 block {'name': 'EngineeringFiles', 'install_own': '$username:$usergroup', 'install_mod': '440', 'install_type': 'all'}；节点 block, file_info, file |
| csrc/scripts/package/module/ascend/OpsTransformer.xml | 打包字段 block {'name': 'OpsTransformer', 'copy_type': 'delivery', 'src_path': '', 'dst_path': '', 'install_path': '', 'install_own': '$username:$usergroup', 'install_mod': '550', 'install_type': 'run;devel'}；节点 block, dir_info, path, file_info, file |
| csrc/scripts/package/module/ascend/OpsTransformerInc.xml | 打包字段 block {'name': 'OpsTransformerInc', 'copy_type': 'delivery', 'src_path': '', 'dst_path': '', 'install_path': '', 'install_own': '$username:$usergroup', 'install_mod': '550', 'install_type': 'all', 'pkg_feature': 'opp_binary'}；节点 block, file_info, file |
| csrc/scripts/package/ops_transformer/ops_transformer.xml | 打包字段 config {'name': 'ops_transformer', 'copy_type': 'delivery', 'src_path': 'lib/', 'dst_path': 'ops_transformer', 'install_type': 'all', 'install_mod': '550', 'install_own': '$username:$usergroup'}；节点 config, package_info, product_name, chip_name, func_name, suffix, install_script, help, cleanup, generate_info, OPS_TRANSFORMER_VERSION, OPS_TRANSFORMER_TIMESTAMP, os, os_version, arch, file_info, file, block_info, block, dir_info, path |
| csrc/scripts/package/ops_transformer/scripts/cleanup.sh | Shell入口 ；参数  |
| csrc/scripts/package/ops_transformer/scripts/empty_package_scripts/install.sh | Shell入口 getdate, logandprint；参数  |
| csrc/scripts/package/ops_transformer/scripts/help.info | 静态版本/依赖/安装清单：--full Install full mode; --install-path=<path> Install product to specific dir path; --install-for-all Install for all user; --quiet Quiet install mode, skip human- |
| csrc/scripts/package/ops_transformer/scripts/install.sh | Shell入口 startlog, exitlog, get_installed_info, clean_before_reinstall；参数 --docker-root, --full, --help, --input-path, --install-for-all |
| csrc/scripts/package/ops_transformer/scripts/opp_common.sh | Shell入口 getdate, logandprint, createrelativelysoftlink, createOpapiLatestSoftlink；参数 --relative-to |
| csrc/scripts/package/ops_transformer/scripts/opp_custom_install.sh | Shell入口 ；参数 --install-path, --latest-dir, --version-dir |
| csrc/scripts/package/ops_transformer/scripts/opp_custom_uninstall.sh | Shell入口 ；参数 --install-path, --latest-dir, --version-dir |
| csrc/scripts/package/ops_transformer/scripts/opp_install.sh | Shell入口 get_opts, init_install_env, log_with_errorlevel, get_installed_info；参数 --chip, --docker-root, --feature, --install, --install_for_all |
| csrc/scripts/package/ops_transformer/scripts/opp_uninstall.sh | Shell入口 get_opts, get_docker_install_path, log_with_errorlevel, check_directory_exist；参数 --docker-root, --package, --recreate-softlink, --remove-install-info, --uninstall |
| csrc/scripts/package/ops_transformer/scripts/uninstall.sh | Shell入口 getdate, logandprint；参数 --aa, --install-path, --quiet, --uninstall |
| csrc/scripts/package/ops_transformer/scripts/ver_check.sh | Shell入口 getdate, logandprint, check_path_pre, select_last_dir_component；参数  |
| csrc/scripts/package/package.py | 接口 get_comments, get_compress_cmd, make_parse_option, generate_info_content, generate_version_header_content, generate_customized_file; 拒绝 raise CompressError(package_name.getvalue()); raise UnknownOperateTypeError(f'unknown operate type {operate_type}') |

本次仅源码/结构化配置阅读，没有运行上游工具、编译、安装/卸载、环境修改、包上传或NPU；Guide的Host/工具facet不等于完整Operator/外部依赖/运行时验证。


## Mooncake依赖脚本的目录、版本与实际副作用

mooncake_installer.sh把启动时pwd作为REPO_ROOT，默认Go1.23.8与yalantinglibs0.5.6；--yes只省交互，不是只读或预检模式。apt/yum分支安装系统依赖，apt还移除OpenMPI；yum分支额外源码构建yaml-cpp。后续构建安装yalantinglibs、处理submodule、写/usr/local/go并可能追加用户bashrc PATH，均是实际环境修改。本次没有运行它。

目录存在时clone helper直接跳过，不验证revision；yum分支使用thirdparties目录也需要前置环境核对。submodule流程只以首项的.git文件/目录判断已初始化，未证明全部模块都处于所需commit；缺.gitmodules直接失败。Go仅识别aarch64/x86_64映射arm64/amd64。具体下载/构建检查与末尾“Installation Complete”打印不能替代库版本、linker路径、Mooncake初始化或传输业务验收；它也不自动安装/证明目标connector全部兼容。
