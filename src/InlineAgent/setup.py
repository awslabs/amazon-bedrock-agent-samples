import setuptools
import versioneer

setuptools.setup(version=versioneer.get_version(), cmdclass=versioneer.get_cmdclass())
