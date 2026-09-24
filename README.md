# Amazon Adjacent Opportunity Forecast

面向 Amazon 垂直品牌卖家的 Codex Skill：从现有 ASIN 或关键词出发，研究约 18 个月后的相邻新品、图案配色与套装机会。

核心原则：

- TimesFM 只承担有真实历史序列的数量预测，并与简单模型比较。
- 预测对象是“人群 × 问题 × 场景 × 新产品方向 × 站点”，不是把原 ASIN 销量直接外推成新品销量。
- 主动检查高度匹配的现有款、低星反馈和增长乏力反例；重大反证未解除时，不升级为量产或预售建议。
- 每次运行都必须实际完成 MiroFish 场景验证并核验原始记录；失败时整次流程阻断，不输出优先开发、预售或可售产品图结论。
- 冻结预测规则，使用后续新增月份检验，避免在同一批历史数据上反复挑赢家。
- 不预测利润，不把搜索量、帖子数或模拟 Agent 比例冒充购买人数。

## 安装

将本仓库克隆到 Codex skills 目录：

```sh
git clone https://github.com/jackasdundingwang-design/amazon-adjacent-opportunity-forecast.git \
  ~/.codex/skills/amazon-adjacent-opportunity-forecast
```

数量脚本的环境与 TimesFM 版本要求见 [`references/timesfm.md`](references/timesfm.md)。

## 结构

- `SKILL.md`：技能入口和完整工作流
- `references/opportunity-gates.md`：反例、增量机制与商业交付闸门
- `references/mirofish-run.md`：MiroFish 强制运行、结果核验与失败阻断协议
- `references/model-validation.md`：多模型比较和前向冻结规则
- `references/design-opportunities.md`：图案、配色和套装研究规则
- `references/timesfm.md`：TimesFM 2.5 集成约束
- `scripts/forecast.py`：18 个月代理序列预测脚本
- `scripts/test_forecast.py`：合成数据单元测试

## 当前边界

这是研究与验证流程，不是“爆品保证器”。MCP 调用、社会与政策数据、人口估计及 MiroFish 场景推演仍由代理编排；MiroFish 是必跑项但尚非自动调度，脚本不会自动批准模型或产品进入生产。
