/* DataCrew Telco Studio — demo data.
 * Everything in this file is synthetic. Operator, people, systems and figures are
 * fictional and exist only to drive the simulation. Market facts live in RESEARCH
 * and carry their source URL.
 */
window.DC = {};

/* ------------------------------------------------------------------ */
/* Human roles. Agents never sign a gate; each role is a named person. */
/* ------------------------------------------------------------------ */
DC.ROLES = {
  PO:   { title: 'Data Product Owner',        person: 'Aisha Rahman',   team: 'Business', plane: 'build' },
  ARCH: { title: 'Data Architect',            person: 'Marco Bianchi',  team: 'Dev',      plane: 'build' },
  STEW: { title: 'Data Steward',              person: 'Lena Fischer',   team: 'Governance', plane: 'build' },
  ENG:  { title: 'Engineering Lead',          person: 'Rahul Menon',    team: 'Dev',      plane: 'build' },
  QA:   { title: 'QA Lead',                   person: 'Sofia Alvarez',  team: 'Dev',      plane: 'build' },
  CHG:  { title: 'Change Manager (CAB)',      person: 'Tom O’Neill', team: 'Managed Services', plane: 'operate' },
  SEC:  { title: 'Security & Privacy Officer',person: 'Grace Okafor',   team: 'Risk',     plane: 'all' },
  MLL:  { title: 'ML Lead / Model Risk',      person: 'Kenji Watanabe', team: 'AI',       plane: 'build' },
  NOC:  { title: 'NOC Shift Lead',            person: 'Priya Natarajan',team: 'Managed Services', plane: 'operate' },
  SDM:  { title: 'Service Delivery Manager',  person: 'David Kowalski', team: 'Managed Services', plane: 'operate' },
  PRB:  { title: 'Problem Manager',           person: 'Nadia Haddad',   team: 'Managed Services', plane: 'operate' },
  CMP:  { title: 'Campaign Manager',          person: 'Chloe Martin',   team: 'Business', plane: 'consume' },
  CARE: { title: 'Customer Care Lead',        person: 'Samuel Adeyemi', team: 'Business', plane: 'consume' },
  RES:  { title: 'Research Lead',             person: 'Dr. Ines Duarte',team: 'Research', plane: 'all' }
};

/* Action classes used by every plane (Operate enforces them hardest). */
DC.ACTION_CLASSES = [
  { id: 'A0', name: 'Observe',      desc: 'Read metadata, logs, metrics. No change.',                         approval: 'None' },
  { id: 'A1', name: 'Draft',        desc: 'Write drafts, code on a feature branch, sandbox runs.',            approval: 'None (reviewed at next gate)' },
  { id: 'A2', name: 'Reversible',   desc: 'Low-risk, reversible change in a non-prod or bounded scope.',       approval: '1 named approver' },
  { id: 'A3', name: 'Production',   desc: 'Production change, publication, customer-facing message.',         approval: '2 approvers, change record' },
  { id: 'A4', name: 'Irreversible', desc: 'Deletes, access grants, spend, external disclosure.',               approval: 'Never by agent. Human executes.' }
];

/* ------------------------------------------------------------------ */
/* Agent catalog, by plane                                             */
/* ------------------------------------------------------------------ */
DC.AGENTS = {
  build: [
    { id: 'b-orch',  name: 'Delivery Orchestrator', role: 'Plans the run, routes work, assembles the delivery pack', out: 'Intake brief, plan, delivery pack', cls: 'A1', gate: 'G0' },
    { id: 'b-req',   name: 'Business Analyst',      role: 'Turns the business ask into requirements, rules and consumer questions', out: 'BR-###, NFR-###, CQ-###', cls: 'A1', gate: 'G1' },
    { id: 'b-map',   name: 'Source Mapping Analyst',role: 'Reads BSS/OSS/network metadata, maps to TM Forum SID, classifies PII', out: 'Source inventory, mapping, DQ rules, classification', cls: 'A0', gate: 'G2' },
    { id: 'b-arch',  name: 'Solution Architect',    role: 'Designs the medallion model, data product boundary, ADRs and cost', out: 'Logical + physical design, ADRs', cls: 'A1', gate: 'G3' },
    { id: 'b-eng',   name: 'Data Engineer',         role: 'Generates ingest, dbt and streaming code on a feature branch', out: 'Pull request with code + unit tests', cls: 'A1', gate: 'G4' },
    { id: 'b-qa',    name: 'Quality Engineer',      role: 'Runs tests, reconciles every hop, builds the evidence pack', out: 'Test evidence, reconciliation report', cls: 'A1', gate: 'G5' },
    { id: 'b-ml',    name: 'ML Engineer',           role: 'Builds features, trains and evaluates the model, writes the model card', out: 'Feature set, model, model card, bias report', cls: 'A1', gate: 'G6' },
    { id: 'b-rel',   name: 'Release Engineer',      role: 'Packages the release with verify and rollback steps', out: 'Release bundle, change request', cls: 'A2', gate: 'G7' },
    { id: 'b-sem',   name: 'Semantic & AI Context', role: 'Builds the semantic view, verified questions and AI context', out: 'Semantic view, eval report', cls: 'A1', gate: 'G8' },
    { id: 'b-pub',   name: 'Data Product Publisher',role: 'Writes the contract and marketplace listing; hands over to Operate', out: 'ODCS contract, listing, Operate pack', cls: 'A3', gate: 'G9' },
    { id: 'b-gov',   name: 'Governance & Lineage',  role: 'Keeps catalog, glossary and column lineage true at every gate', out: 'Catalog assets, lineage completeness', cls: 'A1', gate: 'evidence' }
  ],
  operate: [
    { id: 'o-watch', name: 'Watch Desk',            role: 'Watches network, platform and model signals around the clock', out: 'Deduplicated events', cls: 'A0' },
    { id: 'o-tri',   name: 'Triage & Correlation',  role: 'Groups alarms into one incident, scores customer and revenue impact', out: 'Incident with impact score', cls: 'A0' },
    { id: 'o-diag',  name: 'Diagnosis (RCA)',       role: 'Tests root-cause hypotheses against topology, changes and KEDB', out: 'Ranked hypotheses with evidence', cls: 'A0' },
    { id: 'o-res',   name: 'Resolution',            role: 'Proposes runbook actions with blast radius and rollback', out: 'Action plan for approval', cls: 'A2' },
    { id: 'o-sla',   name: 'SLA & Batch Guard',     role: 'Predicts SLA breaches for pipelines, jobs and enterprise circuits', out: 'Breach forecast', cls: 'A0' },
    { id: 'o-comms', name: 'Comms',                 role: 'Drafts stakeholder and customer updates for approval', out: 'Status page / account update drafts', cls: 'A1' },
    { id: 'o-prb',   name: 'Problem & Knowledge',   role: 'Writes known-error and runbook entries after the incident', out: 'KEDB entry, runbook update', cls: 'A1' },
    { id: 'o-fin',   name: 'FinOps & Capacity',     role: 'Tracks compute, energy and licence cost against budget', out: 'Cost anomaly report', cls: 'A0' },
    { id: 'o-rep',   name: 'Service Reporting',     role: 'Writes the service review and MTTR / autonomy metrics', out: 'Service report', cls: 'A0' }
  ],
  consume: [
    { id: 'c-ask',   name: 'Ask-Your-Data',         role: 'Answers business questions through the certified semantic layer only', out: 'Answer + SQL + lineage', cls: 'A0' },
    { id: 'c-ins',   name: 'Insight Scout',         role: 'Finds anomalies and drivers and explains them in business language', out: 'Insight cards', cls: 'A0' },
    { id: 'c-nba',   name: 'Next-Best-Action',      role: 'Turns insight into a proposed action with expected value', out: 'Action proposal for approval', cls: 'A2' },
    { id: 'c-care',  name: 'Care Copilot',          role: 'Supports agents and customers with account, network and bill context', out: 'Suggested reply, case summary', cls: 'A1' },
    { id: 'c-b2b',   name: 'Enterprise Account Agent', role: 'Prepares SLA reviews and renewal risk for account managers', out: 'Account brief', cls: 'A1' },
    { id: 'c-exec',  name: 'Exec Briefing',         role: 'Writes the weekly steering brief across domains', out: 'Steering brief', cls: 'A0' }
  ]
};

