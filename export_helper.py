import argparse
from pathlib import Path
import sys
from typing import Sequence


def setup_parser(parser: argparse.ArgumentParser, params: Sequence[str]):
    PARAMS_KEY = 'params'

    class SetParamsFromFile(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            secrets_file = values
            obj = {} # type: ignore

            # we control the file with secrets so exec is fine
            exec(secrets_file.read_text(), {}, obj)

            pdict = {k: obj[k] for k in params}
            setattr(namespace, PARAMS_KEY, pdict)

    class SetParam(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            pdict = getattr(namespace, PARAMS_KEY, {})
            pdict[self.dest] = values
            setattr(namespace, PARAMS_KEY, pdict)

    class SetOutput(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            output_path = values

            def dump_to_stdout(data):
                sys.stdout.write(data)

            def dump_to_file(data):
                with output_path.open('w') as fo:
                    fo.write(data)
                print(f'saved data to {output_path}', file=sys.stderr)

            if output_path is None:
                dumper = dump_to_stdout
            else:
                dumper = dump_to_file

            setattr(namespace, 'dumper', dumper)

    parser.add_argument(
        '--secrets',
        type=Path,
        action=SetParamsFromFile,
        required=False,
        help=f'.py file containing {", ".join(params)} variables',
    )
    gr = parser.add_argument_group('API parameters')
    for param in params:
        gr.add_argument('--' + param, type=str, action=SetParam)

    parser.add_argument(
        'path',
        type=Path,
        action=SetOutput,
        nargs='?',
        help='Optional path to backup, otherwise will be printed to stdout',
    )
