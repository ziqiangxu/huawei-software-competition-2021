from typing import List, Tuple

from device import *


class State:
    """
    全局状态保存类
    """
    def __init__(self):
        self._server_types: List[ServerType] = []
        self._server_types_hash = {}
        self._vm_types: List[VmType] = []
        self._vm_types_hash = {}
        # TODO 优化选择服务器的策略，和查找可用服务器的算法
        self.servers: List[Server] = []
        self._vms: Dict[int, Vm] = {}  # 以虚拟机id为key
        self._server_num = -1

    @property
    def server_types(self):
        return self._server_types

    @server_types.setter
    def server_types(self, types: List[ServerType]):
        # 对服务器按照内存从小到大排序
        types.sort(key=ServerType.get_memory, reverse=True)
        for t in types:
            key = t.server_model.strip()
            self._server_types_hash[key] = t
        self._server_types = types

    @property
    def vm_types(self):
        return self._vm_types

    @vm_types.setter
    def vm_types(self, types: List[VmType]):
        for t in types:
            key = t.vm_model.strip()
            self._vm_types_hash[key] = t
        self._vm_types = types

    def get_vm_type(self, vm_model: str):
        """
        根据型号获取虚拟机类型
        :param vm_model:
        :return:
        """
        key = vm_model.strip()
        return self._vm_types_hash[key]

    def get_server_type(self, server_model: str):
        """
        根据型号获取服务器类型
        :param server_model:
        :return:
        """
        key = server_model.strip()
        return self._server_types_hash[key]

    def get_top_memory_server_type(self) -> ServerType:
        """
        获取内存最大的服务器
        :return:
        """
        return self._server_types[0]

    def deploy_vm(self, vm: Vm, server: Server = None) -> Tuple[Server, str]:
        """
        :param vm:
        :param server:
        :return: server and which node the vm deploy
        """
        if server:
            node = server.deploy_vm(vm)
            self._vms[vm.id_] = vm
            return server, node

        for s in self.servers:
            try:
                node = s.deploy_vm(vm)
                self._vms[vm.id_] = vm
                return s, node
            except MyException:
                continue
        raise MyException('Failed to deploy on the exist server, new server required')

    def free_vm(self, id_: int):
        """
        # TODO 根据给定的
        释放某个虚拟机
        :param id_: id of the vm
        :return:
        """
        vm: Vm = self._vms.pop(id_)
        server = vm.server
        server.free_vm(vm)

    def plan_server(self, type_: ServerType):
        """
        :param type_:
        :return:
        """
        server = Server(type_)
        self.servers.append(server)
        return server

    def install_server(self, server_list: List[Server]):
        """
        购买来了服务器，对服务器进行安装编号
        :param server_list: 服务器列表
        :return:
        """
        for server in server_list:
            self._server_num += 1
            server.id_ = self._server_num

    def find_server_type_for_vm(self, vm_type: VmType) -> ServerType:
        """
        为某虚拟机类型寻找一个合适的服务器类型
        :param vm_type:
        :return:
        """
        for s in self._server_types:
            if s.can_deploy_vm(vm_type):
                return s


state = State()
