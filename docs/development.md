# Development workflow

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
```

## Verification

```bash
make check
make simulate
```

`make check` compiles the Python source and runs every hardware-independent
unit test. `make simulate` exercises the installed CLI, Robot API, protocol,
sensor model, telemetry path, and calibration classifier without opening a
serial or network connection.

## Change discipline

- Keep vendor files outside this project unchanged.
- Add pure decision logic before connecting it to actuation.
- Add a unit test for every protocol command and safety bound.
- Update `STATUS.md` only after distinguishing simulation, bench, and floor
  validation.
- Never make a later test depend on bypassing an earlier safety gate.

## Generated files

Virtual environments, bytecode, package metadata, logs, and calibration
recordings are ignored. They should not be committed.
