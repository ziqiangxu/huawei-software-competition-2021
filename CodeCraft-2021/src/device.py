import warnings
from typing import Dict, List


# import logging

# from public import MyException
THRESHOLD_TYPE = 4
THRESHOLD_TYPE_RE = 1 / THRESHOLD_TYPE
THRESHOLD_SERVER_CONVERT = 5
THRESHOLD_SERVER_CONVERT_RE = 1 / THRESHOLD_SERVER_CONVERT
TYPE_COMPUTE = 0
TYPE_BALANCE = 1
TYPE_MEMORY = 2


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
        if (self.memory / self.core_num) < THRESHOLD_TYPE_RE:
            self.device_type = TYPE_COMPUTE
        elif (self.memory / self.core_num) > THRESHOLD_TYPE:
            self.device_type = TYPE_MEMORY
        else:
            self.device_type = TYPE_BALANCE

        # 是否双节点部署
        if res[3] == ' 1' or res[3] == '1':
            self.is_double = True
        else:
            self.is_double = False

        self._prefer_server: List[ServerType] = []

    @property
    def prefer_server(self):
        return self._prefer_server

    def find_prefer_server(self, server_types: List):
        for type_ in server_types:
            type_: ServerType
            if type_.can_deploy_vm(self):
                if 2 > type_.mem_core_ratio > 1:
                    self._prefer_server.append(type_)
                # self._prefer_server.append(type_)

        # return

        # TODO 还需要再斟酌，这样可能会造成空间的浪费

        # TODO 还需要再斟酌，这样可能会造成空间的浪费
        if self.device_type == TYPE_COMPUTE:
            # 计算型虚拟机则选择计算型服务器
            self._prefer_server.sort(key=ServerType.get_mem_core_ratio)
        elif self.device_type == TYPE_MEMORY:
            self._prefer_server.sort(key=ServerType.get_mem_core_ratio, reverse=True)
        # elif self.device_type == TYPE_BALANCE:
        #     self._prefer_server.sort(key=ServerType.get_price_index, reverse=False)
        return

    def __str__(self):
        return f'vm model: {self.vm_model}, ' \
               f'core num: {self.core_num}, ' \
               f'memory: {self.memory}, ' \
               f'is double: {self.is_double}'


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
        self.half_core = self.core_num // 2
        self.memory = int(res[2])
        self.half_memory = self.memory // 2
        self.price = int(res[3])
        self.energy_cost = int(res[4])
        self.mem_core_ratio = self.memory / self.core_num  # 按值的大小分为: 0-4计算型， >4存储型
        # 通过对80个服务器进行数据相关性分析得：
        # price_pre = 219 x core + 104 x mem
        # 1000 * energy_pre = 275 x core + 130 x mem
        # 后期基于服务器价格排名
        price_pre = self.price - 219 * self.core_num + 104 * self.memory
        self.price_index = (self.price - price_pre) / price_pre  # 价格的偏离程度，此指数越小越好
        # 前期基于能耗排名
        energy_pre = 275 * self.core_num + 130 * self.memory
        self.energy_index = (self.energy_cost - energy_pre) / energy_pre  # 能耗的偏离程度，此指数越小越好

    def get_price_index(self):
        return self.price_index

    def get_mem_core_ratio(self):
        return self.mem_core_ratio

    def get_memory(self):
        return self.memory

    def can_deploy_vm(self, vm_type: VmType):
        """
        判断是否可以部署某种类型的虚拟机
        :param vm_type:
        :return:
        """
        if vm_type.is_double:
            return self.core_num >= vm_type.core_num and self.memory >= vm_type.memory
        else:
            return self.core_num // 2 >= vm_type.core_num and self.memory // 2 >= vm_type.memory

    def __str__(self):
        return f'server model：{self.server_model}, ' \
               f'core num：{self.core_num}, ' \
               f'memory: {self.memory}, ' \
               f'price: {self.price}, ' \
               f'energy_cost: {self.energy_cost}'


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
        warnings.warn('', DeprecationWarning)
        return self.type_.memory // 2 - self._memory_used_b

    def get_available_memory(self):
        node_memory = self.type_.memory // 2
        return node_memory - self._memory_used_a, node_memory - self._memory_used_b

    def get_available_core(self):
        node_core = self.type_.core_num // 2
        return node_core - self._core_used_a, node_core - self._core_used_b

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
        不考虑服务器的结构
        D双节点，A节点，B节点, F失败
        :param vm:
        :return:
        """
        # logging.debug(f'Deploying a vm: {vm}')
        if vm.type_.is_double:
            if self._deploy_vm_double(vm):
                return 'D'
            return 'F'
        else:
            # Try node A
            if self._deploy_vm_a(vm):
                return 'A'
            # Try node B
            if self._deploy_vm_b(vm):
                return 'B'
            return 'F'

    def proper_deploy_vm(self, vm: Vm) -> str:
        """
        TODO 查看服务器的内存和核心结构，如果不合适则不进行部署
        D双节点，A节点，B节点, F失败
        :param vm:
        :return:
        """
        vm_type = vm.type_
        if vm_type.is_double:
            # TODO 还没有对双节点部署优化
            return self.deploy_vm(vm)
        else:
            if self._proper_deploy_vm_a(vm):
                return 'A'
            elif self._proper_deploy_vm_b(vm):
                return 'B'
            return 'F'

    def _proper_deploy_vm_b(self, vm: Vm) -> bool:
        mem = self.type_.half_memory - self._memory_used_b
        core = self.type_.half_core - self._core_used_b
        if mem == 0 or core == 0:
            return False
        vm_type = vm.type_
        if mem / core > THRESHOLD_SERVER_CONVERT and vm_type.device_type == TYPE_MEMORY:
            return False
        # 计算型服务器不接收存储型的虚拟机了
        elif mem / core < THRESHOLD_SERVER_CONVERT_RE and vm_type.device_type == TYPE_COMPUTE:
            return False
        else:
            return self._deploy_vm_b(vm)

    def _proper_deploy_vm_a(self, vm: Vm) -> bool:
        mem = self.type_.half_memory - self._memory_used_a
        core = self.type_.half_core - self._core_used_a
        if mem == 0 or core == 0:
            return False
        vm_type = vm.type_
        # 存储型的服务器不接收计算型的虚拟机了
        if mem / core > THRESHOLD_SERVER_CONVERT and vm_type.device_type == TYPE_COMPUTE:
            return False
        # 计算型服务器不接收存储型的虚拟机了
        elif mem / core < THRESHOLD_SERVER_CONVERT_RE and vm_type.device_type == TYPE_MEMORY:
            return False
        else:
            return self._deploy_vm_a(vm)

    def _deploy_vm_double(self, vm: Vm) -> bool:
        half_core = vm.type_.core_num // 2
        half_mem = vm.type_.memory // 2
        node_core = self.type_.core_num // 2
        node_memory = self.type_.memory // 2

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
        vm.deployed_to(self, 'D')
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
        vm.deployed_to(self, 'A')
        return True

    def _deploy_vm_b(self, vm: Vm) -> bool:
        core = vm.type_.core_num
        mem = vm.type_.memory
        node_memory = self.type_.memory // 2
        node_core = self.type_.core_num // 2

        if (self._memory_used_b + mem) > node_memory or (self._core_used_b + core) > node_core:
            # raise MyException('Failed to deploy on node B')
            return False

        self._memory_used_b += mem
        self._core_used_b += core
        self._vms_b[vm.id_] = vm
        vm.deployed_to(self, 'B')
        return True

    def check_test(self):
        """
        检查核心数和内存
        :return:
        """
        mem_a = 0
        core_a = 0
        mem_b = 0
        core_b = 0

        for vm in self._vms_a.values():
            assert vm.node == 'A'
            mem_a += vm.type_.memory
            core_a += vm.type_.core_num

        for vm in self._vms_b.values():
            assert vm.node == 'B'
            mem_b += vm.type_.memory
            core_b += vm.type_.core_num

        for vm in self._vms_double.values():
            assert vm.node == 'D'
            mem_a += vm.type_.memory // 2
            mem_b += vm.type_.memory // 2
            core_a += vm.type_.core_num // 2
            core_b += vm.type_.core_num // 2

        assert mem_a == self._memory_used_a and mem_a <= self.type_.memory // 2
        assert mem_b == self._memory_used_b and mem_b <= self.type_.memory // 2
        assert core_a == self._core_used_a and core_a <= self.type_.core_num // 2
        assert core_b == self._core_used_b and core_b <= self.type_.core_num // 2
