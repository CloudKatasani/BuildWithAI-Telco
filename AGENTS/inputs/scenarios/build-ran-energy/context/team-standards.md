# NorthStar Telecom data team standards (attached context)

- STD-01 Analytics joins on the pseudonymous subscriber key, never on MSISDN (TEL-C4).
- STD-02 Every gold table has an ODCS data contract and a named Data Product Owner.
- STD-03 dbt models use incremental materialisation with a unique key; tests on every key column.
- STD-04 Weekly marts are ready by Monday 06:00 UTC.
- STD-05 Marketing features need consent_marketing = 'Y' per line (TEL-C3).
- STD-06 Production changes are deployed only in the Tuesday 01:00-03:00 UTC window, outside network freeze.
