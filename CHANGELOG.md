# Changelog

## [1.0.2](https://github.com/ElliNet13/ElliNetIRCd/compare/v1.0.1...v1.0.2) (2026-04-28)


### Bug Fixes

* Replace placeholder author email in setup.cfg ([c094552](https://github.com/ElliNet13/ElliNetIRCd/commit/c09455233fb7c22fb2b8191a05ccbfbc6892b4a3))
* Some clients crash while parsing ISUPPORT if there is a key with no value ([e411731](https://github.com/ElliNet13/ElliNetIRCd/commit/e41173112d7dc69b96939ead0d6212931c5b269c))

### [1.0.1](https://www.github.com/ElliNet13/ElliNetIRCd/compare/v1.0.0...v1.0.1) (2026-04-28)


### Documentation

* Add casing to README name ([4026ecf](https://www.github.com/ElliNet13/ElliNetIRCd/commit/4026ecf38621bff4b7c8fb8aab8e76eccc3aaa66))


### Miscellaneous

* Add package auto updates ([b056b73](https://www.github.com/ElliNet13/ElliNetIRCd/commit/b056b7326e5496b0e0864966ed25a84472b36794))


### Dependencies

* **deps:** update dependency idna to v3.13 ([#5](https://www.github.com/ElliNet13/ElliNetIRCd/issues/5)) ([d05a15d](https://www.github.com/ElliNet13/ElliNetIRCd/commit/d05a15d4e59f12a483c719c60a9ae8c437e539e6))
* **deps:** update dependency python to v3.14.4 ([#4](https://www.github.com/ElliNet13/ElliNetIRCd/issues/4)) ([19f926d](https://www.github.com/ElliNet13/ElliNetIRCd/commit/19f926dd475fba54fcb79f2efc87bd5af874412c))

## 1.0.0 (2026-04-27)


### Bug Fixes

* concurrent writes ([069f891](https://www.github.com/ElliNet13/ElliNetIRCd/commit/069f8916620852ef9d6734af617d6531f72ab8b8)), closes [#17](https://www.github.com/ElliNet13/ElliNetIRCd/issues/17)
* each rpl starts with the nick ([2ab4a28](https://www.github.com/ElliNet13/ElliNetIRCd/commit/2ab4a28b1930775ba1f3f0b657ff8fb18c437d3e))
* Fix tests by removing lines from requirements release-as:1.0.0 ([c1489e5](https://www.github.com/ElliNet13/ElliNetIRCd/commit/c1489e525610732255b4b6905ca8739bb609fbdf))
* Get requirements to work release-as:1.0.0 ([6f44fc1](https://www.github.com/ElliNet13/ElliNetIRCd/commit/6f44fc16ea4498bf19015267478124d7006b4b66))
* ghost nick after half-registration ([8a5f866](https://www.github.com/ElliNet13/ElliNetIRCd/commit/8a5f866bf2bd56aec6175e4b379afd90189f638d))
* ignore missing token in PONG ([8e1a07c](https://www.github.com/ElliNet13/ElliNetIRCd/commit/8e1a07c804b2fa9e87ffbffbb7de012c0bf0bb7c))
* ircexception format ([956fbd6](https://www.github.com/ElliNet13/ElliNetIRCd/commit/956fbd60e6ec9e0ff90f5f483b487ed30e2c86f4))
* log all PING/PONG in DEBUG, send HOST in PONG ([f9f45a2](https://www.github.com/ElliNet13/ElliNetIRCd/commit/f9f45a2ae54f8a36cf63cc72877e424b900dc28b))
* log channel-send messages ([401d256](https://www.github.com/ElliNet13/ElliNetIRCd/commit/401d2563285bcb095763fb0763a61cbb6dd9a3f6))
* setup was still v1 ([5cc0601](https://www.github.com/ElliNet13/ElliNetIRCd/commit/5cc0601209d325303cb5b5e3c5c111d386746619))
* typo in 005 ([1576911](https://www.github.com/ElliNet13/ElliNetIRCd/commit/15769114d88ba0b3b93fda71be51b53f9bc8d586))
* VERSION file not part of sdist ([c112853](https://www.github.com/ElliNet13/ElliNetIRCd/commit/c1128536ce708a37acf4661dc52b43ded5fc7460)), closes [#9](https://www.github.com/ElliNet13/ElliNetIRCd/issues/9)
* was using ADDR instead of HOST ([ec765b6](https://www.github.com/ElliNet13/ElliNetIRCd/commit/ec765b66704769137ed4c9c2680cdef20113dc21))


### Improvements

* only IO-log ping/pong in DEBUG ([1442f79](https://www.github.com/ElliNet13/ElliNetIRCd/commit/1442f796535531161e65fa8eb8d0df13ff085d9d))
* use dedicated logger for [IO] ([1549f80](https://www.github.com/ElliNet13/ElliNetIRCd/commit/1549f80819ac90dae99dc9d202aedc7534ec24cf))


### Refactors

* aioircd v2 ([77b49cd](https://www.github.com/ElliNet13/ElliNetIRCd/commit/77b49cdd1a6b06f5102fb9f331553678602e9da4))
* new test framework ([d652048](https://www.github.com/ElliNet13/ElliNetIRCd/commit/d652048401a123708d7bbb78927b194622449e5d))


### Miscellaneous

* CI/CD via github action ([2825d2e](https://www.github.com/ElliNet13/ElliNetIRCd/commit/2825d2e9d1ed18eed0db8ae1b82d302ff19b4602))
* systemd integration ([27da982](https://www.github.com/ElliNet13/ElliNetIRCd/commit/27da9823b2c6cafa5ffce8baf5339bb047081f48))

### [2.0.6](https://www.github.com/readthedocs-fr/aioircd/compare/v2.0.5...v2.0.6) (2021-12-05)


### Bug Fixes

* concurrent writes ([069f891](https://www.github.com/readthedocs-fr/aioircd/commit/069f8916620852ef9d6734af617d6531f72ab8b8)), closes [#17](https://www.github.com/readthedocs-fr/aioircd/issues/17)


### Miscellaneous

* CI/CD via github action ([2825d2e](https://www.github.com/readthedocs-fr/aioircd/commit/2825d2e9d1ed18eed0db8ae1b82d302ff19b4602))
* systemd integration ([27da982](https://www.github.com/readthedocs-fr/aioircd/commit/27da9823b2c6cafa5ffce8baf5339bb047081f48))
