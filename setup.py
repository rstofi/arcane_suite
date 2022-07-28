from setuptools import setup, find_packages

setup(name = 'arcane-suite',
	version = '0.0.1',
	license = 'GPLv3',
	description = 'arcane_suite is an arbitrary set of radio astronomical pipelines using the Snakemake workflow manager.',
	url = 'https://github.com/rstofi/arcane-suite',
	author = 'Kristof Rozgonyi',
	author_email = 'Kristof.Rozgonyi@physik.uni-muenchen.de',
	packages = [
        "src"
    ],
    install_requires = [
    	"numpy>=1.22.0"
    ],
    classifiers = [
	    'Topic :: Scientific/Engineering :: Astronomy',
    	'Programming Language :: Python'
    ],
    entry_points = {
        'console_scripts': [
     		#Here comes the command-line executable scripts
        ],
    },
)
