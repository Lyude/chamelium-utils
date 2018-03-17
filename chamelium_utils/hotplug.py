from tabulate import tabulate
from chamelium_utils.common import *

def show(chameleon, args, parser):
    table = list()
    for port in chameleon.GetSupportedInputs():
        table.append([port,
                      chameleon.GetConnectorType(port),
                      str(chameleon.IsPhysicalPlugged(port)),
                      str(chameleon.IsPlugged(port))])

    print(tabulate(table, headers=[
        "Port", "Type", "Physically plugged", "Plugged"]))

def plug(chameleon, args, parser):
    for port in args.ports:
        print("Plugging %d..." % port)
        chameleon.Plug(port)

def unplug(chameleon, args, parser):
    for port in args.ports:
        print("Unplugging %d..." % port)
        chameleon.Unplug(port)

def reset(chameleon, args, parser):
    print("Resetting chameleon...")
    chameleon.Reset()

def pulse(chameleon, args, parser):
    print("Firing %d HPD pulses on port %d, deassert interval=%dms, assert interval=%dms, end level=%s..." % (
        args.count, args.port, args.deassert_interval,
        args.assert_interval if args.assert_interval != None else args.deassert_interval,
        args.end_level))
    chameleon.FireHpdPulse(args.port,
                           args.deassert_interval * 1000,
                           args.assert_interval, args.count,
                           0 if args.end_level == 'low' else 1)
