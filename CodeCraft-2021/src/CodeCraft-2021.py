import sys
# import logging
import time

from device import ServerType, VmType
from dispatcher import Dispatcher, Request
from store import state


def main():
    # to read standard input
    # process

    # #获取服务器类型
    server_type_num = int(sys.stdin.readline())
    # logging.info(f'Number of all server we can purchase: {server_type_num}')
    server_types = []
    for i in range(server_type_num):
        server_type = ServerType(sys.stdin.readline())
        server_types.append(server_type)
    state.server_types = server_types
    # logging.info(server_types)

    # #获取虚拟机类型
    vm_type_num = int(sys.stdin.readline())
    # logging.info(f'Number of all VM we are selling: {vm_type_num}')
    vm_types = []
    for i in range(vm_type_num):
        vm_types.append(VmType(sys.stdin.readline()))
    state.vm_types = vm_types
    # logging.info(vm_types)

    # #获取T天的用户请求
    dispatcher = Dispatcher()
    serve_days = int(sys.stdin.readline())
    for day in range(serve_days):
        request_num = int(sys.stdin.readline())
        requests = []
        for i in range(request_num):
            req = Request(sys.stdin.readline())
            requests.append(req)
        dispatcher.handle_requests(requests)
        # if day == 2:
        #     # 只处理部分的请求，进行测试
        #     break
    # logging.info(f'{request_count} requests has been handled')
    sys.stdout.flush()


def compute_cost(start):
    expense = state.total_server_expense()
    print(f'Total time cost: {time.time() - start}, '
          f'{expense[1]} servers installed and have cost: {expense[0] / 1000000000} Billion\n')


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.ERROR)
    start = time.time()

    main()

    compute_cost(start)
