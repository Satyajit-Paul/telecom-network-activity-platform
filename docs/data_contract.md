# Source and fixture contract

## Public source

- Dataset: [Telecommunications — SMS, Call, Internet — Milan](https://doi.org/10.7910/DVN/EGZHFV).
- Source description: [Barlacchi et al., Scientific Data](https://www.nature.com/articles/sdata201555).
- Data: historical, anonymized activity by geographic square, time interval, and country code.
- Access: the Dataverse page lists custom terms. Review them before downloading, redistribution, or dashboard publishing. The current repository contains none of the public data.
- The publication states that interval starts are Unix timestamps in **milliseconds**, and an interval lasts 600,000 milliseconds.

The following positional contract for daily files is a working assumption until a source file is inspected: `square_id`, `interval_start_ms`, `country_code`, `sms_in`, `sms_out`, `call_in`, `call_out`, `internet`. Verify delimiter, field order, null semantics, country codes, units, and uniqueness from the actual file and source documentation during ingestion work. In particular, do not silently interpret empty measures as zero until the source rules are confirmed.

## Synthetic fixtures

The generator writes headerless tab-separated batches using the assumed column order above. These are fictional records created for engineering tests; their values do not represent real Milan observations.

| Batch | Intended scenario |
|---|---|
| `baseline.tsv` | Normal observations, one exact duplicate, one missing key, one negative measure, one invalid number, and one malformed row |
| `late.tsv` | One previously omitted key arriving after the baseline |
| `correction.tsv` | A later version of an existing baseline key with a changed internet activity value |
| `manifest.json` | Seed, schema, counts, and expected scenario keys |

The fixture represents delivery order by file, not a real source update timestamp. The ingestion design must supply batch metadata and a deterministic conflict-resolution rule. Tests must process these fixtures separately from public data.

