from setuptools import setup, find_packages

setup(
    name="mistral_chatbot",
    version="0.1.0",
    description="A chatbot application using the Mistral AI API",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "mistralai",
        "numpy",
    ],
    python_requires=">=3.8",
)