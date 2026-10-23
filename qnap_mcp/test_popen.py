import subprocess, time
p = subprocess.Popen(["./qmcp", "--confighome", "NAS27B823", "--debug"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(1)
print(p.poll())
print("OUT:", p.stdout.read())
print("ERR:", p.stderr.read())
