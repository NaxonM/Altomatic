## PySide6 MVVM Migration Guide (Linux-Compatible AI Agent)

### Phase 0 – Environment & Baseline
1. **Set Up Workspace**
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt` (log missing packages).
2. **Project Recon**
   - Run static inventory scripts (e.g., `python scripts/list_modules.py`); store output in `docs/migration/current_ui.json`.
   - Parse `src` to enumerate UI classes; document dependencies.
3. **Baseline Metrics**
   - Execute existing automated tests (`pytest`, etc.) and record results.
   - Measure app start time via headless script; note manual checks required for visuals.

### Phase 1 – Foundation Preparation
1. **Add PySide6 Dependencies**
   - `pip install PySide6 pytest-qt ruff mypy`.
   - Update dependency files (`pyproject.toml`, `requirements.txt`).
2. **Establish MVVM Skeleton**
   - Create directories: `src/app/views`, `viewmodels`, `models`, `services`, `resources`.
   - Implement `base_view.py` and `base_viewmodel.py` with signal and state helpers.
3. **Configure Tooling**
   - Add `ruff` and `mypy` configs; ensure CI scripts call lint, type check, and tests.
   - Introduce automation tasks (`Makefile` or `invoke`) for `lint`, `type`, `test`.

### Phase 2 – Design System Bootstrap
1. **Design Tokens**
   - Create `resources/design_tokens.py` defining colors, typography, spacing.
   - Generate base stylesheet `resources/styles/base.qss` referencing tokens.
2. **Reusable Widgets**
   - Implement shared widgets (buttons, cards, toolbars) under `resources/widgets`.
   - Add unit tests validating widget properties without UI rendering.

### Phase 3 – Pilot Screen Migration
1. **Select Pilot Modules** (e.g., login, dashboard) based on usage frequency.
2. **ViewModel Conversion**
   - Port existing logic into `viewmodels/<module>_viewmodel.py` with unit tests.
   - Mock services to isolate logic in automated tests.
3. **View Construction**
   - Build PySide6 views using design-system components.
   - Configure feature flags in `settings.json` to toggle legacy vs. new views.

### Phase 4 – Systematic Module Migration
For each remaining screen:
1. Document legacy behavior in `docs/migration/<module>.md` with data flow notes.
2. Scaffold corresponding ViewModel and View following pilot patterns.
3. Extend automated tests (unit + smoke) to cover new logic.
4. Update feature flags and remove legacy code post-verification.

### Phase 5 – UX Enhancements
1. **Micro-Interactions**
   - Implement animation helpers (`utils/animations.py`) for consistent transitions.
2. **Productivity Features**
   - Add command palette infrastructure and notification service with file logging.
3. **Contextual Support**
   - Integrate tooltip/help metadata via JSON assets consumed by views.

### Phase 6 – Quality & Localization
1. Expand pytest suites for services and viewmodels; configure `pytest-qt` smoke tests.
2. Implement static checks ensuring accessibility attributes (`accessibleName`) are set.
3. Integrate `babel` extraction scripts and maintain `.po` files for translations.

### Phase 7 – Performance Tooling
1. Add profiling decorators (`utils/profiling.py`) logging execution times.
2. Provide CLI profiling scripts storing outputs in `reports/performance/`.
3. Replace heavy list models with `QAbstractItemModel` implementations where applicable.

### Phase 8 – Packaging & Release Support
1. Create `pyinstaller.spec` and `scripts/build_app.py` for cross-platform builds.
2. Automate regression pipeline (`make ci`) running lint, type check, tests, build.
3. Maintain machine-readable release checklist `docs/migration/release_checklist.yaml` marking manual human validations.

### Phase 9 – Human Touchpoints
1. Track manual verification needs in `docs/migration/manual_verifications.md`.
2. Update `migration_status.json` after each phase with completion flags and pending tasks.
