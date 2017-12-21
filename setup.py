try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Raspberry Pi Camera Scheduler',
    'author': 'Damon McCullough',
    'url': 'https://github.com/damonmcc/ViewHive',
    'download_url': 'https://github.com/damonmcc/ViewHive.git',
    'author_email': 'damonmcc1391@gmail.com',
    'version': '0.7',
    'install_requires': ['nose', 'pigpio', 'PIL', 'picamera'],
    'packages': ['viewhive'],
    'scripts': ['bin/ir_test'],
    'name': 'ViewHive'
}

setup(**config)
