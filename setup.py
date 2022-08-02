from setuptools import setup, find_packages


setup()

"""
setup(name = 'arcane_suite',
	version = '0.0.1',
	license = 'GPLv3',
	description = 'arcane_suite is an arbitrary set of radio astronomical pipelines using the Snakemake workflow manager.',
	url = 'https://github.com/rstofi/arcane-suite',
	author = 'Kristof Rozgonyi',
	author_email = 'Kristof.Rozgonyi@physik.uni-muenchen.de',
	packages = [
        "src/arcane_suite"
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
     		'init_otfms=src.init_otfms:main'
        ],
    },
)
"""