# This file is part of nvitop, the interactive Nvidia-GPU process viewer.
# License: GNU GPL version 3.

# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
# pylint: disable=invalid-name

import datetime

import psutil
from cachetools.func import ttl_cache

from .utils import bytes2human, timedelta2human, Snapshot


class GProcess(psutil.Process):
    def __init__(self, pid, device, gpu_memory, type='C'):  # pylint: disable=redefined-builtin
        super(GProcess, self).__init__(pid)
        self._ident = (self.pid, self._create_time, device.index)
        self._hash = None

        super(GProcess, self).cpu_percent()
        self.device = device
        self.gpu_memory = gpu_memory
        self._type = ''
        self.type = type

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = ''
        if 'C' in value:
            self._type += 'C'
        if 'G' in value:
            self._type += 'G'
        if self._type == 'CG':
            self._type = 'C+G'

    @ttl_cache(ttl=2.0)
    def snapshot(self):
        try:
            running_time = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.create_time())
            snapshot = Snapshot(
                device=self.device,
                gpu_memory=self.gpu_memory,
                gpu_memory_human=bytes2human(self.gpu_memory),
                type=self.type,
                running_time=running_time,
                running_time_human=timedelta2human(running_time)
            )
            snapshot.__dict__.update(super(GProcess, self).as_dict())
            if len(snapshot.cmdline) == 0:  # pylint: disable=no-member
                raise psutil.Error
        except psutil.Error:
            return None
        else:
            return snapshot

    @staticmethod
    @ttl_cache(ttl=30.0)
    def get(pid, device):
        return GProcess(pid, device, gpu_memory=0, type='')