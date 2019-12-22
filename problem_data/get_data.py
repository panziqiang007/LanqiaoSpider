# coding:utf-8
import os
import re
import traceback

import mongo
from config import USERS
from const import *
from utils import driver_util
from utils.InSite import *

# judge_status_url = "http://lx.lanqiao.cn/status.page"
wait_time = 10
# http://lx.lanqiao.cn/status.page?sename=&seprname=(query)
base_search_url = "http://lx.lanqiao.cn/status.page?sename=&seprname="


class GetData:
    def __init__(self, driver, path,user):
        self.driver = driver
        self.path = path
        self.user = user

    def get_problem_data(self, problem):
        driver = self.driver
        title = problem[PROBLEM.TITLE]
        user = self.user
        driver.get(base_search_url + title)
        try:
            try:
                detail_link = WebDriverWait(driver, wait_time).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         "#status-list > tr:nth-child(1) > td:nth-child(11) > a"))
                )
                detail_link.click()
            except TimeoutException:
                # print('''not find submit detail,that mean you don't try this problem''')
                self.submit_problem(problem[PROBLEM.HREF])
                self.get_problem_data(problem)
                return
            ## 下载按钮s
            ## 判断页面是否存在, even can search submisson info,but still juding.
            try:
                WebDriverWait(driver, wait_time).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         "#detailcases > table > tbody > tr:nth-child(2) > td:nth-child(6) > a:nth-child(1)"))
                )
            except TimeoutException:
                print('''not find submit detail,that mean this submission still judging''')
                # try again
                self.get_problem_data(problem)
                return

            buttons = driver.find_elements(By.CSS_SELECTOR, "#detailcases > table > tbody > tr > td > a")
            try:
                file_dict = {}
                for root, dirs, files in os.walk(self.path):
                    for file in files:
                        file_dict[file] = True
                input_dict = {
                    "输入": 'input',
                    "输出": 'output'
                }
                click_cnt = 0
                for btn in buttons:
                    lick_text = btn.get_attribute('onclick')
                    lick_num = re.search(r'\d+', lick_text).group(0)
                    lick_name = btn.text
                    # print(lick_name + lick_num)
                    file_name = input_dict[lick_name] + lick_num + ".txt";
                    if file_dict.get(file_name, False):
                        print(file_name + ":exist")
                    else:
                        print(file_name + ": not exist,downloading...")
                        btn.click()
                        click_cnt += 1
                        self.user.tryCnt -= 1
                        if self.user.tryCnt == 0:
                            print("user {} tryCnt run out".format(self.user.name))
                            break
                        time.sleep(1)
                # checking if total file equals  problem data
                if click_cnt == buttons.__len__:
                    problem[PROBLEM.STATE] = STATE_VALUE.DATA_SUCCESS
                else:
                    print("----------get problem data unknown error--------")
                    print("get file {}, not enough for {}".format(click_cnt, buttons.__len__))
                    problem[PROBLEM.STATE] = STATE_VALUE.DATA_ERROR
                print("-----get problem data success-----")
            except Exception as e:
                traceback.print_exc()
                # gain data error
                problem[PROBLEM.STATE] = STATE_VALUE.DATA_ERROR
                user.canTry = False
                print("-----click error by lanqiao server, get problem data error-----")
            mongo.save_problem(problem)
            # close driver at here
            driver.close()
            return
        except TimeoutException:
            problem[PROBLEM.STATE] = STATE_VALUE.DATA_ERROR
            print("get problem data error")
            mongo.save_problem(problem)

    def submit_problem(self, href):
        driver = self.driver
        #         http://lx.lanqiao.cn/submit.page?gpid=T71
        #         http://lx.lanqiao.cn/problem.page?gpid=T71
        href = href.replace("problem", "submit")
        # print(href)
        driver.get(base_practice_url + href)
        try:
            submit_btn = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     "body > div.bodydiv > div.submitform > div.subrow > input"))
            )
            submit_btn.click()
        except TimeoutException:
            print('''submit problem error''')


def check_problem_set():
    for problem_set in mongo.problem_set_table.find():
        name = problem_set[PROBLEM_SET.NAME]
        total = problem_set[PROBLEM_SET.TOTAL]
        begin_prefix = tag_dict[name]
        id_reg = {"$regex": "^" + begin_prefix}
        success_query = {PROBLEM.ID: id_reg, PROBLEM.STATE: STATE_VALUE.DATA_SUCCESS}
        print(success_query)
        query_cnt = mongo.problem_table.count_documents(success_query)
        if int(total) == query_cnt:
            print(name + "total=" + str(total) + ": OK")
        else:
            print("problem_data: " + str(query_cnt) + " not enough for " + str(total))
            query = {PROBLEM.ID: id_reg, PROBLEM.STATE: STATE_VALUE.HTML_SUCCESS}
            print(query)
            find_problem = mongo.problem_table.find_one(query)
            if find_problem:
                return find_problem
            query = {PROBLEM.ID: id_reg, PROBLEM.STATE: STATE_VALUE.DATA_ERROR}
            find_problem = mongo.problem_table.find_one(query)
            if find_problem:
                return find_problem
            else:
                print("all ok !!!!!!")
                return


def spider(base_save_path, user):
    # 获取爬取的题目
    problem = check_problem_set()
    print(problem)
    if not problem:
        print("ALL ok !!!!")
        return
    title = problem[PROBLEM.TITLE]
    path = base_save_path + '\\' + title
    driver = driver_util.get_driver_with_download_path(path)
    InSite(driver=driver, username=user.username, password=user.password).in_practice_set_site()
    GetData(driver=driver, path=path,user = user).get_problem_data(problem=problem)
    # 休息一下，时间太短爬取会被封掉下载文件资格，
    '''
        下载一个半就GG了，第二天（24小时之后，才能下载）
        所以一个账号每天只能爬取一道题
    '''
    # try again
    if user.tryCnt != 0 and user.canTry:
        spider(base_save_path, user)
    try:
        # print("close in 132")
        driver.quit()
    except Exception:
        print("close driver exception 136")


def main():
    base_save_path = r'E:\problem_data'
    for user in USERS:
        # if user.real_name == "李明忠":
        #     continue
        print(user.real_name + ": begin--------------")
        spider(user=user, base_save_path=base_save_path)
        print(user.real_name + ": over------------")


if __name__ == "__main__":
    '''
        empty
    '''
    main()
