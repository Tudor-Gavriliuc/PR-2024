import subprocess

if __name__ == "__main__":
    processes = []
    try:
        for i in range(5):  # Start 5 nodes
            p = subprocess.Popen(["python3", "raft_node.py", str(i)])
            processes.append(p)
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
            p.wait()
