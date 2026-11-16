# inputs/

What the agents work on during a demo. Everything is synthetic: the operator (NorthStar Telecom),
the people, the systems and every value. Personal-looking columns (`msisdn`, `full_name`,
`date_of_birth`) hold fake values in a non-dialable `+999` range and are classified Restricted, so
the agents never read them; the tools return counts and lengths only.

## datasets/

| Folder | Content | Used by |
|---|---|---|
| `tables/*.csv` | 11 tables: CRM customers, billing accounts and invoices, daily xDR usage, care tickets (TMF621), PM cell KPIs (15-min style counters), cell inventory (TMF639), and four gold data products (churn risk, cell energy, usage-to-bill reconciliation, enterprise SLA) | Build (sandbox SQL, profiling, DQ), Consume (certified metrics) |
| `reference/source_metadata.yaml` | Systems, tables, columns, types, keys, classification, owners, ingestion pattern | Build mapping and design |
| `reference/glossary.yaml`, `sid.yaml` | Business glossary and TM Forum SID / TMF Open API map | Build, Consume |
| `reference/semantic_metrics.yaml` | Certified metrics (expression, allowed dimensions, verified questions) and lineage | Consume |
| `operations/*.json` | Alarms (TMF642 shape), change records, KEDB, topology, KPIs, pipeline runs, model metrics, cost vs budget | Operate |
| `MANIFEST.yaml` | Row counts, owning system and classification of every file | Everyone |

Edit any file to change the story (for example raise an alarm's severity or add a cell), then
restart the runtime. To rebuild the files from the deterministic generator:

```bash
python -m telcocrew datasets --generate        # add --rows 20000 for a larger estate
python -m telcocrew datasets                   # show what is loaded
```

Point the runtime at another inputs folder with `TELCOCREW_INPUTS_DIR=/path`.

## scenarios/

One folder per demo scenario. `scenario.yaml` says which track, whether it runs the whole
pipeline or one agent, the request, the context attached for the agents, the datasets involved,
the approvals the audience will see, the expected live duration and presenter notes.

| Scenario | Track | Runs |
|---|---|---|
| `build-churn-360` | Build | Full pipeline G0–G9 for the Subscriber Churn 360 data product |
| `build-ran-energy` | Build | Full pipeline for the RAN energy savings data product |
| `build-enterprise-sla` | Build | Pipeline without the ML stage (no model needed) |
| `operate-ran-incident` | Operate | P1 RAN cluster incident with a planted prompt injection |
| `operate-churn-mart-sla` | Operate | DataOps: two causes, one incident, mart restored before SLA |
| `operate-model-drift` | Operate | MLOps: drift after a tariff launch, shadow retrain |
| `consume-cco-questions` | Consume | Three CCO questions through the semantic layer |
| `consume-guardrail-probe` | Consume | PII and out-of-scope requests that must be refused |
| `consume-retention-action` | Consume | Next-best-action proposal routed to approvers |
| `consume-care-incident` | Consume | Care copilot during the network incident |
| `consume-exec-brief` | Consume | Weekly steering brief from certified metrics |

Add your own: copy a folder, change `scenario.yaml` and `request.md`, and it appears in
`python -m telcocrew scenarios` and on the web page.
