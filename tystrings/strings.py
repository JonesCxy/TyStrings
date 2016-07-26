import os
import re
import codecs
import subprocess
from . import logger, BEER_EMOJI, DONE_FORMAT, SUCCESS_FORMAT

STRING_FILE = 'Localizable.strings'


class Strings(object):
    def __init__(self, target_dir, encoding='utf_16_le'):
        self.__dir = target_dir
        self.encoding = encoding
        self.filename = os.path.join(target_dir if target_dir else '', STRING_FILE)
        self.__reference = {}

    def generate(self, files):
        self.__generate_reference()
        script = 'genstrings'
        for filename in files:
            script += ' %s' % filename
        self.__run_script('%s -o %s' % (script, self.__dir))
        self.__translate()

    @staticmethod
    def __run_script(script):
        logger.debug('\nrun: %s' % script)
        process = subprocess.Popen(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = ''
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                output += line
                logger.debug(line.strip())
        logger.debug(BEER_EMOJI + ' process finished with %s' % ('success' if
                                                      process.returncode == 0 or process.returncode is None else
                                                     ('exit code %r' % process.returncode)))

        return process.returncode, output

    def __generate_reference(self):
        self.__reference = {}
        if os.path.exists(self.filename):
            f = codecs.open(self.filename, "r", encoding=self.encoding)
            for line in f:
                match = re.match(r'"(?P<key>.*?)" = "(?P<value>.*?)";', line)
                if match is not None:
                    key = match.group('key')
                    value = match.group('value')
                    self.__reference[key] = value
            f.close()
        logger.info(DONE_FORMAT.format('Generated Reference'))
        logger.info('count: %r' % len(self.__reference))

    def __translate(self):
        sum = 0
        translated = {}
        f = codecs.open(self.filename, "r", encoding=self.encoding)
        lines = f.readlines()
        for (index, line) in enumerate(lines):
            match = re.match(r'"(?P<key>.*?)" = "(?P<value>.*?)";', line)
            if match is not None:
                key = match.group('key')
                result = self.__reference.get(key, None)

                if result is not None:
                    value = match.group('value')
                    if self.__reference[key] != value:
                        line = '"%s" = "%s";\n' % (key, result)
                        lines[index] = line
                        sum += 1
                        translated[key] = result
        f.close()

        logger.info(DONE_FORMAT.format('Translated Strings'))
        logger.info('count: %r' % sum)
        logger.debug('')
        for k in translated.keys():
            logger.debug('%s => %s' % (k, translated[k]))

        f = codecs.open(self.filename, "w+", encoding=self.encoding)
        f.writelines(lines)
        f.flush()
        f.close()
        logger.info(SUCCESS_FORMAT.format('Write strings file to: %s' % self.filename))