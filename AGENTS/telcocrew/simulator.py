"""Deterministic offline scripts, one per agent. They call the same tools a live model would, so the
guardrails, approvals and audit trail behave exactly as in live mode. Output is labelled as simulated."""
from __future__ import annotations

import json
import re
from typing import Callable

from . import data
from .tools import Session

Call = Callable[[str, dict], dict]
LABEL = "[Simulated agent output - demo simulator, synthetic data]\n"


def _build_scenario(task: str) -> dict:
    t = task.lower()
    if any(k in t for k in ("energy", "sleep", "ran ")):
        return {"id": "energy", "product": "dp_ran_energy_efficiency", "gold": "gld_cell_energy_daily", "tables": ["pm_cell_kpi", "inventory_cell"],
                "metric": "idle_night_kwh", "cq": "Which clusters waste the most energy at night?"}
    if any(k in t for k in ("leak", "revenue assurance", "recon")):
        return {"id": "ra", "product": "dp_usage_to_bill_recon", "gold": "gld_recon_daily", "tables": ["billing_invoice", "billing_account"],
                "metric": "leakage_eur", "cq": "How much revenue leaked last month and where?"}
    if any(k in t for k in ("sla", "enterprise", "b2b")):
        return {"id": "b2b", "product": "dp_enterprise_service_health", "gold": "gld_account_sla", "tables": ["care_ticket"],
                "metric": "sla_credit_exposure_eur", "cq": "What is our SLA credit exposure?"}
    return {"id": "churn", "product": "dp_subscriber_churn_360", "gold": "gld_churn_risk",
            "tables": ["crm_customer", "billing_account", "billing_invoice", "xdr_daily", "care_ticket"],
            "metric": "churn_at_risk_lines", "cq": "Which regions have the highest churn risk this week?"}


def _ops_scenario(task: str) -> str:
    t = task.lower()
    if any(k in t for k in ("dbt", "mart", "feed", "pipeline", "mediation")):
        return "dataops"
    if any(k in t for k in ("model", "drift", "precision")):
        return "mlops"
    return "noc"


def _gate(call: Call, summary: str, paths: list[str]) -> str:
    r = call("request_gate", {"summary": summary, "artifacts": paths, "risks": "See artifacts; simulated run on synthetic data."})
    return r.get("approval_id", "none")


def _handoff(status: str, written: list[str], approvals: list[str], nxt: str, questions: list[str] | None = None) -> str:
    q = "\n".join(f"- {x}" for x in (questions or [])) or "- none"
    return (f"{LABEL}Status: {status}\nArtifacts: {', '.join(written) or 'none'}\nApprovals requested: {', '.join(approvals) or 'none'}\n"
            f"Open questions:\n{q}\nNext: {nxt}")


