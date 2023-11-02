from setuptools import setup, find_packages

setup(
    name='clickwrap',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    author='Your Name',
    author_email='your.email@example.com',
    description='A simple ClickUp API wrapper',
)
