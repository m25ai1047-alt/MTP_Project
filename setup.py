"""
Automated Root Cause Analysis System
Setup configuration for installation and distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
def read_requirements(file_path):
    """Read requirements from file, filtering comments and empty lines"""
    requirements = []
    if Path(file_path).exists():
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

# Core requirements (consolidated from all modules)
core_requirements = [
    # Anomaly Detection
    'scikit-learn>=1.0.0',
    'pandas>=1.3.0',
    'joblib>=1.0.0',
    'numpy>=1.21.0',

    # Code Indexing
    'tree-sitter-languages>=1.6.0',
    'chromadb>=0.4.0',
    'sentence-transformers>=2.2.0',
    'rank-bm25>=0.2.2',
    'watchdog>=2.1.0',

    # RCA Agent
    'fastapi>=0.95.0',
    'uvicorn[standard]>=0.20.0',
    'pydantic>=1.10.0',
    'requests>=2.28.0',
    'python-dotenv>=1.0.0',
]

setup(
    name="rca-system",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated Root Cause Analysis for Microservices using RAG and Anomaly Detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rca-system",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/rca-system/issues",
        "Source": "https://github.com/yourusername/rca-system",
        "Documentation": "https://github.com/yourusername/rca-system/wiki",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=core_requirements,
    extras_require={
        "dev": [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'flake8>=5.0.0',
            'mypy>=1.0.0',
            'pre-commit>=3.0.0',
        ],
    },
    entry_points={
        "console_scripts": [
            "rca-analyze=src.rca_agent.cli:main",
            "rca-train=src.anomaly_detector.train_model:main",
            "rca-index=src.code_indexer.bulk_indexer_enhanced:main",
            "rca-server=src.rca_agent.main_rca_agent:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
