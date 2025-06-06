from setuptools import setup, find_packages

setup(
    name="txt2sql",
    version="1.0.0",
    description="Agente SQL Interativo para dados do SUS",
    author="Data Science Team",
    packages=find_packages(),
    install_requires=[
        "langchain-ollama>=0.1.0",
        "langchain-community>=0.2.0",
        "langchain>=0.2.0",
        "sqlalchemy>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "txt2sql=src.main:main",
        ],
    },
)