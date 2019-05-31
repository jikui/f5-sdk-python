# F5 Cloud SDK

## Table of Contents
- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Developer Setup](#developer-setup)
- [Artifacts](#artifacts)

## Introduction

This project provides a use case focused python SDK for interacting with F5 products, specifically around cloud and automation.  The UX will closely mirror established, successful SDK's such as Azure, AWS and Google python SDK's.

## Quick Start

Pre-Release Note: Currently published in an artifactory repo.

```bash
pip3 install f5-cloud-sdk --extra-index-url https://***REMOVED***/artifactory/api/pypi/f5-cloud-solutions-pypi/simple
```

## Developer Setup

### Installation

Note: A virtual environment should be created first.  See [python docs](https://docs.python.org/3/library/venv.html) for more details.

```bash
pip3 install -r requirements.txt
pip3 install .
```

Note: Python 2.7 can be run via a container - `docker run --rm -it -v $(pwd):/usr/dir python:2.7 /bin/bash`

### Testing

This project uses `Make` as a build automation tool... check out the Makefile for the full set of recipes.

- Run unit tests: ```make unit_test```
- Run linter: ```make lint```
- Build code coverage documentation: ```make coverage```
- Build code documentation: ```make code_docs```

## Artifacts

- Index: https://cloudsolutions.pages.***REMOVED***/f5-cloud-sdk
- Code coverage report: https://cloudsolutions.pages.***REMOVED***/f5-cloud-sdk/coverage/
- Code documentation: https://cloudsolutions.pages.***REMOVED***/f5-cloud-sdk/code-docs/

