# -*- coding:utf-8 -*-
import re

import pymongo
# from config import *
from config import MONGO
from const import *

client = pymongo.MongoClient(MONGO.URL)
# dblist = client.list_database_names()
# if MONGO.DB in dblist:
#     print("数据库已存在！")

db = client[MONGO.DB]

problem_table = db[MONGO.TABLE.PROBLEM]
problem_set_table = db[MONGO.TABLE.PROBLEM_SET]
test_table = db[MONGO.TABLE.TEST]
problem_data_table = db[MONGO.TABLE.PROBLEM_DATA]


def sava_problem_data(problem_data):
    try:
        if problem_data_table.find_one({"name": problem_data['name']}):
            new_problem_set = {"$set", problem_data}
            if problem_data_table.updata_one({"name": problem_data['name']}, new_problem_set):
                print('update to mongoDB successfully', problem_data)
        else:
            if problem_data_table.insert_one(problem_data):
                print('save to mongoDB successfully', problem_data)
    except Exception:
        print('save to mongoDB error', problem_data)


def save_problem_set(problem_set):
    try:
        if problem_set_table.find_one({"name": problem_set['name']}):
            new_problem_set = {"$set", problem_set}
            if problem_set_table.updata_one({"name": problem_set['name']}, new_problem_set):
                print('update to mongoDB successfully', problem_set)
        else:
            if problem_set_table.insert_one(problem_set):
                print('save to mongoDB successfully', problem_set)
    except Exception:
        print('save to mongoDB error', problem_set)


def update_problem_with_new_filed(problem):
    try:
        query = {PROBLEM.ID: problem[PROBLEM.ID]}
        if problem_table.delete_one(query):
            if problem_table.insert_one(problem):
                print('update to mongoDB successfully', problem)
    except Exception:
        print('save to mongoDB error', problem)


def save_problem(problem):
    try:
        if problem_table.find_one({"id": problem['id']}):
            try:
                new_problem = {"$set", problem}
                if problem_table.update_one({"id": problem['id']}, new_problem):
                    print('update to mongoDB successfully', problem)
            except Exception:
                # 更新插入更多字段会出错
                query = {PROBLEM.ID: problem[PROBLEM.ID]}
                if problem_table.delete_one(query):
                    if problem_table.insert_one(problem):
                        print('update to mongoDB successfully', problem)
        else:
            if problem_table.insert_one(problem):
                print('save to mongoDB successfully', problem)
    except Exception:
        print('save to mongoDB error', problem)


def __update_all_problem_state__():
    query = {PROBLEM.STATE: STATE_VALUE.HTML_ERROR}
    new_problem = {"$set": {PROBLEM.STATE: STATE_VALUE.HTML_SUCCESS}}
    if problem_table.update_many(query, new_problem):
        print('update to mongoDB successfully', new_problem)


if __name__ == "__main__":
    ""
    # query = {PROBLEM.TIME_LIMIT: None}
    # print(query)
    # problems = problem_table.find(query)
    # print(problems)
    # for problem in problems:
    #     print(problem)
    #     problem[PROBLEM.TIME_LIMIT] = 1.0
    #     problem[PROBLEM.MEMORY_LIMIT] = 256.0
    #     problem_table.find_one_and_update({PROBLEM.ID: problem[PROBLEM.ID]}, {"$set": problem})
