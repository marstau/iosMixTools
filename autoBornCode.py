#! /usr/bin/python
# -*- coding: UTF-8 -*-
import os,sys
import random
import logging
import string
import re
from hashlib import md5
import time
import json
import shutil
import hashlib 
import time
import argparse
import sys
import os
import logging
import hashlib
import fnmatch
from optparse import OptionParser
import shutil
import re
import platform
from enum import Enum
import zipfile

script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]

logging.basicConfig(level=logging.DEBUG,#控制台打印的日志级别
                    filename='info.log',
                    filemode='w',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    #a是追加模式，默认如果不写的话，就是追加模式
                    format=
                    '%(asctime)s - %(levelname)s: %(message)s' #日志格式
                    )

_FILE_SLIM = (100*1024*1024) # 100MB

WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

resource_path = ""
target_path = os.path.join(script_path, "target_resource")

#匹配规则，路径包含path_include且不包含path_exclude的才会创建对应类型的文件
match_rule = {
    ".png": {
        "path_include": os.path.sep + "res",
    },
    ".lua": {
        # "path_include": "src",
        "path_exclude": os.path.sep + "res",
    },
}
#确保添加的函数不重名
funcname_set = set()

#单词列表，用以随机名称
with open(os.path.join(script_path, "./word_list.json"), "r") as fileObj:
    word_name_list = json.load(fileObj)

#获取一个随机名称
def getOneName():
    global word_name_list
    return random.choice(word_name_list)

# 获取lua垃圾方法
def getLuaFuncText():
    global funcname_set
    new_func_name = getOneName()
    while new_func_name in funcname_set:
        new_func_name = getOneName()
    funcname_set.add(new_func_name)

    argv_name = getOneName()
    text = [
        '\nlocal function '+new_func_name+'()\n',
        '\tlocal %s = %d + %d\n' %(argv_name, random.randint(1, 1000), random.randint(1, 1000)),
        '\treturn %s\n' %(argv_name),
        'end\n'
    ]
    return ''.join(text)

#获取png内容
def getPngText():
    text = str(random.randint(1, 100)) * random.randint(1024, 10240)
    text = text + "0000000049454e44ae426082".decode('hex')
    return text

#添加单个文件
def addSingleFile(file_path):
    global logging
    global target_path
    logging.info("add file " + file_path.replace(target_path, ""))
    _, file_type = os.path.splitext(file_path)
    if file_type == ".lua":
        with open(file_path, "w") as fileObj:
            func_num = random.randint(2, 5)
            for j in range(0, func_num):
                func_text = getLuaFuncText()
                fileObj.write(func_text)
            fileObj.close()
    elif file_type == ".png":
        with open(file_path, "wb") as fileObj:
            fileObj.write(getPngText())
            fileObj.close()
    
def addFileTo(parent_folder, level, min_file_num = 0):
    global logging
    global match_rule, target_path
    create_folder_list = []
    for parent, folders, files in os.walk(parent_folder):
        target_file_type = ""
        relative_path = parent.replace(target_path, "")
        for file_type, match_config in match_rule.items():

            if "path_exclude" in match_config and relative_path.find(match_config["path_exclude"]) != -1:
                continue
            if not "path_include" in match_config or relative_path.find(match_config["path_include"]) != -1:
                target_file_type = file_type
                break
        if target_file_type == "":
            continue

        #创建文件数量
        new_file_num = random.randint(int(len(files) / 2), len(files)) + min_file_num
        for i in range(0, new_file_num):
            file_path = os.path.join(parent, getOneName() + target_file_type)
            addSingleFile(file_path)

        #防止创建太多层的文件夹
        if level > 2:
            continue
        #创建文件夹数量
        lenOfFolders = len(folders)
        new_fold_num = random.randint(int(lenOfFolders / 2), lenOfFolders)

        # logging.info("len(folders)=" + str(len(folders)) + "," + str(type(lenOfFolders/2)) + ", new_fold_num=" + str(type(new_fold_num)))
        for i in range(0, new_fold_num):
            target_folder = os.path.join(parent, getOneName())
            #为了不阻断os.walk,延后创建文件夹
            create_folder_list.append(target_folder)

    for folder_path in create_folder_list:
        try:
            logging.info("create folder " + folder_path.replace(target_path, ""))
            os.mkdir(folder_path)
            addFileTo(folder_path, level + 1, random.randint(2, 5))
        except Exception as e:
            logging.info(e)