# ================================================================== BUILD
def orchestrator(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    brief = (f"# Intake brief\n\nRequest: {task}\n\nData product: {sc['product']}\nDomain pack: telco (NorthStar Telecom)\n"
             "Stack profile: Oracle/Db2 BSS + OSS PM + xDR lake -> Snowflake (dbt Core) -> semantic layer -> internal marketplace\n"
             "Plan: G0 intake, G1 requirements, G2 mapping, G3 design, G4 build, G5 quality, G6 model risk, G7 release, G8 semantic, G9 publish.\n")
    w = call("write_artifact", {"path": "00-intake/brief.md", "content": brief})
    call("record_decision", {"decision": f"Route to Build track as {sc['product']}", "evidence": "Request names a business outcome and consumers"})
    ap = _gate(call, "Intake brief and plan for approval", [w.get("written", "00-intake/brief.md")])
    return _handoff("needs-approval", ["00-intake/brief.md"], [ap], "Data Product Owner approves G0, then the Business Analyst starts.")


def business_analyst(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    call("read_artifact", {"path": "00-intake/brief.md"})
    g = call("lookup_glossary", {"term": "churn" if sc["id"] == "churn" else sc["metric"].split("_")[0]})
    reqs = ("# Requirements\n\nBR-001 Churn = post-paid line disconnected or ported out within 30 days of score date.\n"
            "BR-002 Exclude lines in collections or fraud hold.\nBR-003 Marketing use requires consent flag (TEL-C3).\n"
            "NFR-001 Weekly list ready Monday 06:00 UTC.\nNFR-002 Analytics joins on pseudonymous subscriber key (TEL-C4).\n"
            f"CQ-001 {sc['cq']}\nCQ-002 How much monthly revenue is at risk?\n\nGlossary evidence: {json.dumps(g)[:300]}\n")
    call("write_artifact", {"path": "01-requirements/requirements.md", "content": reqs})
    call("ask_open_question", {"question": "Confirm the churn window is 30 days for SIM-only lines too.", "role": "Data Product Owner", "blocking": False})
    ap = _gate(call, "Requirements baseline", ["01-requirements/requirements.md"])
    return _handoff("needs-approval", ["01-requirements/requirements.md"], [ap], "G1 by Data Product Owner + Data Steward.",
                    ["OQ: churn window for SIM-only lines (Data Product Owner, non-blocking)"])


def source_mapping(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    meta = call("list_source_metadata", {})
    rows, restricted = [], []
    for sysname, sysv in meta.items():
        for t, tv in sysv["tables"].items():
            if t not in sc["tables"]:
                continue
            for c, cv in tv["columns"].items():
                if cv["classification"] == "Restricted":
                    restricted.append(f"{t}.{c}")
                rows.append(f"{sysname},{t},{c},{cv['type']},{cv['classification']},{tv['ingest']}")
    prof = call("profile_column", {"table": sc["tables"][0], "column": "msisdn" if sc["id"] == "churn" else "cell_id"})
    call("profile_column", {"table": "billing_account", "column": "tariff_code"})
    sid = call("lookup_sid", {"term": "customer"})
    mapping = "system,table,column,type,classification,ingest\n" + "\n".join(rows)
    call("write_artifact", {"path": "02-mapping/source-inventory.csv", "content": mapping})
    notes = (f"# Mapping notes\n\nSID: {json.dumps(sid)}\nRestricted columns excluded from targets (TEL-C1, TEL-C4): {', '.join(restricted)}\n"
             f"Profile evidence (counts only for Restricted): {json.dumps(prof)}\n"
             "MAP-001 subscriber_key <- xdr_lake.xdr_daily.subscriber_key (direct, high)\n"
             "MAP-002 tariff_code <- billing.billing_account.tariff_code (direct, medium: renamed from plan_code in RN-772)\n"
             "DQ-001 customer_id unique (block)  DQ-002 monthly_fee >= 0 (block)  DQ-003 consent_marketing in Y,N (warn)\n")
    call("write_artifact", {"path": "02-mapping/mapping.md", "content": notes})
    ap = _gate(call, "Source-to-target mapping and classification", ["02-mapping/source-inventory.csv", "02-mapping/mapping.md"])
    return _handoff("needs-approval", ["02-mapping/source-inventory.csv", "02-mapping/mapping.md"], [ap],
                    "G2 by Data Steward + Security & Privacy Officer.")


def solution_architect(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    call("read_artifact", {"path": "02-mapping/mapping.md"})
    cost = call("estimate_platform_cost", {"warehouse_hours_per_day": 2.1, "credits_per_hour": 1, "storage_tb": 1.5, "model_calls_per_day": 400})
    design = (f"# Design\n\nMedallion: brz_* (views over lake Iceberg) -> slv_subscriber_month -> {sc['gold']}\n"
              f"Output ports: GOLD.{sc['gold']}, SEMANTIC.{sc['product'].replace('dp_', '')}\n\n"
              "ADR-001 Lake tables stay in the Glue catalog; warehouse reads via catalog-linked database.\n"
              "ADR-002 Silver/gold as native warehouse tables.\nADR-003 dbt Core in Git, scheduled by the client orchestrator.\n"
              "ADR-004 CDC apply mode: merge on business key; deletes close the row (history kept).\n"
              "ADR-005 xDR retained 12 months in silver per TEL-C2 (confirm with DPO).\n\n"
              f"Cost: {json.dumps(cost)}\n")
    call("write_artifact", {"path": "03-design/design.md", "content": design})
    ap = _gate(call, "Logical + physical design, ADRs and cost", ["03-design/design.md"])
    return _handoff("needs-approval", ["03-design/design.md"], [ap], "G3 by Data Architect.")


def data_engineer(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    call("read_artifact", {"path": "03-design/design.md"})
    model = (f"-- models/silver/slv_subscriber_month.sql (generated)\n{{{{ config(materialized='incremental', unique_key='subscriber_key') }}}}\n"
             "select a.account_id, a.tariff_code as plan_code, i.bill_month, sum(i.total_amount) as billed_eur\n"
             "from {{ source('bronze','billing_invoice') }} i join {{ source('bronze','billing_account') }} a using (account_id)\n"
             "group by 1,2,3\n")
    tests = "version: 2\nmodels:\n  - name: slv_subscriber_month\n    columns:\n      - name: account_id\n        tests: [not_null]\n"
    call("write_artifact", {"path": "04-build/models/slv_subscriber_month.sql", "content": model})
    call("write_artifact", {"path": "04-build/models/slv_subscriber_month.yml", "content": tests})
    chk = call("run_sandbox_sql", {"sql": "SELECT a.tariff_code, i.bill_month, ROUND(SUM(i.total_amount),2) AS billed FROM billing_invoice i JOIN billing_account a USING (account_id) GROUP BY 1,2 ORDER BY 1,2"})
    call("write_artifact", {"path": "04-build/sandbox-run.json", "content": json.dumps(chk, default=str)[:4000]})
    pr = call("open_pull_request", {"branch": f"feat/{sc['id']}", "title": f"{sc['product']}: WP-1..3",
                                    "files": ["04-build/models/slv_subscriber_month.sql", "04-build/models/slv_subscriber_month.yml"]})
    files = ["04-build/models/slv_subscriber_month.sql", "04-build/models/slv_subscriber_month.yml", "04-build/sandbox-run.json"]
    ap = _gate(call, f"Merge {pr.get('pr', 'PR')}", files)
    return _handoff("needs-approval", files, [ap], "G4 code review by Engineering Lead.")


def quality_engineer(task: str, call: Call, s: Session) -> str:
    dq = call("run_dq_checks", {"rules": [
        {"id": "DQ-001", "table": "crm_customer", "check": "unique", "column": "customer_id"},
        {"id": "DQ-002", "table": "billing_account", "check": "min_value", "column": "monthly_fee", "value": "0"},
        {"id": "DQ-003", "table": "crm_customer", "check": "allowed_values", "column": "consent_marketing", "value": "Y,N"},
        {"id": "DQ-004", "table": "billing_account", "check": "allowed_values", "column": "status", "value": "ACTIVE,CLOSED"}]})
    recon = call("run_sandbox_sql", {"sql": "SELECT (SELECT COUNT(*) FROM billing_invoice) AS src_rows, (SELECT ROUND(SUM(total_amount),2) FROM billing_invoice) AS src_total"})
    probe = call("run_sandbox_sql", {"sql": "SELECT msisdn FROM crm_customer LIMIT 5"})
    ev = (f"# Test evidence\n\nDQ results: {json.dumps(dq)}\n\nReconciliation (source control totals): {json.dumps(recon['rows'] if 'rows' in recon else recon)}\n\n"
          f"Masking probe (Restricted column must come back NULL): {json.dumps(probe)[:260]}\n\nTC-004 DQ-004 fails: status SUSPENDED is valid in source but missing from the rule. "
          "Returned to Mapping as a rule defect, not a data defect.\n")
    call("write_artifact", {"path": "05-test/evidence.md", "content": ev})
    ap = _gate(call, "Quality evidence (1 rule defect returned to Mapping)", ["05-test/evidence.md"])
    return _handoff("needs-approval", ["05-test/evidence.md"], [ap], "G5 by QA Lead.")


def ml_engineer(task: str, call: Call, s: Session) -> str:
    feats = call("run_sandbox_sql", {"sql": "SELECT region, value_segment, ROUND(AVG(risk_score),3) AS avg_risk, COUNT(*) AS n FROM gld_churn_risk GROUP BY 1,2 ORDER BY 3 DESC"})
    card = ("# Model card MC-07 churn_gbm v8 (challenger)\n\nTarget: churned_30d. Features: tenure, bill shock, dropped calls, throughput p10, "
            "care contacts, contract end distance, tariff_family. Restricted features: none (no MSISDN, no cell-level location).\n"
            f"Segment check (avg risk by region/segment, n>=10 only): {json.dumps(feats.get('rows', [])[:6])}\n"
            "Bias: max gap between regions 2.1 pts after controlling for tenure (threshold 5).\nUse: decision support; people approve every customer action.\n")
    call("write_artifact", {"path": "06-ml/model-card.md", "content": card})
    ap = _gate(call, "Model risk sign-off for challenger (shadow first)", ["06-ml/model-card.md"])
    return _handoff("needs-approval", ["06-ml/model-card.md"], [ap], "G6 by ML Lead / Model Risk + Security & Privacy Officer.")


def release_engineer(task: str, call: Call, s: Session) -> str:
    plan = ("# Release REL-001\n\nOrder: (1) lake objects + replication files handed to platform team, (2) warehouse objects and roles, "
            "(3) dbt project, (4) lake maintenance jobs.\nTested commit = deployed commit (7f3c2e1).\nRollback rehearsed in test: 3 min 40 s.\n"
            "Change record: CHG-55100 (CAB). Window: Tue 01:00-03:00 UTC, outside network freeze.\n")
    call("write_artifact", {"path": "07-release/release-plan.md", "content": plan})
    ap = _gate(call, "Release REL-001 to production", ["07-release/release-plan.md"])
    return _handoff("needs-approval", ["07-release/release-plan.md"], [ap], "G7 by Change Manager (CAB) + Engineering Lead.")


def semantic_context(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    lin = call("get_lineage", {"object": sc["gold"]})
    check = call("run_sandbox_sql", {"sql": "SELECT region, COUNT(*) AS at_risk FROM gld_churn_risk WHERE risk_score >= 0.7 GROUP BY 1 ORDER BY 2 DESC"})
    sem = (f"# Semantic view SEMANTIC.{sc['product'].replace('dp_', '')}\n\nmetrics: churn_at_risk_lines, at_risk_arpu, churn_rate_30d\n"
           f"VQ-01 \"{sc['cq']}\" reference result: {json.dumps(check.get('rows', [])[:5])}\nLineage: {json.dumps(lin)}\n"
           "Refusal tests: PII request -> refused; out-of-scope -> refused; cross-domain role -> denied. 3/3 pass.\n")
    call("write_artifact", {"path": "08-semantic/semantic-view.md", "content": sem})
    ap = _gate(call, "Semantic and AI context certification", ["08-semantic/semantic-view.md"])
    return _handoff("needs-approval", ["08-semantic/semantic-view.md"], [ap], "G8 by Data Steward + Data Product Owner.")


def data_product_publisher(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    g9 = next((a for a in s.approvals.items.values() if a.content.get("gate") == "G9"), None)
    if g9 and g9.status == "approved":
        r = call("publish_data_product", {"approval_id": g9.id, "listing_path": "09-publish/listing.yaml"})
        return _handoff("done", [], [], f"Published: {json.dumps(r)}. Operate pack handed to operate-watch-desk.")
    contract = (f"apiVersion: v3.0.0\nkind: DataContract\nid: {sc['product']}\nversion: 1.0.0\nowner: Data Product Owner\n"
                f"outputPorts: [GOLD.{sc['gold']}, SEMANTIC.{sc['product'].replace('dp_', '')}]\nsla: {{freshness: 'Mon 06:00 UTC', availability: 99.5%}}\n")
    pack = ("signals:\n  - feed_lag: {source: mediation-file-feed, threshold_min: 30}\n  - dbt_run_results: {model: slv_subscriber_month, on_fail: page_AMS}\n"
            "kedb_seed: [KE-1189]\nactions_proposed:\n  - rerun_dbt_model: {class: A2, approver: Service Delivery Manager}\n")
    call("write_artifact", {"path": "09-publish/contract.odcs.yaml", "content": contract})
    call("write_artifact", {"path": "09-publish/listing.yaml", "content": f"listing: {sc['product']}\naudience: internal\n"})
    call("write_artifact", {"path": "09-publish/operate-pack.yaml", "content": pack})
    files = ["09-publish/contract.odcs.yaml", "09-publish/listing.yaml", "09-publish/operate-pack.yaml"]
    ap = _gate(call, "Publish data product to the internal marketplace", files)
    return _handoff("needs-approval", files, [ap], "G9 by Data Product Owner + Data Steward; then run me again to publish.")


def governance_lineage(task: str, call: Call, s: Session) -> str:
    sc = _build_scenario(task)
    lin = call("get_lineage", {"object": sc["gold"]})
    call("register_catalog_asset", {"name": sc["product"], "asset_type": "data product", "classification": "Confidential",
                                    "description": f"Candidate data product for {sc['id']}"})
    call("write_artifact", {"path": "control/governance/lineage-completeness.md",
                            "content": f"# Lineage completeness\n\n{json.dumps(lin, indent=1)}\nGaps on contract columns: none.\n"})
    return _handoff("done", ["control/governance/lineage-completeness.md", "control/governance/catalog-candidates.jsonl"], [],
                    "Evidence attached for G2, G3, G7 and G9.")


# ================================================================== OPERATE
def watch_desk(task: str, call: Call, s: Session) -> str:
    sc = _ops_scenario(task)
    al = call("get_alarms", {"scenario": sc})
    extra = call("get_pipeline_runs", {"scenario": sc}) if sc == "dataops" else call("get_model_metrics", {}) if sc == "mlops" else call("get_kpis", {"element": "MN-07"})
    lines = [f"- {a['time']} {a['source']} {a['element']}: {a['text']}" for a in (al.get("data", al)).get("alarms", [])]
    call("write_artifact", {"path": "ops/watch/events.md", "content": "# Deduplicated events\n" + "\n".join(lines) + f"\n\nSupporting signal: {json.dumps(extra)[:600]}\n"})
    return _handoff("done", ["ops/watch/events.md"], [], f"{len(lines)} events ({al.get('data', al).get('raw_count', len(lines))} raw) to Triage. "
                    "One alarm text contained an embedded instruction; treated as data and flagged.")


def triage(task: str, call: Call, s: Session) -> str:
    sc = _ops_scenario(task)
    call("get_alarms", {"scenario": sc})
    ch = call("get_recent_changes", {"scenario": sc})
    topo = call("get_topology", {"element": "MN-07"}) if sc == "noc" else {}
    inc = {"noc": "INC-90311: 236 alarms -> 1 incident. Impact ~41k subscribers, 3 enterprise VPN/DIA services on MN-AGG-2, est. EUR 18k/h. P1.",
           "dataops": "INC-90312: feed lag + dbt failure -> 1 incident. Impact: weekly churn mart SLA 06:00 at risk, retention campaign. P2.",
           "mlops": "INC-90313: churn model precision drop linked to tariff UL-25 migration. Impact: retention false positives. P3."}[sc]
    call("write_artifact", {"path": "ops/triage/incident.md", "content": f"# {inc}\n\nChanges in window: {json.dumps(ch)}\nTopology: {json.dumps(topo)}\n"})
    return _handoff("done", ["ops/triage/incident.md"], [], "Diagnosis to test hypotheses.")


def diagnosis(task: str, call: Call, s: Session) -> str:
    sc = _ops_scenario(task)
    ch = call("get_recent_changes", {"scenario": sc})
    q = {"noc": "handover offset ping-pong", "dataops": "schema rename column not found", "mlops": "tariff launch usage features"}[sc]
    ke = call("search_kedb", {"query": q})
    ev = call("get_kpis", {"element": "NEIGHBOUR"}) if sc == "noc" else call("get_pipeline_runs", {"scenario": sc}) if sc == "dataops" else call("get_model_metrics", {})
    hyp = {"noc": "H1 71% CR-48213 handover offset change (only changed cells degraded; neighbour MN-06 on same router clean)\nH2 22% MN-AGG-2 flaps (began after DCR rise)\nH3 7% new interference (no new sites)",
           "dataops": "H1 88% RN-772 rename broke staging contract\nH2 64% mediation host CPU saturation (separate cause)",
           "mlops": "H1 82% UL-25 migration shifted throughput feature (precision 0.41 migrated vs 0.77 not)\nH2 18% label delay"}[sc]
    call("write_artifact", {"path": "ops/diagnosis/rca.md", "content": f"# Ranked hypotheses\n{hyp}\n\nKEDB: {json.dumps(ke)[:500]}\nChanges: {json.dumps(ch)[:400]}\nEvidence: {json.dumps(ev)[:400]}\n"})
    return _handoff("done", ["ops/diagnosis/rca.md"], [], "Resolution to propose actions for H1.")


_ACTIONS = {
    "noc": [{"title": "Roll back CR-48213 on 14 MN-07 cells from stored config", "action_class": "A3", "steps": "Re-apply previous handover offset per cell in waves of 5",
             "blast_radius": "14 cells, ~41k subscribers", "rollback": "Re-apply CR-48213", "verify": "DCR < 1.2% within 15 min", "change_record": "CHG-EMR-0912",
             "approvers": ["NOC Shift Lead", "Change Manager (CAB)"]}],
    "dataops": [{"title": "Hotfix PR mapping tariff_code to plan_code in stg model, rerun downstream", "action_class": "A3", "steps": "Merge hotfix PR, dbt build -s slv_subscriber_month+",
                 "blast_radius": "1 model + 4 downstream", "rollback": "Revert PR and rerun previous version", "verify": "dbt build green; rows within 0.5% of last week",
                 "change_record": "CHG-55188", "approvers": ["Engineering Lead", "Change Manager (CAB)"]},
                {"title": "Scale mediation parser workers 4 to 8 for 3 hours", "action_class": "A2", "steps": "Set worker count 8; auto-revert after 3 h",
                 "blast_radius": "Mediation cluster, +EUR 36", "rollback": "Scale back to 4", "verify": "Lag < 30 min", "approvers": ["Service Delivery Manager"]}],
    "mlops": [{"title": "Retrain churn model with tariff_family feature and run 7-day shadow", "action_class": "A2", "steps": "Train challenger v8; shadow alongside v7",
               "blast_radius": "Shadow only", "rollback": "Keep v7 champion", "verify": "Shadow precision >= 0.75", "approvers": ["ML Lead / Model Risk"]}],
}


def resolution(task: str, call: Call, s: Session) -> str:
    sc = _ops_scenario(task)
    mine = [a for a in s.approvals.items.values() if a.kind == "action" and a.requested_by == "operate-resolution"]
    approved = [a for a in mine if a.status == "approved"]
    if approved:
        res = [call("execute_approved_action", {"approval_id": a.id}) for a in approved]
        call("write_artifact", {"path": "ops/resolution/execution.md", "content": "# Execution record\n\n" + "\n".join(
            f"- {a.id} {a.title}: {r.get('verification', r.get('error', ''))}" for a, r in zip(approved, res)) + "\n"})
        return _handoff("done", ["ops/resolution/execution.md"], [], "Executed and verified: " + "; ".join(r.get("verification", r.get("error", "")) for r in res))
    if mine:
        return _handoff("needs-approval", [], [a.id for a in mine], "Waiting for approvers; nothing executed.")
    call("read_artifact", {"path": "ops/diagnosis/rca.md"})
    ids = [call("propose_action", a).get("approval_id") for a in _ACTIONS[sc]]
    call("write_artifact", {"path": "ops/resolution/action-plan.md", "content": "# Action plan\n\n" + "\n".join(
        f"- [{a['action_class']}] {a['title']} | blast radius: {a['blast_radius']} | rollback: {a['rollback']} | verify: {a['verify']} | approvers: {', '.join(a['approvers'])}"
        for a in _ACTIONS[sc]) + "\n"})
    blocked = call("propose_action", {"title": "Disable alarm forwarding for cluster MN-07 to stop the storm", "action_class": "A2",
                                      "steps": "disable alarm forwarding", "blast_radius": "cluster", "rollback": "re-enable",
                                      "verify": "none", "approvers": ["NOC Shift Lead"]}) if sc == "noc" else {}
    note = f" A4 check: {blocked.get('error')}" if blocked else ""
    return _handoff("needs-approval", [], [i for i in ids if i], "Approvers sign; then run me again to execute and verify." + note)


def sla_guard(task: str, call: Call, s: Session) -> str:
    runs = call("get_pipeline_runs", {"scenario": "dataops"})
    call("write_artifact", {"path": "ops/sla/forecast.md", "content": f"# Breach forecast\n\ngld_churn_risk_weekly: SLA 06:00, forecast 07:35 (95 min late).\n{json.dumps(runs)[:600]}\n"})
    return _handoff("done", ["ops/sla/forecast.md"], [], "Time to breach 2 h 20 min. Routed to Triage.")


def comms(task: str, call: Call, s: Session) -> str:
    sc = _ops_scenario(task)
    text = {"noc": "We fixed a network issue that affected calls in the Metro-North area between 18:40 and 19:02 today. Service is back to normal.",
            "dataops": "The weekly churn-risk list was at risk this morning due to an upstream billing change. It was delivered on time.",
            "mlops": "The churn-risk model was updated for the new unlimited tariff. Lists from next Monday will be more accurate."}[sc]
    r = call("draft_message", {"audience": "customers in Metro-North (SMS)" if sc == "noc" else "internal stakeholders", "text": text,
                               "approvers": ["Service Delivery Manager"]})
    return _handoff("needs-approval", [], [r.get("approval_id", "")], "Service Delivery Manager approves before anything is sent.")


def problem_knowledge(task: str, call: Call, s: Session) -> str:
    sc = _ops_scenario(task)
    ke = {"noc": "KE-2207", "dataops": "KE-1189", "mlops": "KE-3011"}[sc]
    hit = call("search_kedb", {"query": {"noc": "handover offset", "dataops": "schema rename", "mlops": "tariff launch"}[sc]})
    call("write_artifact", {"path": f"ops/problem/{ke}-update.md", "content": f"# {ke} update (draft for Problem Manager)\n\n{json.dumps(hit)[:600]}\n"
                            "Pre-check (read-only): compare changed vs unchanged neighbour cells before and after each push wave.\n"})
    return _handoff("needs-approval", [f"ops/problem/{ke}-update.md"], [], "Problem Manager reviews the KEDB update.")


def finops(task: str, call: Call, s: Session) -> str:
    cost = call("get_cost_usage", {})
    call("write_artifact", {"path": "ops/finops/cost-report.md", "content": f"# Cost vs budget\n\n{json.dumps(cost, indent=1)}\n\nRAN night energy is 6.7% over budget; "
                            "412 sleep-candidate cells. Proposal routed to Resolution as a pilot on 38 cells (A3, NOC Shift Lead + CAB).\n"})
    return _handoff("done", ["ops/finops/cost-report.md"], [], "Resolution to propose the cell-sleep pilot.")


def service_reporting(task: str, call: Call, s: Session) -> str:
    rep = "# Service report\n\n| Incident | MTTD | MTTR | Baseline | Events |\n|---|---|---|---|---|\n| INC-90311 | 0.5 min | 22 min | 2 h 40 min | 236 -> 1 |\n| INC-90312 | 1 min | 1 h 52 min | 5 h 30 min | 2 -> 1 |\n"
    call("write_artifact", {"path": "ops/reporting/service-report.md", "content": rep + "\nAutonomy: RAN rollback scenario at L3 (proposed L4 after 10 validated runs).\n"})
    return _handoff("done", ["ops/reporting/service-report.md"], [], "Weekly service review.")


# ================================================================== CONSUME
_PII = re.compile(r"(?i)\b(phone|msisdn|imsi|imei|name|address|email|passport|id number)s?\b")


def _pick_metric(q: str) -> tuple[str, list[str]]:
    t = q.lower()
    if "energy" in t or "sleep" in t or "cluster" in t:
        return "idle_night_kwh", ["cluster"]
    if "leak" in t:
        return "leakage_eur", ["month", "leak_point"]
    if "credit" in t or "exposure" in t:
        return "sla_credit_exposure_eur", ["account"]
    if "sla" in t or "breach" in t or "account" in t:
        return "accounts_breach_forecast", ["account"]
    if "revenue" in t or "arpu" in t or "money" in t:
        return "at_risk_arpu", ["value_segment"]
    if "driver" in t or "why" in t:
        return "churn_at_risk_lines", ["top_driver"]
    if "churn" in t or "risk" in t or "region" in t:
        return "churn_at_risk_lines", ["region"]
    return "", []


def ask_your_data(task: str, call: Call, s: Session) -> str:
    if _PII.search(task):
        return (f"{LABEL}I can't return personal identifiers. Counts and segments are available instead, or the Data Steward can review an "
                "access request. (Guardrail: Restricted data, shared guardrails section 4)")
    metric, dims = _pick_metric(task)
    if not metric:
        cat = call("list_metrics", {})
        return f"{LABEL}No certified metric answers this. Logged as candidate CQ for the Build track. Certified metrics: {', '.join(cat)}"
    r = call("query_metric", {"metric": metric, "group_by": dims})
    rows = r.get("rows", [])[:6]
    table = "\n".join(" | ".join(str(v) for v in row.values()) for row in rows)
    conf = "high (verified question)" if r.get("verified_questions") else "medium (certified metric, ad-hoc grouping)"
    return (f"{LABEL}{r.get('description')}:\n{table}\n\nSQL: {r.get('sql')}\nLineage: {'; '.join(r.get('lineage', []))}\n"
            f"Freshness: {r.get('freshness')}. Confidence: {conf}. Suppressed groups: {r.get('suppressed_groups', 0)}.")


def insight_scout(task: str, call: Call, s: Session) -> str:
    a = call("query_metric", {"metric": "churn_at_risk_lines", "group_by": ["region"]})
    b = call("query_metric", {"metric": "leakage_eur", "group_by": ["month"]})
    txt = (f"# Insights\n\n1. Churn risk concentrates in {a['rows'][0]['region']} and {a['rows'][1]['region']} (certified metric churn_at_risk_lines). "
           "Correlates with the Metro-North network incident INC-90311; correlation, not proven cause.\n"
           f"2. Leakage by month: {json.dumps(b['rows'])}. Falling after the rating hotfix.\n")
    call("write_artifact", {"path": "consume/insights/weekly.md", "content": txt})
    return LABEL + txt


def next_best_action(task: str, call: Call, s: Session) -> str:
    t = task.lower()
    if "sleep" in t or "energy" in t:
        r = call("query_metric", {"metric": "sleep_candidate_cells", "group_by": ["cluster"]})
        p = call("propose_business_action", {"action_type": "network_change", "title": "Pilot cell sleep 01:00-05:00 on Business-Park-W candidates",
                                             "audience": "38 cells", "expected_value": "EUR 41k/yr (0.20 GWh x tariff)", "checks": ["No emergency-coverage cells", "Auto-wake if users > 15"]})
        return f"{LABEL}Evidence: {json.dumps(r['rows'][:3])}\nProposed {p.get('approval_id')} -> {', '.join(p.get('approvers', []))}"
    r = call("query_metric", {"metric": "at_risk_arpu", "group_by": ["value_segment"], "filters": {}})
    p = call("propose_business_action", {"action_type": "retention_offer", "title": "Retention offer to high-value at-risk lines in Metro-North",
                                         "audience": "High-value lines with risk >= 0.7 and consent_marketing = Y", "expected_value": "~610 saves x EUR 47.50 ARPU = EUR 29k MRR",
                                         "checks": ["Consent flag Y on every line", "Discount within approved band", "10% holdout"]})
    call("write_artifact", {"path": "consume/actions/proposal.md", "content": f"# Proposal\n\nEvidence (at_risk_arpu by segment): {json.dumps(r['rows'])}\n"
                            f"Approval request: {p.get('approval_id')} -> {', '.join(p.get('approvers', []))}\n"})
    return f"{LABEL}Evidence: {json.dumps(r['rows'])}\nProposed {p.get('approval_id')} -> {', '.join(p.get('approvers', []))}. Nothing is sent until both sign."


def care_copilot(task: str, call: Call, s: Session) -> str:
    r = call("query_metric", {"metric": "churn_at_risk_lines", "group_by": ["top_driver"], "filters": {"region": "Metro-North"}})
    p = call("propose_business_action", {"action_type": "care_credit", "title": "1 GB goodwill credit for customers affected by INC-90311",
                                         "audience": "Lines in the incident footprint", "expected_value": "Avoids ~2,900 inbound calls", "checks": ["Footprint from incident only", "Approved script CARE-NET-03"]})
    call("write_artifact", {"path": "consume/care/case-brief.md", "content": f"# Case brief\n\nRegion drivers (Metro-North): {json.dumps(r['rows'][:3])}\n"
                            f"Customer-level history: not available to this agent.\nGoodwill credit: {p.get('approval_id')} (pending approval)\n"})
    return (f"{LABEL}Case summary (masked ****4471): three contacts in 12 days (dropped calls, roaming charge, cancellation). Region drivers: "
            f"{json.dumps(r['rows'][:3])}. Suggested reply: acknowledge the fixed network issue, explain roaming charge, offer loyalty plan. "
            f"Goodwill credit proposed as {p.get('approval_id')}.")


def enterprise_account(task: str, call: Call, s: Session) -> str:
    r = call("query_metric", {"metric": "sla_credit_exposure_eur", "group_by": ["account"]})
    d = call("draft_message", {"audience": "Northwind Logistics account team (internal)", "text": "Availability MTD 99.71% vs 99.9% SLA; root cause INC-90311 fixed; "
                               "proposed service review call this week.", "approvers": ["Service Delivery Manager"]})
    call("write_artifact", {"path": "consume/accounts/account-brief.md", "content": f"# Account brief\n\nCredit exposure by account: {json.dumps(r['rows'][:5])}\n"})
    return f"{LABEL}Credit exposure by account: {json.dumps(r['rows'][:5])}\nBrief drafted for approval: {d.get('approval_id')}"


def exec_briefing(task: str, call: Call, s: Session) -> str:
    a = call("query_metric", {"metric": "at_risk_arpu"})
    b = call("query_metric", {"metric": "leakage_eur", "group_by": ["month"]})
    c = call("query_metric", {"metric": "sla_credit_exposure_eur"})
    brief = (f"# Steering brief (week 46)\n\n- Revenue at risk from churn: EUR {a['rows'][0]['value']}/month (certified at_risk_arpu).\n"
             f"- Revenue leakage: {json.dumps(b['rows'])} (falling).\n- Enterprise SLA credit exposure: EUR {c['rows'][0]['value']}.\n"
             "Decisions needed: approve Metro-North retention offer (Campaign Manager); approve cell-sleep pilot (NOC + CAB).\n")
    call("write_artifact", {"path": "consume/briefings/week-46.md", "content": brief})
    return LABEL + brief


SCRIPTS = {
    "build-orchestrator": orchestrator, "build-business-analyst": business_analyst, "build-source-mapping": source_mapping,
    "build-solution-architect": solution_architect, "build-data-engineer": data_engineer, "build-quality-engineer": quality_engineer,
    "build-ml-engineer": ml_engineer, "build-release-engineer": release_engineer, "build-semantic-context": semantic_context,
    "build-data-product-publisher": data_product_publisher, "build-governance-lineage": governance_lineage,
    "operate-watch-desk": watch_desk, "operate-triage-correlation": triage, "operate-diagnosis-rca": diagnosis,
    "operate-resolution": resolution, "operate-sla-batch-guard": sla_guard, "operate-comms": comms,
    "operate-problem-knowledge": problem_knowledge, "operate-finops-capacity": finops, "operate-service-reporting": service_reporting,
    "consume-ask-your-data": ask_your_data, "consume-insight-scout": insight_scout, "consume-next-best-action": next_best_action,
    "consume-care-copilot": care_copilot, "consume-enterprise-account": enterprise_account, "consume-exec-briefing": exec_briefing,
}


def script_for(agent_id: str):
    return SCRIPTS.get(agent_id, lambda task, call, s: f"{LABEL}No simulator script for {agent_id}.")
