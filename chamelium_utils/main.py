import argparse
import os
import functools

from urllib.parse import urlparse
from xmlrpc.client import ServerProxy
from chamelium_utils.common import *

def parse_chameleon_url(arg):
    try:
        if not (arg.startswith('http://') or arg.startswith('https://')):
            parts = arg.split(':', maxsplit=2)
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else DEFAULT_RPC_PORT

            arg = 'http://%s:%d' % (host, port)

        return ServerProxy(arg, allow_none=True, use_builtin_types=True)
    except ValueError:
        # we can only hit this if int(parts[1]) fails
        raise argparse.ArgumentTypeError("'%s' is not a valid port" % parts[1])
    except Exception:
        raise argparse.ArgumentTypeError("'%s' is not a valid url" % arg)

parent_parser = argparse.ArgumentParser(
    add_help=False,
    allow_abbrev=True
)
parent_parser.add_argument(
    "--chameleon", metavar='URL',
    help=('The URL to the chameleond instance (defaults to $CHAMELEON_IP)'),
    type=parse_chameleon_url
)

top_args = parent_parser.parse_known_args()[0]

class ChameleonCommand(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if 'parents' not in kwargs:
            kwargs['parents'] = []

        kwargs['parents'].append(parent_parser)
        kwargs['allow_abbrev'] = True
        super().__init__(*args, **kwargs)

        self.set_defaults(subparser=self)

    def add_subparsers(self, *args, **kwargs):
        kwargs['parser_class'] = self.__class__
        return super().add_subparsers(*args, **kwargs)

parser = ChameleonCommand(
    description="A cli utility for controlling the Chamelium"
)

import chamelium_utils.hotplug as hotplug

subparsers = parser.add_subparsers()
parser_show = subparsers.add_parser(
    'status',
    help='Show the status of each port on the Chameleon'
)
parser_show.set_defaults(func=hotplug.show)

parser_plug = subparsers.add_parser(
    'plug',
    help='Plug ports on the Chameleon into the DUT'
)
parser_plug.add_argument(
    'ports',
    help='The ports to plug in',
    nargs='+', type=int
)
parser_plug.set_defaults(func=hotplug.plug)

parser_unplug = subparsers.add_parser(
    'unplug',
    help='Unplug ports on the Chameleon from the DUT'
)
parser_unplug.add_argument(
    'ports',
    help='The ports to unplug',
    nargs='+', type=int
)
parser_unplug.set_defaults(func=hotplug.unplug)

parser_pulse = subparsers.add_parser(
    'pulse',
    help='Send multiple identical HPD pulses'
)
parser_pulse.add_argument(
    'port',
    help='The port to send the pulses on',
    type=int
)
parser_pulse.add_argument(
    'deassert_interval',
    help='The time in ms of the deassert pulse',
    type=int
)
parser_pulse.add_argument(
    '-c', '--count',
    help='How many HPD pulses to send',
    type=int, default=1
)
parser_pulse.add_argument(
    '--assert-interval',
    help='The time in ms of the assert pulse (defaults to the deassert interval)',
    type=int, default=None
)
parser_pulse.add_argument(
    '--end-level',
    help='Whether to end with the hpd line as high or low (plugged or unplugged)',
    type=str, choices=('high', 'low'), default='high'
)
parser_pulse.set_defaults(
    func=hotplug.pulse
)

parser_reset = subparsers.add_parser(
    'reset', help='Reset the Chameleon'
)
parser_reset.set_defaults(func=hotplug.reset)


import chamelium_utils.edid as edid

parser_edid = subparsers.add_parser(
    'edid',
    help='Manage EDID blobs for video ports on the Chamelium'
)
subparsers_edid = parser_edid.add_subparsers()

parser_edid_get = subparsers_edid.add_parser(
    'get',
    help='Retrieve the current edid blob being used on a port'
)
parser_edid_get.add_argument(
    'port',
    help='The port to retrieve the edid from',
    type=int
)
parser_edid_get.add_argument(
    '-o', '--output',
    help='Where to write the EDID to (defaults to /dev/stdout)',
    type=argparse.FileType('wb'),
    default='/dev/stdout'
)
parser_edid_get.set_defaults(func=edid.get)

parser_edid_set = subparsers_edid.add_parser(
    'set',
    help='Set the current EDID for a port on the Chamelium'
)
parser_edid_set.add_argument(
    'port',
    help='The port to set the EDID for',
    type=int
)
parser_edid_set.add_argument(
    'edid_file',
    help='The file to read the EDID from',
    type=argparse.FileType('rb'), nargs='?'
)
parser_edid_set.add_argument(
    '--no-replug',
    help="Don't replug the display after setting the edid",
    default=False, action="store_true"
)
parser_edid_set.add_argument(
    '--default-edid',
    help="Use the Chamelium's default EDID",
    default=False, action='store_true'
)
parser_edid_set.set_defaults(func=edid.set)


import chamelium_utils.screenshot as screenshot

parser_screenshot = subparsers.add_parser(
    'screenshot',
    help="Take a screenshot using the Chameleon's video inputs"
)
parser_screenshot.add_argument(
    '-r', '--replug',
    help='unplug and plug before capturing screen',
    action='store_true'
)
parser_screenshot.add_argument(
    '-e', '--edid-file',
    help='filename of the edid to apply',
    type=argparse.FileType('rb'), default=None,
    metavar='FILE'
)
parser_screenshot.add_argument(
    '-a', '--area',
    help="only capture the given area WxH[+X+Y]",
    type=screenshot.parse_area_arg, default=tuple()
)
parser_screenshot.add_argument(
    '-p', '--port',
    help='the port on the chamelium to capture video output from (default: use first auto-detected port)',
    type=int
)
parser_screenshot.add_argument(
    '-c', '--count',
    help='The number of frames to capture',
    type=screenshot.parse_count_arg,
    default=1
)
parser_screenshot.set_defaults(func=screenshot.screenshot)

single_frame_args = parser_screenshot.add_argument_group(
    'single-frame capture arguments'
)
single_frame_args.add_argument(
    '-o', '--output', type=str,
    help='output file name of screenshot'
)
single_frame_args.add_argument(
    '-v', '--view', metavar='CMD',
    help=('Open the image file with an image viewer after downloading. '
          'CMD defaults to $CHAMELEON_VIEWER'),
    type=screenshot.parse_view_arg, nargs='?', const=''
)

multi_frame_args = parser_screenshot.add_argument_group(
    'multi-frame capture arguments'
)
multi_frame_args.add_argument(
    '-d', '--output-dir',
    help='The directory to output each frame in'
)
multi_frame_args.add_argument(
    '--file-prefix',
    help='The name to prefix each captured frame with'
)
args = parser.parse_args()
if 'func' not in args:
    args.subparser.error('No action specified')

if args.chameleon is not None:
    chameleon = args.chameleon
elif top_args.chameleon is not None:
    chameleon = top_args.chameleon
else:
    try:
        chameleon = os.getenv('CHAMELEON_IP')
        if chameleon is None:
            args.subparser.error('$CHAMELEON_IP is not set and --chameleon was not given')

        chameleon = parse_chameleon_url(chameleon)
    except argparse.ArgumentTypeError as e:
        parser.error('$CHAMELEON_IP: %s' % e.args[0])

__main__ = functools.partial(args.func, chameleon, args, args.subparser)