/* ------------------------------------------------------------------ */
/* Telco domains × Build / Operate / Consume                           */
/* ------------------------------------------------------------------ */
DC.DOMAINS = [
  { name: 'RAN & Core Network',    build: 'PM counters, alarms and inventory into a cell-level data product', operate: 'Agentic NOC: alarm correlation, RCA, cell parameter fixes', consume: 'Energy-saving and capacity recommendations for planners' },
  { name: 'Service Assurance',     build: 'Service topology + KPI lineage from network to service', operate: 'Closed-loop assurance at TM Forum L3–L4 for defined scenarios', consume: 'Customer-impact view per incident for ops directors' },
  { name: 'BSS: Billing & Charging', build: 'Mediation, rating and invoice reconciliation pipelines', operate: 'Bill-run and mediation SLA guard, failed-job triage', consume: 'Revenue leakage answers for finance and RA teams' },
  { name: 'Customer & Care',       build: 'Subscriber 360 with consent-aware features', operate: 'Care-platform and CRM incident triage', consume: 'Care copilot, churn drivers, case summaries' },
  { name: 'Commercial & Marketing',build: 'Churn, propensity and NBA feature store', operate: 'Model drift watch after tariff or price changes', consume: 'Retention and upsell actions with human sign-off' },
  { name: 'Enterprise / B2B',      build: 'SLA and service health 360 (TMF638 / TMF621)', operate: 'Predicted SLA breach and proactive ticketing', consume: 'Account briefs and renewal risk for account managers' },
  { name: 'Fraud & Security',      build: 'CDR + signalling features for SIM-box and IRSF', operate: 'Fraud alert triage with bounded auto-block', consume: 'Fraud loss dashboards and case packs' },
  { name: 'Field Ops & Workforce', build: 'Work-order, skills and parts data product', operate: 'Dispatch optimisation and truck-roll avoidance', consume: 'First-time-fix insights for field managers' },
  { name: 'Finance & Regulatory',  build: 'Regulatory KPIs with column lineage to source', operate: 'Close-cycle job monitoring', consume: 'Regulator-ready answers with evidence' },
  { name: 'IT & Data Platform',    build: 'Platform-as-code, data contracts, catalog', operate: 'DataOps / AMS: pipeline, warehouse, cost', consume: 'Self-service data marketplace' }
];

