try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from ckanclient import __version__, __description__, __long_description__, __license__

setup(
    name='ckanclient',
    version=__version__,
    author='Appropriate Software Foundation, Open Knowledge Foundation',
    author_email='info@okfn.org',
    license=__license__,
    url='http://www.okfn.org/ckanclient/',
    download_url='http://www.okfn.org/ckanclient/',
    description=__description__,
    keywords='data packaging component tool client',
    long_description =__long_description__,
    install_requires=[
        'simplejson',
    ],
    packages=find_packages(exclude=['ez_setup']),
    #scripts = ['bin/ckanclient-admin'],
    include_package_data=True,
    package_data={'ckanclient': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors = {'ckanclient': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', None),
    #        ('public/**', 'ignore', None)]},
    entry_points="""
    #[paste.app_factory]
    #main = ckanclient.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
    # setup.py test command needs a TestSuite so does not work with py.test
    # test_suite = 'nose.collector',
    # tests_require=[ 'py >= 0.8.0-alpha2' ]
)
