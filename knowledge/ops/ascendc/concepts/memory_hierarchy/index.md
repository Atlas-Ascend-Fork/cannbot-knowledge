# Cube 侧存储层级

- [Cube 分形（Fractal）与 ZN/NZ 布局概念](cube_fractal_and_layout_concepts.md)：按 dtype 确定分形轴块；Zz 输入产品组为 Zz × Zn = Nz，Ascend 950PR/950DT 为 Nz × Zn = Nz，区分 512B 输入/L1 分形与 1024B 的 L0C 结果分形。
- [Cube 侧 L1/L0A/L0B/L0C 的存储结构与数据通路](l1_l0_storage_structure_and_data_paths.md)：按产品与接口范围说明四个 Buffer 的结构、通路、对齐和随路操作，区分 512B 普通输入、1024B L0C 结果与 950 专用 32B MX 系数单位。