#----------------------------------------ended add file----------------------
def changeSingleFileMD5(file_path):
    global logging
    _, file_type = os.path.splitext(file_path)
    with open(file_path, "ab") as fileObj:
        if file_type == ".png":
            logging.info("file_path=" + file_path + ", len=" + str(len(string.ascii_letters)))
            text = "".join(random.sample(string.ascii_letters, 11))
            logging.info("file_path=" + file_path + ", text=" + text)
        elif file_type == ".jpg":
            text = "".join(random.sample(string.ascii_letters, 20))
        elif file_type == ".lua":
            text = "\n--#*" + "".join(random.sample(string.ascii_letters, 10)) + "*#--"
        else:
            text = " "*random.randint(1, 100)
        fileObj.write(text.encode())
        fileObj.close()

#改变文件md5
def changeFolderMD5(target_path):
    type_filter = set([".png", ".jpg", ".lua", ".json", ".plist", ".fnt"])
    for parent, folders, files in os.walk(target_path):
        for file in files:
            full_path = os.path.join(parent, file)
            _, file_type = os.path.splitext(full_path)
            if file_type in type_filter:
                changeSingleFileMD5(full_path)

#----------------------------------------------------main------------------------------------------------
        
# def parse_args():
#     global res_path
#     parser = argparse.ArgumentParser(description='资源变异工具')
#     parser.add_argument('--res', dest='res_dir', type=str, required=True, help='资源目录')
#     parser.add_argument('--target', dest='target_dir', type=str, required=False, default=target_path, help='资源导出目录')

#     args = parser.parse_args()
#     return args

class MapperType(Enum):
    array = 1
    map_md5 = 2
    map_relative_path = 3

def FileMd5(filename):
    global WINDOWS_LINE_ENDING
    global UNIX_LINE_ENDING
    calltimes = 0
    hmd5 = hashlib.md5()
    fp = open(filename,"rb")
    f_size = os.stat(filename).st_size
    if f_size>_FILE_SLIM:
        while(f_size>_FILE_SLIM):
            content = fp.read(_FILE_SLIM)
            hmd5.update(content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING))
            f_size/=_FILE_SLIM
            calltimes += 1   #delete
        if(f_size>0) and (f_size<=_FILE_SLIM):
            content = fp.read()
            hmd5.update(content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING))
    else:
        content = fp.read()
        hmd5.update(content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING))
    
    return hmd5.hexdigest()

def LoopDir(root_dir, includes, excludes, mapType=MapperType.map_md5):
    global logging
    mapper = {}
    mapperRelativePath = {}
    array = {}
    count = -1
    for root, dirs, files in os.walk(root_dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in excludes]
        for pat in includes:
            for f in fnmatch.filter(files, pat):
                filePath = os.path.join(root, f)

                md5 = FileMd5(filePath)
                mapper[str(md5)] = filePath
                mapperRelativePath[filePath.replace(root_dir, "")] = str(md5)
                array[count] = filePath
                count += 1
                logging.info(filePath + " [md5] - " + str(md5))
    if mapType == MapperType.array:
        return array
    elif mapType == MapperType.map_md5:
        return mapper
    elif mapType == MapperType.map_relative_path:
        return mapperRelativePath

def Process(directory):
    return LoopDir(directory, ["*.png", "*.jpg"], [])

def ResourceProcess(res_dir, target_dir):
    global resource_path, target_path
    resource_path = res_dir
    target_path = target_dir

    if not os.path.exists(resource_path):
        logging.info("res path not exists: " + resource_path)
        exit(0)
    if target_path != resource_path:
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.copytree(resource_path, target_path)
    
    addFileTo(target_path, 0)
    logging.info("\n\nstart modify file md5")
    changeFolderMD5(target_path)
    # mapper1 = Process(uFromPath)
    logging.info("finish!")

def switch(var, opts):
    return {
        'ResourceProcess': lambda opts: ResourceProcess(opts.res_dir, opts.target_dir),
    }[var](opts)

if __name__ == '__main__':
    import sys
    # TexturePacker check, TortoiseProc check, python version check.
    # txt check: UTF-8 without BOM
    if sys.version_info[:2] < (3, 0):
        raise RuntimeError('Large than Python 3.0 is required')
    parser = OptionParser() 
    parser.add_option("-m", "--method",
                      dest="method",
                      default="copy",
                      help="method name, Available parameters: ResourceProcess")

    parser.add_option("-r", "--res",
                      dest="res_dir",
                      default="./AliasResources",
                      help="资源目录")


    parser.add_option("-t", "--target",
                      dest="target_dir",
                      default="./Output",
                      help="资源导出目录")
    (opts, args) = parser.parse_args()

    switch(opts.method, opts)