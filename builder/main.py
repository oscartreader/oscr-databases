from os.path import join
from os import getcwd
from SCons.Script import DefaultEnvironment, ARGUMENTS # pyright: ignore[reportMissingImports]

errored = 0
errors = []
env = DefaultEnvironment()
config = env.GetProjectConfig()
platform_path = env.PioPlatform().get_dir()
verbose = int(ARGUMENTS.get("PIOVERBOSE", 0))

try:
    import pyjson5
except ImportError:
    env.Execute("$PYTHONEXE -m pip install pyjson5")

from crdb import CRDB, CRDBException

PROJECT_DIR = getcwd()
DESTINATION_DIR = join(PROJECT_DIR, 'sd', '.oscr', 'db')
CRDB_DATA = join(platform_path, 'data')

crdb = CRDB(CRDB_DATA)

print()
print("--------------------------------------------------------")
print("         CRDB Python Processor v1.0.1 (CRDB V{})".format(crdb.version))
print("--------------------------------------------------------")
print()

if verbose:
    print("Processing...")
else:
    print("Processing.", end='')

for coreName in crdb.cores:
    core = crdb.getCore(coreName)

    filename = core.outfile
    enabled = config.get("cores", core.confKey)

    if verbose:
        print(" + " + filename + " ... ", end='')

    if (enabled != "false"):
        try:
            crdb.BuildCRDB(coreName, join(DESTINATION_DIR, filename))
            if verbose:
                print("ok")
            else:
                 print(".", end='')
        except CRDBException as exc:
            errored = 1
            errors.append(exc)
            if verbose:
                print("FAILED!")
            else:
                print("!", end='')

    elif verbose:
        print("skipped")

if verbose:
    print()
    if errored:
        print("Failed.")
    else:
        print("Finished!")
    print("--------------------------------------------------------")
else:
    if errored:
        print("failed")
    else:
        print("finished")

print()

for exc in errors:
    print("Error:", exc)
    exc.printDebug()
    print()

exit(errored)
