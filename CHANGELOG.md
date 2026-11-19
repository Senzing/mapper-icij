# Changelog

All notable changes to this project will be documented in this file.

The changelog format is based on [Keep a Changelog] and [CommonMark].
This project adheres to [Semantic Versioning].

## [Unreleased]

### Changed in Unreleased

- Records use the Entity Specification's FEATURES-array shape: every feature (record type, primary name, addresses,
  countries, group associations, relationship anchor and pointers) is one object in FEATURES; only scalar payload is
  left at the root.
- REL_POINTER_KEY is written as a string, matching the REL_ANCHOR_KEY it points at.
- A node id repeated across node files anchors every one of its records on the bare node id, so relationships reach
  them all (previously the `<id>-<n>` repeats could not be pointed at).
- The sqlite work database is created next to the output file and removed afterwards (`-d` keeps it), never in the
  input folder.
- Empty values (relationships to unknown nodes, missing roles or names) are no longer written.

### Fixed in Unreleased

- icij_config_updates.g2c works on Senzing 4.4: it creates the USED_FROM_DT / USED_THRU_DT elements and attaches them
  to REL_POINTER before adding the REL_POINTER_FROM_DATE / THRU_DATE attributes.

## [1.0.0] - yyyy-mm-dd

### Added to 1.0.0

- Initial content

[CommonMark]: https://commonmark.org/
[Keep a Changelog]: https://keepachangelog.com/
[Semantic Versioning]: https://semver.org/
