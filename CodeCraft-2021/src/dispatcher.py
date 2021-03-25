from typing import List
import logging
import sys

from device import ServerType, VmType, Vm
from store import state, MyException


class Request:
    DEL = 0
    ADD = 1

    def __init__(self, request: str):
        self.action: int
        self.id_: int
        self.vm_type: VmType
        res = request[1: -2].split(',')
        if request[1] == 'a':
            # (add, vmUU5F0, 748984173)\n
            self.action = self.ADD
            self.id_ = int(res[2])
            self.vm_type = state.get_vm_type(res[1])
        elif request[1] == 'd':
            # (del, 617495014)\n
            self.action = self.DEL
            self.id_ = int(res[1])
        else:
            raise NotImplementedError

    def get_vm_model(self):
        t: VmType = self.vm_type
        return t.vm_model


class Dispatcher:
    """
    调度器
    """
    def __init__(self):
        pass

    def handle_requests(self, del_requests: List[Request], add_request: List[Request]):
        """
        TODO 暂时选择内存和核心数最大的服务器，进行虚拟机部署
        :param add_request:
        :type del_requests: object
        :return:
        """
        # TODO 对于一批请求，需要进行采购，分配

        # # 销毁虚拟机
        for r in del_requests:
            # TODO free the resources
            pass

        # 对虚拟机按照内存从小到大排序，并计划需要购买的机器
        add_request.sort(key=Request.get_vm_model)
        planed_server = {}
        server_count = 0
        top_server_type = state.get_top_memory_server_type()
        for r in add_request:
            vm = Vm(r.vm_type, r.id_)
            try:
                state.deploy_vm(vm)
            except MyException:
                # 采购服务器
                server_type = top_server_type
                if server_type.can_deploy_vm(vm.type_):
                    server = state.plan_server(server_type)
                else:
                    server_type = state.find_server_type_for_vm(vm.type_)
                    server = state.plan_server(server_type)
                server_list = planed_server.get(server_type.server_model, [])
                server_count += 1
                server_list.append(server)
                planed_server[server_type.server_model] = server_list
                state.deploy_vm(vm, server)

        # # 扩容
        # TODO 统计purchased_server, 输出
        sys.stdout.write(f'(purchase, {server_count})')
        for server_model, server_list in planed_server.items():
            # 购买若干台
            sys.stdout.write(f'({server_model}, {len(server_list)})\n')
            state.install_server(server_list)

        # # 迁移虚拟机
        sys.stdout.write(f'(migration, 0)\n')

        # # 部署虚拟机
        # 先放大的，再放小的
        logging.debug(add_request)

    def del_vm(self, id_: int):
        # TODO
        pass

    def add_vm(self, type_: VmType, id_: int):
        # TODO
        pass
