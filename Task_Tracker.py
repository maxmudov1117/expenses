import json
from datetime import datetime

import os

filename = "task.json"
usersname = "users.json"

def register(username,password):
    with open(usersname, 'r') as file:
        users = json.load(file)
        user = {
            'username' : username,
            'password' : password
        }
        users.append(user)
        with open(usersname,'w') as f:
            json.dump(users, f, ensure_ascii=False,indent=4)


def load_task(username, status = 'all'):
    with open(filename, 'r', encoding="utf-8") as file:
        tasks = json.load(file)
        filter = []
        for task in tasks:
            if 'username' in task and task['username'] == username:
                filter.append(task)
        tasks = filter

        if status != 'all':
            result = []
            for task in tasks:
                if task['status'] == status:
                    result.append(task)
            tasks = result
    return tasks


def get_next_id(tasks):
    if not tasks:
        return 1
    max_id = 0
    for task in tasks:
        if task['id'] > max_id:
            max_id = task['id']
    return max_id + 1

def load_all_tasks():
    with open(filename, 'r', encoding="utf-8") as file:
        try:
            all_tasks = json.load(file)
        except:
            all_tasks = []

def add(title, username):
    with open(filename, 'r', encoding="utf-8") as file:
        try:
            all_tasks = json.load(file)
        except:
            all_tasks = []
    new_task = {
        'id': get_next_id(all_tasks),
        'title': title,
        'status': 'todo',
        'created_at': str(datetime.now()),
        'username': username
    }
    all_tasks.append(new_task)

    with open(filename, 'w', encoding="utf-8") as file:
        json.dump(all_tasks, file, indent=4, ensure_ascii=False)


def delete(id):
    tasks = load_task(username)
    for task in tasks:
        if task['id'] == id:
            tasks.remove(task)
            break
    with open(filename, 'w') as file:
        json.dump(tasks,file,ensure_ascii=False,indent=4)

def update(id,inp, type = "title"):
    tasks = load_task(username)
    if type == "title":
        for task in tasks:
            if task['id'] == id:
                task['title'] = inp
                task['created_at'] = str(datetime.now())
    elif type == "status":
        for task in tasks:
            if task['id'] == id:
                task['status'] = inp
                task['created_at'] = str(datetime.now())


    with open(filename, 'w') as file:
        json.dump(tasks,file,ensure_ascii=False,indent=4)

def get_id(username):
    return len(load_task(username))

def check(username, password):
    with open(usersname, 'r') as file:
        tasks = json.load(file)
        for task in tasks:
            if task['username'] == username and task['password'] == password:
                return True
        return False




author = input(">>>")
if author == "register":
    username = input("username: ")
    password = input("password")
    register(username,password)
    print("User registrated successfully")

while True:
    username = input("Login (username): ")
    password = input("password")

    while check(username, password):
        text = input("task-cli ")
        if text == 'exit':
            print("Thank you for visiting!!!")
            break
        elif text.startswith('add '):
            title = text[4:].strip()
            add(title, username)
            print(f"Task added successfully (ID: {get_id(username)})")
        elif text.startswith('update'):
            soz = text.split()
            update(int(soz[1])," ".join(soz[2:]))
            print(f"Task updated successfully (ID: {int(soz[1])})")
        elif text.startswith('list'):
            if text == 'list':
                tasks = load_task(username)
            else:
                text = text.split(" ")
                status = text[1]
                tasks = load_task(username,status)
            for i, task in enumerate(tasks, start=1):
                print(f"{task['created_at']} |{task['status']:11} | {i}. {task['title']}")
        elif text.startswith("delete"):
            id = int(text.split()[1])
            delete(id)
            print(f"Task deleted successfully (ID: {id})")
        elif text.startswith("mark"):
            text = text.split()
            id = int(text[1])
            status = text[2]
            update(id,status, type = "status")
            print(f"Task marked successfully (ID: {id})")
    if text == "exit":
        break











