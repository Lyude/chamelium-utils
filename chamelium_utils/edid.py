from .common import *
from sys import stderr

def get(chameleon, args, parser):
    if args.output.isatty():
        print('Refusing to print raw EDID blob to terminal', file=stderr)
        return -1

    args.output.write(chameleon.ReadEdid(args.port))

def set(chameleon, args, parser):
    if args.edid_file != None:
        edid = ChameleonEdid(chameleon, args.edid_file.read())
    elif args.default_edid:
        edid = CHAMELEON_DEFAULT_EDID
    else:
        parser.error('No edid file given and --default-edid not set')

    if not args.no_replug and chameleon.IsPlugged(args.port):
        do_replug = True
        chamelium.Unplug(args.port)
    else:
        do_replug = False

    chameleon.ApplyEdid(args.port, edid.id)

    if do_replug:
        chamelium.Plug(args.port)

    print("EDID changed")
