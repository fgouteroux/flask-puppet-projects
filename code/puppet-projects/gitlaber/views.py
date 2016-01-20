# -*- coding: utf-8 -*-
'''
Flask views
'''
from __future__ import absolute_import

from functools import wraps
import json

from flask import Blueprint, render_template, request,\
                  make_response, jsonify, redirect,\
                  url_for, session

from gitlaber import controllers
from gitlaber import config

view = Blueprint("view", __name__)
gitlab = controllers.Gitlab(session)

def login_required(function):
    """Authentication checker"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        """Redirect to the login page if user is not logged"""
        if not session.get("access_token", False):
            return redirect(url_for('.user_sessions', next=request.url))
        return function(*args, **kwargs)
    return decorated_function


@view.route('/logout')
def logout():
    """Logout and remove session token"""
    session.pop('access_token', None)
    return redirect(url_for('.user_sessions'))


@view.route('/user_sessions')
def user_sessions():
    """Login page"""
    return render_template('user_sessions.html', gitlab_url=config.GITLAB_URL)


@view.route('/login')
def login():
    """
    Check token in session or call the authorize function
    """
    next_url = request.args.get("next", "/")
    if 'access_token' in session:
        redirect(url_for('.authorized', next=next_url))

    return gitlab.auth.authorize(callback=url_for('.authorized', _external=True, next=next_url))


@view.route('/user_sessions/authorized')
def authorized():
    """
    Check the session token with remote application token.
    Then, redirect to url requested if the user have the required rights.
    """
    resp = gitlab.auth.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    session['access_token'] = (resp['access_token'], '')
    user = gitlab.get('/user')
    if user['is_admin']:
        next_url = request.args.get("next", None)
        if next_url:
            return redirect(next_url)
        else:
            return "not logged"
    else:
        return make_response(jsonify({'error': 'Unauthorized access'}), 401)



@view.route('/', methods=['GET'])
@login_required
def index():
    """
    The main page
    """
    current_user = gitlab.get('/user')
    return render_template('index.html',
                           gitlab_url=config.GITLAB_URL,
                           current_user=current_user,
                           users=gitlab.get_all_users(),
                           projects=gitlab.get_all_projects(),
                           project_groups=gitlab.get_all_groups(),
                           projects_groups=gitlab.get_all_groups()
                          )


@view.route('/health', methods=['GET'])
def health():
    """
    Health page to ensure the app goodness
    """
    response = {
        "health": "Good doctor!"
    }
    return jsonify(response), 200


@view.route('/data', methods=['GET'])
@login_required
def data():
    """Jquery requests endpoint"""
    allowed_func = ["projects", "project_branches"]
    request_type = request.args.get("type", None)
    path = request.args.get("path", None)

    if request_type and request_type in allowed_func:

        if request_type == "projects":
            projects = gitlab.get_all_projects()
            myprojects = list()
            for project in projects:
                if project['namespace']['name'] == path:
                    myprojects.append(project['name'])

            return json.dumps(myprojects)

        elif request_type == "project_branches":
            project_branches = gitlab.get_project_branches(path)

            return json.dumps(project_branches)


@view.route('/result', methods=['POST'])
@login_required
def result():
    """Jquery response endpoint"""

    if request.method == "POST":

        if "user" in request.form and request.form["user"]:
            user = request.form["user"]

        if "project" in request.form and request.form["project"]:
            project_name = request.form["project"]
        else:
            project_name = ""

        if "project_group" in request.form and request.form["project_group"]:
            project_group = request.form["project_group"]

        if "project_access_level" in request.form and request.form["project_access_level"]:
            project_access_level = request.form["project_access_level"]

        if "import_url" in request.form and request.form["import_url"]:
            import_url = request.form["import_url"]

        if "project_action" in request.form and request.form["project_action"]:
            project_action = request.form["project_action"]
        else:
            project_action = ""

        if "del_user_project" in request.form and request.form["del_user_project"]:
            del_user_project = request.form["del_user_project"]
        else:
            del_user_project = ""

        if "projects" in request.form and request.form["projects"]:
            projects = request.form["projects"]
        else:
            projects = ""


        if "env_action" in request.form and request.form["env_action"]:
            env_action = request.form["env_action"]
        else:
            env_action = ""

        return render_template('result.html',
                               manage_project=gitlab.manage_project(user,
                                                                    project_name,
                                                                    project_group,
                                                                    project_access_level,
                                                                    project_action,
                                                                    import_url,
                                                                    del_user_project
                                                                   ),
                               manage_user_env=gitlab.manage_user_env(user, projects, env_action)
                              )
