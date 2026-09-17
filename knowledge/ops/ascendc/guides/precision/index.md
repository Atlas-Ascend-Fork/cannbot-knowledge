# 精度验证

- [aclnn 接口调用指南](aclnn_interface_guide.md)：aclnn 接口调用指南：精度验证必须经 torch_aclnn_helper.h 的 EXEC_NPU_CMD 宏构建 PyTorch C++ Extension，Python 侧用 torch.ops.npu.<op> 调用；不存在 torch.ops.aclnn 命名空间。
- [生态算子开源精度标准](ops_precision_standards.md)：生态算子开源精度标准：用平均相对误差 MERE 与最大相对误差 MARE（分母加 1e-7 防除零）判定达标；含迁移场景特殊考虑——950 新增数据类型、量化算子先 round 后 clamp 的测试设计、随机数建议 CPU 生成再传 NPU、跨架构精度对比及 MicroAPI 重写与 SIMT 优化后的验证要求。
- [{{OP_NAME}} 算子精度验证报告（ascend950）](precision_report_template.md)：ascend950 算子精度验证报告的填空模板：抬头记录算子公式、torch.ops.npu 调用式、PyTorch CPU 参考基线与支持 dtype，正文含总览通过率、精度阈值标准、常规 shape 与边界值结果、按 dtype 汇总、950 与 910b 对比及关键发现各节。
- [AscendC 算子精度标准（CPU 真值口径）](precision_standard_v2_1.md)：跨代际移植与反向生成的精度标准（CPU 真值口径）：真值优先 CPU FP64 完整复现公式与边界语义，禁用外部加速器结果当真值；要求覆盖小值域/零值/极值/非对齐/空维/动态 shape，逐输出记录误差指标，不得删失败样本或放宽阈值，正反向级联须验全部梯度。
- [精度测试前置数值验证指南](precision_test_pre_validation_guide.md)：写精度测试脚本之前必做的前置数值验证流程：先用小规模输入（B=1~2、V=16~32）跑 NPU 算子并打印全部输出，手写最简 CPU 参考实现逐元素对比确认语义一致，不一致则先修参考实现。含检查清单、反模式与精度指标的有效点过滤。
- [自定义算子 PyTorch 绑定构建指南（torch_aclnn_helper.h + EXEC_NPU_CMD 标准方式）](pytorch_binding_build_guide.md)：自定义算子 PyTorch 绑定构建的唯一标准方式：用 torch_aclnn_helper.h 的 EXEC_NPU_CMD 宏，禁手调 aclnn C API 或 Pybind 直封。适用于已装 OPP 包、有 libcust_opapi.so 但未注册进 torch.ops.npu 的算子。
- [算子源码逆向分析方法论](source_code_reverse_analysis.md)：无文档算子的源码逆向分析方法论：五步流程为从 _def.cpp 提接口签名与 SoC 配置、逆向计算逻辑、推断输入域约束、提取边界条件、与 PyTorch 对标；并给出代码逆向加数学公式、同类算子类比、shape 关系推断三种测试用例生成策略及有文档时的差异检查清单。
