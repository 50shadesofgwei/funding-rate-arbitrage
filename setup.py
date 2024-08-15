from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

requirements.append('hmx-v2-python @ git+https://github.com/50shadesofgwei/v2-sdk-python.git@main')
requirements.append('gmx_python_sdk @ git+https://github.com/50shadesofgwei/gmx_python_sdk_custom.git@main')

setup(
    name='SynthetixFundingRateArbitrage',
    version='0.3.0',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'project-run = Main.run:run',
            'project-run-demo = Main.run:demo',
            'deploy-collateral-synthetix = TxExecution.Synthetix.run:main',
            'deploy-collateral-hmx = TxExecution.HMX.run:main',
            'close-position-pair = TxExecution.Master.run:main',
            'is-position-open = TxExecution.Master.run:is_position_open'
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
