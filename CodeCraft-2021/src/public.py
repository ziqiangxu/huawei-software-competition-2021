import sys


def log(msg):
    """
    日志只能输出到标准错误流中
    使用logging模块，提交到线上的时候关闭日志输出
    :param msg:
    :return:
    """
    sys.stderr.write(f'{msg}\n')


# class MyException(Exception):
#     # 过多的异常耗时较长
#     def __init__(self, msg: str):
#         super().__init__(msg)
