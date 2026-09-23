# 2026-09-08 接入验证记录

- 独立Python3.11.16环境，timesfm2.0.2、torch2.14.0、numpy2.4.6、huggingface-hub1.30.0已安装。
- 7项合成数据单元测试通过：18个月长度/窗口、短历史降级、缺月/重复月、非法数值、未完整月、全市场覆盖证据、留出数据隔离。合成数据不是市场数据。
- skill-creator quick_validate 返回 Skill is valid。
- 检查已安装源码确认TimesFM2.5类及revision、torch_compile参数；关闭torch.compile减少首次CPU编译开销。
- 模型加载前可用RAM约2.64GiB，未达到本适配器4GiB门槛；未下载权重、未执行真实推理。官方HuggingFace模型API连接另报connection reset，未取得固定模型SHA。
- 尚未完成真实ASIN输入适配、18个月滚动回测、人口估计或MiroFish联调。释放足够内存且恢复模型源访问后，取得官方权重SHA并运行一次真实推理，再补业务回测；不要将本记录当作预测效果证明。
