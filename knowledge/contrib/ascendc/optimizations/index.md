# Ascend C 算子优化经验

## 实验类型

- [受控代码扰动](controlled_code_perturbation/index.md)：通过受控改动代码并比较性能变化沉淀的 180 张知识卡。
- [进化策略实验](evolution_strategies/index.md)：AscendC 算子性能进化优化沉淀的 161 张策略卡（按算子族分组索引）+ 89 条进化运行期发现（X 系列）。
- [MoE Shape 选择](moe_shape_selection/index.md)：MoE 算子 shape/负载参数与性能关系的实测知识卡。
- [MoE 跨卡 dispatch](moe_cross_rank_dispatch/index.md)：专家并行下跨卡 token 分发路径的优化经验，含不适用边界的 1 张知识卡。
