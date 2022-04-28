# Automated Classroom Booking with Prodigit

This simple programs automates the task of booking classes via
[Prodigit](https://prodigit.uniroma1.it). It reads a configuration file
containing yout dredentials and class schedule for the week and tries to book
all of them for the next week.

# Usage

Once the configuration file `conf.json` has ben filled with your information the
program can be used by simply running it as a module. The program expects to
find the configuration file in the current working directory.

```
$ python3 -m prodigit
```

# TODO

It would be nice to also be able to get a list of booked classes and be able to
delete the reservations.
