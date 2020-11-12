import os
import re

import click
from git import Repo, BadName
from github import Github, UnknownObjectException


def get_pr_info(pr_url):
    regex = r"https://github\.com/(.*?)/pull/(\d+)"
    matches = re.match(regex, pr_url)

    client = Github(os.getenv("GITHUB_TOKEN"))

    try:
        repo = client.get_repo(matches.group(1))
        pull_request = repo.get_pull(int(matches.group(2)))

        return dict(
            base_branch=pull_request.base.ref,
            base_sha=pull_request.base.sha,
            base_repo=pull_request.base.repo.clone_url,
            head_branch=pull_request.head.ref,
            head_sha=pull_request.head.sha,
            head_repo=pull_request.head.repo.clone_url,
            is_mergeable=not pull_request.merged and pull_request.mergeable,
        )
    except UnknownObjectException as e:
        click.secho("Failed to locate given Pull request", fg="yellow")

    return {}


def get_git_info(work_dir):
    repo = Repo(work_dir)

    current_commit_tag = next(filter(lambda x: x.commit == repo.head.commit, repo.tags), "")

    previous_tag = ""
    if len(repo.tags) > 2:
        previous_tag = repo.tags[-1]

    return dict(
        current_commit_tag=current_commit_tag,
        previous_tag=str(previous_tag),
        previous_tag_sha=str(previous_tag.tag) if previous_tag else "",
    )


@click.group()
def run():
    pass


@run.command()
@click.option("--pr", default=os.getenv("GITHUB_PR_URL"))
@click.option("--work-dir", default=os.getcwd())
@click.option("--debug", is_flag=True)
def info(pr, debug, work_dir):
    variables = {}
    if pr:
        variables.update(get_pr_info(pr))

    variables.update(get_git_info(work_dir))

    for k, v in variables.items():
        if debug:
            click.secho(f"{k}::{v}", fg="green")

        click.echo(f"::set-output name={k}::{v if type(v) != bool else str(v).lower()}")


@run.command(name="has-changes")
@click.option("--work-dir", default=os.getcwd())
def has_changes(work_dir):
    repo = Repo(work_dir)

    click.echo(f"::set-output name=has_changes::{'true' if repo.is_dirty() else 'false'}")


@run.command(name="is-behind")
@click.option("--pr", default=os.getenv("GITHUB_PR_URL"), required=True)
@click.option("--work-dir", default=os.getcwd())
def is_behind(pr, work_dir):
    pr = get_pr_info(pr)

    repo = Repo(work_dir)
    is_behind = False
    try:
        commits = list(repo.iter_commits(f"origin/{pr['head_branch']}..origin/{pr['base_branch']}"))
        is_behind = len(commits) > 0
    except BadName as e:
        pass

    click.echo(f"::set-output name=is_behind::{str(is_behind).lower()}")
