#!/usr/bin/env python

import logging
import os
import sh

logger = logging.getLogger(__name__)

class WebHookData():
    def __init__(self, provider):
        self.provider = provider
        self.before = None
        self.after = None
        self.repo_name = None
        self.ref_name = None
        self.branch_name = None
        self.repo_url = None

    def get_provider(self):
        return self.provider

    def get_repository_name(self):
        return self.repo_name

    def get_before_sha(self):
        return self.before

    def get_after_sha(self):
        return self.after

    def get_ref(self):
        return self.ref_name

    def is_tag(self):
        return (self.ref_name.find('refs/tags/') == 0)

def git_clone_to_local(dest_directory, webhook_data):
    git = sh.git.bake()
    logger.debug('Making destination directory %s' % dest_directory)
    print ('Making destination directory %s' % dest_directory)
    sh.mkdir('-p', dest_directory)
    sh.cd(dest_directory)
    logger.debug("checking for repo_name %s in %s" % (webhook_data.repo_name, sh.pwd()))
    if not os.path.exists(webhook_data.repo_name):
        logger.debug("Cloning new repository")
        print(git.clone(webhook_data.repo_url, webhook_data.repo_name))
    sh.cd(webhook_data.repo_name)
    print(git.fetch('--all'))

    try:
        git('show-ref', '--heads', webhook_data.branch_name)
        branch_exists = True
    except:
        branch_exists = False

    if branch_exists is False and not webhook_data.is_tag():
        print(git.checkout('-b', webhook_data.branch_name,
                           'origin/%s' % webhook_data.branch_name))
    elif branch_exists:
        git.checkout(webhook_data.branch_name)

    print(git.pull())
    print webhook_data.before, webhook_data.after

def post_receive_handler(provider_info, webhook_data):
    local_dir = provider_info.get('local_repo_dir', None)

    if local_dir:
        git_clone_to_local(local_dir, webhook_data)

        handler = provider_info.get('post_receive_handler', None)
        if handler:
            handler(webhook_data)
