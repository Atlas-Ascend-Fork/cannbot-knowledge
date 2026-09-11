---
type: "Runbook"
title: kernel binary .o 定位：build/packages 不存在
description: CPack 日志里的 ./packages/ 路径是 .run 自解包 staging 内部布局；常驻交付 kernel binary 在 build/ascendc_kernels/binary/<soc>/<op>/，安装后在 $ASCEND_OPP_PATH/vendors/<OpType>/ 下。
tags: [task.debugging, topic.compilation]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# kernel binary .o 定位：build/packages 不存在


## 现象

在对一个按 proto.md 改造为原型一致接口桩的 ACLNN 自定义算子工程（AscendC，ops-registry-invoke 算子仓流程，目标 ascend950）做编译验收时，`cd operators && ./build.sh <OpType>_package` 退出码 0，CPack 打包日志里清楚列出了交付产物的内部路径，例如：

```
Adding files to archive named "custom_opp_ubuntu_x86_64.run"...
./packages/vendors/ThnnFusedGruCellGrad/op_impl/ai_core/tbe/kernel/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_35a6f98eb48c771cd0e8edb80bf279f6.o
./packages/vendors/ThnnFusedGruCellGrad/op_api/lib/libcust_opapi.so
```

随后要对 kernel binary 逐枚执行 strings 检查，按日志里的路径拼接 `build/packages/...` 去找 .o，直接落空（同一命令里两条 ls 各报一次）：

```
ls build/packages/vendors/ThnnFusedGruCellGrad/op_impl/ai_core/tbe/kernel/ascend950/thnn_fused_gru_cell_grad/*.o
ls: cannot access 'build/packages/vendors/ThnnFusedGruCellGrad/op_impl/ai_core/tbe/kernel/ascend950/thnn_fused_gru_cell_grad/*.o': No such file or directory
count=0
```

改用 `find <package>/build -name '*.o'` 全量枚举，返回 28 枚 .o，分布在四类位置——只有其中 3 枚才是最终交付的 kernel binary，其余是 host 侧 CMake 对象、kernel_meta 中间产物和 CPack staging 副本，混在一起很容易拿错。其中交付 kernel binary 的命中（输出 verbatim，路径中工作区前缀以 … 缩写）：

```
…/operators/ThnnFusedGruCellGrad_package/build/ascendc_kernels/binary/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_bf6eb06d4164f1cf9f51a4b1391902a1.o
…/operators/ThnnFusedGruCellGrad_package/build/ascendc_kernels/binary/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_35a6f98eb48c771cd0e8edb80bf279f6.o
…/operators/ThnnFusedGruCellGrad_package/build/ascendc_kernels/binary/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_f44a71c3e89dd2fadd786cc5ca9ee63a.o
```

安装目录查询（`find $ASCEND_OPP_PATH/vendors/ThnnFusedGruCellGrad -name '*.o'`，输出 verbatim，用户名已脱敏）：

```
/home/<user>/Ascend/cann-9.0.0-beta.2/opp/vendors/ThnnFusedGruCellGrad/op_impl/ai_core/tbe/kernel/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_35a6f98eb48c771cd0e8edb80bf279f6.o
/home/<user>/Ascend/cann-9.0.0-beta.2/opp/vendors/ThnnFusedGruCellGrad/op_impl/ai_core/tbe/kernel/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_bf6eb06d4164f1cf9f51a4b1391902a1.o
/home/<user>/Ascend/cann-9.0.0-beta.2/opp/vendors/ThnnFusedGruCellGrad/op_impl/ai_core/tbe/kernel/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_f44a71c3e89dd2fadd786cc5ca9ee63a.o
```

## 适用场景（必填 — 检索前的第一道滤网）

- 工程形态：aclnn / ops-registry-invoke 算子仓开发与验收（CMake + op_build + CPack External 自定义算子包流程）；对 kernel binary 做 strings/nm/objdump/数量核对等产物级检查的场景。
- API 路径：`operators/build.sh <OpType>_package` → CMake 目标 `ascendc_kernels`/`binary` → CPack External 产出 `custom_opp_ubuntu_x86_64.run` → run 包安装到 `$ASCEND_OPP_PATH/vendors/<OpType>/`。
- 验证过的平台与 CANN 版本：ascend950（注册平台名 950）+ CANN cann-9.0.0-beta.2（`$ASCEND_OPP_PATH=/home/<user>/Ascend/cann-9.0.0-beta.2/opp`）。
- 适用粒度（transfer_scope）：platform_wide——凡走 op_build + CPack 的自定义算子仓产物布局一致，与具体算子无关。
- 路线优先级：recommended_fastpath（直接按本文三处 canonical 路径定位，或一次 find 后按路径模式归类）。
- 明确不适用 / 未验证场景：GEIR/TTK 等非 CPack 打包流程；未验证场景——其他 CANN 版本 / 其他 SoC 的产物布局差异。

