---
type: "Runbook"
title: DataCopyPad UB→GM 不收 padParams，3 参重载
description: AscendC DataCopyPad 的 UB→GM 方向只有 (gm, ub, DataCopyExtParams) 三参重载；照搬 GM→UB 的第四参 DataCopyPadExtParams 报 no matching function 编译错。
tags: [task.implementation, topic.data_movement.data_copy, topic.implementation.api_layer.basic_api]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# DataCopyPad UB→GM 不收 padParams，3 参重载


## 现象

在实现 ThnnFusedGruCellGrad 算子仓工程的 group 分支 kernel（`op_kernel/arch35/thnn_fused_gru_cell_grad_group.h`，A×R 2D 分核两阶段结构）时，需要在三个位置做 UB→GM 的搬出：Phase 1 末把局部归约树根从 `cacheBuf`（UB）写进 GM workspace（`Phase1OutputToWorkspace`），以及 Phase 2 把 `postBuf`（UB）里的两路 bias 结果写到 GM（`CopyOutBiasDual` 的 part1/part2 两次拷出）。

实现时按 GM→UB 方向的习惯写法给这三处 `AscendC::DataCopyPad` 都传了第四个参数 `DataCopyPadExtParams`（padParams），随后执行标准构建命令：

```bash
( set -o pipefail; cd operators && ./build.sh ThnnFusedGruCellGrad_package )
```

编译失败，报错原文（每个 dtype × tiling 模板实例重复出现）：

```
/workspace/.../op_kernel/arch35/thnn_fused_gru_cell_grad_group.h:212:9: error: no matching function for call to 'DataCopyPad'
/workspace/.../op_kernel/arch35/thnn_fused_gru_cell_grad_group.h:360:9: error: no matching function for call to 'DataCopyPad'
/workspace/.../op_kernel/arch35/thnn_fused_gru_cell_grad_group.h:370:9: error: no matching function for call to 'DataCopyPad'
RuntimeError: Kernel Compilation Error: OpType ThnnFusedGruCellGrad Kernel File .../thnn_fused_gru_cell_grad_apt.cpp!
```

关键判别信号：同一文件里有 4 个 `DataCopyPad` 调用点，报错的 212/360/370 三行**恰好全部是 UB→GM 方向**（dst 为 GlobalTensor、src 为 LocalTensor）；行 332 的 `CopyInWorkspace` 是 GM→UB 方向（dst 为 UB `preRegion_`、src 为 GM `wsGm_`），同样带第四参 padParams 却编译通过。

另注意：构建最先抛出的错误可能是 FATBIN 阶段的 `ld.lld: error: cannot open .../kernel_meta/....o: No such file or directory`——这只是上游 clang 编译失败导致 .o 未生成的下游症状，需要往前翻日志找真正的 C++ 报错行。

## 适用场景

- 工程形态：算子仓开发（ops-registry-invoke 流程，AscendC 模板 kernel，aclnn ST 联调）；任何需要在 kernel 内把 UB 数据拷出到 GM 的场景。
- API 路径：AscendC 基础 API `AscendC::DataCopyPad`（`kernel_operator.h`），配 `DataCopyExtParams` / `DataCopyPadExtParams`。
- 验证过的平台与 CANN 版本：Ascend 950（构建目标 `ThnnFusedGruCellGrad_ascend950`）+ CANN 9.0.0-beta.2（`/home/<user>/Ascend/cann-9.0.0-beta.2`）。与 frontmatter `platforms` 一致。
- 适用粒度：operator_family——DataCopyPad 重载集合是 CANN 基础 API 语义，跨算子一致。
- 路线优先级：recommended_fastpath（UB→GM 一律 3 参调用）。
- 明确不适用/未验证：GM→UB 方向第四参 `DataCopyPadExtParams` 是合法且必需的（本 trace 行 332 的用法编译通过并运行正确）；其他 CANN 版本的重载集合未验证。

## 根因

`DataCopyPad` 的重载集合按搬运方向不对称：UB→GM 方向只提供 3 参重载 `DataCopyPad(GlobalTensor, LocalTensor, DataCopyExtParams)`，不存在带 `DataCopyPadExtParams` 的 4 参形式；padParams（源侧 pad 语义）只在 GM→UB 方向有意义/有重载。

## 解决配方

before（`CopyOutBiasDual` 内，照搬 GM→UB 的 4 参写法，编译错在 360/370 行）：

```cpp
    if (part1 > 0) {
        AscendC::DataCopyExtParams ext;
        ext.blockLen = static_cast<uint32_t>(part1 * elemSz);
        ext.blockCount = 1;
        ext.srcStride = 0;
        ext.dstStride = 0;
        ext.rsv = 0;
        AscendC::DataCopyPadExtParams<D_T> padParams{false, 0, 0, 0};
        AscendC::DataCopyPad(Base::gmInBias_[aOff], Base::postBuf_.template Get<D_T>(), ext, padParams);
    }
    if (part2 > 0) {
        AscendC::DataCopyExtParams ext;
        ext.blockLen = static_cast<uint32_t>(part2 * elemSz);
        ext.blockCount = 1;
        ext.srcStride = 0;
        ext.dstStride = 0;
        ext.rsv = 0;
        AscendC::DataCopyPadExtParams<D_T> padParams{false, 0, 0, 0};
        AscendC::DataCopyPad(Base::gmHidBias_[aOff - biasBoundary],
                             Base::postBuf_.template Get<D_T>()[static_cast<uint32_t>(part1)], ext, padParams);
    }
```

