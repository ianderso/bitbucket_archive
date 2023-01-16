# coding=utf-8
from subprocess import call
from atlassian.bitbucket import Cloud
from boto3 import client
from botocore.exceptions import ClientError
import argparse


def get_clone_url(repository, type='https'):
    links = repository.get_data('links')
    for link in links['clone']:
        if type == link['name']:
            return link['href']

def get_repository(username, password, workspace, repository_slug):
    cloud = Cloud( username=username, password=password)
    return cloud.workspaces.get(workspace).repositories.get(repository_slug)

def clone_repository(repository):
    print ("Cloning", repository.name)
    try:
        call("git clone --quiet --mirror {repo_url}".format(repo_url=get_clone_url(repository)), shell=True)
    except:
        print ("Failed to clone", repository.name)
        exit()

def compress_repository(repository):
    print ("Compressing", repository.name)
    try:
        call("tar -cjf {slug}.git.tbz {slug}.git".format(slug=repository.slug), shell=True)
    except:
        print ("Failed to Compress", repository.name)
        exit()
    try:
        call("rm -Rf {slug}.git".format(slug=repository.slug), shell=True)
    except:
        print ("Failed to Remove", repository.name)
        exit()

def upload_repo_s3(repository, bucket, path):
    s3_client = client('s3')
    print("S3 Uploading", repository.name)
    try:
        s3_client.upload_file("{slug}.git.tbz".format(slug=repository.slug), bucket, "{path}/{slug}.git.tbz".format(path=path, slug=repository.slug))
    except ClientError as e:
        print(e)
        exit()

def delete_repository(repository):
    try:
        repository.delete()
    except:
        print ("Failed to Delete", repository.name, "From Bitbucket")
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
    parser.add_argument('repository', nargs='*', help="instead of using a repository file, repositories can be specified on the cli")
    args = parser.parse_args()

    if args.repository:
        repos_to_archive = args.repository
    elif args.file:
        repos_to_archive = get_repositories_from_file(args.file)
    else:
        print("Must specify one of --file or repository")
        exit()

    for repo in repos_to_archive:
        repository = get_repository(args.username, args.password, args.workspace, repo)
        clone_repository(repository)
        compress_repository(repository)
        upload_repo_s3(repository, args.bucket, args.path)
        delete_repository(repository)