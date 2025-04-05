# set-image-tag

This action sets image tag based on GitHub event type:

- pull_request: `pr-<pr number>`
- push: `<branch>-<github short sha>`
- others: `<ref_name>` (release: tag name)

## Inputs

no inputs

## Outputs

- tag

## Usage

```yaml

```
