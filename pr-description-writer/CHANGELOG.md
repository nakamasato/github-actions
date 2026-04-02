# Changelog

## [1.18.0](https://github.com/nakamasato/github-actions/compare/pr-description-writer-v1.17.0...pr-description-writer-v1.18.0) (2026-04-02)


### Features

* **action:** enhance PR description generation with LLM support ([#46](https://github.com/nakamasato/github-actions/issues/46)) ([6b8ea82](https://github.com/nakamasato/github-actions/commit/6b8ea82d42467f43cc9ff7806c5b31ed1c0b0dc6))
* add reusable Claude Code project summary workflow ([#111](https://github.com/nakamasato/github-actions/issues/111)) ([c43c26f](https://github.com/nakamasato/github-actions/commit/c43c26fb736423769b37d262c64b6a09a9f4ef5a))
* only run pr-description-writer when PR description is empty ([#91](https://github.com/nakamasato/github-actions/issues/91)) ([bbcacc1](https://github.com/nakamasato/github-actions/commit/bbcacc1f60f33a58a58f606f4e521f3e6dfa554e))
* **pr-description-writer:** add automated PR description generation ([#43](https://github.com/nakamasato/github-actions/issues/43)) ([241a49f](https://github.com/nakamasato/github-actions/commit/241a49f0c115e654e173da30a1c44648d34f2650))
* **pr-description-writer:** add CLAUDE.md for code guidance ([#45](https://github.com/nakamasato/github-actions/issues/45)) ([aefb273](https://github.com/nakamasato/github-actions/commit/aefb27360ae23eaa7a33fa7f0664ea74b77a4ce8))
* **pr-description-writer:** add default pr prompt and update default model ([#52](https://github.com/nakamasato/github-actions/issues/52)) ([2aa0873](https://github.com/nakamasato/github-actions/commit/2aa087367a0bad798e29dab795e9db05aa1d80ef))
* **pr-description-writer:** add prompt to job summary for debugging ([#51](https://github.com/nakamasato/github-actions/issues/51)) ([335883e](https://github.com/nakamasato/github-actions/commit/335883edf9847690d6c85f5bc7541d2b4ae8f030))
* **pr-description-writer:** include patches to generate pr description ([#50](https://github.com/nakamasato/github-actions/issues/50)) ([b83a042](https://github.com/nakamasato/github-actions/commit/b83a042a9ea06f48c53d53d9cd41d037518a7efc))
* **pr-description-writer:** only update description ([#48](https://github.com/nakamasato/github-actions/issues/48)) ([0e13830](https://github.com/nakamasato/github-actions/commit/0e138302bb205d655a1e6fe6ac632377929ace78))


### Bug Fixes

* **deps:** update dependency @actions/core to v3 ([#197](https://github.com/nakamasato/github-actions/issues/197)) ([c4c596f](https://github.com/nakamasato/github-actions/commit/c4c596f074abc5a5da8da2dd7fcd4166b4bc2478))
* **deps:** update dependency @actions/github to v6.0.1 ([#59](https://github.com/nakamasato/github-actions/issues/59)) ([ec34da2](https://github.com/nakamasato/github-actions/commit/ec34da24210b8acce270462c9e0ee065af869988))
* **deps:** update dependency @actions/github to v9 ([#206](https://github.com/nakamasato/github-actions/issues/206)) ([ea47913](https://github.com/nakamasato/github-actions/commit/ea4791364c7e8b821f3e531a410aed2a6a540813))
* **deps:** update dependency axios to v1.10.0 ([#67](https://github.com/nakamasato/github-actions/issues/67)) ([73f5f59](https://github.com/nakamasato/github-actions/commit/73f5f59bdfd670ec9bff224a8097ff95e092c116))
* **deps:** update dependency axios to v1.11.0 ([#102](https://github.com/nakamasato/github-actions/issues/102)) ([88452ad](https://github.com/nakamasato/github-actions/commit/88452ade4c63c4b5d2f7f9b190e25ad5f4044d74))
* **deps:** update dependency axios to v1.12.1 ([#150](https://github.com/nakamasato/github-actions/issues/150)) ([f9649c7](https://github.com/nakamasato/github-actions/commit/f9649c739bfb261be8020dcec265c29aa29b31c7))
