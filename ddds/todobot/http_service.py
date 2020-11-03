# -*- coding: utf-8 -*-

import json

from flask import Flask, request
from jinja2 import Environment
from urllib.request import Request, urlopen
import todoist
from todoist.api import TodoistAPI
from tova_key import key as tovakey

app = Flask(__name__)
environment = Environment()

def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

def extract_projects(api):
    projects = []
    for project in api.state['projects']:
        projects.append((project['name'], project['id']))
    return projects
	
@app.route("/get_projects", methods=['POST'])
def get_projects(key=tovakey):
    api = TodoistAPI('cfe47f00114285b63c26f70ee05aafe093e8c839')
    api.sync()
    projects = []
    for project in api.state['projects']:
        projects.append(project['name'])
    projects = ', '.join([str(elem) for elem in projects]) 
    return query_response(value=projects, grammar_entry=None)
	
@app.route("/create_project", methods=['POST'])
def create_project(key=tovakey):
    api = TodoistAPI('cfe47f00114285b63c26f70ee05aafe093e8c839')
    api.sync()
    payload = request.get_json()
    project_to_add = payload["context"]["facts"]["project_to_add"]["value"]
    added_project = api.projects.add(project_to_add)
    api.commit()
    print("ADDED PROJECT:", added_project)
    return action_success_response()
	
@app.route("/create_task", methods=['POST'])
def create_task(key=tovakey):
    api = TodoistAPI('cfe47f00114285b63c26f70ee05aafe093e8c839')
    api.sync()
    payload = request.get_json()
    task_to_add = payload["context"]["facts"]["task_to_add"]["value"]
    if "project_to_add" in payload['context']['facts'].keys():
        target_project = payload["context"]["facts"]["project_to_add"]["grammar_entry"]
        print("TARGET PROJECT: ", target_project)
        projects = extract_projects(api)
        project_found = false
        for project in projects:
            if project[0].lower == target_project:
                project_found = true
                added_task = api.items.add(task_to_add, project_id=project[1])
        if project_found == false:
            added_project = api.projects.add(target_project)
            added_task = api.items.add(task_to_add, project_id=added_project['id'])
    else:
        added_task = api.items.add(task_to_add)
    print("ADDED TASK: ", added_task)
    api.commit()
    return action_success_response()