/* ------------------------------------------------------------------ */
/* BUILD scenarios. Steps are generated from these fields by app.js.   */
/* ------------------------------------------------------------------ */
DC.BUILD_SCENARIOS = [
  {
    id: 'churn', name: 'Subscriber Churn 360 & Retention', domain: 'Commercial & Marketing', sponsor: 'Chief Commercial Officer',
    ask: 'We are losing post-paid customers after the price rise. I need a weekly churn-risk list with the reasons, so retention can act before contracts end. Care and marketing must use the same numbers.',
    product: 'dp_subscriber_churn_360', baselineWeeks: 12, agentWeeks: 3,
    sources: [
      { sys: 'Billing (Oracle)',      obj: 'INVOICE, ACCOUNT, TARIFF_PLAN',   ingest: 'CDC (GoldenGate)', cls: 'Confidential' },
      { sys: 'CRM',                   obj: 'customer, contract, consent',     ingest: 'API batch (daily)', cls: 'Restricted (PII)' },
      { sys: 'Network xDR lake',      obj: 'data_session_xdr, voice_cdr',     ingest: 'Iceberg on S3',     cls: 'Confidential' },
      { sys: 'Care ticketing',        obj: 'TROUBLE_TICKET (TMF621)',         ingest: 'CDC',               cls: 'Internal' },
      { sys: 'NPS survey tool',       obj: 'survey_response',                 ingest: 'File drop (daily)', cls: 'Internal' }
    ],
    rules: ['BR-01 Churn = post-paid line disconnected or ported out within 30 days of the score date', 'BR-02 Exclude lines in collections or fraud hold', 'BR-03 Use consent flag before any marketing feature is used'],
    dq: ['MSISDN unique per active line', 'Invoice total = sum of invoice lines (±0.01)', 'Consent flag not null for marketing-eligible lines', 'xDR completeness ≥ 99.5% per day'],
    metrics: [{ n: 'churn_rate_30d', d: 'Lines churned in 30 days / active lines at start' }, { n: 'at_risk_arpu', d: 'Monthly ARPU of lines with risk score ≥ 0.7' }, { n: 'save_rate', d: 'Saved lines / lines offered retention' }],
    cqs: ['Which regions have the highest churn risk this week?', 'What are the top three drivers of churn for high-value customers?', 'How much monthly revenue is at risk?'],
    ml: { model: 'Gradient-boosted churn classifier', target: 'churned_30d', features: 'tenure, bill shock, dropped-call rate, data throughput p10, care contacts 30d, contract end distance, NPS', metric: 'AUC 0.84, top-decile lift 4.1' },
    consumers: ['Retention marketing', 'Care copilot', 'Finance'],
    tables: { bronze: 'brz_billing_invoice', silver: 'slv_subscriber_month', gold: 'gld_churn_risk_weekly' }
  },
  {
    id: 'energy', name: 'RAN Energy Savings Insights', domain: 'RAN & Core Network', sponsor: 'Network Operations Director',
    ask: 'Energy is our fastest-growing network cost. Show me which cells can sleep at night without hurting customers, and how much we would save.',
    product: 'dp_ran_energy_efficiency', baselineWeeks: 14, agentWeeks: 4,
    sources: [
      { sys: 'OSS PM (15-min counters)', obj: 'pm_cell_kpi (PRB use, users, throughput)', ingest: 'Streaming (Kafka)', cls: 'Internal' },
      { sys: 'Network inventory',        obj: 'site, cell, carrier (TMF639)',            ingest: 'API batch (daily)', cls: 'Internal' },
      { sys: 'Smart power meters',       obj: 'site_energy_kwh',                         ingest: 'File drop (hourly)', cls: 'Internal' },
      { sys: 'Alarm manager',            obj: 'fm_alarm',                                ingest: 'Streaming',         cls: 'Internal' }
    ],
    rules: ['BR-01 A cell is a sleep candidate if PRB use < 10% for 4+ consecutive hours over 14 of the last 21 nights', 'BR-02 Never propose sleep for cells flagged as emergency-service coverage', 'BR-03 Savings use the site tariff in force on the day'],
    dq: ['Counter completeness ≥ 98% per cell-day', 'No negative energy readings', 'Every cell maps to exactly one site', 'Timestamp aligned to 15-min grid'],
    metrics: [{ n: 'kwh_per_tb', d: 'Site energy kWh / data volume TB' }, { n: 'sleep_candidate_cells', d: 'Cells meeting BR-01 and BR-02' }, { n: 'est_annual_saving_eur', d: 'Modelled kWh saved × tariff' }],
    cqs: ['Which clusters waste the most energy at night?', 'What is the estimated saving if we enable sleep on all candidates?', 'Did any sleep window hurt customer KPIs last month?'],
    ml: { model: 'Per-cell traffic forecaster (hourly)', target: 'prb_util_next_24h', features: 'hour, weekday, holiday, events, neighbour load, weather', metric: 'MAPE 7.9% on night hours' },
    consumers: ['RAN planning', 'NOC', 'Energy & sustainability'],
    tables: { bronze: 'brz_pm_cell_kpi', silver: 'slv_cell_hour', gold: 'gld_cell_energy_daily' }
  },
  {
    id: 'ra', name: 'Revenue Assurance: Usage-to-Bill', domain: 'BSS: Billing & Charging', sponsor: 'CFO / Head of Revenue Assurance',
    ask: 'Audit says we leak revenue between the network and the bill. I need a daily reconciliation from switch to invoice with every gap explained.',
    product: 'dp_usage_to_bill_recon', baselineWeeks: 10, agentWeeks: 2.5,
    sources: [
      { sys: 'Mediation',           obj: 'mediated_cdr',               ingest: 'File drop (15-min)', cls: 'Confidential' },
      { sys: 'Online charging (OCS)',obj: 'rated_event',               ingest: 'CDC',               cls: 'Confidential' },
      { sys: 'Billing (Oracle)',    obj: 'INVOICE_LINE',               ingest: 'CDC (GoldenGate)',  cls: 'Confidential' },
      { sys: 'Interconnect',        obj: 'tap_file, settlement',       ingest: 'File drop (daily)', cls: 'Confidential' }
    ],
    rules: ['BR-01 Every chargeable network event must reach a rated event within 4 hours', 'BR-02 Every rated event must reach an invoice line in its bill cycle', 'BR-03 Zero-rated events are leakage only if the tariff says chargeable'],
    dq: ['CDR sequence numbers have no gaps per switch per hour', 'Rated amount ≥ 0', 'Bill cycle id valid for account', 'Duplicate CDR rate < 0.01%'],
    metrics: [{ n: 'leakage_eur', d: 'Value of chargeable events with no invoice line' }, { n: 'recon_match_rate', d: 'Matched events / chargeable events' }, { n: 'mean_detect_hours', d: 'Hours from event to leakage detection' }],
    cqs: ['How much revenue leaked last month and where?', 'Which switch or tariff has the most unmatched events?', 'Is leakage trending up since the charging upgrade?'],
    ml: { model: 'Isolation-forest anomaly detector on recon gaps', target: 'unsupervised', features: 'switch, tariff, hour, event type, gap size', metric: 'Precision@50 = 0.78 on labelled history' },
    consumers: ['Revenue assurance', 'Finance', 'Internal audit'],
    tables: { bronze: 'brz_mediated_cdr', silver: 'slv_event_chain', gold: 'gld_recon_daily' }
  },
  {
    id: 'b2b', name: 'Enterprise SLA & Service Health 360', domain: 'Enterprise / B2B', sponsor: 'Enterprise Business Director',
    ask: 'Our top 200 enterprise customers find SLA breaches before we do. Give account managers one view of service health, open tickets and SLA credit exposure.',
    product: 'dp_enterprise_service_health', baselineWeeks: 9, agentWeeks: 2,
    sources: [
      { sys: 'Service inventory', obj: 'service, resource (TMF638/639)', ingest: 'API batch (hourly)', cls: 'Internal' },
      { sys: 'Trouble ticketing', obj: 'trouble_ticket (TMF621)',        ingest: 'CDC',               cls: 'Internal' },
      { sys: 'Transport KPIs',    obj: 'circuit_kpi (latency, loss)',    ingest: 'Streaming',         cls: 'Internal' },
      { sys: 'Contract mgmt',     obj: 'sla_term, credit_rule',          ingest: 'API batch (daily)', cls: 'Confidential' }
    ],
    rules: ['BR-01 Availability is measured per circuit per calendar month, excluding approved maintenance windows', 'BR-02 SLA credit uses the contract version in force on the breach date', 'BR-03 A ticket counts against SLA only if customer-impacting'],
    dq: ['Every circuit maps to one customer account', 'Ticket open < close timestamp', 'KPI samples ≥ 95% per circuit-day', 'Maintenance windows have an approved change id'],
    metrics: [{ n: 'availability_pct', d: 'Up minutes / scheduled minutes' }, { n: 'sla_credit_exposure_eur', d: 'Credits due if current month closed now' }, { n: 'mttr_hours', d: 'Mean time to restore customer-impacting tickets' }],
    cqs: ['Which top-200 accounts are at risk of an SLA breach this month?', 'What is our SLA credit exposure?', 'Which circuits fail most often?'],
    ml: null,
    consumers: ['Account managers', 'Enterprise NOC', 'Finance'],
    tables: { bronze: 'brz_trouble_ticket', silver: 'slv_circuit_day', gold: 'gld_account_sla_monthly' }
  },
  {
    id: 'fraud', name: 'SIM-box & IRSF Fraud Signals', domain: 'Fraud & Security', sponsor: 'Head of Fraud Management',
    ask: 'SIM-box bypass and international revenue share fraud cost us every week. I want daily risk scores per SIM with evidence the fraud team can act on.',
    product: 'dp_fraud_signals', baselineWeeks: 11, agentWeeks: 3,
    sources: [
      { sys: 'Voice CDR',          obj: 'voice_cdr',                    ingest: 'File drop (15-min)', cls: 'Confidential' },
      { sys: 'Signalling probes',  obj: 'ss7_diameter_events',          ingest: 'Streaming',          cls: 'Restricted' },
      { sys: 'Subscriber KYC',     obj: 'kyc_record',                   ingest: 'CDC',                cls: 'Restricted (PII)' },
      { sys: 'Roaming',            obj: 'tap_in_records',               ingest: 'File drop (daily)',  cls: 'Confidential' }
    ],
    rules: ['BR-01 A SIM-box candidate makes > 90% outbound on-net calls from one cell with < 2 distinct IMEIs per day', 'BR-02 IRSF watch-list numbers come from the GSMA hot-number feed', 'BR-03 Scores are evidence for analysts; blocking stays a human decision'],
    dq: ['IMSI present on every CDR', 'Call duration ≥ 0', 'Hot-number list not older than 24 h', 'KYC joins only through pseudonymised key'],
    metrics: [{ n: 'fraud_loss_eur', d: 'Confirmed fraud value' }, { n: 'alerts_precision', d: 'Confirmed / reviewed alerts' }, { n: 'time_to_block_h', d: 'Hours from first fraud event to block' }],
    cqs: ['How many SIM-box candidates did we find this week?', 'What was confirmed fraud loss last month?', 'Which destinations drive IRSF exposure?'],
    ml: { model: 'Graph + gradient-boosted SIM-box classifier', target: 'confirmed_simbox', features: 'call fan-out, cell stickiness, IMEI churn, on-net ratio, top-up pattern', metric: 'Precision 0.91 at 0.6 recall' },
    consumers: ['Fraud analysts', 'Interconnect', 'Security operations'],
    tables: { bronze: 'brz_voice_cdr', silver: 'slv_sim_day', gold: 'gld_fraud_score_daily' }
  }
];

