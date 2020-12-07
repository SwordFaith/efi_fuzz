from qiling.os.uefi.fncc import *
from qiling.os.const import *
from qiling.os.uefi.const import *
from qiling.os.uefi.utils import *
# from qiling.const import *
from ctypes import Structure, c_uint64, sizeof

class EFI_MMRAM_DESCRIPTOR(Structure):
    _fields_ = [
        ('PhysicalStart', c_uint64),
        ('CpuStart', c_uint64),
        ('PhysicalSize', c_uint64),
        ('RegionState', c_uint64),
    ]
EFI_MMRAM_OPEN = 0x00000001
EFI_MMRAM_CLOSED = 0x00000002
EFI_MMRAM_LOCKED = 0x00000004
EFI_CACHEABLE = 0x00000008
EFI_ALLOCATED = 0x00000010
EFI_NEEDS_TESTING = 0x00000020
EFI_NEEDS_ECC_INITIALIZATION = 0x00000040

def hook_GetCapabilities(ql, address, params):
    number_of_map_info_entries = 1 # We only support one smram region
    struct_size = sizeof(EFI_MMRAM_DESCRIPTOR)
    buffer_size = number_of_map_info_entries * struct_size
    write_int64(ql, params["MmramMapSize"], buffer_size)
    if params['MmramMap'] != 0:
        ptr  = ql.os.heap.alloc(buffer_size)
        efi_mmram_descriptor = EFI_MMRAM_DESCRIPTOR()
        efi_mmram_descriptor.PhysicalStart = ql.os.smm.smbase
        efi_mmram_descriptor.CpuStart = ql.os.smm.smbase
        efi_mmram_descriptor.PhysicalSize = ql.os.smm.smram_size
        efi_mmram_descriptor.RegionState = EFI_ALLOCATED
        ql.mem.write(ptr, convert_struct_to_bytes(efi_mmram_descriptor))
        write_int64(ql, params['MmramMap'], ptr)
        return EFI_SUCCESS
    return EFI_BUFFER_TOO_SMALL

def init_GetCapabilities(ql):
    ql.set_api("GetCapabilities", hook_GetCapabilities)

