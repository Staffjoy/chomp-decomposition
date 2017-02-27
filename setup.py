from setuptools import setup, find_packages

version = "1.0"
setup(name="chomp",
      packages=find_packages(),
      version=version,
      description="Staffjoy V1 Forecast to Shifts Decomposition Tool",
      author="Philip Thomas",
      author_email="philip@staffjoy.com",
      license="MIT",
      url="https://github.com/staffjoy/chomp-decomposition",
      download_url="https://github.com/StaffJoy/chomp-decomposition/archive/%s.tar.gz" % version,
      keywords=["staffjoy-api", "staffjoy", "staff joy", "chomp"],
      install_requires=["requests[security]"], )