/* Gate definitions for Build. Approvers by role key. */
DC.BUILD_GATES = {
  G0: { name: 'Intake accepted',           approvers: ['PO'],          check: ['Business outcome stated', 'Sponsor named', 'Stack profile valid'] },
  G1: { name: 'Requirements approved',     approvers: ['PO', 'STEW'],  check: ['Every rule has an id', 'Consumer questions in business language', 'NFRs for freshness and retention'] },
  G2: { name: 'Mapping & classification',  approvers: ['STEW', 'SEC'], check: ['Every source column classified', 'PII has a masking policy', 'Ingestion pattern per table'] },
  G3: { name: 'Design approved',           approvers: ['ARCH'],        check: ['ADRs signed', 'Cost estimate with arithmetic', 'Data product boundary drawn'] },
  G4: { name: 'Pull request merged',       approvers: ['ENG'],         check: ['All unit tests pass', 'No secrets in code', 'Code matches design'] },
  G5: { name: 'Quality evidence accepted', approvers: ['QA'],          check: ['Hop reconciliation within tolerance', 'DQ rules executed', 'Idempotent rerun'] },
  G6: { name: 'Model risk sign-off',       approvers: ['MLL', 'SEC'],  check: ['Model card complete', 'Bias test per segment', 'No restricted features'] },
  G7: { name: 'Release to production',     approvers: ['CHG', 'ENG'],  check: ['Tested commit = deployed commit', 'Rollback rehearsed', 'Change record raised'] },
  G8: { name: 'Semantic & AI certified',   approvers: ['STEW', 'PO'],  check: ['Every CQ answered or justified', 'Eval set passed', 'Refusal cases pass'] },
  G9: { name: 'Publish data product',      approvers: ['PO', 'STEW'],  check: ['Contract versioned', 'Lineage complete on contract columns', 'Operate pack delivered'] }
};

