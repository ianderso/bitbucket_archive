# Bitbucket Repo Archiver

This script simplifies the process of archiving and removing old repositories from bitbucket. The repositories are backed up with the git --mirror to retain tags and branches, and then compressed and uploaded to Amazon S3, then finally deleted from BitBucket.

## Requirements

- Python 3.8 or higher
- Boto3
- atlassian-python-api

## Installation

Clone the repository to your desired location. Then, make the directory a Python vm

`python3 -m venv bitbucket-archive`

Change directory into the repo directory, and enable the vm

`cd bitbucket-archive
 source bin/activate`

Then install python requirements with:

`pip install -r requirements.txt`

## Usage

`usage: main.py [-h] -u USERNAME -p PASSWORD [--workspace WORKSPACE] [--bucket BUCKET] [--path PATH] [--file FILE] [repository ...]

positional arguments:
  repository            instead of using a repository file, repositories can be specified on the cli

options:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Bitbucket Username
  -p PASSWORD, --password PASSWORD
                        Bitbucket Password
  --workspace WORKSPACE
                        Bitbucket workspace containing the repositories to be archived
  --bucket BUCKET       S3 bucket to put compressed repositories
  --path PATH           Path in the S3 bucket to use (default: git-archive)
  --file FILE           Text file containing repo slugs, one per line`