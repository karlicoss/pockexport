import argparse
from pathlib import Path
import sys
from typing import Sequence, Dict, Any, Optional, Union


Json = Dict[str, Any]


def Parser(*args, **kwargs):
    # just more reasonable default for literate usage
    return argparse.ArgumentParser( # type: ignore[misc]
        *args,
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=100), # type: ignore
        **kwargs,
    )


def setup_parser(parser: argparse.ArgumentParser, *, params: Sequence[str], extra_usage: Optional[str]=None):
    PARAMS_KEY = 'params'

    # eh, doesn't seem to be possible to achieve this via mutually exclusive groups in argparse...
    # and still, cryptic error message if you forget to specify either :(
    set_from_file = False
    set_from_cmdl = False

    class SetParamsFromFile(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if set_from_cmdl:
                raise RuntimeError("Please use either --secrets or individual --param arguments")
            nonlocal set_from_file; set_from_file = True

            secrets_file = values
            obj = {} # type: ignore

            # we control the file with secrets so exec is fine
            exec(secrets_file.read_text(), {}, obj)

            def get(k):
                if k not in obj:
                    raise RuntimeError("Couldn't extract '{}' param from file {} (got {})".format(k, secrets_file, obj))
                return obj[k]

            pdict = {k: get(k) for k in params}
            setattr(namespace, PARAMS_KEY, pdict)

    class SetParam(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if set_from_file:
                raise RuntimeError("Please use either --secrets or individual --param arguments")
            nonlocal set_from_cmdl; set_from_cmdl = True

            pdict = getattr(namespace, PARAMS_KEY, {})
            pdict[self.dest] = values
            setattr(namespace, PARAMS_KEY, pdict)

    class SetOutput(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            output_path = values

            def dump_to_stdout(data):
                sys.stdout.write(data)

            def dump_to_file(data):
                with output_path.open('w', encoding='utf-8') as fo:
                    fo.write(data)
                print('saved data to {output_path}'.format(output_path=output_path), file=sys.stderr)

            if output_path is None:
                dumper = dump_to_stdout
            else:
                dumper = dump_to_file

            setattr(namespace, 'dumper', dumper)

    paramss = ' '.join(f'--{p} <{p}>' for p in params)
    # TODO extract export programmatically?

    sep = '\n: '
    secrets_example = sep + sep.join(f'{p} = "{p.upper()}"' for p in params)

    parser.epilog = f'''
Usage:

*Recommended*: create =secrets.py= keeping your api parameters, e.g.:

{secrets_example}


After that, use:

: ./export.py --secrets /path/to/secrets.py

That way you type less and have control over where you keep your plaintext secrets.

*Alternatively*, you can pass parameters directly, e.g.

: ./export.py {paramss}

However, this is verbose and prone to leaking your keys/tokens/passwords in shell history.

    '''

    if extra_usage is not None:
        parser.epilog += extra_usage

    parser.epilog += '''

I *highly* recommend checking exported files at least once just to make sure they contain everything you expect from your export. If not, please feel free to ask or raise an issue!
    '''

    parser.add_argument(
        '--secrets',
        metavar='SECRETS_FILE',
        type=Path,
        action=SetParamsFromFile,
        required=False,
        help='.py file containing API parameters',
    )
    gr = parser.add_argument_group('API parameters')
    for param in params:
        gr.add_argument('--' + param, type=str, action=SetParam)

    parser.add_argument(
        'path',
        type=Path,
        action=SetOutput,
        nargs='?',
        help='Optional path where exported data will be dumped, otherwise printed to stdout',
    )


import logging
def setup_logger(logger: Union[str, logging.Logger], level='DEBUG', **kwargs):
    """
    Wrapper to simplify logging setup.
    """
    def mklevel(level: Union[int, str]) -> int:
        if isinstance(level, str):
            return getattr(logging, level)
        else:
            return level
    lvl = mklevel(level)

    if isinstance(logger, str):
        logger = logging.getLogger(logger)

    try:
        # try logzero first, so user gets nice colored logs
        import logzero  # type: ignore
        # TODO meh, default formatter shorthands logging levels making it harder to search errors..
    except ModuleNotFoundError:
        import warnings
        warnings.warn("You might want to install 'logzero' for nice colored logs")

        # ugh. why does it have to be so verbose?
        logger.setLevel(lvl)
        ch = logging.StreamHandler()
        ch.setLevel(lvl)
        FMT = '[%(levelname)s %(name)s %(asctime)s %(filename)s:%(lineno)d] %(message)s'
        ch.setFormatter(logging.Formatter(FMT))
        logger.addHandler(ch)
    else:
        logzero.setup_logger(logger.name, level=lvl)
