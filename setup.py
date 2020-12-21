from setuptools import setup

with open('requirements.txt') as f:
    deps = f.readlines()

setup(
    name='netprobe',
    version='1.0.1',
    packages=[''],
    url='https://github.com/jdcasey/netprobe',
    license='GPLv3',
    author='John Casey',
    author_email='jdcasey@commonjava.org',
    description='Runs various diagnostics on the local network connection, and exposes it via Telegram MTProto and/or '
                'Google Firestore database records',
    install_requires=deps,
    entry_points={
        'console_scripts': [
            'netprobe-run = netprobe.command:run'
        ]
    }
)