after（去掉 UB→GM 方向的第四参，保留 `DataCopyExtParams` 承载 blockLen/blockCount/stride；同型修复也应用于 212 行的 `Phase1OutputToWorkspace`）：

```cpp
    if (part1 > 0) {
        AscendC::DataCopyExtParams ext;
        ext.blockLen = static_cast<uint32_t>(part1 * elemSz);
        ext.blockCount = 1;
        ext.srcStride = 0;
        ext.dstStride = 0;
        ext.rsv = 0;
        AscendC::DataCopyPad(Base::gmInBias_[aOff], Base::postBuf_.template Get<D_T>(), ext);
    }
    if (part2 > 0) {
        AscendC::DataCopyExtParams ext;
        ext.blockLen = static_cast<uint32_t>(part2 * elemSz);
        ext.blockCount = 1;
        ext.srcStride = 0;
        ext.dstStride = 0;
        ext.rsv = 0;
        AscendC::DataCopyPad(Base::gmHidBias_[aOff - biasBoundary],
                             Base::postBuf_.template Get<D_T>()[static_cast<uint32_t>(part1)], ext);
    }
```

修复后 `./build.sh ThnnFusedGruCellGrad_package` 输出 `SUCCESS` 并生成 `custom_opp_ubuntu_x86_64.run`。

## 设计决策

- 判别方法以"报错行号的方向"为准：同文件混用两个方向时，逐行核对 dst/src 是 GlobalTensor 还是 LocalTensor——报错行清一色落在 UB→GM 方向、GM→UB 方向的 4 参调用不报错，即可定位为方向不对称而非拼写问题。
- 参照系：同工程 base 内核 `CopyOutBias` 的 UB→GM 写法本来就是 3 参形式 `AscendC::DataCopyPad(gmInBias_[aOff], postBuf_.Get<D_T>(), cp)`（blockCount=3 + srcStride/dstStride），且 Branch-0 ST 20/20 通过——修复直接向这一已验证写法看齐。
- 当前方案属 recommended_fastpath：UB→GM 需要"裁掉尾部 garbage lane"时，用 `blockLen=valid 字节数` 表达（如 `aLen_ * sizeof(float)`），不依赖 pad 语义。

## 系统信息

- 工程布局：`operators/ThnnFusedGruCellGrad_package/{op_kernel,op_host,tests}`，构建入口 `operators/build.sh <pkg>`；kernel 源 `op_kernel/arch35/thnn_fused_gru_cell_grad_group.h`（本卡改动文件），共享 VF 链 `op_kernel/arch35/thnn_fused_gru_cell_grad_kernel.h`，base 内核 `op_kernel/arch35/thnn_fused_gru_cell_grad_base.h`（3 参参照写法来源）。
- 工具链：CANN 9.0.0-beta.2（编译器 `compiler/tikcpp`，`asc_op_compile_base` 打包链）；目标 ascend950。

## 预防

- 写 UB→GM 搬出时先默写 3 参签名 `(gm, ub, DataCopyExtParams)`；padParams 只出现在 GM→UB。
- 同文件两个方向混用时，把"方向注释"写在每处 DataCopyPad 上方（本工程 base kernel 即如此），报错时可直接对行核对。
- 见到 `ld.lld: cannot open ....o` 先怀疑上游 C++ 编译失败，用 `grep -iE "error:" | grep -ivE "ld.lld|No such file"` 滤出真实报错。

## 验证信号

本卡验证来自该 group kernel 的首次编译修复轮（开发会话内 `./build.sh` 构建输出）：

- 修复前：`no matching function for call to 'DataCopyPad'` ×3（行 212/360/370）+ `Kernel Compilation Error`（来源平台：950；证据等级：tool_observed）。
- 修复后：同一构建命令输出 `Compile op info cfg successfully` / `SUCCESS`，自解压 run 包生成成功（来源平台：950；证据等级：tool_observed）。

## 失效边界

- GM→UB 方向带 padParams 合法（本 trace 中 `CopyInWorkspace` 以 4 参形式编译通过并参与后续全部 ST 通过）。
- 重载集合验证于 CANN 9.0.0-beta.2 / ascend950；其他 CANN 版本未验证（跨版本迁移时以对应版本头文件为准）。

## 坏实践

- 从 GM→UB 调用复制粘贴后只改指针不改参数个数——本卡 before 即此产物。
- 把 `ld.lld: cannot open *.o` 当作链接/构建系统问题去排查（真实原因在上游编译阶段）。

## 误诊

无（本闭环一次定位一次修复）。

## 未决事项

无。
