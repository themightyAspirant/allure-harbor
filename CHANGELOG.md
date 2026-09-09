# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Common Changelog](https://common-changelog.org/).
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-09

### Added

- FastAPI service to upload a ZIP of Allure results and generate a shareable HTML report
- REST endpoints to list, fetch, and delete report metadata
- Static hosting of generated reports at `/reports/{id}/`
- ZIP slip, zip bomb, and upload size protections
- Docker Compose stack with Allure CLI, JRE, and optional Nginx

### Changed

- Open all HTTP endpoints to anyone who can reach the host; access control is expected at the network layer

### Fixed

- Resolve the Allure CLI via PATH on Windows so Scoop `allure.cmd` shims work with subprocess

