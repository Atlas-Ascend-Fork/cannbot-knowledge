---
type: Guide
title: AscendC 编译缓存：确定性有效等级与两层缓存字段
description: 解释后端激活如何给FX与AOTAutograd缓存细节加入NPU有效等级，并区分字段记录、图失效和模型数值保证。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/deterministic_cache.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
created_at: '2026-11-10T12:07:13Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# AscendC 编译缓存：确定性有效等级与两层缓存字段

## 固定主线与范围

依据 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `deterministic_cache.py`、AscendC后端激活入口及确定性getter。发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 缺少同路径 `deterministic_cache.py`，不把主线patch回推到该发布版；也不据缺路径否定其他版本的缓存机制。

这里只记录实际字段写入和调用边界，没有构造缓存对象、加载缓存、编译模型或验证设备；整卡未知平台，保持 `draft`、空列表。确定性等级的产品、CANN门槛与公开配置仍按[set_deterministic_level](../../../../training/apis/torch_npu/set_deterministic_level.md)核对。

## 后端激活直接安装patch

`_BACKEND_LOADERS` 将精确字符串 `ascendc` 映射到 `_load_ascendc_backend()`；该loader先调用 `patch_npu_deterministic_level_cache_keys()`，再导入AscendC后端。不是仅定义但没有入口的辅助函数。

patch保存原 `FxGraphHashDetails.__init__` 和 `AOTAutogradCacheDetails.__init__`，分别包装后替换；类上的标志避免重复安装。包装仍先执行原构造函数，没有在此删除上游已有缓存细节。

每次构造这些细节时，只有环境值 `TORCHINDUCTOR_NPU_BACKEND == "ascendc"`，才额外设置 `self.npu_deterministic_level = torch_npu.npu._get_deterministic_level()`。此判断没有strip或大小写归一化，不能把类似拼写当作同一门控；其他后端也不能仅因patch已安装就假定拥有相同字段。

## 记录的是同步后的有效等级

该字段使用整数等级，不是简单记录 `are_deterministic_algorithms_enabled()` 的布尔值。有效等级不同的状态，不应仅凭布尔值都为真就认为缓存身份相同。

所读 `_get_deterministic_level()` 先取C++等级，再调用 `_sync_deterministic_level()` 协调PyTorch布尔状态：等级0而布尔已开启时变为1；等级大于等于1而布尔关闭时变为0；发生冲突时还将结果写回C++。所以这个getter在冲突场景并非单纯观察请求值。

不要为了尝试命中缓存而反复交替使用两套确定性设置。公开接口已经要求协调配置且不支持多线程改动；本卡的字段逻辑不能把不一致的运行状态变成合法训练配方。

## 两个字段入口不等于自动失效所有已编译对象

这个patch针对FX图hash细节与AOTAutograd缓存细节，在创建相应对象时记录等级；它本身没有修改已生成kernel、已经持有的compiled callable或捕获图，也没有主动清空所有缓存。不能由新增字段推导改变等级后已有运行对象必然重新编译或重新捕获。

这里也没有读取上游所有缓存hash/序列化消费者，因此不把字段存在直接写成“已实测不同等级绝不会命中同一旧制品”。需要确认目标版本确实执行这两个构造及相应查询，并区分编译缓存查询、生成代码与实际下发的有效等级。

[MegaCache](../../../apis/torch_npu/megacache_artifacts.md)的save/load打包与此字段patch是不同层次；加载成功不证明等级、软硬件和模型状态全部匹配，[自动预编译缓存](torch_npu_automatic_precompile_cache.md)的Guard放宽也不能被这个单一字段替代。

实际评估应在固定输入与软件栈下记录请求等级、布尔状态、同步后的有效等级、所选后端、缓存查询/生成物和模型输出，再分别比较冷启动、重编译和稳态。本卡没有运行这些实验，也不以缓存隔离机制认证全部算子或跨batch模型结果一致。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/deterministic_cache.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）
