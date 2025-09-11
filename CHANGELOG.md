# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# Unreleased

# Added
- [arturraczka/order_settlement_snapshot] order settlement snapshot

# [1.2.2]

### Fixed
- [arturraczka] debt counting fix

# [1.2.1]

### Added
- [arturraczka] fixy_Q3: pre-commit hooks, admin fixes, repo cleanup

# [1.2.0]

### Added
- [arturraczka] finanse_fixy: extended reports, fixes to finances and more

# [1.1.1]

### Fixed
- [arturraczka] Fixes to Order finances

# [1.1.0]

### Added
- [arturraczka] Order finances in admin and reports; scheduled order summary email

# [1.0.4]

### Changed
- [arturraczka] Replace dot with comma as dec sep in reports


# [1.0.3]
### Fix
- [marcinkosztolowicz] Fix error when order (box) is empty

# [1.0.2]
### Fix
- [marcinkosztolowicz] Fix error exporting all orders csv when item is duplicated in any order
- [marcinkosztolowicz] Change MassOrderBoxReport items in box order by producer short name
- [marcinkosztolowicz] Change  items in producer product order by  box number

# [1.0.1]
### Fix
- [marcinkosztolowicz] Fix http 500 when weight scheme 0.000 is added during product creation.

# [1.0.0]
### Added
- [marcinkosztolowicz] Deployment IaC
- [arturraczka] Code

## [0.1.0] - WIP
### Added
- [marcinkosztolowicz] Dockerfile
- [marcinkosztolowicz] Makefile
- [marcinkosztolowicz] Added configurable config path for allowed hosts and env variables
### Fix
- [marcinkosztolowicz] createing producer in panel admin
