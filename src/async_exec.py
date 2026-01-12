from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread
from datetime import datetime, timedelta
from time import sleep

LEASE_DURATION_SECONDS = 10
HEARTBEAT_INTERVAL_SECONDS = 10

class AttemptStore:
    def __init__(self):
        self.attempts = {}

    def add_attempt(self, attempt_id, info={}):
        self.attempts[attempt_id] = {
            "info": info,
            "last_heartbeat": datetime.now()
        }
        print(f"Added attempt ID: {self.attempts}")

    def get_attempt(self, attempt_id):
        return self.attempts.get(attempt_id)
        
    def update_heartbeat(self, attempt_id):
        print("Updating heartbeat for attempt ID:", attempt_id)
        attempt = self.attempts.get(attempt_id)
        print("Current attempt data:", attempt)
        if attempt:
            self.attempts[attempt_id]['last_heartbeat'] = datetime.now()
            print(f"Updated heartbeat for attempt ID: {attempt_id}")
        else:
            print(f"attempt ID {attempt_id} not found in attempts store!")

class TaskStore:
    def __init__(self):
        self.tasks = {}

    def add_task(self, fn, request_id, function_args):
        current_ts = datetime.now()
        self.tasks[request_id] = {
            "function": fn,
            "function_args": function_args,
            "status": "running",
            "last_heartbeat": current_ts,
            "lease_expiry": current_ts + timedelta(seconds=LEASE_DURATION_SECONDS),
            "attempt_id": request_id
        }

    def get_task(self, request_id):
        return self.tasks.get(request_id)
    
    def update_heartbeat(self, request_id):
        if request_id in self.tasks:
            current_ts = datetime.now()
            self.tasks[request_id]['last_heartbeat'] = current_ts
            self.tasks[request_id]['lease_expiry'] = current_ts + timedelta(seconds=LEASE_DURATION_SECONDS)

    def set_task_status(self, request_id, status):
        if request_id in self.tasks:
            self.tasks[request_id]['status'] = status


class AsyncExecutor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stop_heartbeat_monitor = Event()
        self.task_store = TaskStore()
        self.attempt_store = AttemptStore()
        self.start_heartbeat_monitor()

    def submit(self, fn, *args, **kwargs):
        print("Submitting async task...", args, kwargs)
        self.task_store.add_task(fn, args[0], kwargs)
        self.attempt_store.add_attempt(args[0])
        future = self.executor.submit(fn, *args, **kwargs)
        return future

    def heartbeat_monitor(self):

        print("Heartbeat monitor started.")

        while not self.stop_heartbeat_monitor.is_set():
            print("Heartbeat monitor checking tasks...")
            print("All Tasks:",self.task_store.tasks)
            print("All attempts:",self.attempt_store.attempts)
            for id, task in list(self.task_store.tasks.items()):
                attempt_id = task['attempt_id']
                last_heartbeat = self.attempt_store.attempts.get(attempt_id)['last_heartbeat']
                status = task['status']
                lease_duration = timedelta(seconds=LEASE_DURATION_SECONDS)
                current_ts = datetime.now()

                if status == "running" and (current_ts - last_heartbeat) > lease_duration:
                    print(f"Resubmitting task {id} due to heartbeat timeout.")
                    print((current_ts - last_heartbeat), lease_duration)
                    self.submit(task['function'], id, **task['function_args'])
                    self.task_store.set_task_status(id, "resubmitted")
                elif status == "completed":
                    del self.task_store.tasks[id]
                    del self.attempt_store.attempts[attempt_id]
                    print(f"Task {id} is completed or not running. Status: {status}")
                        
            self.stop_heartbeat_monitor.wait(HEARTBEAT_INTERVAL_SECONDS)
                    
        print("Heartbeat monitor stopped.")
    
    def start_heartbeat_monitor(self):
        self.stop_heartbeat_monitor.clear()
        monitor_thread = Thread(target=self.heartbeat_monitor, daemon=True)
        monitor_thread.start()

    def stop_threadpool(self):
        self.stop_heartbeat_monitor.set()
        self.executor.shutdown(wait=True)
    
    def set_task_status(self, request_id, status):
        self.task_store.set_task_status(request_id, status)

async_executor = AsyncExecutor(max_workers=4)
attempt_store = AttemptStore()

def async_task(fn):
    def wrapper(*args, **kwargs):
        stop_heatbeat = Event()

        def task_heartbeat(request_id):
            while not stop_heatbeat.is_set():
                sleep(30)
                async_executor.attempt_store.update_heartbeat(request_id)
                print(f"Heartbeat sent for request ID: {request_id}")
                
                if stop_heatbeat.wait(timeout=1): 
                    print(f"Heartbeat thread for request ID: {request_id} exiting.")
                    break

                attempt_status = async_executor.task_store.get_task(request_id)
                if attempt_status is None or attempt_status['status'] != "running":
                    print(f"Stopping heartbeat for request ID: {request_id} as task is no longer running.")
                    break

        print("Starting heartbeat thread for request ID:", args[0])
        stop_heatbeat.clear()
        t = Thread(target=task_heartbeat, args=(args[0],), daemon=True)
        t.start()
        result = fn(*args, **kwargs)
        print(f"Result: {result}")
        stop_heatbeat.set()
        t.join()
        print(f"Heartbeat thread for request ID: {args[0]} stopped.")
        return result
    return wrapper