## 判别方法

三层定位（按需取用）：

1. **常驻交付 kernel binary**（做完 build 后一直存在，做产物级检查用这批）：
   `<package>/build/ascendc_kernels/binary/<soc>/<op>/<OpType>_<32位hash>.o`，每个 dtype 组合恰好一枚（本例 fp32/fp16/bf16 三组合 → 3 枚）。
2. **CPack staging**（对应 CPack 日志里 `./packages/...` 相对路径的真实落点，位于自解包目录内）：
   `<package>/build/_CPack_Packages/Linux/External/custom_opp_ubuntu_x86_64.run/packages/vendors/...`。
3. **run 包安装目录**（执行过 run 包安装后）：
   `$ASCEND_OPP_PATH/vendors/<OpType>/op_impl/ai_core/tbe/kernel/<soc>/<op>/`。

用 `find <package>/build -name '*.o'` 全量枚举时，按下表归类判别，避免拿错：

| 类别 | 路径模式 | 本例数量 | 是否交付物 |
|---|---|---|---|
| 交付 kernel binary | `build/ascendc_kernels/binary/<soc>/<op>/<OpType>_<hash>.o` | 3 | 是 |
| CPack staging 副本 | `build/_CPack_Packages/Linux/External/*.run/packages/vendors/...` | 3 | 是（同上 3 枚的打包副本） |
| host 侧 CMake 对象 | `build/CMakeFiles/cust_optiling_obj|cust_proto_obj|cust_opapi_obj/...` | 10 | 否 |
| kernel_meta 中间产物 | `build/<OpType>_<soc>/kernel_N/kernel_meta_*/kernel_meta/*.o`（含 `*_infer_channel_dav-c310-cube_0.o`、`*_vec_0.o`、`*_0.o`） | 12 | 否 |

安装目录单独查：`find $ASCEND_OPP_PATH/vendors/<OpType> -name '*.o'`。

## 设计决策

- 诊断路线选择：先按 CPack 日志相对路径猜 `build/packages`（实测失败），再改用 `find` 全量枚举后按路径模式归类——一次 find 即给出全部落点，无需逐个读 CMake install/CPack 配置推导。备选（读 CMakeLists 的 install 规则推导产物路径）未采用，成本高于一次 find。当前方案属 recommended_fastpath。
- 交付物判别以路径模式（`ascendc_kernels/binary/<soc>/<op>/`）而非文件数量为准：`.o` 总数随 host 目标数、dtype 组合数、kernel_meta 结构变化，只有路径模式稳定。

## 系统信息

- 构建机：x86_64 Ubuntu，GCC 13.3.0，CMake + op_build + CPack External。
- 目标 SoC：ascend950（arch35）；CANN cann-9.0.0-beta.2，`$ASCEND_OPP_PATH=/home/<user>/Ascend/cann-9.0.0-beta.2/opp`。
- 目录布局：`operators/<OpType>_package/{op_host,op_kernel,op_graph,tests}`；`build.sh` 在 `operators/` 下以包名为参数调用。
- 相关文件（与本次事件流实际读写/枚举一一对应）：
  - `build/ascendc_kernels/binary/ascend950/thnn_fused_gru_cell_grad/ThnnFusedGruCellGrad_<hash>.o` ×3（交付 kernel binary）
  - `build/_CPack_Packages/Linux/External/custom_opp_ubuntu_x86_64.run/packages/vendors/...`（staging）
  - `$ASCEND_OPP_PATH/vendors/ThnnFusedGruCellGrad/op_impl/ai_core/tbe/kernel/ascend950/thnn_fused_gru_cell_grad/` ×3（安装后）
  - `build/<OpType>_ascend950/kernel_{0,1,2}/kernel_meta_*/kernel_meta/`（中间产物，勿当交付物）

## 完整代码

定位/枚举探针（可执行；`<pkg>` = 算子包根目录，`<OpType>`/`<op>` = PascalCase/snake_case 算子名）：

