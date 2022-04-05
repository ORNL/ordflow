from codecs import open
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()

with open(os.path.join(here, 'dflow/__version__.py')) as f:
    __version__ = f.read().split("'")[1]

requirements = ['requests']

setup(
    name='dflow',
    version=__version__,
    description="Python interface to ORNL's DataFlow",
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Cython',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering :: Information Analysis'],
    keywords=['data transfer', 'REST', 'Globus', 'metadata', 'scientific', 'instruments', 'network'],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    url='https://github.com/ORNL/dflow',
    license='MIT',
    author='S. Somnath',
    author_email='somnaths@ornl.gov',
    install_requires=requirements,
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    platforms=['Linux', 'Mac OSX', 'Windows 10/8.1/8/7'],
    # package_data={'sample':['dataset_1.dat']}
    test_suite='pytest',
    # dependency='',
    # dependency_links=[''],
    include_package_data=False,
)
