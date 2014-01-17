try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='CoMoTo',
    version='0.1',
    description='Web application for software collaboration detection',
    author='Charlie Meyer',
    author_email='charlie@charliemeyer.net',
    url='https://comoto.cs.illinois.edu',
    install_requires=[
        "Pylons==0.9.7",
        "SQLAlchemy>=0.5",
        "BeautifulSoup",
        "elixir",
        "formbuild==2.2.0",
        "pygments",
        "turbomail",
        "shabti==0.3.2c",
        "sqlalchemy-migrate==0.6",
        "webob==1.0.8"
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'mossweb': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'mossweb': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['Elixir', 'PasteScript', 'Pylons', 'Shabti'],
    entry_points="""
    [paste.app_factory]
    main = mossweb.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
