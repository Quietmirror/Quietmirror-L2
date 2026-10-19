"""Bound one child process tree; no changes to system policy or other jobs."""
import argparse, ctypes, json, os, subprocess, sys, time
from ctypes import wintypes as w
from pathlib import Path

class Basic(ctypes.Structure):
    _fields_=[('PerProcessUserTimeLimit',ctypes.c_int64),('PerJobUserTimeLimit',ctypes.c_int64),('LimitFlags',w.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',w.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
class IO(ctypes.Structure):
    _fields_=[(n,ctypes.c_uint64) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class Limits(ctypes.Structure):
    _fields_=[('BasicLimitInformation',Basic),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
class Memory(ctypes.Structure):
    _fields_=[('dwLength',w.DWORD),('dwMemoryLoad',w.DWORD)]+[(n,ctypes.c_uint64) for n in ('ullTotalPhys','ullAvailPhys','ullTotalPageFile','ullAvailPageFile','ullTotalVirtual','ullAvailVirtual','ullAvailExtendedVirtual')]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--memory-gib',type=float,default=4);ap.add_argument('--timeout',type=int,default=2400);ap.add_argument('--log',required=True);ap.add_argument('command',nargs=argparse.REMAINDER);a=ap.parse_args()
    command=a.command[1:] if a.command[:1]==['--'] else a.command
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE
    k.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD];k.SetInformationJobObject.restype=w.BOOL
    k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];k.AssignProcessToJobObject.restype=w.BOOL
    k.QueryInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p];k.QueryInformationJobObject.restype=w.BOOL
    k.TerminateJobObject.argtypes=[w.HANDLE,w.UINT];k.TerminateJobObject.restype=w.BOOL
    k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
    mem=Memory();mem.dwLength=ctypes.sizeof(mem);k.GlobalMemoryStatusEx(ctypes.byref(mem))
    cap=min(a.memory_gib,6.0,mem.ullTotalPhys/2**30*.4)
    info=Limits();info.BasicLimitInformation.LimitFlags=0x2000|0x200;info.JobMemoryLimit=int(cap*2**30)
    job=k.CreateJobObjectW(None,None)
    if not job or not k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info)):raise ctypes.WinError(ctypes.get_last_error())
    log=Path(a.log);log.parent.mkdir(parents=True,exist_ok=True);t=time.monotonic();reason=None;child=None
    try:
        with log.open('wb') as stream:
            child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            if not k.AssignProcessToJobObject(job,w.HANDLE(child._handle)):
                child.terminate();raise ctypes.WinError(ctypes.get_last_error())
            print(json.dumps({'pid':child.pid,'log':str(log),'memory_cap_gib':cap}),flush=True)
            while child.poll() is None:
                k.GlobalMemoryStatusEx(ctypes.byref(mem))
                if time.monotonic()-t>a.timeout:reason='TIMEOUT'
                if mem.ullAvailPhys<512*1024**2:reason='SYSTEM_FREE_MEMORY_BELOW_512_MIB'
                if reason:
                    k.TerminateJobObject(job,137);child.wait();break
                time.sleep(1)
        k.QueryInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info),None)
        result=dict(command=command,returncode=child.returncode,reason=reason,seconds=round(time.monotonic()-t,2),memory_cap_gib=cap,peak_job_memory_gib=round(info.PeakJobMemoryUsed/2**30,3),log=str(log))
        log.with_suffix('.guard.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True)
        return child.returncode if child.returncode else (137 if reason else 0)
    finally:k.CloseHandle(job)
if __name__=='__main__':sys.exit(main())