```bash
# 0) 反例：按 CPack 日志相对路径拼接（预期失败，该目录常驻不存在）
ls <pkg>/build/packages/vendors/<OpType>/op_impl/ai_core/tbe/kernel/ascend950/<op>/*.o

## 1) 常驻交付 kernel binary（每 dtype 组合一枚，hash 后缀）
ls <pkg>/build/ascendc_kernels/binary/ascend950/<op>/

## 2) CPack staging（CPack 日志 ./packages/... 的真实落点）
find <pkg>/build/_CPack_Packages -name '*.o'

## 3) run 包安装目录
find $ASCEND_OPP_PATH/vendors/<OpType> -name '*.o'

## 4) 全量枚举 + 人工按路径模式归类（交付物/主机对象/kernel_meta 中间产物）
find <pkg>/build -name '*.o' | sort
```

## 预防

- 不要按 CPack 日志的 `./packages/...` 相对路径去 `build/packages/` 下找产物——那是 `.run` 自解包内部布局，实体在 `_CPack_Packages/Linux/External/*.run/packages/` staging 内。
- 对 kernel binary 做 strings/nm/objdump/计数检查前，先 `find build -name '*.o'` 枚举并按 `ascendc_kernels/binary/<soc>/<op>/` 路径模式筛出交付物，避免把 kernel_meta 的 `*_infer_channel_dav-c310-cube_0.o` 或 host 侧 CMake .o 计入交付物口径。
- 验收口径若要求「.o 数量 == dtype 组合数」，计数对象应是第 1 类交付物（或第 3 类安装物），不是 find 的全部结果。

## 验证信号

以下信号来自一次自定义算子接口桩工程的编译验收：亲自执行 build.sh、按日志路径 ls、find 全量枚举与安装目录查询取得。

- `./build.sh <OpType>_package` 退出码 0（BUILD_EXIT=0），CPack 日志列出 `./packages/vendors/.../<OpType>_<hash>.o` 等包内文件（来源平台：950；证据等级：tool_observed）
- `ls build/packages/vendors/.../*.o` → `No such file or directory`，count=0（来源平台：950；证据等级：tool_observed）
- `find <pkg>/build -name '*.o'` 返回 28 枚：交付 kernel binary 3 枚位于 `build/ascendc_kernels/binary/ascend950/<op>/`；staging 副本 3 枚位于 `build/_CPack_Packages/Linux/External/custom_opp_ubuntu_x86_64.run/packages/vendors/...`；host CMake 对象 10 枚；kernel_meta 中间产物 12 枚（来源平台：950；证据等级：tool_observed）
- `find $ASCEND_OPP_PATH/vendors/<OpType> -name '*.o'` 返回与交付物相同的 3 枚已安装 .o（来源平台：950；证据等级：tool_observed）
- 交付 .o 数量 3 == proto dtype 组合数 3（fp32/fp16/bf16，构建日志 `[ascend950] Generating <OpType>_<hash>` 恰 3 次）（来源平台：950；证据等级：tool_observed）

## 失效边界

- 观察来自单次构建（CANN cann-9.0.0-beta.2、ascend950、CPack External 流程）；其他 CANN 版本或其他打包方式（直接 make install、非 CPack）的布局可能不同——未验证，推断可迁移。
- `kernel_N` 中间目录数量随 dtype 组合数变化（本例 3 组合 → kernel_0/1/2）；`<OpType>_<hash>` 的 hash 由 op_build 按源内容生成，跨算子/跨内容不同，不可当稳定文件名引用。
- `build/packages` 是否会在某些时序（如 CPack 中途、未清理的旧构建）下以实体目录存在，未验证；本文只证实「本次 build 完成后该路径不存在、交付物在 ascendc_kernels/binary 下」。

## 坏实践

- 按 CPack 日志相对路径 `./packages/...` 拼出 `build/packages/...` 直接找产物 → `No such file or directory`（本例实测踩坑）。
- `find build -name '*.o'` 后不归类，把 kernel_meta 的 `*_infer_channel_dav-c310-cube_0.o`/`*_0.o` 或 host 侧 CMake .o 当成交付 kernel binary 去做 strings/符号检查 → 计数与结论口径错误。

## 误诊

- 本次验收中曾把一次交错执行的两条 `ls`（op_host+op_kernel 一条、op_graph 一条）输出误读为「op_kernel 下含有 legacy_v1_infer_example.cpp / proto.cc 等文件」，后续 `head` 该路径报不存在后重新 `ls -la` 才纠正（这些文件实际在 op_graph）——多目录并列 ls 时输出按目录分段交错，读结果须按目录头归属逐段核对，勿凭印象归目录。

## 未决事项

- `build/packages` 路径在何种流程/时序下会以实体目录出现未验证（如需绝对排除误用，可补一次 CPack 中途态观察）。
- 其他 CANN 版本 / 其他 SoC（如 a2/a3）下同名产物路径是否一致未验证。
