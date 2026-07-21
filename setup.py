from setuptools import setup, find_packages

setup(
    name="forensic-suite",
    version="2.0.0",
    description="Framework de Analisis Forense Digital con cadena de custodia MP 2017",
    author="Tr3w01",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
    ],
    extras_require={
        "full": ["cryptography>=41.0.0", "requests>=2.28.0"],
        "dev": ["pytest>=7.0", "pytest-cov>=4.0"],
    },
    entry_points={
        "console_scripts": [
            "forensic_suite=forensic_suite.__main__:main",
            "fs=forensic_suite.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
    ],
)
