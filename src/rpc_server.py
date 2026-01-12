from flask import Flask, request, jsonify
from time import sleep
from async_exec import async_executor, async_task
import sys
import signal

app = Flask(__name__)

# Define the function to run when the signal is caught
def signal_handler(sig, frame):
    print('SIGINT (Ctrl+C) received. Shutting down gracefully...')
    async_executor.stop_threadpool()
    print("RPC server stopped.")
    sys.exit()

# Register the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)

class RequestStore:
    def __init__(self):
        self.store = {}

    def add_request(self, request_id, result, status, error=None):
        data = {"result": result, "error": error, "status": status}
        self.store[request_id] = data
        print(f"Stored request {request_id} with {data}")

    def get_request(self, request_id):
        return self.store.get(request_id)


request_store = RequestStore()    

def add(x, y):
    print("Simulating a long computation...")
    sleep(40)
    return x + y

def check_task_status(data):
    request_id = data.get('id')
    stored = request_store.get_request(request_id)
    if stored:
        return jsonify(id=request_id, result=stored['result'], status=stored['status'], error=stored['error'])
    else:
        print("Request ID not found:", request_id)
        return jsonify(error="Request ID not found"), 404

def submit_async_task(method, params, request_id):
    if method == 'async_add':
        request_store.add_request(request_id, result={}, status="running")
        async_executor.submit(async_add, request_id, params)

@async_task
def async_add(request_id, params):
    x = params.get('x')
    y = params.get('y')
    sleep(60)
    request_store.add_request(request_id, result=x + y, status="completed")
    async_executor.task_store.set_task_status(request_id, "completed")
    return x + y

@app.route('/rpc', methods=['POST'])
def rpc_handler():

    if not request.is_json:
        return jsonify(error="Invalid JSON"), 400

    data = request.get_json()
    method = data.get('method')
    params = data.get('params', {})
    request_id = data.get('id')
    print(f"Received RPC method: {method} with params: {params} and id: {request_id}")

    if request_id is None:
        return jsonify(error="Missing request ID", status="error", id=request_id), 400
    
    if request_store.get_request(request_id):
        stored = request_store.get_request(request_id)
        return jsonify(id=request_id, result=stored['result'], error=stored['error'], status=stored['status'])

    if method == 'hello':
        return jsonify(result="Hello from http-rpc!", status="completed", id=request_id)
    
    elif method == 'add':
        if len(params) != 2:
            return jsonify(error="Invalid parameters", status="error", id=request_id), 400
        result = add(**params)
        request_store.add_request(request_id=request_id, result=result, status="completed")
        return jsonify(result=result, status="completed", id=request_id)
    
    elif method == 'async_add':
        print("Received async_add request")
        if len(params) != 2:
            return jsonify(error="Invalid parameters", status="error", id=request_id), 400
        submit_async_task(method, params, request_id)
        request_store.add_request(request_id=request_id, result=None, status="running")
        return jsonify(result="Task submitted", status="running", id=request_id)

    elif method == 'check_task_status':
        return check_task_status(data)
    
    else:
        print("method not found:", method)
        return jsonify(error="Method not found", status="error", id=request_id), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)