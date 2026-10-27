# Advanced Python Calculator

A modular command-line calculator built with Python and pandas.

## Running and testing

Install dependencies with `python -m pip install -r requirements.txt`, then run
`python -m app.calculator_repl`. Run the complete test suite with
`python -m pytest --cov=app --cov-report=term-missing`.

The ten operations are `add`, `subtract`, `multiply`, `divide`, `power`,
`root`, `modulus`, `int_divide`, `percent`, and `abs_diff`.
Enter calculations as `divide 10 3`. Commands include `help`, `history`,
`clear`, `undo`, `redo`, `save`, `load`, and `exit`.

## Stage 2: history and logging

Each new calculation records a UTC ISO 8601 timestamp. History displays and pandas
CSV exports include operand1, operand2, operation, result, and timestamp. CSV loading
preserves timestamps. Stage 1 CSV files without a timestamp remain supported;
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
log handle when finished.

Malformed CSV, missing columns, unsupported operations, non-finite numeric data,
invalid timestamps, encoding failures, and permission errors produce meaningful
HistoryError messages. Invalid loads preserve existing history. Missing files
produce an empty history, matching Stage 1 behavior. At startup, an unreadable
history reports an error and starts with empty history; the REPL continues.
Save failures retain the calculation in memory and its undo snapshot, report the
failure, and allow subsequent commands or a save retry.

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
