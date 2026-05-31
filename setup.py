"""
setup.py - Install dependencies
"""

from setuptools import setup, find_packages

setup(
    name="prismcorp-advisor-core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Flask==2.3.0",
        "Flask-CORS==4.0.0",
        "python-dotenv==1.0.0",
    ],
    python_requires=">=3.8",
)
