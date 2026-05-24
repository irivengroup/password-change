# Control Node Compatibility

## Supported control node model

This project is designed for modern Ansible execution environments while remaining usable from a RHEL 7 based control node when Ansible is executed from a dedicated Python 3.10+ virtual environment.

The RHEL 7 system Python 2.7 runtime is not supported for this project.

## Recommended RHEL 7 setup

```bash
python3.10 -m venv /opt/iriven/venvs/changepassword
source /opt/iriven/venvs/changepassword/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-control-rhel7.txt
ansible --version
```

## Compatibility guardrails

- The role filter plugin avoids Python 3.7+ only syntax.
- CI validates the project with Python 3.10 and Python 3.12.
- `requirements.txt` pins `ansible-core` to the 2.17 line to preserve Python 3.10 control-node compatibility.
- Managed nodes must expose a Python interpreter compatible with the selected `ansible-core` version.

## Unsupported

- Running the project with `/usr/bin/python` from stock RHEL 7.
- Running the project with Python 2.7.
- Running the CI/Molecule toolchain on the legacy RHEL 7 system Python.
