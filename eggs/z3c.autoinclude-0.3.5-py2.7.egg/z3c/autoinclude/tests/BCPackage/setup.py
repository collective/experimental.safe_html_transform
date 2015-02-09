from setuptools import setup, find_packages

version = '0.1'

setup(name='BCPackage',
      version=version,
      description="",
      long_description="""\
""",
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
      ],
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      package_data = {'': ['*.zcml',]},
      packages=find_packages(),
      namespace_packages=['b'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
	  'TestDirective',
	  'SiblingPackage',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
