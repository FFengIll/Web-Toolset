import logging
import sys

__all__=['logging']

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(filename)s [%(lineno)d] %(levelname)s: %(message)s', )
formatter = logging.Formatter(
    '%(asctime)s %(filename)s [%(lineno)d] %(levelname)s: %(message)s', datefmt='%Y-%m-%d, %a, %H:%M:%S')
console.setFormatter(formatter)

logger = logging.getLogger('test')
logger.setLevel(logging.INFO)
logger.addHandler(console)
logging = logger
