from typing import Dict
# import logging

# from public import MyException


class VmType:
    """
    虚拟机类型
    """

    def __init__(self, info: str):
        """
        (型号, CPU 核数, 内存大小, 是否双节点部署)
        (vm38TGB, 124, 2, 1)\n
        """
        res = info[1:-2].split(',')
        self.vm_model = res[0]
        self.core_num = int(res[1])
        self.memory = int(res[2])

        # 是否双节点部署
        if res[3] == ' 1' or res[3] == '1':
            self.is_double = True
        else:
            self.is_double = False

    def __str__(self):
        return f'vm model: {self.vm_model}, ' \
               f'core num: {self.core_num}, ' \
               f'memory: {self.memory}, ' \
               f'is double: {self.is_double}'


class Vm:
    """
    虚拟机，为每个虚拟机创建一个VM对象
    """
    def __init__(self, type_: VmType, id_: int):
        """
        (vm38TGB, 124, 2, 1)\n
        """
        self.type_ = type_
        self.id_ = id_
        self.server = None
        self.node = ''  # D, A, B where the vm be deployed

    def deployed_to(self, server, node: str):
        """
        :param server: Server, deploy the vm to a server
        :param node:
        :return:
        """
        self.server = server
        self.node = node


class ServerType:
    """
    服务器类型
    """

    def __init__(self, info: str):
        """
        (型号, CPU 核数, 内存大小, 硬件成本, 每日能耗成本
        example of the info: (host0Y6DP, 300, 830, 141730, 176)\n
        """
        res = info[1:-2].split(',')
        self.server_model = res[0]
        self.core_num = int(res[1])
        self.memory = int(res[2])
        self.price = int(res[3])
        self.energy_cost = int(res[4])

    def get_memory(self):
        return self.memory

    def can_deploy_vm(self, vm_type: VmType):
        """
        判断是否可以部署某种类型的虚拟机
        :param vm_type:
        :return:
        """
        if vm_type.is_double:
            return self.core_num > vm_type.core_num and self.memory > vm_type.memory
        else:
            return self.core_num // 2 > vm_type.core_num and self.memory // 2 > vm_type.memory

    def __str__(self):
        return f'server model：{self.server_model}, ' \
               f'core num：{self.core_num}, ' \
               f'memory: {self.memory}, ' \
               f'price: {self.price}, ' \
               f'energy_cost: {self.energy_cost}'


class Server:
    """
    服务器，为每个采购的服务器创建一个Server对象
    """

    def __init__(self, type_: ServerType):
        """
        :param type_: 服务器类型
        """
        self.type_ = type_
        self._memory_used_a = 0
        self._memory_used_b = 0
        self._core_used_a = 0
        self._core_used_b = 0
        self._up = False  # False为关机状态
        self._id: int = -1  # 只有采购之后才会分配id, -1表示在购买计划中
        self._vms_double: Dict[int, Vm] = {}
        self._vms_a: Dict[int, Vm] = {}
        self._vms_b: Dict[int, Vm] = {}

    def get_round_available_memory(self):
        """
        获取大约可用的内存（目前使用b节点的可用内存代替）
        :return:
        """
        return self.type_.memory // 2 - self._memory_used_b

    def free_vm(self, vm: Vm):
        """
        释放资源，然后从列表中删除对象
        :param vm:
        :return:
        """
        type_ = vm.type_
        if 'D' == vm.node:
            vm_table = self._vms_double
            half_mem = type_.memory // 2
            self._memory_used_a -= half_mem
            self._memory_used_b -= half_mem
            half_core = type_.core_num // 2
            self._core_used_a -= half_core
            self._core_used_b -= half_core
        elif 'A' == vm.node:
            vm_table = self._vms_a
            self._memory_used_a -= type_.memory
            self._core_used_a -= type_.core_num
        elif 'B' == vm.node:
            vm_table = self._vms_b
            self._memory_used_b -= type_.memory
            self._core_used_b -= type_.core_num
        else:
            # raise MyException('Unexpected node')
            raise NotImplementedError()
        vm_table.pop(vm.id_)

    @property
    def id_(self):
        assert self._id != -1
        return self._id

    @id_.setter
    def id_(self, value):
        self._id = value

    def deploy_vm(self, vm: Vm) -> str:
        """
        D双节点，A节点，B节点, F失败
        :param vm:
        :return:
        """
        # logging.debug(f'Deploying a vm: {vm}')
        if vm.type_.is_double:
            if self._deploy_vm_double(vm):
                vm.deployed_to(self, 'D')
                return 'D'
            else:
                return 'F'
        else:
            # Try node A
            if self._deploy_vm_a(vm):
                vm.deployed_to(self, 'A')
                return 'A'
            # Try node B
            elif self._deploy_vm_b(vm):
                vm.deployed_to(self, 'B')
                return 'B'
            else:
                return 'F'

    def _deploy_vm_double(self, vm: Vm) -> bool:
        core = vm.type_.core_num
        mem = vm.type_.memory
        node_memory = self.type_.memory // 2
        node_core = int(self.type_.core_num // 2)

        half_mem = mem // 2
        half_core = core // 2
        if (self._memory_used_a + half_mem) > node_memory or (self._memory_used_b + half_mem) > node_memory:
            # raise MyException('Memory used out')
            return False
        if (self._core_used_a + half_core) > node_core or (self._core_used_b + half_core) > node_core:
            # raise MyException('Core used out')
            return False
        # Success to deploy
        self._memory_used_a += half_mem
        self._memory_used_b += half_mem
        self._core_used_a += half_core
        self._core_used_b += half_core
        self._vms_double[vm.id_] = vm
        return True

    def _deploy_vm_a(self, vm: Vm) -> bool:
        core = vm.type_.core_num
        mem = vm.type_.memory
        node_memory = self.type_.memory // 2
        node_core = int(self.type_.core_num // 2)

        if (self._memory_used_a + mem) > node_memory or (self._core_used_a + core) > node_core:
            # raise MyException('Failed to deploy on node A')
            return False

        self._memory_used_a += mem
        self._core_used_a += core
        self._vms_a[vm.id_] = vm
        return True

    def _deploy_vm_b(self, vm: Vm):
        core = vm.type_.core_num
        mem = vm.type_.memory
        node_memory = self.type_.memory // 2
        node_core = int(self.type_.core_num // 2)

        if (self._memory_used_b + mem) > node_memory or (self._core_used_b + core) > node_core:
            # raise MyException('Failed to deploy on node B')
            return False

        self._memory_used_b += mem
        self._core_used_b += core
        self._vms_b[vm.id_] = vm
        return True
