import asyncio
import json
import os
from collections import defaultdict

async def fetch_system_stats():
    ps_process = asyncio.create_subprocess_exec('/usr/bin/ps', '-A', '-o', 'pid,ppid,%cpu,cputime,%mem,nlwp,rss,cmd', '--cumulative', 'Sww', '--no-headers', stdout=asyncio.subprocess.PIPE)
    fh_process = asyncio.create_subprocess_exec('/usr/bin/bash', '-c', 'ls -m /proc/[0-9]*/fd --color=never -w0', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    lsof_process = asyncio.create_subprocess_exec("lsof", "-n", "-i", stdout=asyncio.subprocess.PIPE)

    ps_process, fh_process, lsof_process = await asyncio.gather(ps_process, fh_process, lsof_process)
    ps_info, fh_response, lsof_response = await asyncio.gather(
        ps_process.stdout.read(),
        fh_process.stdout.read(),
        lsof_process.stdout.read(),
    )

    # Free subprocess resources once output is collected
    del ps_process
    del fh_process
    del lsof_process

    return ps_info, fh_response, lsof_response

async def fetch_kernel_info(kernel_manager):
    kernels: dict[str, dict] = {kernel["id"]: kernel for kernel in kernel_manager.list_kernels()}
    kernel_files = os.listdir("/home/jupyter/.local/share/jupyter/runtime/")
    for kernel_file in kernel_files:
        if not kernel_file.startswith("kernel-"):
            continue
        kernel_id = kernel_file[7:-5]  # Remove 'kernel-' and '.json' from the beginning and end of the filename.
        if kernel_id not in kernels:
            continue
        with open(f"/home/jupyter/.local/share/jupyter/runtime/{kernel_file}") as kf:
            kernels[kernel_id].update(json.load(kf))
    return kernels

async def build_proc_info(ps_response, fh_response):
    proc_info = {}
    for line in ps_response.decode().splitlines():
        pid, ppid, cpu_pct, cputime, mem_pct, threads, mem_bytes, cmd = line.split(maxsplit=7)
        proc_info[pid] = {
            "pid": pid,
            "ppid": ppid,
            "cpu_pct": cpu_pct,
            "cputime": cputime,
            "mem_pct": mem_pct,
            "threads": threads,
            "mem_bytes": mem_bytes,
            "cmd": cmd,
        }
    for record in fh_response.decode().split("\n\n"):
        proc_path, file_handles = record.splitlines()
        pid = proc_path.split('/')[2]
        fh_count = len(file_handles.split())
        if pid in proc_info:
            proc_info[pid]["open_files"] = fh_count
    return proc_info


async def build_edges_map(lsof_response, kernels):
    edges = set()
    pid_port_listens = {}
    pid_connections = defaultdict(set)
    for line in lsof_response.decode().splitlines()[1:]:
        cmd, pid, user, fd, itype, _, _, node, conn = line.split(maxsplit=8)
        connection_string, connection_type = conn.split()
        if connection_type == '(LISTEN)':
            pid_port_listens[connection_string] = pid
        elif '->' in conn:
            source, dest = connection_string.split('->')
            pid_connections[pid].add((source, dest))

    for pid, portmap in pid_connections.items():
        for source, dest in portmap:
            child = pid_port_listens.get(dest, None)
            if child is not None and pid != child:
                edges.add((pid, child))

    kernel_by_pid_index = {}
    for kernel in kernels.values():
        ip = kernel.get("ip")
        control_port = kernel.get("control_port")
        pid = pid_port_listens.get(f"{ip}:{control_port}", None)
        if pid is not None:
            kernel["pid"] = pid
            kernel_by_pid_index[pid] = kernel

    return edges, kernel_by_pid_index
