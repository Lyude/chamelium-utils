import re
import argparse
import time
import tempfile
import subprocess
import os
from .common import *

def default_output_suffix():
    return time.strftime("%Y%m%d-%H%M%S")

def parse_area_arg(arg):
    matches = re.match(r"(?P<w>\d+)x(?P<h>\d+)(\+(?P<x>\d+)\+(?P<y>\d+))?",
                       arg).groupdict()
    try:
        w = int(matches['w'])
        h = int(matches['h'])
        x = int(matches['x']) if matches['x'] else 0
        y = int(matches['y']) if matches['y'] else 0
    except Exception as e:
        raise argparse.ArgumentTypeError()

    return (x, y, w, h)

def round_resolution(resolution, align):
    rounded_resolution = list(resolution)
    for idx, i in enumerate(rounded_resolution):
        if i % align:
            rounded_resolution[idx] += align - (i % align)
    rounded_resolution = tuple(rounded_resolution)

    # The chamelium only likes 8-bit aligned values, e.g. those divisible by 8,
    # so make sure to just use the closest resolutionolution possible
    if resolution != rounded_resolution:
        print("Rounded resolution from %dx%d+%d+%d to %dx%d+%d+%d" % (
            *resolution, *rounded_resolution))

    return rounded_resolution

def parse_count_arg(arg):
    count = int(arg)
    if count < 1:
        raise argparse.ArgumentTypeError()

    return count


def screenshot(chameleon, args, parser):
    # Validate arguments
    if args.count > 1:
        if args.output:
            parser.error("--output is only for single-frame captures")
        if args.view:
            parser.error("--view cannot be used in multi-frame capture mode")

        if args.output_dir:
            if not os.path.exists(args.output_dir):
                os.mkdir(args.output_dir)
            elif not os.path.isdir(args.output_dir):
                parser.error("%s is not a directory" % args.output_dir)
        else:
            args.output_dir = "chamelium-screenshot-%s" % default_output_suffix()
            os.mkdir(args.output_dir)
        if not args.file_prefix:
            args.file_prefix = "frame"
    else:
        if args.output_dir:
            parser.error("--output-dir is only for multi-frame captures")
        if args.file_prefix:
            parser.error("--file-prefix is only for multi-frame captures")

        # Default output settings
        if not args.output:
            if args.view:
                args.output = tempfile.NamedTemporaryFile(suffix='.png')
            else:
                args.output = open("chamelium-screenshot-%s.png" %
                                   default_output_suffix(), "w+b")

    if args.port:
        port = args.port
    if not args.port:
        port = chameleon.ProbeInputs()[0]
        print('Using auto-detected port %d (%s)' % (
            port, chameleon.GetConnectorType(port)))

    was_plugged = chameleon.IsPlugged(port)
    if was_plugged and (args.replug or args.edid_file):
        print('Unplugging...')
        chameleon.Unplug(port)

    if args.edid_file:
        edid = ChameleonEdid(chameleon, args.edid_file.read())
        chameleon.ApplyEdid(port, edid.id)

    if not chameleon.IsPlugged(port):
        print('Plugging...')
        chameleon.Plug(port)

    try:
        if args.area:
            port_type = chameleon.GetConnectorType(port)
            if port_type == 'HDMI':
                x, y, width, height = round_resolution(args.area, 16)
            else:
                x, y, width, height = round_resolution(args.area, 8)
        else:
            x = 0; y = 0
            width, height = chameleon.DetectResolution(port)

        print('screen size %dx%d' % (width, height))

        # Make sure we can capture the specified number of frames
        frame_limit = chameleon.GetMaxFrameLimit(port, width, height)
        if args.count > frame_limit:
            parser.error(
                '--count: Chameleon can only capture up to %d frames on port %d' % (
                    frame_limit, port))

        print('Capturing %d frames with geometry %dx%d+%d+%d' %
              (args.count, width, height, x, y))
        chameleon.CaptureVideo(port, args.count, x, y, width, height)

        def read_frame(idx, output_path):
            frame = chameleon.ReadCapturedFrame(idx)
            with tempfile.NamedTemporaryFile(suffix='.rgb') as f:
                f.write(frame)
                f.flush()
                subprocess.check_call([
                    'convert', '-size', '%dx%d' % (width-x, height-y),
                    '-depth', '8',
                    f.name, output_path
                ])

        if args.count == 1:
            print("Outputting to %s..." % args.output.name)
            read_frame(0, args.output.name)
            view_file = args.output.name

            if args.view:
                print('Opening with "%s"' % args.view)
                subprocess.check_call([*args.view.split(), view_file])
        else:
            print("Saving frames in %s..." % args.output_dir)
            capture_name = lambda idx: "%s/%s-%d.png" % (
                    args.output_dir, args.file_prefix, idx)
            for i in range(0, chameleon.GetCapturedFrameCount()):
                read_frame(i, capture_name(i))
                print('.', end='', flush=True)

            print('')

    finally:
        if not was_plugged:
            print('Unplugging to the original state...')
            chameleon.Unplug(port)
