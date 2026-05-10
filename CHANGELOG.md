# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-05-10

### Added
- Detect the WD My Passport's lock state on launch via sysfs and skip the
  password prompt when the disk is already unlocked.
- Show the detected drive's model and capacity in the main window.
- "Refresh" button to re-detect the drive without restarting the app.
- Auto-refresh the displayed state about three seconds after a successful unlock
  so the form disappears once the kernel has re-enumerated the device.
- Pass `-d <device>` to `wdpass` based on the detected sysfs path instead of
  relying on the tool's own auto-detection.

### Fixed
- Respect the system GTK theme so labels remain readable under Ubuntu's dark
  mode. Previously a hardcoded light window background made the title,
  subtitle, and "Password:" label render as white-on-white.
- `install.sh` now detects when the `wdpass` pipx venv points at a Python
  interpreter that no longer exists (e.g. after an Ubuntu major-version
  upgrade) and rebuilds the venv. The previous "already installed → `pipx
  upgrade`" path could not recover from a dead interpreter and left the app
  silently broken.

## [0.1.0] - 2025-12-06

### Added
- Initial GTK3 GUI for unlocking Western Digital My Passport drives on
  Ubuntu/Linux, wrapping the `wdpass` command-line tool.
- `install.sh` and `uninstall.sh` for one-shot setup, including a desktop
  entry under the Applications menu.
