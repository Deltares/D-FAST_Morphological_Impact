# Technical Description

This is the technical reference manual.

## Design Considerations

1. This new program is to replace WAQMorf which was developed for the
SIMONA system.
1. This program must give the same results for the same input as
WAQMorf.
1. Users must be able to run this program in batch mode from the
command line.
1. This program should read relevant data directly from D-Flow FM
map-files instead of intermediate XYZ files as required by WAQMorf for
SIMONA results.
1. A simple graphical user interface could support users with the input
specification.

WAQMorf didn't use an input file as such to run. The program required
the user to answer a number of questions interactively. The answers to
the questions could be prepared in advance and written to a textfile
that could subsequently be redirected to standard in to mimic running
the program in batch mode.

## Code Design



## Coding Conventions

This program has been programmed following PEP 8 style guide.

## Testing

## Command Line Arguments

| short | long         | description                                 |
|-------|:-------------|:--------------------------------------------|
| -i    | --input_file | name of configuration file                  |
| -v    | --verbosity  | set verbosity level of run-time diagnostics <br> DEBUG, {INFO}, WARNING, ERROR or CRITICAL)  |
