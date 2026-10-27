# Advanced Python Calculator

A modular command-line calculator built with Python and pandas.

## Installation

Use Python 3.12, matching the GitHub Actions environment. Create a virtual
environment from the project directory:

```sh
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or activate it on macOS/Linux:

```sh
source .venv/bin/activate
```

Install dependencies and create your local configuration:

```sh
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` (PowerShell: `Copy-Item .env.example .env`;
macOS/Linux: `cp .env.example .env`). Adjust the values described below.
Keep `.env` local; it is ignored by Git.

## Running and testing

Install dependencies with `python -m pip install -r requirements.txt`, then run
`python -m app.calculator_repl`. Run the complete test suite with
`python -m pytest --cov=app --cov-report=term-missing`.

The ten operations are `add`, `subtract`, `multiply`, `divide`, `power`,
`root`, `modulus`, `int_divide`, `percent`, and `abs_diff`.
Enter calculations as `divide 10 3`. Commands include `help`, `history`,
`clear`, `undo`, `redo`, `save`, `load`, and `exit`.

## Usage

Enter `<operation> <number1> <number2>` at the `>>>` prompt.

| Operation | Example | Result |
| --- | --- | --- |
| add | `add 5 3` | 8 |
| subtract | `subtract 5 3` | 2 |
| multiply | `multiply 5 3` | 15 |
| divide | `divide 10 4` | 2.5 |
| power | `power 2 -3` | 0.125 |
| root | `root -27 3` | -3 |
| modulus | `modulus 10 3` | 1 |
| int_divide | `int_divide -10 3` | -4 |
| percent | `percent 25 200` | 12.5 |
| abs_diff | `abs_diff 5 12` | 7 |

Integer division follows Python's `//` convention: round the quotient down toward
negative infinity. Thus `-10 // 3` is `-4`, rather than truncating toward zero.
Complex and non-finite results are rejected with a readable error before changing
history, saving CSV, or clearing redo. Division by zero and invalid roots also
report errors and allow another command.

| Command | Behavior |
| --- | --- |
| help | Show operations, commands, and examples |
| history | Display saved results, operands, and timestamps |
| clear | Clear history; undo can restore it |
| undo | Restore the preceding history state |
| redo | Restore the last undone history state |
| save | Save current history to the configured CSV |
| load | Load the configured CSV; undo can restore the previous state |
| exit | Close the log file and exit; Ctrl+C and EOF also exit |

Colorama initializes Windows console support. Successful results and confirmations
are green, errors red, nonfatal warnings yellow, help/headings cyan, and history
blue. Every colored message resets its style. Redirected output, `TERM=dumb`,
and the presence of `NO_COLOR` use plain text. CSV and log files contain no
presentation color codes.

## History and logging

Each new calculation records a UTC ISO 8601 timestamp. History displays and pandas
CSV exports include operand1, operand2, operation, result, and timestamp. CSV loading
preserves timestamps and reconstructs Calculation objects without recomputing
stored, rounded results. Stage 1 CSV files without a timestamp remain supported;
their timestamps are blank because the original calculation time is unknown.

Only the newest configured number of calculations remains in history. Memento
snapshots preserve timestamps and evicted rows so undo and redo restore the exact
previous history. Clear and manual load are also undoable. Failed calculations
and invalid CSV loads leave undo/redo intact. A new calculation clears redo.
Auto-save runs after additions, clears, undo, redo, and successful manual loads.

The LoggingObserver writes calculation operation, operands, stored result, and
calculation timestamp through Python logging at INFO level. History restoration
and clearing generate INFO events. REPL arithmetic failures use WARNING and
validation or persistence failures use ERROR. Log records also include event time.
Calculators embedded in other Python code should call `close()` to release the
log handle when finished. LoggingObserver delegates file ownership to
`app.logger.Logger`, which uses Python's logging module and the configured
filename, directory, and encoding.

Malformed CSV, missing columns, unsupported operations, non-finite numeric data,
invalid timestamps, encoding failures, and permission errors produce meaningful
HistoryError messages. Invalid loads preserve existing history. Missing files
produce an empty history, matching Stage 1 behavior. At startup, an unreadable
history reports an error and starts with empty history; the REPL continues.
Save failures retain the calculation in memory and its undo snapshot, report the
failure, and allow subsequent commands or a save retry. Invalid configuration or an
unavailable log destination produces a readable startup error and exits before
entering the REPL.

## Configuration

Copy `.env.example` to `.env` and adjust values. python-dotenv loads configuration;
existing environment variables take precedence. Relative paths use the current
working directory.

| Variable | Default | Meaning / validation |
| --- | --- | --- |
| CALCULATOR_LOG_DIR | logs | Nonempty log directory |
| CALCULATOR_HISTORY_DIR | data | Nonempty history directory |
| CALCULATOR_LOG_FILE | calculator.log | Nonempty log filename, resolved under log directory |
| CALCULATOR_HISTORY_FILE | history.csv | Nonempty CSV filename, resolved under history directory |
| CALCULATOR_MAX_HISTORY_SIZE | 100 | Positive integer; keeps newest entries |
| CALCULATOR_AUTO_SAVE | true | true or false, case insensitive |
| CALCULATOR_PRECISION | 10 | Integer decimal places from 0 through 15; rounds stored and returned results |
| CALCULATOR_MAX_INPUT_VALUE | 1e100 | Finite positive maximum absolute operand value |
| CALCULATOR_DEFAULT_ENCODING | utf-8 | Recognized Python encoding for CSV and log files |

For compatibility, a history filename containing a directory (for example,
`data/history.csv`) or an absolute path is used directly. An absolute log filename
is also used directly. The legacy `CALCULATOR_MAX_HISTORY` remains supported when
`CALCULATOR_MAX_HISTORY_SIZE` is absent; the new name takes precedence.
Input values must be finite and within the configured bound. Invalid environment
settings raise ConfigurationError with the setting name. Factory arithmetic
strategies, the Observer interface, and the Memento caretaker remain in place.


## Design and testing

`app.calculator.Calculator` is the public facade; `app.calculator_repl` provides the
command-line interface. The operation Factory creates all ten arithmetic strategies.
The Memento caretaker stores copies of history for undo/redo. History observers
handle calculation logging and pandas auto-save. `Calculation.to_dict()` and
`Calculation.from_dict()` serialize and reconstruct results with their timestamps;
`History.calculations` exposes independent reconstructed objects while history and
Memento snapshots retain the established DataFrame representation.

Custom ValidationError, ConfigurationError, HistoryError, and OperationError
provide meaningful failures. DivisionByZeroError also inherits ZeroDivisionError
for compatibility; OperationError also inherits ValueError.

Run the complete suite and enforce the assignment's minimum coverage:

```sh
python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

The tests cover all operations, negative exponents, invalid results, configuration,
CSV errors, timestamps, history limits, observers, undo/redo, REPL recovery, and
terminal-independent color behavior. Abstract methods and the module launch guard
use `# pragma: no cover` for intentionally excluded statements.

## Continuous integration

`.github/workflows/python-app.yml` runs on pushes and pull requests targeting
`main`. GitHub Actions checks out the repository, configures Python 3.12 on
Ubuntu, installs `requirements.txt`, and runs pytest with coverage. The current
workflow enforces **100% application statement coverage**, stricter than the
assignment's 90% minimum. A failed test or lower coverage fails the job.
Use `python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=100`
locally to run the same coverage check.

Review changes, make descriptive commits that reflect your development progress,
and push them to GitHub yourself. Check the Actions tab for a successful workflow
run before submitting. The workflow tests the application; it does not deploy it.