/* ------------------------------------------------------------------ */
/* OPERATE scenarios                                                    */
/* ------------------------------------------------------------------ */
DC.OPERATE_SCENARIOS = [
  {
    id: 'noc', name: 'Metro-North RAN cluster degradation', tower: 'Network NOC', autonomyFrom: 'L2', autonomyTo: 'L4 (scenario)',
    summary: 'Dropped-call rate jumps on 14 cells in one cluster at 18:40. Same minute: a transport link flaps and a parameter change was pushed at 18:31.',
    signals: [
      ['18:40:12', 'PM',        'DCR > 3.5% on 14 cells, cluster MN-07', 'crit'],
      ['18:40:31', 'Alarm',     'S1 link flap on router MN-AGG-2 (x6 in 2 min)', 'warn'],
      ['18:40:44', 'Alarm',     '212 duplicate cell-unavailable alarms', 'warn'],
      ['18:41:02', 'Change',    'CR-48213: handover offset change pushed 18:31 to 14 cells', 'info'],
      ['18:41:20', 'Care',      'Care calls from postcode MN7 up 3.2× vs baseline', 'warn']
    ],
    correlation: '236 raw alarms → 1 incident (INC-90311). Impact: ~41k subscribers, 3 enterprise sites, est. €18k/h revenue at risk.',
    hypotheses: [
      { h: 'Handover offset change CR-48213 causes ping-pong handovers', conf: 0.71, ev: 'Only the 14 changed cells degraded; handover failures up 9×; started 9 min after push' },
      { h: 'Transport link MN-AGG-2 flapping', conf: 0.22, ev: 'Flaps began after DCR rise; neighbouring cells on same router are clean' },
      { h: 'Interference from new neighbour site', conf: 0.07, ev: 'No new sites in 30 days in KEDB or inventory' }
    ],
    actions: [
      { id: 'ACT-1', desc: 'Roll back CR-48213 on the 14 cells (stored config)', cls: 'A3', approvers: ['NOC', 'CHG'], blast: '14 cells, ~41k subs', rollback: 'Re-apply CR-48213', verify: 'DCR < 1.2% within 15 min' },
      { id: 'ACT-2', desc: 'Open transport ticket for MN-AGG-2 flap (no change)', cls: 'A1', approvers: [], blast: 'None', rollback: 'n/a', verify: 'Ticket acknowledged' }
    ],
    verify: 'DCR back to 0.9% in 11 min. Handover failures normal. Care call rate falling.',
    comms: 'We fixed a network issue that affected calls in the Metro-North area between 18:40 and 19:02 today. Service is back to normal. Enterprise customers at 3 sites will receive an incident report within 24 hours.',
    commsApprovers: ['SDM'],
    kedb: 'KE-2207: Handover offset changes > 2 dB on dense urban clusters cause ping-pong. Pre-check: simulate in digital twin; push in waves of 3 cells with 10-min guard.',
    metrics: { mttd: '0.5 min', mttr: '22 min', baseline: '2 h 40 min', alarms: '236 → 1' }
  },
  {
    id: 'dataops', name: 'Nightly churn mart SLA breach', tower: 'Data Platform AMS', autonomyFrom: 'L2', autonomyTo: 'L3',
    summary: 'The 06:00 churn-risk mart is late. Mediation file feed is 2 h behind and a dbt model failed on a schema change upstream.',
    signals: [
      ['03:12:05', 'Feed',  'Mediation file feed lag 118 min (SLA 30)', 'warn'],
      ['03:40:41', 'dbt',   'Model slv_subscriber_month failed: column “plan_code” not found', 'crit'],
      ['03:41:10', 'Schema','Source BILLING.TARIFF_PLAN renamed plan_code → tariff_code (deploy 22:15)', 'info'],
      ['03:45:00', 'SLA',   'Forecast: gld_churn_risk_weekly 06:00 SLA will miss by ~95 min', 'crit']
    ],
    correlation: '2 failures, 1 cause chain. Downstream: churn mart, care copilot features, Monday retention campaign.',
    hypotheses: [
      { h: 'Upstream column rename broke staging model contract', conf: 0.88, ev: 'Billing release note RN-772 lists rename; data contract test caught it' },
      { h: 'Mediation lag is a separate capacity issue', conf: 0.64, ev: 'Mediation host CPU 97% since 02:50; unrelated to rename' }
    ],
    actions: [
      { id: 'ACT-1', desc: 'Hotfix PR: map tariff_code → plan_code in stg model; run in dev, then prod rerun', cls: 'A3', approvers: ['ENG', 'CHG'], blast: '1 model + 4 downstream', rollback: 'Revert PR, rerun previous version', verify: 'dbt build green, row counts within 0.5% of last week' },
      { id: 'ACT-2', desc: 'Scale mediation parser workers 4 → 8 for 3 h', cls: 'A2', approvers: ['SDM'], blast: 'Mediation cluster, +€36 cost', rollback: 'Scale back to 4', verify: 'Lag < 30 min' }
    ],
    verify: 'Lag back to 12 min at 04:31. dbt build green 05:22. Mart delivered 05:41, within SLA.',
    comms: 'The weekly churn-risk list was at risk this morning due to an upstream billing change. It was delivered at 05:41, on time. No action needed from retention teams.',
    commsApprovers: ['SDM'],
    kedb: 'KE-1189: Upstream schema rename without contract notice. Fix: add billing release feed to change radar; contract tests on all billing staging models.',
    metrics: { mttd: '1 min', mttr: '1 h 52 min', baseline: '5 h 30 min', alarms: '2 → 1' }
  },
  {
    id: 'mlops', name: 'Churn model drift after tariff change', tower: 'AI / MLOps', autonomyFrom: 'L1', autonomyTo: 'L3',
    summary: 'Two weeks after a new unlimited-data tariff, the churn model’s precision drops and the save team reports many false positives.',
    signals: [
      ['Mon 07:00', 'Model',  'PSI on feature data_throughput_p10 = 0.31 (threshold 0.2)', 'warn'],
      ['Mon 07:00', 'Model',  'Precision@top-decile 0.62 vs 0.78 at validation', 'crit'],
      ['Mon 07:05', 'Business','Save team: 38% of contacted customers had no intent to leave', 'warn'],
      ['Mon 07:06', 'Catalog','Tariff UL-25 launched 14 days ago, 210k migrations', 'info']
    ],
    correlation: 'Feature drift linked to tariff UL-25 migration. 210k lines changed usage pattern without changing churn intent.',
    hypotheses: [
      { h: 'Tariff migration changed throughput distribution; model reads it as dissatisfaction', conf: 0.82, ev: 'Drift concentrated in migrated lines; non-migrated precision steady at 0.77' },
      { h: 'Label delay: recent churners not yet in labels', conf: 0.18, ev: 'Label lag normal (30 d)' }
    ],
    actions: [
      { id: 'ACT-1', desc: 'Retrain with tariff_family feature and post-migration window; shadow for 7 days', cls: 'A2', approvers: ['MLL'], blast: 'Shadow only, no customer impact', rollback: 'Keep current champion', verify: 'Shadow precision ≥ 0.75' },
      { id: 'ACT-2', desc: 'Promote challenger to champion after shadow', cls: 'A3', approvers: ['MLL', 'PO'], blast: 'Weekly churn list for ~1.2M lines', rollback: 'Re-promote previous model version', verify: 'Save-team false positive rate < 20%' }
    ],
    verify: 'Challenger shadow precision 0.79. Promoted Monday. False-positive feedback down to 14%.',
    comms: 'The churn-risk model was updated to account for the new unlimited tariff. Lists from next Monday will be more accurate. Retention scripts do not change.',
    commsApprovers: ['PO'],
    kedb: 'KE-3011: Tariff launches shift usage features. Add tariff-launch event to drift monitor; auto-open shadow retrain proposal.',
    metrics: { mttd: '1 day', mttr: '9 days', baseline: '6–8 weeks', alarms: '4 → 1' }
  }
];

/* ------------------------------------------------------------------ */
/* CONSUME: personas and certified answers                             */
/* ------------------------------------------------------------------ */
DC.PERSONAS = [
  { id: 'cco',  title: 'Chief Commercial Officer', product: 'dp_subscriber_churn_360' },
  { id: 'nod',  title: 'Network Operations Director', product: 'dp_ran_energy_efficiency' },
  { id: 'cfo',  title: 'CFO / Revenue Assurance', product: 'dp_usage_to_bill_recon' },
  { id: 'care', title: 'Customer Care Lead', product: 'dp_subscriber_churn_360' },
  { id: 'eam',  title: 'Enterprise Account Manager', product: 'dp_enterprise_service_health' }
];

