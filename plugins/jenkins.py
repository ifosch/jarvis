from slackbot.bot import respond_to
from slackbot_settings import *
import requests
from requests.auth import HTTPBasicAuth
import json
import re


class Jenkins():
    def __init__(self, url=None, username=None, password=None):
        if url is None:
            self.url = JENKINS_URL
        else:
            self.url = url
        if username is None:
            self.username = JENKINS_USER
        else:
            self.username = username
        if password is None:
            self.password = JENKINS_PASSWORD
        else:
            self.password = password
        response = requests.get(self._build_api_url(), auth=HTTPBasicAuth(self.username, self.password))
        self.data = json.loads(response.text)
        self.job_count = len(self.data['jobs'])

    def job_list(self):
        return [job['name'] for job in self.data['jobs']]

    def _build_api_url(self, path = None):
        if path is None:
            path = "{}/".format(self.url)
        return "{}{}".format(path, 'api/json')

    def _build_crumbIssuer_url(self):
        crumbIssuer_url = "{}/crumbIssuer/".format(self.url)
        return "{}".format(self._build_api_url(crumbIssuer_url))

    def _get_crumb(self):
        response = requests.get(self._build_crumbIssuer_url(), auth=HTTPBasicAuth(self.username, self.password))
        crumb_data = json.loads(response.text)
        return crumb_data['crumbRequestField'], crumb_data['crumb']

    def _get_job_data(self, job_name):
        for job in self.data['jobs']:
            if job['name'] == job_name:
                return job

    def _build_build_url(self, job_name):
        job = self._get_job_data(job_name)
        return "{}build".format(job['url'])

    def _build_buildWithParams_url(self, job_name):
        job = self._get_job_data(job_name)
        return "{}buildWithParameters".format(job['url'])

    def build(self, job_name, job_params=None):
        if job_params is None or job_params == {}:
            build_method=self._build_build_url
        else:
            build_method=self._build_buildWithParams_url
        auth = HTTPBasicAuth(self.username, self.password)
        crumb_data = self._get_crumb()
        headers = {crumb_data[0]: crumb_data[1]} #, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        url = build_method(job_name)
        response = requests.post(url, auth=auth, headers=headers, data=job_params)
        return response.text


@respond_to('^list$', re.IGNORECASE)
def list(message):
    J = Jenkins()
    reply = "I found {} jobs:\n".format(J.job_count)
    for job in J.job_list():
      reply += "{}\n".format(job)
    message.reply(reply)


@respond_to('build ([^ ]*)(.*)', re.IGNORECASE)
def build(message, job, args):
    J = Jenkins()
    params = {key: value for (key, value) in [param.split('=') for param in args.split()]}
    reply = J.build(job, params)
    if reply == '':
        message.react('ok_hand')
    else:
        message.reply("{}".format(reply))
