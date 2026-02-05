from setuptools import setup, find_packages

setup(
    name="ai-code-doc-generator-engine",
    version="0.1.0",
    description="Python analysis engine for AI Code Documentation Generator",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "hypothesis>=6.82.0",
            "black>=23.7.0",
            "mypy>=1.4.0",
        ]
    },
)
