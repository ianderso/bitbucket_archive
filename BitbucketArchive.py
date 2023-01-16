# coding=utf-8
from subprocess import call
from atlassian.bitbucket import Cloud
from boto3 import client
from botocore.exceptions import ClientError
import argparse
import logging
import sys

def get_clone_url(repository, type='https'):
    links = repository.get_data('links')
    for link in links['clone']:
        if type == link['name']:
            return link['href']

def get_repository(username, password, workspace, repository_slug):
    cloud = Cloud( username=username, password=password)
    return cloud.workspaces.get(workspace).repositories.get(repository_slug)

def clone_repository(repository):
    logging.info ("Cloning %s", repository.name)
    try:
        call("git clone --quiet --mirror {repo_url}".format(repo_url=get_clone_url(repository)), shell=True)
    except:
        logging.error ("Failed to clone %s", repository.name)
        exit()

def compress_repository(repository):
    logging.info ("Compressing %s", repository.name)
    try:
        call("tar -cjf {slug}.git.tbz {slug}.git".format(slug=repository.slug), shell=True)
    except:
        logging.error ("Failed to Compress %s", repository.name)
        exit()
    try:
        call("rm -Rf {slug}.git".format(slug=repository.slug), shell=True)
    except:
        logging.error ("Failed to Remove %s", repository.name)
        exit()

def upload_repo_s3(repository, bucket, path):
    s3_client = client('s3')
    logging.info("S3 Uploading %s", repository.name)
    try:
        s3_client.upload_file("{slug}.git.tbz".format(slug=repository.slug), bucket, "{path}/{slug}.git.tbz".format(path=path, slug=repository.slug))
    except ClientError as e:
        logging.error(e)
        exit()

def delete_repository(repository):
    try:
        repository.delete()
    except:
        logging.error ("Failed to Delete %s From Bitbucket", repository.name)
        exit()

def get_repositories_from_file(file):
    with open(file, "r") as repofile:
        return repofile.read().splitlines()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="Bitbucket Username", required=True)
    parser.add_argument("-p", "--password", help="Bitbucket Password", required=True)
    parser.add_argument("--workspace", help="Bitbucket workspace containing the repositories to be archived")
    parser.add_argument("--bucket", help="S3 bucket to put compressed repositories")
    parser.add_argument("--path", default="git-archive", help="Path in the S3 bucket to use (default: git-archive)")
    parser.add_argument('--file', help="Text file containing repo slugs, one per line")
    parser.add_argument('--logfile', help='filename to log output')
    parser.add_argument('repository', nargs='*', help="instead of using a repository file, repositories can be specified on the cli")
    args = parser.parse_args()

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
        exit()

    for repo in repos_to_archive:
        repository = get_repository(args.username, args.password, args.workspace, repo)
        clone_repository(repository)
        compress_repository(repository)
        upload_repo_s3(repository, args.bucket, args.path)
        delete_repository(repository)