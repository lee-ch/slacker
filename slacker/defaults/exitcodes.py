# Default exit code, try not to use it when something else
# is more appropriate
EX_GENERIC = 1

# Salt SSH "Thin" deployment failures
EX_THIN_PYTHON_INVALID = 10
EX_THIN_DEPLOY = 11
EX_THIN_CHECKSUM = 12
EX_MOD_DEPLOY = 13
EX_SCP_NOT_FOUND = 14

# One of a collection failed
EX_AGGREGATE = 20

# The os.EX_* exit codes are Unix only, so in the interest of
# cross-platform-ness, define them explicitly here.
#
# These constants are documented here:
# https://docs.python.org/2/library/os.html#OS.EX_OK

EX_OK = 0
EX_USAGE = 64
EX_DATAERR = 65
EX_NOINPUT = 66
EX_NOUSER = 67
EX_NOHOST = 68
EX_UNAVAILABLE = 69
EX_SOFTWARE = 70
EX_OSERR = 71
EX_CANTCREAT = 73
EX_TEMPFAIL = 75
EX_NOPERM = 77

# Salt specific exit codes are defined below:

# keepalive exit code is a hint that the process should be restarted
SALT_KEEPALIVE = 99

# SALT_BUILD_FAIL is used when salt fails to build something, like a container
SALT_BUILD_FAIL = 101