DC.ANSWERS = [
  { p: 'cco', q: 'Which regions have the highest churn risk this week?', kw: ['region', 'churn', 'risk'],
    a: 'North-East and Metro-North lead churn risk this week. Both regions saw the most dropped-call complaints after the price rise.',
    table: [['Region', 'At-risk lines', 'Risk vs last wk'], ['North-East', '18,420', '+21%'], ['Metro-North', '15,980', '+34%'], ['Coastal', '9,110', '+4%'], ['Capital', '8,760', '−2%']],
    sql: "SELECT region, COUNT(*) AS at_risk_lines\nFROM SEMANTIC.churn_360\nWHERE risk_score >= 0.7 AND score_week = CURRENT_WEEK\nGROUP BY region ORDER BY 2 DESC;",
    lineage: 'gld_churn_risk_weekly ← slv_subscriber_month ← Billing.INVOICE, CRM.contract, xDR', conf: 'High (verified question VQ-01)',
    action: { title: 'Launch retention offer to 4,212 high-value at-risk lines in Metro-North', cls: 'A3', approvers: ['CMP', 'SEC'], value: 'Expected save: ~610 lines, €29k MRR protected', checks: ['Consent flag = marketing-OK on all 4,212', 'Offer within approved discount band', 'Holdout group of 10% kept'] } },
  { p: 'cco', q: 'What are the top three drivers of churn for high-value customers?', kw: ['driver', 'why', 'reason'],
    a: 'For lines with ARPU above €45, the model’s top drivers are bill shock after the price rise, contract ending within 60 days, and two or more care contacts in 30 days.',
    table: [['Driver', 'Share of risk (SHAP)', 'Lines affected'], ['Bill shock > 15%', '31%', '22,300'], ['Contract end < 60 d', '24%', '17,900'], ['Care contacts ≥ 2', '17%', '11,450']],
    sql: "SELECT driver, AVG(shap_share) FROM SEMANTIC.churn_drivers\nWHERE arpu_band = 'HIGH' GROUP BY driver ORDER BY 2 DESC LIMIT 3;",
    lineage: 'gld_churn_drivers ← model churn_gbm v7 (model card MC-07)', conf: 'High (verified question VQ-02)' },
  { p: 'cco', q: 'How much monthly revenue is at risk?', kw: ['revenue', 'arpu', 'money', 'mrr'],
    a: 'Monthly recurring revenue at risk is €2.31M across 52,270 lines with risk score 0.7 or higher. That is 3.4% of post-paid MRR.',
    table: [['Segment', 'Lines', 'MRR at risk'], ['High value', '14,880', '€1.12M'], ['Mid value', '21,640', '€0.86M'], ['Low value', '15,750', '€0.33M']],
    sql: "SELECT value_segment, COUNT(*), SUM(arpu) FROM SEMANTIC.churn_360\nWHERE risk_score >= 0.7 GROUP BY 1;",
    lineage: 'metric at_risk_arpu (BR-01, glossary: “At-risk ARPU”)', conf: 'High (certified metric)' },
  { p: 'nod', q: 'Which clusters waste the most energy at night?', kw: ['energy', 'cluster', 'night', 'waste'],
    a: 'Five clusters account for 46% of night-time energy on cells with under 10% load. Industrial-South is the largest.',
    table: [['Cluster', 'Idle-night kWh / day', 'Sleep candidates'], ['Industrial-South', '4,820', '61 cells'], ['Airport-East', '3,910', '44 cells'], ['Business-Park-W', '3,350', '38 cells'], ['University', '2,780', '29 cells']],
    sql: "SELECT cluster, SUM(idle_night_kwh) FROM SEMANTIC.cell_energy\nWHERE day >= CURRENT_DATE - 21 GROUP BY 1 ORDER BY 2 DESC;",
    lineage: 'gld_cell_energy_daily ← slv_cell_hour ← OSS PM, power meters', conf: 'High (verified question VQ-11)',
    action: { title: 'Raise change: enable cell sleep 01:00–05:00 on 38 cells in Business-Park-W (pilot)', cls: 'A3', approvers: ['NOC', 'CHG'], value: 'Est. saving €41k / year for this pilot', checks: ['No emergency-coverage cells (BR-02)', 'Forecast load < 10% on all 38 cells', 'Auto-wake if users > 15 per cell'] } },
  { p: 'nod', q: 'What is the estimated saving if we enable sleep on all candidates?', kw: ['saving', 'save', 'estimate'],
    a: 'Enabling sleep on all 412 candidate cells would save about 2.9 GWh a year, roughly €610k at current tariffs. The forecast holds customer impact under 0.1% of night sessions.',
    table: [['Scope', 'Cells', 'GWh / yr', '€ / yr'], ['Pilot (Business-Park-W)', '38', '0.20', '41k'], ['Top 5 clusters', '201', '1.52', '318k'], ['All candidates', '412', '2.91', '610k']],
    sql: "SELECT scope, SUM(est_kwh_saved)/1e6, SUM(est_saving_eur)\nFROM SEMANTIC.cell_energy_scenarios GROUP BY 1;",
    lineage: 'metric est_annual_saving_eur (BR-03) ← traffic forecaster v3', conf: 'Medium (model-based estimate)' },
  { p: 'cfo', q: 'How much revenue leaked last month and where?', kw: ['leak', 'leakage', 'revenue assurance'],
    a: 'October leakage was €184k, down 22% on September. 61% came from roaming data events that were rated but missed the bill cycle.',
    table: [['Leak point', '€', 'Share'], ['Rated, not billed (roaming data)', '112k', '61%'], ['Mediated, not rated', '47k', '26%'], ['Zero-rated in error', '25k', '13%']],
    sql: "SELECT leak_point, SUM(leakage_eur) FROM SEMANTIC.recon\nWHERE month = '2026-10' GROUP BY 1 ORDER BY 2 DESC;",
    lineage: 'gld_recon_daily ← slv_event_chain ← Mediation, OCS, Billing', conf: 'High (verified question VQ-21)',
    action: { title: 'Open RA case and re-bill 3,140 roaming events (€112k)', cls: 'A3', approvers: ['PO', 'CHG'], value: '€112k recovered', checks: ['Events inside re-bill window', 'Customer notice template approved', 'Finance posting period open'] } },
  { p: 'cfo', q: 'Is leakage trending up since the charging upgrade?', kw: ['trend', 'upgrade', 'charging'],
    a: 'No. Leakage rose for 9 days after the charging upgrade on 2 Sept, then fell below the previous baseline once the rating hotfix landed.',
    table: [['Period', 'Avg daily leakage'], ['Aug (before)', '€7.1k'], ['2–11 Sept', '€11.8k'], ['Oct', '€5.9k']],
    sql: "SELECT period, AVG(leakage_eur) FROM SEMANTIC.recon_daily GROUP BY 1;", lineage: 'metric leakage_eur', conf: 'High' },
  { p: 'care', q: 'Why are care calls up in Metro-North today?', kw: ['care', 'calls', 'why', 'metro'],
    a: 'Care calls from Metro-North rose 3.2× at 18:40 because of a network incident (INC-90311). It was fixed at 19:02. Agents can use the approved script.',
    table: [['Topic', 'Calls since 18:40'], ['Dropped calls', '1,204'], ['No data', '418'], ['Billing', '96']],
    sql: "SELECT topic, COUNT(*) FROM SEMANTIC.care_contacts\nWHERE region='Metro-North' AND ts >= '18:40' GROUP BY 1;",
    lineage: 'care_contacts ← Care ticketing; incident link from Operate INC-90311', conf: 'High',
    action: { title: 'Send proactive SMS apology + 1 GB data credit to 41k affected subscribers', cls: 'A3', approvers: ['CARE', 'SEC'], value: 'Avoids est. 2,900 inbound calls', checks: ['Affected list from incident footprint only', 'Message text approved by comms', 'Opt-out honoured'] } },
  { p: 'care', q: 'Summarise this customer’s last three contacts', kw: ['summarise', 'summary', 'customer', 'contacts'],
    a: 'Customer ****4471 called three times in 12 days: dropped calls at home, a bill query about roaming, and a cancellation question. Risk score 0.83. Suggested: acknowledge the network fix, explain the roaming charge, offer the loyalty plan.',
    table: [['Date', 'Channel', 'Topic', 'Outcome'], ['4 Nov', 'App chat', 'Dropped calls', 'Ticket raised'], ['9 Nov', 'Voice', 'Roaming charge', 'Explained'], ['15 Nov', 'Voice', 'Cancellation', 'Callback booked']],
    sql: "-- Care copilot reads via row-access policy for the agent's queue only\nSELECT * FROM SEMANTIC.case_timeline WHERE customer_key = :ctx_customer;",
    lineage: 'case_timeline (masked view) ← CRM, Care ticketing', conf: 'High (masked: MSISDN shown last 4 only)' },
  { p: 'eam', q: 'Which top-200 accounts are at risk of an SLA breach this month?', kw: ['sla', 'breach', 'account', 'enterprise'],
    a: 'Seven top-200 accounts are forecast to breach availability SLA this month. Three share one aggregation router in the East region.',
    table: [['Account', 'Avail. MTD', 'SLA', 'Credit exposure'], ['Northwind Logistics', '99.71%', '99.9%', '€18.4k'], ['Contoso Health', '99.82%', '99.95%', '€12.0k'], ['Fabrikam Retail', '99.86%', '99.9%', '€6.1k']],
    sql: "SELECT account, availability_mtd, sla_target, credit_exposure\nFROM SEMANTIC.account_sla WHERE breach_forecast = TRUE;",
    lineage: 'gld_account_sla_monthly ← Service inventory, Tickets, Transport KPIs, Contracts', conf: 'High',
    action: { title: 'Open proactive tickets + schedule SLA review calls for 7 accounts', cls: 'A2', approvers: ['SDM'], value: 'Protects €58k credit exposure + renewal risk', checks: ['Account owner notified', 'No customer message before NOC confirms root cause'] } },
  { p: 'eam', q: 'What is our SLA credit exposure?', kw: ['credit', 'exposure'],
    a: 'If November closed now, SLA credits due would be €58.2k across 7 accounts, versus €21k in October.',
    table: [['Month', 'Credit exposure'], ['Sep', '€17.5k'], ['Oct', '€21.0k'], ['Nov (to date)', '€58.2k']],
    sql: "SELECT month, SUM(sla_credit_exposure_eur) FROM SEMANTIC.account_sla GROUP BY 1;", lineage: 'metric sla_credit_exposure_eur (BR-02)', conf: 'High' }
];

