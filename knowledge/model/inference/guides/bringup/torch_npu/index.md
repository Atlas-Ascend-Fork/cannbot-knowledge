# TorchNPU模型开发指南

汇集固定版本证据支持的模型相关知识；具体适用范围以卡片正文为准。

- [libtorch_npu构建与C++部署：ABI、链接和TorchScript产物](torch_npu_libtorch_build_and_deployment.md)：区分C++ bundle与Python wheel的ABI默认值，保存初始化、链接依赖和TorchScript示例的版本边界。
- [TorchNPU运行环境：pip、Docker与升级的版本约束](torch_npu_runtime_packages_and_containers.md)：区分产品系列、pip包、镜像标签及宿主运行依赖，保留双语安装页中的旧版本矩阵和不一致。
- [TorchNPU源码构建：工具链、增量编译与导入排障](torch_npu_source_build_and_linkage.md)：按固定提交区分双语版本示例、Ninja/Mold/CCache作用和wheel身份，定位子模块、链接、ABI及导入路径故障。
- [TorchAir 环境排查：依赖库下载失败与 TE/Protobuf 重复描述符](torchair_build_and_te_package_conflicts.md)：区分编译依赖下载与运行期 TE/CANN 配套错误，保留具体包路径和版本证据。
- [TorchAir 源码构建：目标 Python、ABI 与运行环境分离](torchair_source_build_environment.md)：区分只生成 wheel、CPU 调试及 NPU 执行的依赖，核对目标解释器、C++11 ABI、子模块和构建产物路径。
