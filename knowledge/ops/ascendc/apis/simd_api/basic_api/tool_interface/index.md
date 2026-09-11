# 工具接口

- [执行模式](execution_mode/index.md)：通过模板函数封装AIC与AIV分离模式的硬件条件分支，在指定执行单元下执行特定函数，避免代码中显式使用硬件条件分支。
- [numeric limits utils](numeric_limits_utils/index.md)：返回指定数据类型的最小正的非正规值，支持标量和矢量两种接口，矢量接口为dstLocal前count个元素赋该值。
- [系统初始化](system_init/index.md)：初始化AI Core全局状态，包括AIC与AIV的公共状态及各自特有状态；不同产品实际执行的初始化项存在差异。
- [系统资源与变量](system_resources_and_variables/index.md)：获取当前AI处理器架构版本号。
