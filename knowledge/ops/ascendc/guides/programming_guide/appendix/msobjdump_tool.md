---
type: Guide
title: msobjdump工具
description: 本工具主要针对工程编译生成的算子ELF文件（Executable and Linkable Format）提供解析和解压功能，并将结果信息以可读形式呈现，方便开发者直观获得kernel文件信息。当前支持解析融合编译工程、标准/简易自定义算子工程，以及Kernel直调工程生成的相关产物。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/msobjdump_tool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# msobjdump工具

本工具主要针对工程编译生成的算子ELF文件（Executable and Linkable Format）提供解析和解压功能，并将结果信息以可读形式呈现，方便开发者直观获得kernel文件信息。当前支持解析融合编译工程、标准/简易自定义算子工程，以及Kernel直调工程生成的相关产物。
## 工具安装
1.  安装msobjdump工具。
工具跟随CANN软件包发布（参考环境准备完成CANN安装），其路径默认为${INSTALL_DIR}/tools/msobjdump，其中${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。
2.  设置环境变量。
-   root用户安装Ascend-cann-toolkit包时
-   非root用户安装Ascend-cann-toolkit包时
3.  检查工具是否安装成功。
执行如下命令，若能正常显示--help或-h信息，则表示工具环境正常，功能可正常使用。
## 命令格式
-   解析ELF文件的命令
参数说明
参数（区分大小写）：可选/必选：说明
--dump-elf ，-d：必选：解析ELF文件中包含的device信息，如文件名、文件类型、文件长度、符号表等，并终端打屏显示。`表示待解析ELF文件路径，如/home/op_api/lib_api.so。支持两种打印模式：简单打印：默认仅打印部分device信息。全量打印：与--verbose配套使用，开启全量device信息打屏显示。不同工程打印字段信息不同，具体参见表4和表6。
--verbose，-V：可选：必须与--dump-elf配套使用，用于开启ELF文件中全量打印device信息功能。
-   解压ELF文件的命令
参数说明
参数（区分大小写）：可选/必选：说明
--extract-elf ，-e：必选：解压ELF文件中包含的device信息，并按解析结果落盘到输出路径下。表示待解压ELF文件路径，如/home/op_api/lib_api.so。默认路径：解压结果文件默认落盘到当前执行路径下。自定义路径：可与--out-dir配套使用，设置落盘路径。
--out-dir ，-o：可选
