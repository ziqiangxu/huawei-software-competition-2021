from typing import List
import logging

from public import MyException


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
        # TODO


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
        self._vms_double: List[Vm] = []
        self._vms_a: List[Vm] = []
        self._vms_b: List[Vm] = []

    @property
    def id_(self):
        return self._id

    @id_.setter
    def id_(self, value):
        self._id = value

    def deploy_vm(self, vm: Vm):
        logging.debug(f'Deploying a vm: {vm}')
        if vm.type_.is_double:
            self._deploy_vm_double(vm)
        else:
            # Try node A
            try:
                self._deploy_vm_a(vm)
            except MyException:
                # Try node B
                self._deploy_vm_b(vm)

    def _deploy_vm_double(self, vm: Vm):
        core = vm.type_.core_num
        mem = vm.type_.memory
        node_memory = self.type_.memory // 2
        node_core = int(self.type_.core_num // 2)

        half_mem = mem // 2
        half_core = core // 2
        if (self._memory_used_a + half_mem) > node_memory or (self._memory_used_b + half_mem) > node_memory:
            raise MyException('Memory used out')
        if (self._core_used_a + half_core) > node_core or (self._core_used_b + half_core) > node_core:
            raise MyException('Core used out')
        # Success to deploy
        self._memory_used_a += half_mem
        self._memory_used_b += half_mem
        self._core_used_a += half_core
        self._core_used_b += half_core
        self._vms_double.append(vm)
        # TODO output to std
        return True

    def _deploy_vm_a(self, vm: Vm):
        core = vm.type_.core_num
        mem = vm.type_.memory
        node_memory = self.type_.memory // 2
        node_core = int(self.type_.core_num // 2)

        if (self._memory_used_a + mem) > node_memory or (self._core_used_a + core) > node_core:
            raise MyException('Failed to deploy on node A')

        self._memory_used_a += mem
        self._core_used_a += core
        self._vms_a.append(vm)
        # TODO output to std

    def _deploy_vm_b(self, vm: Vm):
        core = vm.type_.core_num
        mem = vm.type_.memory
        node_memory = self.type_.memory // 2
        node_core = int(self.type_.core_num // 2)

        if (self._memory_used_b + mem) > node_memory or (self._core_used_b + core) > node_core:
            raise MyException('Failed to deploy on node B')

        self._memory_used_b += mem
        self._core_used_b += core
        self._vms_b.append(vm)
        # TODO output to std
