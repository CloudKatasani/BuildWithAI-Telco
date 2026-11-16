# Build, Operate and Consume with AI in Telco: Market Research

| | |
|---|---|
| Date | 2026-11-16 |
| Scope | Agentic AI for data and AI engineering (Build), network and IT operations (Operate) and business self-service (Consume) across telco domains |
| Companion | `docs/AgentWorkflow_Build_Operate_Consume.md` (operating model), `demo/` (interactive demo) |

## 1. Summary

1. **Operators have moved from pilots to agents, but few scale.** McKinsey finds nearly every
   telco piloting AI, yet only 57% scale use cases across several domains, led by customer
   service and networks. Value comes from redesigning end-to-end processes rather than adding
   isolated pilots.
2. **Autonomy is granted one scenario at a time.** TM Forum Level 4 validations are scoped to
   single use cases (for example service assurance on one service, or RAN energy saving).
   About 81% of operators target L4 or higher by 2030; about 20% expect it by 2027.
   Telefónica ended 2025 with 12 operational L4 use cases.
3. **Coordination across systems is where the return is.** HFS Research (with Amdocs) finds
   ROI appears when agents coordinate actions across systems and functions, such as churn
   prevention and revenue assurance, not when they automate single tasks.
4. **The data foundation is the bottleneck.** Nokia, AWS and Databricks are partnering on the
   data and control layer for autonomous networks, aimed at fragmented telco data. TM Forum
   Catalysts show an agentic NOC built as an "agent of agents" over a shared Snowflake data
   foundation. Legacy BSS/OSS and talent gaps keep many operators on incremental automation.
5. **Generic models fall short on telco tasks.** GSMA launched Open Telco AI at MWC 2026
   (open telco models, datasets, a Telco Capability Index). GSMA says only 16% of telco GenAI
   deployments target network operations.
6. **Standards are converging on MCP inside ODA.** TM Forum's 2026 AI-native blueprint
   projects support the Model Context Protocol within ODA components; Project ONE adds the
   Agent-to-Agent protocol. This is Catalyst-level practice, not yet a mandated standard.
7. **Regulation makes human oversight a requirement, not a preference.** EU AI Act high-risk
   duties (risk management, logging, human oversight) cover AI used as safety components in
   critical digital infrastructure. Recent amendments moved Annex III dates to December 2027;
   NIS2 applies now.

**Implication for the demo:** one agent workforce across Build, Operate and Consume, on
certified data products, with named people approving every consequential step, and autonomy
raised scenario by scenario.

## 2. Findings by plane

### 2.1 Build with AI (data and AI engineering)

| Signal | Evidence | Design response |
|---|---|---|
| Data silos block AI at scale | Nokia + AWS + Databricks data/control layer; HFS on cross-system coordination | Data products with contracts are the unit of delivery |
| Legacy BSS/OSS slows change | TM Forum and trade coverage of L4 obstacles | Mapping agent reads metadata only; maps to TM Forum SID; CDC and batch paths |
| Agents need governed context | Google Cloud "Autonomous Data Steward"; TM Forum ODA + MCP | Semantic layer and AI context certified at a gate (G8) before any agent uses it |
| Model risk must be evidenced | EU AI Act high-risk duties | Model card, bias test, model-risk gate (G6) |

### 2.2 Operate with AI (NOC, DataOps, MLOps)

| Signal | Evidence | Design response |
|---|---|---|
| L4 per scenario | TM Forum ANLAV validations; NBN Co L4 limited to one service | Autonomy level tracked per scenario |
| Agentic NOC pattern | TM Forum Catalyst "Agentic NOC" | Watch, triage, diagnose, resolve, comms, knowledge agents |
| Network ops is under-served by GenAI | GSMA: 16% of deployments | Operate plane covers network, data platform and models |
| Accountability for actions | ServiceNow "accountable AI" coverage; EU AI Act | Action classes A0–A4; A3 needs two approvers and a rollback; A4 human-only |

### 2.3 Consume with AI (business self-service)

| Signal | Evidence | Design response |
|---|---|---|
| Care is the most scaled use case | Vodafone TOBi/SuperTOBi above 70% end-to-end resolution (company-reported); Verizon testing agents in care | Care copilot with masked data and approved scripts |
| Revenue impact still small | McKinsey: AI under 2% of revenue for most operators testing it | Consume turns answers into actions with expected value, approved by owners |
| Trust in numbers | Industry focus on governed semantic layers | Answers only from certified metrics, with SQL and lineage shown |

## 3. Telco domains covered

RAN and core network; service assurance; BSS billing, charging and revenue assurance; customer
and care; commercial and marketing; enterprise / B2B; fraud and security; field operations;
finance and regulatory; IT and data platform. The demo's Overview page maps each domain to a
Build, Operate and Consume use case.

