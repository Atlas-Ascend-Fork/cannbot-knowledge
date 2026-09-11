---
type: API
title: 卷积格式转换
description: 在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过NZ2ND能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/convolution_format_conversion.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# 卷积格式转换

在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过[NZ2ND](nz2_nd.md)能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：

**图1** NC1HWC0转换为NHWC格式<a name="zh-cn_topic_0000002515830464_fig63620361414"></a>  

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/Fixpipe_NC1HWC0_NHWC.png)


特别的，针对Ascend 950PR/Ascend 950DT产品，还支持Fixpipe指令通过[NZ2DN](nz2_dn.md)能力，将L0C Buffer上数据转为NCHW格式输出。转换示意图如下所示：

**图2**  NC1HWC0转换为NCHW格式<a name="fig188671630134414"></a>  

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/Fixpipe_NC1HWC0_NCHW.png)



<!-- cannbot:related:start -->
## 相关

- [NZ2DN](nz2_dn.md)（`related`）：特别的，针对Ascend 950PR/Ascend 950DT产品，还支持Fixpipe指令通过NZ2DN能力，将L0C Buffer上数据转为NCHW格式输出。转换示意图如下所示：；矩阵搬出时将 NZ 格式矩阵转换为 DN 格式矩阵。通过 FixpipeParamsArch3510 的 config=CFG_COLUMN_MAJOR 开启。。格式转换卡指定 950 的 NZ2DN 输出 NCHW，API 卡补齐列主序开关和 DN stride 参数。
- [NZ2ND](nz2_nd.md)（`related`）：在卷积运算中，L0C Buffer上存放的数据格式为NC1HWC0格式，Fixpipe指令通过NZ2ND能力，支持将L0C Buffer上数据转为NHWC格式输出。转换示意图如下所示：；矩阵搬出时将 NZ 格式矩阵转换为 ND 格式矩阵。通过 Fixpipe/DataCopy 的 config=CFG_ROW_MAJOR 或 nz2ndEn=true 开启。。格式转换卡指定 Fixpipe 的 NZ2ND 能力输出 NHWC，API 卡补齐行主序开关、stride 和目标不重叠合同。
<!-- cannbot:related:end -->
