import socket
import subprocess
import sys
import time

active_processes = {}

neo4j_start_command = [
    "docker", "run",
    "--publish=7474:7474", "--publish=7687:7687",
    "--volume=./data:/data",
    "--env=NEO4J_AUTH=none",
    "--env=NEO4J_apoc_export_file_enabled=true",
    "--env=NEO4J_apoc_import_file_enabled=true",
    "--env=NEO4J_apoc_import_file_use__neo4j__config=true",
    "--env=NEO4J_PLUGINS=[\"apoc\"]",
    "neo4j"
]

backend_start_command = [
    "uv", "run", "fastapi", "dev"
]

frontend_start_command = [
    "npm", "run", "dev"
]

stderr_log_file = open("stderr.log", "w")
neo4j_stdout_log_file = open("neo4j_stdout.log", "w")
backend_stdout_log_file = open("backend_stdout.log", "w")
frontend_stdout_log_file = open("frontend_stdout.log", "w")

components = {
    "neo4j": (neo4j_start_command, "./neo4j-populate", neo4j_stdout_log_file, 7687),
    "backend": (backend_start_command, "./musicgraph-backend", backend_stdout_log_file, 8000),
    "frontend": (frontend_start_command, "./musicgraph-frontend", frontend_stdout_log_file, 5173),
}

def wait_for_port(port, host="localhost", timeout=60):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, TimeoutError, OSError):
            if time.time() - start_time > timeout:
                print(f"Timeout: port {port} didn't answer after {timeout} seconds.")
                return False
            time.sleep(1)

def start_subprocess(command, active_directory, stdout_file, port, stderr_file = stderr_log_file):
    print(f"Calling command {command[0]}")
    process_call = subprocess.Popen(
        command,
        cwd = active_directory,
        stdout = stdout_file,
        stderr = stderr_file
    )
    #if wait_for_port(port):
    #    return process_call
    #else:
    #    print(f"Failed to call command {command[0]}")
    return process_call

def end_subprocess(process_call):
    process_call.terminate()
    process_call.wait()


if __name__ == "__main__":
    active_executions = {}

    for component, (command, directory, stdout_file, port) in components.items():
        active_executions[component] = start_subprocess(command, directory, stdout_file, port)

    print("Musicgraph started for tests with success!")
    
    try:
        while True:
            restarted_component = input("Type the name of a component to re-initiate it. Type \"exit\" to end all the processes: ")
            if restarted_component == "exit":
                print("Shutting down all the processes")
                for call in active_executions.values():
                    end_subprocess(call)

                stderr_log_file.close()
                neo4j_stdout_log_file.close()
                backend_stdout_log_file.close()
                frontend_stdout_log_file.close()

                sys.exit(0)
            elif restarted_component in components:
                print(f"Restarting {restarted_component}")
                end_subprocess(active_executions[restarted_component])
                active_executions[restarted_component] = start_subprocess(
                    components[restarted_component][0],
                    components[restarted_component][1],
                    components[restarted_component][2],
                )
            else:
                print("Invalid input. Try again.")
                
    except KeyboardInterrupt:
        print("Shutting down all the processes")
        for call in active_executions.values():
            end_subprocess(call)

        stderr_log_file.close()
        neo4j_stdout_log_file.close()
        backend_stdout_log_file.close()
        frontend_stdout_log_file.close()

        sys.exit(0)