## 4. Caveats

- Most 2026 material is vendor- or operator-authored. Outcomes such as resolution rates or
  fraud reductions are self-reported.
- No McKinsey figure sizes the total telco agentic AI market; McKinsey Global Institute
  estimates up to $16B of new value from AI automation for US telecom by 2030.
- EU AI Act dates changed in 2026; confirm against the Official Journal before relying on them.
- Demo figures (lead times, MTTR, savings) are simulated. Measure your own baseline in a pilot.

## 5. Sources

- [Fierce Network: Telcos pick up the pace to Level 4 autonomous networks](https://www.fierce-network.com/cloud/telcos-hit-level-4-autonomous-network-milestone-says-tm-forum)
- [TelecomLead: Autonomous telecom networks 2026](https://telecomlead.com/5g/autonomous-telecom-networks-2026-deutsche-telekom-telefonica-china-mobile-and-verizon-push-toward-level-4-127994)
- [Telecoms Tech News: Level 4 autonomous networks explained](https://www.telecomstechnews.com/news/level-4-autonomous-networks-explained/)
- [TM Forum Inform: Telcos on collaboration and metrics to reach L4](https://inform.tmforum.org/features-and-opinion/telcos-spell-out-importance-of-collaboration-and-metrics-to-reach-an-level-4/)
- [McKinsey: Telcos' AI inflection point](https://www.mckinsey.com.br/industries/technology-media-and-telecommunications/our-insights/telcos-ai-inflection-point-what-leaders-do-to-capture-value)
- [McKinsey: Scaling the AI-native telco](https://www.mckinsey.com.br/industries/technology-media-and-telecommunications/our-insights/scaling-the-ai-native-telco)
- [TelecomTV: McKinsey on agentic AI monetisation](https://www.telecomtv.com/content/ai/mckinsey-agentic-ai-can-unlock-new-monetisation-opportunities-for-telcos-56334/)
- [GSMA: Open Telco AI launch](https://www.gsma.com/newsroom/?p=25564)
- [AT&T: Open Telco AI](https://about.att.com/blogs/2026/open-telco-ai.html)
- [TM Forum Inform: Agentic NOC](https://inform.tmforum.org/research-and-analysis/proofs-of-concept/agentic-noc-ai-native-operations-for-the-autonomous-telco)
- [TM Forum Inform: Project ONE aims to deliver agentic ODA](https://inform.tmforum.org/features-and-opinion/project-one-aims-to-deliver-agentic-oda/)
- [TM Forum Inform: Agentic service assurance](https://inform.tmforum.org/research-and-analysis/proofs-of-concept/bringing-agentic-service-assurance-closer-to-autonomous-networks-/)
- [TM Forum Inform: Turning agentic AI into a safe, scalable operational capability](https://inform.tmforum.org/research-and-analysis/proofs-of-concept/turning-agentic-ai-into-a-safe-scalable-operational-capability)
- [HFS Research / Amdocs: Agentic AI telco operating model (PDF)](https://solutions.amdocs.com/rs/647-OJR-802/images/HFS-MIR-2026-agentic-ai-telco-operating-model.pdf?version=0)
- [RCR Wireless: Nokia, AWS and Databricks telco AI control layer](https://www.rcrwireless.com/20260624/network-infrastructure/nokia-aws-databricks-telco-ai-control)
- [Google Cloud: Rise of the agentic telco](https://cloud.google.com/transform/google-cloud-rise-of-the-agentic-telco-mwc)
- [Databricks: How telecommunications leaders are putting AI to work (PDF)](https://www.databricks.com/es/sites/default/files/2026-05/how-telecommunications-leaders-putting-ai-work.pdf)
- [ServiceNow: Autonomous networks, accountable AI](https://www.servicenow.com/community/telecom-articles/autonomous-networks-accountable-ai/ta-p/3547269)
- [TelecomTV: The week in AI-native telco, Sept 2026](https://www.telecomtv.com/content/ai/the-week-in-ai-native-telco-19-25-sept-2026-56343/amp/)
- [CX Today: Verizon CEO on AI agents in customer service](https://cxtoday.com/verizon-ceo-ai-agents-could-displace-a-large-percentage-of-customer-service-jobs)
- [DAC Beachcroft: AI Act enforced, delayed and amended](https://www.dacbeachcroft.com/en/what-we-think/ai-act-enforced-delayed-and-amended)
- [Bayern Innovativ: EU postpones AI rules for critical infrastructure](https://www.bayern-innovativ.de/en/emagazine/detail/eu-postpones-ai-regulations-for-critical-infrastructure)
