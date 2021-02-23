from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


print(find_packages())

setup(
        name='MAGE-Tab merger',
        version='0.0.2',
        description='Merges MAGE-Tab files considering covariates',
        long_description=readme(),
        packages=find_packages(),
        install_requires=['pandas', "networkx==2.5", "jinja2"],
        author='Pablo Moreno',
        long_description_content_type='text/markdown',
        author_email='',
        scripts=['merge_condensed_sdrfs.py', 'merge_sdrfs.py', 'merge_baseline_configuration_xmls.py'],
        license='MIT'
    )