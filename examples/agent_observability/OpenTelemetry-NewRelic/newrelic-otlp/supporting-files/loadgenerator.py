import os, random, sys, signal, time

def signal_handler(signal, frame):
    print("\nCtrl-C received. Stopping load generator.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

languages = ["dotnet", "go", "java", "javascript", "python", "ruby", "rust"]

while True:
    n = random.randint(1, 100)
    for language in languages:
        os.system(f"curl http://{language}:8080/fibonacci?n={n} > /dev/null 2>&1")
    time.sleep(1)
