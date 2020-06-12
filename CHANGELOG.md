# Changelog

## Current (in progress)

- Add pyOpenSSL requirement for python3.7 compatibility [#197](https://github.com/etalab/croquemort/pull/197)
- Clarify that the `Content-Type` HTTP header is cleaned [#202](https://github.com/etalab/croquemort/pull/202)

## 2.1.0 (2019-05-07)

- Fix HEAD timeout handling [#95](https://github.com/opendatateam/croquemort/pull/95)
- Remove homepage/dashboard [#140](https://github.com/opendatateam/croquemort/pull/140)

## 2.0.4 (2018-01-24)

- Fix packaging and other enhancements [#49](https://github.com/opendatateam/croquemort/pull/49)

## 2.0.3 (2018-01-08)

- Fix setup.py

## 2.0.2 (2018-01-08)

- Fix publish job on Circle

## 2.0.1 (2018-01-08)

- Add packaging workflow, publish on Pypi

## 2.0.0 (2017-10-23)

Mandatory migrations from `1.0.0` to `2.0.0`:

```bash
# Launch the migrations service - logs will be displayed here
nameko run croquemort.migrations --config config.yaml
# In another terminal session
nameko shell
>>> n.rpc.migrations.migrate_from_1_to_2()
```

### Breaking changes

- Hash prefixes in Redis DB
  [#26](https://github.com/opendatateam/croquemort/issues/26)
  — associated migration: `add_hash_prefixes`
- Redirection support
  [#1](https://github.com/opendatateam/croquemort/issues/1)
  — associated migration: `migrate_urls_redirect`

### Features

- Webhook support
  [#24](https://github.com/opendatateam/croquemort/issues/24)

### Misc

- Remove logbook in favor of logging
  [#29](https://github.com/opendatateam/croquemort/issues/29)

## 1.0.0 (2017-01-23)

- Initial version
