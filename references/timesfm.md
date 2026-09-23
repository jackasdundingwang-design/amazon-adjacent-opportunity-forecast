# TimesFM 集成合同

核验日期：2026-09-08。官方来源：https://github.com/google-research/timesfm ，模型：https://huggingface.co/google/timesfm-2.5-200m-pytorch 。官方仓库约31,704 stars；skills.sh 搜索官方 timesfm-forecasting 为170安装，社区 k-dense-ai 为约1.4K安装。选择官方 API，不照搬其未经本市场校准的区间表述。

代码发行版固定 `timesfm[torch]==2.0.2`，对应模型版本2.5（包版本不等于模型版本）。权重2.5为Apache-2.0；官方README说明3.0权重仅限非商业非生产，不能随最新版本升级。2.5支持零样本单序列、最多16,384历史点、分位数头。当前适配器使用小批量CPU与至多512个月上下文，不训练模型。未来社会/政策冲击不由历史曲线自动识别。

## 环境与运行

在技能目录建立独立环境，勿修改全局 Python：

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python 'timesfm[torch]==2.0.2' psutil
.venv/bin/python scripts/forecast.py --check
.venv/bin/python scripts/forecast.py --input /absolute/monthly.json --backend seasonal
.venv/bin/python scripts/forecast.py --input /absolute/monthly.json --backend timesfm --revision MODEL_COMMIT
```

首次真实模型运行会从 Hugging Face 下载约800MB权重并缓存；绝不上传输入销量。revision 必须为模型仓库40位提交SHA，从官方模型 API 取得并记录，不用 floating main。少于4GiB可用内存或2GiB可用磁盘时脚本拒绝载入，仍可运行季节性基线。CPU运行速度取决于机器；可只保留基线并说明模型未运行。依赖安装失败不得伪造输出。

## 输入

JSON字段：`as_of`(YYYY-MM-DD)、`series_id`、`source`、`scope`(sample/category_proxy/market)、`unit`(units/searches)、`observations`(按月连续且已结束的 `month` YYYY-MM / `value` 数值列表)。非销量序列只输出其本身单位，不能称容量。market 必须附 `coverage_evidence`。至少12个月，最多512个月；缺月/缺失值/无穷/负数报错，不能静默drop或当零；断货与促销修正应另存来源和原值。小时/日数据不得装作月数据。

输出写至标准输出JSON。包含未来18个自然月的点值、模型原始分位数（如有）、月份7–18及1–18点值合计、不包含年度概率区间。至少42个月时以前24个月以上训练、末18个月留出，计算MAE、WAPE、偏差和名义80%范围经验覆盖率；这是单窗口回顾性诊断。数据不足则回测null，不能宣称通过。

预测月份从最后观测月开始，不是从采集日开始；`stale_months>0`说明历史已过期，必须补到最近完整月后才用于“从现在起18个月”的报告，不能平移旧预测日期。

正式量化采用前还需要冻结多个历史版本，滚动回测18个月，比较ETS/阻尼趋势，检验持续增益与分位校准；本脚本不自动批准模型进入生产。不提供 XReg 接口，未来协变量也不可把已知未来结果泄漏进去。
