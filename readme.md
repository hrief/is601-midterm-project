# IS601 Midterm Project – Advanced Python Calculator

This project is an advanced command-line calculator. It builds on the calculator application from earlier modules by adding more arithmetic operations, calculation history, undo/redo functionality, logging, configuration settings, and automated testing.

The calculator uses several design patterns, including Factory, Memento, and Observer. It also uses pandas to manage calculation history and save it to CSV files.

For the optional advanced feature, I added color-coded terminal output using Colorama to make the calculator easier to use.

## Features

The main features of the calculator include:

- Ten arithmetic operations
- A command-line interface (REPL)
- Calculation history managed with pandas
- Automatic saving and loading of history using CSV files
- Timestamps for calculations
- Undo and redo functionality
- Logging for calculations and errors
- Environment-based configuration using a `.env` file
- Input validation and error handling
- Color-coded output using Colorama
- Unit tests with pytest
- Automated testing and code coverage through GitHub Actions

## Installation

The project uses Python 3.12, which is also the version used in the GitHub Actions workflow.

First, clone the repository and navigate to the project folder:

```bash
git clone https://github.com/hrief/is601-midterm-project.git
cd is601-midterm-project
```

Next, create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

On Windows using PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Calculator

To start the calculator, run:

```bash
python -m app.calculator_repl
```

The calculator will open an interactive command-line interface where you can enter calculations and other commands.

The general format for calculations is:

```text
<operation> <number1> <number2>
```

For example:

```text
add 10 5
multiply 6 4
divide 20 5
```

You can enter `help` at any time to display the available commands.

## Supported Operations

The calculator supports the following ten arithmetic operations:

| Operation | Example | Expected Result |
|---|---|---|
| Addition | `add 10 5` | 15 |
| Subtraction | `subtract 10 5` | 5 |
| Multiplication | `multiply 10 5` | 50 |
| Division | `divide 10 5` | 2 |
| Exponentiation | `power 2 3` | 8 |
| Root | `root 27 3` | 3 |
| Modulus | `modulus 10 3` | 1 |
| Integer Division | `int_divide 10 3` | 3 |
| Percentage | `percent 25 200` | 12.5 |
| Absolute Difference | `abs_diff 10 15` | 5 |

The calculator also supports negative numbers and decimal values.

For example, `power 2 -3` returns `0.125`.

Integer division uses Python's `//` operator, meaning the result is rounded down. For example, `int_divide -10 3` returns `-4`.

The calculator checks for invalid calculations, such as division by zero, and displays an error instead of crashing. Complex and non-finite results are also rejected.

## Calculator Commands

In addition to arithmetic operations, the REPL supports several commands for managing calculation history.

| Command | Description |
|---|---|
| `help` | Displays available operations and commands |
| `history` | Shows previous calculations |
| `clear` | Clears calculation history |
| `undo` | Reverses the most recent history change |
| `redo` | Restores an undone change |
| `save` | Manually saves history to a CSV file |
| `load` | Loads history from a CSV file |
| `exit` | Exits the calculator |

For example, you can perform several calculations, enter `history` to view them, and then use `undo` or `redo` to move between previous history states.

Clearing history can also be undone.

## Calculation History

One of the main additions to this version of the calculator is the ability to store and manage calculation history using pandas.

Each calculation records:

- The operation performed
- The two input values
- The calculated result
- A timestamp

History is stored in a pandas DataFrame and can be saved to a CSV file.

By default, the history file is located at:

```text
data/history.csv
```

When the calculator starts, it attempts to load the existing history file. This allows calculations to be retained between sessions.

The calculator also supports automatic saving, which is enabled by default.

The maximum number of history entries can be changed through the configuration file. The default limit is 100 calculations.

CSV records can be converted back into `Calculation` objects when loading history, including their stored results and timestamps.

## Design Patterns

This project uses three design patterns that were covered in the course.

### Factory Pattern

The Factory pattern is used to create the different arithmetic operations.

Instead of placing all ten calculations directly inside the REPL, each operation has its own class. The `OperationFactory` selects and creates the correct operation based on the command entered.

This makes the code easier to organize and allows additional operations to be added without making major changes to the REPL.

### Memento Pattern

The Memento pattern is used for undo and redo functionality.

Before a change is made to calculation history, the calculator saves a copy of its previous state. The caretaker manages these saved states and allows the user to restore them.

This is useful when a calculation is added accidentally or when the user wants to recover cleared history.

### Observer Pattern

The Observer pattern is used to handle logging and automatic saving.

When calculation history changes, registered observers are notified. The logging observer records relevant activity, while the auto-save observer writes the updated history to the CSV file.

This separates these tasks from the main calculator logic and makes the application easier to maintain.

## Logging

The calculator records activity using Python's logging module.

By default, log messages are saved to:

```text
logs/calculator.log
```

Logging includes information about calculations, history changes, and errors.

The project uses different logging levels, including INFO, WARNING, and ERROR, depending on the type of event.

The logging functionality is handled through a dedicated Logger class and the logging observer.

## Configuration

The calculator uses `python-dotenv` to load settings from a `.env` file.

The following settings are available:

| Setting | Default Value | Purpose |
|---|---|---|
| `CALCULATOR_LOG_DIR` | `logs` | Directory for log files |
| `CALCULATOR_HISTORY_DIR` | `data` | Directory for calculation history |
| `CALCULATOR_LOG_FILE` | `calculator.log` | Log filename |
| `CALCULATOR_HISTORY_FILE` | `history.csv` | History filename |
| `CALCULATOR_MAX_HISTORY_SIZE` | `100` | Maximum number of stored calculations |
| `CALCULATOR_AUTO_SAVE` | `true` | Enables or disables automatic saving |
| `CALCULATOR_PRECISION` | `10` | Number of decimal places used for results |
| `CALCULATOR_MAX_INPUT_VALUE` | `1e100` | Maximum allowed absolute input value |
| `CALCULATOR_DEFAULT_ENCODING` | `utf-8` | File encoding |

These settings make it possible to change how the calculator behaves without modifying the source code.

The application also validates configuration values and displays an error if a setting is invalid.

## Error Handling

The calculator includes input validation and error handling to prevent invalid calculations from stopping the application.

In most cases, the calculator displays a readable error message and allows the user to try another command.

## Color-Coded Output

For the optional advanced feature, I chose to implement color-coded output using Colorama. I chose to do this because different colors can be used to make the terminal output easier to understand.

