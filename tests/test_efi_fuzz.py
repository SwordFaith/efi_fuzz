#!/usr/bin/env python3

try:
    import monkeyhex
except ImportError:
    pass

from qiling import Qiling
from qiling.const import QL_INTERCEPT
from qiling.os.uefi.utils import read_int64, write_int64

import sys
sys.path.append('..')
from taint.tracker import *
import mockito
import taint
import rom

def test_uninitialized_memory_tracker():
    TEST_NAME = b'UninitializedMemoryTracker'

    enable_trace = True
    ql = Qiling(['./bin/EfiFuzzTests.efi'],
                ".",                                        # rootfs
                console=True if enable_trace else False,
                stdout=1 if enable_trace else None,
                stderr=1 if enable_trace else None,
                output='debug')

    # NVRAM environment.
    ql.env.update({'TestName': TEST_NAME, 'foo': b'\xde\xad\xbe\xef'})

    def validate_taint_set_variable(ql, address, params):
        assert params['VariableName'] == 'bar' and params['DataSize'] == 0x14
        begin = params['Data']
        end = params['Data'] + params['DataSize']
        tainted_bytes = ql.tainters['uninitialized'].get_taint_range(begin, end)
        assert tainted_bytes == [True, True, True, True, True, True, False, False, False, False,
                                 True, True, True, True, True, True, True, False, True, True]
        # Un-taint to avoid crashing the process.
        ql.tainters['uninitialized'].set_taint_range(begin, end, False)
        return (address, params)

    # Hook SetVariable() to check the taint on the buffer.
    set_variable_spy = mockito.spy(validate_taint_set_variable)
    ql.set_api("SetVariable", set_variable_spy, QL_INTERCEPT.ENTER)

    # okay, ready to roll.
    taint.tracker.enable(ql, ['uninitialized'])
    ql.run()

    # Make sure that SetVariable() was intercepted once.
    mockito.verify(set_variable_spy, times=1).__call__(*mockito.ARGS)

def test_firmware_volume():
    TEST_NAME = b'FirmwareVolume'

    enable_trace = True
    ql = Qiling(['./bin/EfiFuzzTests.efi'],
                ".",                                        # rootfs
                console=True if enable_trace else False,
                stdout=1 if enable_trace else None,
                stderr=1 if enable_trace else None,
                output='debug')

    # NVRAM environment.
    ql.env.update({'TestName': TEST_NAME})

    rom.install(ql, "./res/$0AGD000.FL1")

    def validate_read_section(ql, address, params):
        buffer_size = read_int64(ql, params['BufferSize'])
        buffer = ql.mem.read(read_int64(ql, params['Buffer']), buffer_size)
        assert buffer.decode('utf-16').strip('\x00') == 'DxeMain.efi'
        return (address, params)

    # Hook ReadSection() to check the taint on the buffer.
    read_section_spy = mockito.spy(validate_read_section)
    ql.set_api("ReadSection", read_section_spy, QL_INTERCEPT.EXIT)

    # okay, ready to roll.
    ql.run()

    # Make sure that ReadSection() was intercepted once.
    mockito.verify(read_section_spy, times=1).__call__(*mockito.ARGS)