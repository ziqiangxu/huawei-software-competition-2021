from typing import List
# import logging
import sys

from device import ServerType, VmType, Vm
from store import state


class Request:
    DEL = 0
    ADD = 1

    def __init__(self, request: str):
        self.action: int
        self.id_: int
        self._vm_type: VmType
        res = request[1: -2].split(',')
        if request[1] == 'a':
            # (add, vmUU5F0, 748984173)\n
            self.action = self.ADD
            self.id_ = int(res[2])
            self._vm_type = state.get_vm_type(res[1])
        elif request[1] == 'd':
            # (del, 617495014)\n
            self.action = self.DEL
            self.id_ = int(res[1])
        else:
            raise NotImplementedError

    @property
    def vm_type(self) -> VmType:
        return self._vm_type

    def get_vm_model(self):
        t: VmType = self.vm_type
        return t.vm_model


class Dispatcher:
    """
    调度器
    """
    def __init__(self):
        pass

    def handle_requests(self, requests: List[Request]):
        """
        TODO 暂时选择内存和核心数最大的服务器，进行虚拟机部署
        :param requests:
        :return:
        """
        # 对虚拟机按照内存从小到大排序，并计划需要购买的机器
        # TODO 不可随便排序，排序之后顺序就不对了
        # add_request.sort(key=Request.get_vm_model)

        planed_server = {}
        deploy_record = []
        for r in requests:
            if Request.DEL == r.action:
                state.del_vm(r.id_)
                continue
                
            vm = Vm(r.vm_type, r.id_)
            deploy_record.append(vm)

            node = state.add_vm(vm)

            # except MyException:
            if node == 'F':
                # 采购服务器
                server_type = state.find_server_type_for_vm(vm.type_)
                server = state.plan_server(server_type)
                server_list = planed_server.get(server_type.server_model, [])
                server_list.append(server)
                planed_server[server_type.server_model] = server_list
                # 新的服务器，一定可以部署这个虚拟机
                state.add_vm(vm, server)
                # node = state.deploy_vm(vm, server)
                # assert node != 'F'

        # #### 扩容

        # #### 对服务器进行整理，方便下次更快进行检索
        # state.sort_server_by_memory()

        # >>> 输出
        # 扩容
        sys.stdout.write(f'(purchase, {len(planed_server)})\n')
        for key_model, value_list in planed_server.items():
            # 购买若干台
            sys.stdout.write(f'({key_model}, {len(value_list)})\n')
            state.install_server(value_list)
        # 迁移虚拟机
        sys.stdout.write(f'(migration, 0)\n')
        # 部署
        for vm in deploy_record:
            if vm.type_.is_double:
                sys.stdout.write(f'({vm.server.id_})\n')
            else:
                sys.stdout.write(f'({vm.server.id_}, {vm.node})\n')
        # <<< 输出
        # ### 部署虚拟机
        # 先放大的，再放小的
        # logging.debug(add_request)

        # for server in state.servers:
        #     server.check_test()