/* Guardrail replies for the consume agent */
DC.GUARDRAILS = [
  { kw: ['phone number', 'msisdn', 'address', 'home address', 'id number', 'passport', 'export all customers', 'list customers with'], reply: 'I can’t return personal identifiers. The semantic layer masks PII for your role. I can give you counts or segments instead, or route an access request to the Data Steward.', rule: 'Guardrail: PII masking (Restricted class)' },
  { kw: ['competitor', 'stock price', 'weather tomorrow', 'football'], reply: 'That question is outside the certified data products I can use. I only answer from governed telco data products so every answer has lineage.', rule: 'Guardrail: out-of-scope' },
  { kw: ['delete', 'drop table', 'grant', 'disable alarm'], reply: 'I can’t change systems from here. I can draft a request, and a named approver decides. Irreversible actions (class A4) are always carried out by people.', rule: 'Guardrail: action class A4' }
];

/* ------------------------------------------------------------------ */
/* Team enablement                                                     */
/* ------------------------------------------------------------------ */
DC.TEAMS = [
  { id: 'dev', name: 'Dev & Data Engineering', lead: 'Engineering Lead',
    shift: 'From hand-writing pipelines to reviewing agent pull requests against an approved design.',
    agents: ['Source Mapping Analyst', 'Solution Architect', 'Data Engineer', 'Quality Engineer', 'Release Engineer'],
    gates: ['G3 Design (Data Architect)', 'G4 Merge (Engineering Lead)', 'G5 Quality (QA Lead)', 'G7 Release (with CAB)'],
    kit: ['Stack profile (dbt, Snowflake/Databricks, Kafka, GoldenGate)', 'TM Forum SID mapping pack', 'PR review checklist', 'Golden synthetic datasets per domain'],
    kpis: ['Lead time request → data product', 'PR first-pass approval rate', 'Defects found after G5', 'Share of code generated vs rewritten'],
    plan: ['Days 1–30: one slice (churn 360) in sandbox, every gate run by people', 'Days 31–60: two domains in parallel, reuse mapping packs', 'Days 61–90: agents own WP-1..3 by default; engineers own design and review'] },
  { id: 'ams', name: 'Managed Services (AMS / NOC)', lead: 'Service Delivery Manager',
    shift: 'From reading alarms to approving ranked, evidenced actions with a rollback attached.',
    agents: ['Watch Desk', 'Triage & Correlation', 'Diagnosis (RCA)', 'Resolution', 'SLA & Batch Guard', 'Comms', 'Problem & Knowledge'],
    gates: ['A2 actions: NOC Shift Lead or SDM', 'A3 actions: + Change Manager', 'Customer comms: SDM', 'KEDB entries: Problem Manager'],
    kit: ['environment.yaml / signals.yaml / kedb.yaml / actions.yaml from Build', 'Runbooks as code', 'Autonomy level per scenario (TM Forum L0–L5)', 'Shift handover brief template'],
    kpis: ['MTTD / MTTR per tower', 'Alarm-to-incident compression', 'Share of incidents with agent-proposed fix accepted', 'Repeat incidents after KEDB entry'],
    plan: ['Days 1–30: shadow mode, agents propose, people act', 'Days 31–60: A2 actions with one-click approval for 5 scenarios', 'Days 61–90: L4 for two validated scenarios; monthly autonomy review'] },
  { id: 'ai', name: 'AI & ML Engineering', lead: 'ML Lead',
    shift: 'From building one model at a time to running a governed model factory on certified data products.',
    agents: ['ML Engineer', 'Semantic & AI Context', 'Ask-Your-Data', 'Next-Best-Action', 'Drift watch (Operate)'],
    gates: ['G6 Model risk (ML Lead + Security & Privacy)', 'G8 Semantic & AI certification', 'Champion promotion (A3)'],
    kit: ['Feature store contracts', 'Model card + bias template', 'Evaluation sets per consumer question', 'Prompt and context registry'],
    kpis: ['Time from data product to model in shadow', 'Eval pass rate per release', 'Drift detection to retrain time', 'Answer accuracy on verified questions'],
    plan: ['Days 1–30: churn and energy models on certified gold only', 'Days 31–60: eval harness gates every agent and prompt change', 'Days 61–90: drift-to-retrain loop at L3 with ML Lead approval'] },
  { id: 'res', name: 'Research & Innovation', lead: 'Research Lead',
    shift: 'From one-off notebooks to experiments that run on governed data and graduate through the same gates.',
    agents: ['Insight Scout', 'Ask-Your-Data (sandbox)', 'ML Engineer (experiment mode)', 'Governance & Lineage'],
    gates: ['Experiment charter (Research Lead + Data Steward)', 'Graduation to Build at G1', 'Telco benchmark review (e.g. GSMA Telco Capability Index)'],
    kit: ['Synthetic data generators (CDR, PM counters, tickets)', 'Benchmark harness for telco-tuned models', 'Digital-twin sandbox for network actions', 'Research-to-product template'],
    kpis: ['Experiments started / graduated', 'Time from idea to governed prototype', 'Benchmark score on telco tasks', 'Reuse of research assets in Build'],
    plan: ['Days 1–30: sandbox with synthetic CDR / PM data', 'Days 31–60: two experiments (RAN sleep policy, care intent) with charters', 'Days 61–90: one graduates into Build via G1'] }
];

