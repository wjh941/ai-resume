# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

求职者在浏览器中整理简历、经历证据、职业方向和投递行动；其中一部分用户需要用年度资料辅助判断目标岗位。

## Product Purpose

AI Resume 将用户已有的简历、经历和职业规划资料组织为可执行的求职管理工作台。成功标准是用户能形成下一步行动，而不是把泛化建议当作实时招聘结论。

## Positioning

产品以用户自身资料、可验证经历和归档职业资料生成分层建议，并明确区分精简版行动提示与专业版证据依据。

## Operating Context

用户在桌面浏览器中完成岗位查询、职业规划、职业测评、简历修改、投递跟踪和年度就业洞察查询。独立 HTML 看板通过现有后端 API 工作，也能在演示或离线状态显示本地框架。

## Capabilities and Constraints

- H5 开发服务器保持 `127.0.0.1:5186`，FastAPI 后端保持 `127.0.0.1:8000`。
- 所有既有 API 与数据库结构保持兼容；报告能力只添加字段和端点。
- 年度就业洞察使用归档资料，不抓取招聘网站，不构成实时岗位、薪资或录用承诺。
- 精简版面向快速行动；专业版在会员授权后展示证据映射、资料范围与更完整行动计划。
- 用户可选择目标岗位和年份查询年度就业洞察。

## Evidence on Hand

- 独立 HTML 工作台：`resume-miniprogram/public/premium-dashboard.html`
- 报告层 API：`resume-backend/app/services/report_tiering.py`
- 年度就业洞察 API：`resume-backend/app/api/assessment.py`

## Product Principles

- 把岗位判断落到可验证的经历和下一步行动。
- 明确资料范围与不确定性，避免制造实时数据假象。
- 专业版提供依据，不以复杂术语替代可执行建议。
- 权益限制由服务端执行，前端只解释当前可见内容。

## Accessibility & Inclusion

所有新增面向用户的文字使用简体中文；模式切换和证据展开可用键盘操作，并为状态变化提供可读提示。
