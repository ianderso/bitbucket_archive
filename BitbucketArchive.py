# coding=utf-8
from subprocess import call
from argparse import ArgumentParser
import sys
import logging
from atlassian.bitbucket import Cloud
from boto3 import client
from botocore.exceptions import ClientError

def get_clone_url(repository, clone_type='https'):
    links = repository.get_data('links')
    for link in links['clone']:
        if clone_type == link['name']:
            return link['href']

def get_repository(cloud, workspace, repository_slug):
    return cloud.workspaces.get(workspace).repositories.get(repository_slug)

def clone_repository(repository):
    logging.info ("Cloning %s", repository.name)
    repo_url = get_clone_url(repository)
    try:
        call(f"git clone --quiet --mirror {repo_url}", shell=True)
    except Exception as e:
        logging.error ("Failed to clone %s, error was %s", repository.name, e)
        sys.exit()

def compress_repository(repository):
    slug=repository.slug
    logging.info ("Compressing %s", repository.name)
    try:
        call(f"tar -cjf {slug}.git.tbz {slug}.git", shell=True)
    except Exception as e:
        logging.error ("Failed to Compress %s, error was %s", repository.name, e)
        sys.exit()
    try:
        call(f"rm -Rf {slug}.git", shell=True)
    except Exception as e:
        logging.error ("Failed to Remove %s, error was %s", repository.name, e)
        sys.exit()

def upload_repo_s3(repository, s3client, bucket, path):
    slug=repository.slug
    logging.info("S3 Uploading %s", repository.name)
    try:
        s3client.upload_file(f"{slug}.git.tbz", bucket, f"{path}/{slug}.git.tbz")
    except ClientError as s3_error:
        logging.error(s3_error)
        sys.exit()

def delete_repository(repository):
    try:
        logging.info("Deleting %s from BitBucket", repository.name)
        repository.delete()
    except Exception as e:
        logging.error ("Failed to Delete %s From Bitbucket, error was %s", repository.name, e)
        sys.exit()

def get_repositories_from_file(file):
    with open(file, "r") as repofile:
        return repofile.read().splitlines()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-u", "--username", help="Bitbucket Username", required=True)
    parser.add_argument("-p", "--password", help="Bitbucket Password", required=True)
    parser.add_argument("--workspace",
        help="Bitbucket workspace containing the repositories to be archived")
    parser.add_argument("--bucket", help="S3 bucket to put compressed repositories")
    parser.add_argument("--path", default="git-archive",
        help="Path in the S3 bucket to use (default: git-archive)")
    parser.add_argument('--file', help="Text file containing repo slugs, one per line")
    parser.add_argument('--logfile', help='filename to log output')
    parser.add_argument('repository', nargs='*',
        help="instead of using a repository file, repositories can be specified on the cli")
    args = parser.parse_args()

    cloud = Cloud( username=args.username, password=args.password)
    s3_client = client('s3')

    handlers = [logging.StreamHandler(sys.stdout)]
    if args.logfile:
        handlers.append(logging.FileHandler("debug.log"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers
    )

    if args.repository:
        repos_to_archive = args.repository
    elif args.file:
        repos_to_archive = get_repositories_from_file(args.file)
    else:
        logging.error("Must specify one of --file or repository")
        sys.exit()

    for repo in repos_to_archive:
        archive_repository = get_repository(cloud, args.workspace, repo)
        clone_repository(archive_repository)
        compress_repository(archive_repository)
        upload_repo_s3(archive_repository, s3_client, args.bucket, args.path)
        delete_repository(archive_repository)
