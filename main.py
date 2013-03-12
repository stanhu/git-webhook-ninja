#!/usr/bin/env python

from flask import Flask, request
from webhook_handler import WebHookData, post_receive_handler

import ipaddr
import json
import logging
import settings

app = Flask(__name__)
logger = logging.getLogger(__name__)

def parse_github_data(data):
    """
    Parses GitHub JSON WebHook data.  See:

    https://help.github.com/articles/post-receive-hooks
    """
    assert('before' in data)
    assert('after' in data)
    assert('repository' in data)
    assert('ref' in data)
    webhook_data = WebHookData('github')
    repo_data = data['repository']
    webhook_data.before = data['before']
    webhook_data.after = data['after']
    webhook_data.repo_name = data['repository']['name']
    ref = data['ref']
    webhook_data.ref_name = ref
    webhook_data.branch_name = ref.replace('refs/heads/', '')
    webhook_data.repo_url = "%s:%s/%s.git" % \
        (settings.PROVIDERS['github']['ssh_account'],
         repo_data['owner']['name'], repo_data['name'])

    return [webhook_data]

def parse_bitbucket_data(data):
    """
    Parses BitBucket JSON WebHook data.  See:

    https://confluence.atlassian.com/display/BITBUCKET/POST+Service+Management
    """
    assert('canon_url' in data)
    assert('commits' in data)
    assert('repository' in data)
    data_by_branch = {}

    for commit in data['commits']:
        webhook_data = data_by_branch.setdefault(commit['branch'],
                                                 WebHookData('bitbucket'))
        repo_data = data['repository']
        webhook_data.repo_name = repo_data['slug']
        webhook_data.repo_url = "%s:%s/%s.git" % \
            (settings.PROVIDERS['bitbucket']['ssh_account'],
             repo_data['owner'], repo_data['slug'])
        webhook_data.ref_name = 'refs/heads/%s' % commit['branch']
        webhook_data.branch_name = commit['branch']
        if webhook_data.before is None:
            webhook_data.before = commit['raw_node'] + "^1"
        webhook_data.after = commit['raw_node']

    return data_by_branch.values()

def parse_data(data):
    """
    Parse a JSON data payload and determine whether it is a GitHub or a
    BitBucket Webhook request.
    """
    if 'commits' not in data:
        return []

    # First, determine whether this is a GitHub data request.
    if 'before' in data and 'after' in data and 'repository' in data \
            and 'ref' in data:
        logger.debug("GitHub data detected!")
        return parse_github_data(data)
    elif 'canon_url' in data and 'repository' in data:
        logger.debug("BitBucket data detected!")
        return parse_bitbucket_data(data)
    else:
        return []

def handle_data(data):
    """
    Automatically parse the JSON data received and dispatch the requests
    to the appropriate handlers specified in settings.py.
    """
    webhook_data_list = parse_data(data)
    logger.debug("raw data %s" % webhook_data_list)

    for webhook_data in webhook_data_list:
        provider_info = settings.PROVIDERS.get(webhook_data.provider, None)

        if provider_info:
            post_receive_handler(provider_info, webhook_data)

def check_whitelist_ips(remote_addr):
    """
    Verify that the given IP address is on the whitelist of allowed providers.
    Returns True if the IP is allowed, False otherwise.
    """
    for _, provider_data in settings.PROVIDERS.iteritems():
        whitelist = provider_data.get('whitelist_ips', [])

        for ip_addr in whitelist:
            if remote_addr in ipaddr.IPNetwork(ip_addr):
                return True
    return False

@app.route("/", methods=['POST'])
def index():
    """
    Entry point from Web server"
    """
    if request.method == 'POST':
        valid_ip = check_whitelist_ips(ipaddr.IPAddress(request.remote_addr))

        if not valid_ip:
            logger.error("Received POST request from invalid IP: %s" %
                         request.remote_addr)
            return "ERROR"

        if request.json:
            # Most providers don't use JSON mime-types, but in case they do
            # handle it.
            logger.debug("Handling json")
            handle_data(request.json)
        elif 'payload' in request.form:
            logger.debug("Decoding payload: %s" % request.form['payload'])
            # BitBucket includes newlines in the message data; disable
            # strict checking
            json_data = json.loads(request.form['payload'], strict=False)
            handle_data(json_data)
        return "OK"
    return "OK"

if __name__ == "__main__":
    app.run(debug=settings.DEBUG, host=settings.LISTEN_IP,
            port=settings.LISTEN_PORT)
