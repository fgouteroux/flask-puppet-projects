# -*- coding: utf-8 -*-
'''
Flask controller
'''

from __future__ import absolute_import

import os
import json

from flask_oauthlib.client import OAuth

from gitlaber import config

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def _raise_error_from_response(response):
    """
    Tries to parse error message from response and raises error.
    """
    try:
        message = response.data['message']
    except (KeyError, ValueError):
        message = response.raw_data
    raise StandardError(message)


def find_element_in_list(list_element, search_element, match_element):
    """Return the position of an element in a dictionnary list

    :param list_element: the dictionnary list
    :param search_element: the value of searched element
    :param match_element: the searched key
    :return: the position of searched element
    """

    try:
        for element in list_element:
            if getattr(element, match_element, None) == search_element:
                return list_element.index(element)
    except ValueError:
        pass


class Gitlab(object):
    """Gitlab class"""

    def __init__(self, session):
        """setup the token used for all the api calls and all the urls for the current session

        :param session: session
        """
        def get_gitlab_token():
            """Return session token"""
            return session.get('access_token')

        self.oauth = OAuth()
        self.auth = self.oauth.remote_app(
            'gitlab',
            consumer_key=config.GITLAB_APP_ID,
            consumer_secret=config.GITLAB_APP_SECRET,
            base_url=config.GITLAB_URL,
            access_token_url='{0}/oauth/token'.format(config.GITLAB_URL),
            authorize_url='{0}/oauth/authorize'.format(config.GITLAB_URL),
            content_type='application/json'
        )
        self.auth.tokengetter(get_gitlab_token)
        self._url = '{0}/api/v3'.format(self.auth.base_url)


    @staticmethod
    def getall(method, *args, **kwargs):
        """Auto-iterate over the paginated results of various methods of the API.
        Pass the GitLabAPI method as the first argument, followed by the
        other parameters as normal. Include `page` to determine first page to poll.
        Remaining kwargs are passed on to the called method, including `per_page`.

        :param method: Actual method to call
        :param *args: Positional arguments to actual method
        :param rpath: Relative resource path, like '/users'
        :param page: Page number to start at
        :param **kwargs: Keyword arguments to actual method
        :return: Yields each item in the result until exhausted, and then
        implicit StopIteration; or no elements if error
        """
        rpath = kwargs.pop('rpath', '')
        page = kwargs.pop('page', '')
        if not all([page, rpath]):
            raise RuntimeError('Missing rpath or page arguments')
        while True:
            results = method(*args, rpath=rpath, page=page, **kwargs)
            if not results:
                break
            for result in results:
                yield result
            page += 1


    def get(self, path):
        """Send get request (with auth)"""
        url = '%s%s' % (self._url, path)
        try:
            request = self.auth.get(url)
        except Exception:
            raise StandardError(
                "Failed to get a response from: %s" % url)

        if request.status == 200:
            return request.data
        else:
            _raise_error_from_response(request)


    def post(self, path, params=None):
        """Send post request (with auth)"""
        url = '%s%s' % (self._url, path)
        try:
            if params:
                request = self.auth.post(url, params)
            else:
                request = self.auth.post(url)
        except Exception:
            raise StandardError(
                "Failed to post data at: %s" % url)

        if request.status == 201:
            return request.data
        else:
            _raise_error_from_response(request)


    def put(self, path, params):
        """Send put request (with auth)"""
        url = '%s%s' % (self._url, path)
        try:
            request = self.auth.put(url, params)
        except Exception:
            raise StandardError(
                "Failed to update data at: %s" % url)

        if request.status == 200:
            return request.data
        else:
            _raise_error_from_response(request)


    def delete(self, path):
        """Send delete request (with auth)"""
        url = '%s%s' % (self._url, path)
        try:
            request = self.auth.delete(url)
        except Exception:
            raise StandardError(
                "Failed to delete data from: %s" % url)

        if request.status == 200:
            return request.data
        else:
            _raise_error_from_response(request)


    def get_paginated_resources(self, rpath, page=1, per_page=20):
        """Return a dictionary list for a given resource

        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        :return: returs a dictionary of the given resource searched, false if there is an error
        """
        try:
            url = '%s%s' % (self._url, rpath)
            params = {'page': page, 'per_page': per_page}

            request = self.auth.get(url, params)
        except Exception:
            raise StandardError(
                "Failed to get a response from: %s" % url)

        if request.status == 200:
            return request.data
        else:
            _raise_error_from_response(request)


    def get_all_users(self):
        """Return a user list"""
        users = [x for x in self.getall(self.get_paginated_resources,
                                        rpath='/users',
                                        page=1,
                                        per_page=20)
                ]
        return sorted(users, key=lambda k: k['name'])


    def get_all_groups(self):
        """Return a group list"""
        users = [x for x in self.getall(self.get_paginated_resources,
                                        rpath='/groups',
                                        page=1,
                                        per_page=20)
                ]
        return sorted(users, key=lambda k: k['name'])


    def get_all_projects(self):
        """Returns a dictionary list of all the projects

        :return: list with the repo name, description, last activity,web url...
        """
        users = [x for x in self.getall(self.get_paginated_resources,
                                        rpath='/projects/all',
                                        page=1,
                                        per_page=20)
                ]
        return sorted(users, key=lambda k: k['name'])


    def get_project_with_namespace(self, path_with_namespace):
        """Retrieve project information

        :param path_with_namespace: mygroup/myproject
        """
        try:
            for project in self.get_all_projects():
                if project['path_with_namespace'] == path_with_namespace:
                    return project
        except ValueError:
            pass


    def get_project_branches(self, path_with_namespace):
        """List all the branches from a project

        :param path_with_namespace: mygroup/myproject
        :return: list of project branches
        """
        try:
            project_id = self.get_project_with_namespace(path_with_namespace)['id']
            project_branches = []
            branches = self.get('/projects/{0}/repository/branches'.format(project_id))
            for branch in branches:
                project_branches.append(branch['name'])
            return project_branches
        except ValueError:
            pass


    def get_projects_in_group(self, group):
        """Returns a dictionary list of all the projects for a group name

        :param group: group name
        :return: list with the repo name, description, last activity,web url...
        """
        result = list()
        for project in self.get_all_projects():
            if project['namespace']['name'] == group:
                result.append(project)
        return result


    def get_group_with_name(self, name):
        """Retrieve group information

        :param name: group name
        """
        try:
            for group in self.get_all_groups():
                if name == group['name']:
                    return group
        except ValueError:
            pass


    def get_member_group(self, group_name, username):
        """Lists the members of a given group name

        :param group_name: the group_name id
        :return: the group's members
        """
        try:
            group_id = self.get_group_with_name(group_name)['id']
            group_members = self.get('/groups/{0}/members'.format(group_id))
            for member in group_members:
                if username == member['username']:
                    return member
        except ValueError:
            pass


    def manage_project(self, user, name, group, access, action, import_url, del_user_project):
        """
        Manage projects
        """
        username = str(user.split(",")[0])
        user_id = int(user.split(",")[1])
        result = list()
        path = group + "/" + name
        project = self.get_project_with_namespace(path)

        if action == "create":

            if project == None:

                pgroup = self.get_group_with_name(group)
                member = self.get_member_group(group, username)

                if import_url:

                    # Create Project
                    op_project = "Create new project {0} in {1}".format(name, group)
                    new_project_url = '/projects'
                    new_project_data = {
                        "name":name,
                        "namespace_id":pgroup['id'],
                        "import_url":import_url
                        }
                    new_project = self.post(new_project_url, new_project_data)
                    result.append({op_project: new_project})

                    if member == None:
                        # Add member permissions
                        op_member = "Add member {0} on project {1}".format(username, name)
                        op_member_url = '/projects/{0}/members'.format(new_project['id'])
                        op_member_data = {
                            "id":new_project['id'],
                            "user_id":user_id,
                            "access_level":access
                            }
                        member = self.post(op_member_url, op_member_data)
                        result.append({op_member: member})

                    # Beacuse we import project from an url, we cannot fork directly.
                    # Create User Project
                    op_user_project = "Create new project {0} for {1}".format(name, username)
                    new_user_project_url = '/projects?sudo={0}'.format(username)
                    new_user_project_data = {
                        "name":name,
                        "import_url":import_url
                        }
                    new_user_project = self.post(new_user_project_url, new_user_project_data)
                    result.append({op_user_project: new_user_project})

                    # Create fork relation
                    op_fork = "Create fork relation from project \
                              {0} in namespace {1}".format(name, username)
                    fork_url = '/projects/{0}/fork/{1}'.format(new_user_project['id'],
                                                               new_project['id']
                                                              )
                    fork = self.post(fork_url)
                    result.append({op_fork: fork})

                else:
                    # Create Project
                    op_project = "Create new project {0} in {1}".format(name, group)
                    new_project_url = '/projects'
                    new_project_data = {
                        "name":name,
                        "namespace_id":pgroup['id']
                        }
                    new_project = self.post(new_project_url, new_project_data)
                    result.append({op_project: new_project})

                    if member == None:
                        # Need member permissions on project target
                        # before fork it under user namespace
                        op_member = "Add member {0} on project {1}".format(username, name)
                        op_member_url = '/projects/{0}/members'.format(new_project['id'])
                        op_member_data = {
                            "id":new_project['id'],
                            "user_id":user_id,
                            "access_level":access
                            }
                        member = self.post(op_member_url, op_member_data)
                        result.append({op_member: member})

                    op_fork = "Fork project {0} in namespace {1}".format(name, username)
                    fork_url = '/projects/fork/{0}?sudo={1}'.format(new_project['id'], username)
                    fork = self.post(fork_url)
                    result.append({op_fork: fork})

            else:
                result.append({"Error": "Project {0} already exists".format(path)})

        elif action == "delete":

            op_project = "Delete project {0} in {1}".format(name, group)

            if project:
                result.append({op_project: self.delete('/projects/{0}'.format(project['id']))})
            else:
                result.append({"Error": "Project {0} not found".format(path)})

            if del_user_project:
                path = username + "/" + name
                current_user_project = self.get_project_with_namespace(path)

                if current_user_project:
                    op_user_project = "Delete project {0} in {1}".format(name, username)
                    user_project = self.delete('/projects/{0}'.format(current_user_project['id']))
                    result.append({op_user_project: user_project})
                else:
                    result.append({"Error": "Project {0} not found".format(path)})

        return result

    def manage_user_env(self, user, projects, env_action):
        """
        Manage user env
        """

        username = str(user.split(",")[0])
        user_id = int(user.split(",")[1])
        result = list()
        projects = json.loads(projects)

        for project in projects:
            path = project['group'] + "/" + project['name']
            current_project = self.get_project_with_namespace(path)

            if current_project:

                member = self.get_member_group(project['group'], username)

                op_branch = "{0} branch {1} in project {2}".format(env_action,
                                                                   username,
                                                                   project['name']
                                                                  )
                op_member = "{0} member {1} on project {2}".format(env_action,
                                                                   username,
                                                                   project['name']
                                                                  )

                if env_action == "create":

                    branch_url = '/projects/{0}/repository/branches'.format(current_project['id'])
                    current_project_branches = self.get(branch_url)
                    index_branch = find_element_in_list(current_project_branches, username, "name")
                    print index_branch

                    if project['branch'] and index_branch == None:

                        branch_data = {
                            "id":current_project['id'],
                            "branch_name":username,
                            "ref":project['branch']
                            }
                        branch = self.post(branch_url, branch_data)
                        result.append({op_branch: branch})
                    else:
                        result.append({op_branch: "Nothing to do"})

                    if project['access']:

                        # Check if user is already in project's group
                        if member == None:

                            current_project_members = []
                            op_member_url = '/projects/{0}/members'.format(current_project['id'])
                            for member in self.get(op_member_url):
                                current_project_members.append(member['id'])

                            if not user_id in current_project_members:
                                op_member_data = {
                                    "id":current_project['id'],
                                    "user_id":user_id,
                                    "access_level":project['access']
                                    }
                                member = self.post(op_member_url, op_member_data)
                                result.append({op_member: member})

                    else:
                        result.append({op_member: "Nothing to do"})

                elif env_action == "delete":

                    current_project_branches = []
                    branch_url = '/projects/{0}/repository/branches'.format(current_project['id'])
                    for branch in self.get(branch_url):
                        current_project_branches.append(branch['name'])

                    if username in current_project_branches:
                        branch = self.delete('{0}/{1}'.format(branch_url, username))
                        result.append({op_branch: branch})
                    else:
                        result.append({op_branch: "Nothing to do"})

                    member_url = '/projects/{0}/members'.format(current_project['id'])
                    current_project_members = self.get(member_url)
                    index_member = find_element_in_list(current_project_members, user_id, "id")

                    if index_member >= 0:
                        member = self.delete('{0}/{1}'.format(member_url,
                                                              current_project_members[index_member]
                                                             )
                                            )
                        result.append({op_member: member})

                    else:
                        result.append({op_member: "Nothing to do"})

            else:
                result.append({"Error": "Project {0} not found".format(path)})

        return result
