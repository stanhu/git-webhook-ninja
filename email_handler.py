import git_commit_notifier_config
import os

def load_config(provider, repository_name):
    """
    Return a git-commit-notifier configuration file for the given
    repository.
    """
    return git_commit_notifier_config.REPO_CONFIG_MAP.get(repository_name,
                                                          None)

def git_commit_notifier_handler(webhook_data):
    """
    Default git-commit-notifer hook.
    """
    config_file = load_config(webhook_data.get_provider(),
                              webhook_data.get_repository_name())

    if config_file:
        os.system("echo %s %s %s | %s %s" %
                  (webhook_data.get_before_sha(),
                   webhook_data.get_after_sha(),
                   webhook_data.get_ref(),
                   GIT_COMMIT_NOTIFIER_BIN,
                   config_file))
    else:
        print('No config file found for repo %s' %
              webhook_data.get_repository_name())
