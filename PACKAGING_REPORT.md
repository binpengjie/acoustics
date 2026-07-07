# PACKAGING_REPORT

## Windows Readiness
The package is designed for Windows local use with Python 3.11, Streamlit, and CPU inference. Runtime scripts use relative paths from the package folder.

## Dependency Pinning
`scikit-learn==1.2.2` is pinned because the Line B ExtraTrees joblib was created with sklearn 1.2.2. Newer sklearn versions can fail to unpickle old tree models.

## Offline Use
No internet is required after dependencies are installed. For a fully offline factory PC, pre-download wheel files or install on a connected machine and copy the `.venv` with the package.

## Linux/Server Test Limitation
The package was generated and smoke-tested on the Linux server. Actual double-click `.bat` behavior must be verified on a Windows PC.


## Smoke Test

Smoke test passed on the Linux server using the package code:

- Line A model loaded.
- Line B model loaded with sklearn 1.2.2.
- Single-file inference succeeded.
- Small OK/NG batch inference succeeded.
- Required output columns were present.
- Streamlit app syntax compiled.
- Windows `.bat` files use relative paths.

Actual double-click execution must still be verified on a Windows PC with Python 3.11.


## Installer Robustness Update

`install_env.bat` was rewritten after a Windows user reported `'py' is not recognized`. The installer now checks `OKNG_PYTHON`, `py`, `python`, `python3`, common install folders, and optionally `winget`. It supports offline `wheelhouse/` installs and logs details to `logs/install_env.log`.

WSL-to-Windows `cmd.exe` simulation was run for:

- `install_env.bat --help`
- `run_app.bat --check`
- `run_cli_batch.bat --help`

These command parsing branches passed. Full package installation still must be tested on a real Windows PC.
