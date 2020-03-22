import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="socket.engine",
    version="0.2.0",
    author="Jeremy Kanovsky",
    author_email="kanovsky.jeremy@gmail.com",
    description="A universal communication engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0xJeremy/socket.engine",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
)