from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='SynthetixFundingRateArbitrage',
    version='0.1.0',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'project-run = SynthetixFundingRateArbitrage.Main.run:run',
            'deploy-collateral = SynthetixFundingRateArbitrage.TxExecution.Synthetix.run:main',
            'close-all-positions = SynthetixFundingRateArbitrage.TxExecution.Master.run:run'
        ],
    },

    description='Delta-neutral funding rate arbitrage searcher',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='zk50.eth',
    url='https://github.com/50shadesofgwei/SynthetixFundingRateArbitrage',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ]
)