import argparse
import os
import logging
import collections
from .version import __version__
from .tylogger import logger
from .strings import Strings
from .translator import Translator
from tabulate import tabulate


def parent_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-v', '--verbose', action="store_true", dest="verbose", help="show more debugging information")
    parser.add_argument('--utf8', action="store_true", dest="utf8", help="use encoding UTF-8")
    return parser


def extant_file(x):
    """
    'Type' for argparse - checks that file exists but does not open.

    http://stackoverflow.com/questions/11540854/file-as-command-line-argument-for-argparse-error-message-if-argument-is-not-va
    """
    if not os.path.exists(x):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: x does not exist
        raise argparse.ArgumentTypeError("{0} does not exist".format(x))
    return x


def arg_parser():
    description = r"""
  _______     _____ _        _
 |__   __|   / ____| |      (_)
    | |_   _| (___ | |_ _ __ _ _ __   __ _ ___
    | | | | |\___ \| __| '__| | '_ \ / _` / __|
    | | |_| |____) | |_| |  | | | | | (_| \__ \
    |_|\__, |_____/ \__|_|  |_|_| |_|\__, |___/
        __/ |                         __/ |
       |___/                         |___/
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=description)
    parser.add_argument('--version', action='version', version=__version__)
    subparsers = parser.add_subparsers(title='subcommands', dest='action')

    generate_parser = subparsers.add_parser('generate', parents=[parent_parser()],
                                            help='generate `.strings` file from source code files.')
    generate_parser.add_argument('files', metavar='file', nargs='+', help='source file .[mc]')
    generate_parser.add_argument('-a', '--aliases', nargs='+', help='aliases')
    generate_parser.add_argument('-o', '--output', nargs='+', dest='destinations', help='place output files in dirs')

    translate_parser = subparsers.add_parser('translate', parents=[parent_parser()],
                                             help='using Baidu Translate Service to translate `.strings` file.')
    translate_parser.add_argument('source', help='source `.strings` file')
    translate_parser.add_argument('destination', help='destination, a file or directory')
    translate_parser.add_argument('--dst-lang', required=True, help='destination language')
    translate_parser.add_argument('-s', '--src-lang', help='source language')

    lint_parser = subparsers.add_parser('lint', parents=[parent_parser()],
                                        help='Validates a `.strings` file.')
    lint_parser.add_argument('file', help='`.strings` file', type=extant_file)
    return parser


def main(argv=None):
    parser = arg_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.action == 'generate':
        generate(args=args, parser=parser)
    elif args.action == 'translate':
        translate(args=args)
    elif args.action == 'lint':
        lint(args=args)

    exit(0)


def generate(args, parser):
    for filename in args.files:
        if not os.path.exists(filename):
            parser.error('\'%s\' not exists' % filename)
        elif os.path.isdir(filename):
            parser.error('\'%s\' is a directory' % filename)

    dsts = args.destinations if args.destinations else ["."]

    strings = Strings(aliases=args.aliases, encoding=args.utf8)
    for dst in dsts:
        strings.generate(files=args.files, dst=dst)
    logger.success('have fun!')


def translate(args):
    translator = Translator(args.source, lang=args.src_lang)
    translator.translate(args.destination, dst_lang=args.dst_lang)
    logger.success('have fun!')


def lint(args):
    logger.process('Parsing Source Reference...')
    elems = Strings.parsing_elems(filename=args.file, encoding='utf8' if args.utf8 else None)
    logger.process('Check Duplicate Keys...')
    duplicates = []
    for item, count in collections.Counter([e[0] for e in elems]).items():
        if count > 1:
            duplicates.append((item, count))

    if duplicates:
        table = []
        table_file = []
        logger.info('Find the following:')
        for key, count in duplicates:
            table.append([key, count])
            for elem in elems:
                if elem[0] == key:
                    table_file.append([elem[2], elem[0], elem[1]])
        logger.info(tabulate(table, headers=['Key', 'Count'], showindex='always', tablefmt="orgtbl"))
        logger.debug('Detail:')
        logger.debug(tabulate(table_file, headers=['Line', 'Key', 'Value'], tablefmt="orgtbl"))
        logger.error('Duplicate Keys')
        exit(1)

    logger.success('lint success')


if __name__ == '__main__':
    main()