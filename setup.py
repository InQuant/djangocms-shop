#!/usr/bin/env python
from setuptools import setup, find_packages
import shop

REQUIREMENTS = [
    'Django>=2.1,<3.1',
    'django-filer>=1.7',
    'django-ipware',
    'django-fsm>=2.7',
    'django-fsm-admin',
    'djangorestframework>=3.9,<4',
    # 'django-rest-auth',
    'Django-Select2',
    'django-admin-sortable2',
    # 'django-formtools',
    # 'django_polymorphic',
    'django-post_office',
    'django-cms>=3.7',
]

CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Framework :: Django',
    'Framework :: Django :: 2.1',
    'Framework :: Django :: 2.2',
    'Framework :: Django :: 3.0',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
]

setup(
    author="Lutz Mende",
    author_email="lutz.mende@inquant.de",
    name="djangocms-shop",
    version=shop.__version__,
    description="A RESTful e-commerce framework based on DjangoCMS",
    long_description='',
    long_description_content_type='text/markdown',
    url='',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['tests', 'docs']),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
)