/* ------------------------------------------------------------------ */
/* Market research. Each item cites a source.                          */
/* ------------------------------------------------------------------ */
DC.RESEARCH = [
  { k: 'Autonomous networks', t: 'Operators target Level 4 in defined scenarios, not whole networks. 81% target L4+ by 2030; about 20% expect it by 2027. Telefónica ended 2025 with 12 operational L4 use cases.', src: 'TelecomLead / TM Forum, 2026', url: 'https://telecomlead.com/5g/autonomous-telecom-networks-2026-deutsche-telekom-telefonica-china-mobile-and-verizon-push-toward-level-4-127994' },
  { k: 'L4 validation', t: 'TM Forum reports operators picking up pace toward L4, with agentic AI the main driver. Validations are scoped to single use cases (for example service assurance on one service).', src: 'Fierce Network, 2026', url: 'https://www.fierce-network.com/cloud/telcos-hit-level-4-autonomous-network-milestone-says-tm-forum' },
  { k: 'Adoption gap', t: 'Nearly all telcos pilot AI, but only 57% scale use cases across multiple domains, led by customer service and networks. Value comes from redesigning end-to-end processes, not isolated pilots.', src: 'McKinsey, Telcos’ AI inflection point', url: 'https://www.mckinsey.com.br/industries/technology-media-and-telecommunications/our-insights/telcos-ai-inflection-point-what-leaders-do-to-capture-value' },
  { k: 'Agentic monetisation', t: 'McKinsey argues agentic AI opens new monetisation, beyond cost, for operators that rebuild operating models around it.', src: 'TelecomTV / McKinsey, 2026', url: 'https://www.telecomtv.com/content/ai/mckinsey-agentic-ai-can-unlock-new-monetisation-opportunities-for-telcos-56334/' },
  { k: 'Telco-grade models', t: 'GSMA launched Open Telco AI at MWC 2026: open telco models, datasets and a Telco Capability Index. GSMA says only 16% of telco GenAI deployments target network operations.', src: 'GSMA, March 2026', url: 'https://www.gsma.com/newsroom/?p=25564' },
  { k: 'Agentic ODA + MCP', t: 'TM Forum’s 2026 AI-native blueprint projects support Model Context Protocol inside ODA components; Catalysts show an agentic NOC over a shared data foundation.', src: 'TM Forum Inform', url: 'https://inform.tmforum.org/research-and-analysis/proofs-of-concept/agentic-noc-ai-native-operations-for-the-autonomous-telco' },
  { k: 'Coordination beats tasks', t: 'HFS (with Amdocs) finds ROI appears when agents coordinate across systems, e.g. churn prevention and revenue assurance, not single-task bots.', src: 'HFS Research, 2026', url: 'https://solutions.amdocs.com/rs/647-OJR-802/images/HFS-MIR-2026-agentic-ai-telco-operating-model.pdf?version=0' },
  { k: 'Data foundation', t: 'Nokia, AWS and Databricks partner on the data and control layer for autonomous networks, targeting fragmented telco data silos.', src: 'RCR Wireless, June 2026', url: 'https://www.rcrwireless.com/20260624/network-infrastructure/nokia-aws-databricks-telco-ai-control' },
  { k: 'Care at scale', t: 'Vodafone reports TOBi / SuperTOBi above 70% end-to-end resolution with an 8-point NPS gain; Verizon is testing agents across customer service.', src: 'Vodafone FY2026 results, as reported in trade press (TelecomTV)', url: 'https://www.telecomtv.com/content/ai/the-week-in-ai-native-telco-19-25-sept-2026-56343/amp/' },
  { k: 'Regulation', t: 'EU AI Act high-risk duties (human oversight, logging, risk management) cover AI used as safety components of critical digital infrastructure; recent amendments moved Annex III dates to Dec 2027. NIS2 applies now.', src: 'DAC Beachcroft, 2026', url: 'https://www.dacbeachcroft.com/en/what-we-think/ai-act-enforced-delayed-and-amended' }
];
