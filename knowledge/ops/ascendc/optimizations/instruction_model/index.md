# 指令模型

- [Reg矢量计算接口的发射能力与理论吞吐口径（Ascend 950PR/950DT）](reg_vector_issue_and_theoretical_perf.md)：按接口、类型和工作量选取单指令理论并行度，核对单双发模式及端口约束；同位宽单 VL 换算与循环成本是附加假设下的推导参考，不构成实际耗时界限，瓶颈须实测。
- [Cube 指令理论性能折算口径与峰值可达性判定](cube_instruction_theoretical_perf.md)：固定单次 Mmad shape 的利用率公式含分形对齐膨胀与头开销 Δt；按 m/n 是否满 16、k 是否满 k0 算理论上界，供切分与搬运方案实测前参考，不代表整个实现的性能上界或收益排序。
- [SIMT 指令理论性能口径与有效吞吐判定](simt_instruction_theoretical_perf.md)：SIMT 理论值的单位是“单个 Vector Core 每 cycle 元素数”，且只对单一硬件指令实现的接口给出。按 128/64/32/16 四档识别待测瓶颈候选；实际主导时延与否须结合调用频次、依赖和调度实测。
