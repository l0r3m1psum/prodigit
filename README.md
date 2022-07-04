# Automated Classroom Booking with Prodigit

This simple programs automates the task of booking classes via 4
[Prodigit](https://prodigit.uniroma1.it). It reads a configuration file 5
containing your credentials and class schedule for the week and tries to book 6
all of them for the next week. The initial reversing of the Prodigit API was
done by [@deborahdore](https://github.com/deborahdore) `:)`.

# Usage

Once the configuration file `conf.json` has ben filled with your information the
program can be used by simply running it as a module. The program expects to
find the configuration file in the current working directory.

```
$ python3 -OO -m prodigit
```

# Quirks and Defects of Prodigit

Prodigit is implemented in the oddest possible way, it is full of stange stuff,
for examples the endpoints reply to you with `OK` and return code 200 even if
they don't book any class so checking for errors is not useful and the only way
to know if your class was really booked is to check your INBOX.

If you ever get impostor syndrom, always think about the fact that someone
somewhere was paid to build Prodigit. This should make you feel better.

# TODO

It would be nice to also be able to get a list of booked classes and be able to
delete the reservations.
