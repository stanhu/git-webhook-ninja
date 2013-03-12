# Git WebHook Ninja

__by Stan Hu (stanhu at gmail.com)

git-webhook-ninja (for lack of a better name) is an extensible, post-receive
Git Web server that automatically handles GitHub and Bitbucket WebHook
requests.

Out of the box, it can automatically send e-mail notifications upon a Git push
event using git-commit-notifier
(https://github.com/git-commit-notifier/git-commit-notifier) for either Git host
provider.  However, it can be extend to do other tasks, such as pulling in
local changes and restarting a Web frontend automatically.

## Details

git-webhook-ninja performs the following sequence of actions:

1. Receives a POST request, verifies that the IP address is allowed, and
   automatically detects whether it is a GitHub or a Bitbucket request.

2. Runs 'git clone' of the local repository of the code if it does not exist.

3. Runs 'git checkout' of the given the branch if it does not exist yet.

4. Runs 'git pull' in the current repository.

5. Determines the starting and ending SHA ID of the Git commits from the payload data.
   Runs 'git-commit-notifier' for the before and after SHA ID of the request.

## Requirements

* Python 2.7 or higher.
* pip
* virtualenv

## Installing

1.  Create a virtual environment (see https://python-guide.readthedocs.org/en/latest/dev/virtualenvs/).

2.  Install the requirements:

```bash
pip install -r requirements.txt
```

3.  Copy settings.py.example to settings.py:

```bash
cp settings.py.example settings.py
```

4.  Edit settings.py and configure the local interface and ports.  For example, to run the
server on all interfaces and port 8888, set the configuration variables as such:
```
LISTEN_IP = '0.0.0.0'
LISTEN_PORT = 8888
```

4.  If you are using git-commit-notifier, set the full pathname of GIT_COMMIT_NOTIFIER_BIN in
settings.py.

5.  git-commit-notifier requires a configuration file to run.  This program supports the ability
to map custom configuration files per repository names.  Copy git_commit_notifier_config.py.example
to git_commit_notifier_config.py:

```
cp git_commit_notifier_config.py.example git_commit_notifier_config.py
```

6.  For each repository name, add an entry git_commit_notifier_config.py to the REPO_CONFIG_MAP
 dictionary.  For example, if you had a repository named 'project-A' and 'project-B', you might have:

```
REPO_CONFIG_MAP = {
    'project-A' : '/home/user/git-commit-notifier-project-A.yml',
    'project-B' : '/home/user/git-commit-notifier-project-B.yml'
}
```

NOTE: This configuration file assumes that repository names are unique across Git host providers.
If you do not want to make that assumption, you can create a new handler in settings.py
to do this.

7.  Configure the destination path for your repositories by editing the 'local_repo_dir'
variables in the PROVIDERS dictionary.  For example, if you wish to have Git repositories locally
cloned in '/home/builder/github', you would edit the line:

```
'local_repo_dir' : '/home/builder/github'
```

NOTES: It is recommended but not required that you specify a different
local_repo_dir for each Git provider.  You run the risk of conflicts if you
have the same repository name on different providers.

IMPORTANT: Be sure that the user that will be running the program has
permissions to create directories in each of the local repository directories.

8.  Run the main program:

```
python main.py
```

Your server should now be ready to receive WebHook requests.

9.  Configure your GitHub and/or Bitbucket repositories to send WebHook requests to your
URL.  For example, if your hostname is mydomain.com and runs on port 8888, the URL would be:

```
http://mydomain.com:8888/
```

You may want to run this process under initctl or supervisord, but that is beyond the scope
of this document.  Currently reverse proxies such as nginx are not supported, but this could
be made to work (see https://dustri.org/b/?p=579).

Stan Hu
stanhu at gmail.com