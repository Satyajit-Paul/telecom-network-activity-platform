# Source and fixture contract

## Public source

- Dataset: [Telecommunications — SMS, Call, Internet — Milan](https://doi.org/10.7910/DVN/EGZHFV).
- Source description: [Barlacchi et al., Scientific Data](https://www.nature.com/articles/sdata201555).
- Data: historical, anonymized activity by geographic square, time interval, and country code.
- Access and reuse: Harvard Dataverse's dataset metadata states that the data is released under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), with attribution and share-alike requirements for adapted databases. The dataset's custom terms also request a hyperlink reading [from BigDataChallenge contest](https://theodi.fbk.eu/openbigdata/). Review the terms when publishing derived datasets or visualizations. The repository contains none of the public data.
- The first daily file is `sms-call-internet-mi-2013-11-01.txt`, Dataverse file ID `2674255`, 322,874,887 bytes, MD5 `658c49f8e3c7910bd3bb2bafbf62cdce` according to Dataverse metadata. A guestbook response is required for download.
- The publication states that interval starts are Unix timestamps in **milliseconds**, and an interval lasts 600,000 milliseconds.

The positional contract for daily files is `square_id`, `interval_start_ms`, `country_code`, `sms_in`, `sms_out`, `call_in`, `call_out`, `internet`. Inspection of the first 50,000 lines of the checksum-verified 2013-11-01 file found headerless tab-separated records with eight fields, 127 distinct squares, 105 distinct country-code values, and no repeated three-field keys in that sample. This ordered prefix is not representative and does not prove uniqueness for other records or days. The sample contains country code `0`; preserve it as a source code rather than mapping it to a country without supporting documentation.

Blank measures are common: the inspected sample has 16,720 blank `sms_in` fields and 24,204 blank `internet` fields, among others. They are retained as blanks in raw storage; do not silently interpret them as zero until the source rules are confirmed. The sample spans 2013-10-31 23:00 through 2013-11-01 22:50 UTC, consistent with a Milan local day; store UTC timestamps and document the reporting timezone in downstream models.

The local sample is created only after verifying the full source file's published MD5. `scripts/create_sample.py` stores the source and sample SHA-256 hashes in a local provenance sidecar. The first 50,000 lines produced a sample SHA-256 of `a4e3e7615c153c89215f76d572ec396bce78fd822c8662f7153ad962d889c699`. Both source data and sidecar are excluded from Git.

## Synthetic fixtures

The generator writes headerless tab-separated batches using the assumed column order above. These are fictional records created for engineering tests; their values do not represent real Milan observations.

| Batch | Intended scenario |
|---|---|
| `baseline.tsv` | Normal observations, one exact duplicate, one missing key, one negative measure, one invalid number, and one malformed row |
| `late.tsv` | One previously omitted key arriving after the baseline |
| `correction.tsv` | A later version of an existing baseline key with a changed internet activity value |
| `manifest.json` | Seed, schema, counts, and expected scenario keys |

The fixture represents delivery order by file, not a real source update timestamp. The ingestion design must supply batch metadata and a deterministic conflict-resolution rule. Tests must process these fixtures separately from public data.

The current loader preserves valid source fields as JSON arrays and puts invalid rows in `raw.rejected_records` with their reason and line number. It keeps blank measures unchanged. Batch SHA-256 and source system form the replay identity; repeated file bytes for the same source are skipped. Duplicate business keys and corrections are deliberately retained in raw and will be resolved downstream. Structural CSV parsing failures roll back the batch rather than accepting partial data.

