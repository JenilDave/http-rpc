import requests
import time
import uuid

class RPCClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def retry(num_retries=3, delay_seconds=2):
        def decorator_retry(func):
            def wrapper_retry(*args, **kwargs):
                for attempt in range(num_retries):
                    try:
                        return func(*args, **kwargs)
                    except requests.exceptions.RequestException as e:
                        if attempt == num_retries - 1:
                            print(f"Max retries reached. Raising exception: {e}")
                            raise
                        print(f"Attempt {attempt + 1} failed. Retrying in {delay_seconds} seconds...")
                        time.sleep(delay_seconds)
            return wrapper_retry
        return decorator_retry

    @retry(num_retries=3, delay_seconds=2)
    def post_request(self, method, params, request_id=None):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }
        response = requests.post(self.base_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if 'error' in result and result['error'] is not None:
            raise Exception(f"RPC Error: {result['error']} {result.get('message', '')}")
        return result

    def __getattribute__(self, name):
        # Define a wrapper function that will receive the arguments

        if name in ['base_url', 'post_request', 'retry', '__class__', '__init__', '__getattribute__']:
            return super().__getattribute__(name)

        def wrapper(*args, **kwargs):
            print(f"RPC to: {name} with args: {args} and kwargs: {kwargs}")
            request_id = kwargs.get('id', "") or str(uuid.uuid4())
            response = self.post_request(method=name, params=kwargs, request_id=request_id)
            return response
        
        return wrapper


if __name__ == "__main__":
    client = RPCClient("http://localhost:5000/rpc")
    # print(client.add(x=5, y=3))
    
    status = client.add(x=5, y=3)
    print(status)
    request_id = status['id']
    print("Submitted async task, initial status =", status)
    while status['status'] == "running":
        time.sleep(5)
        status = client.check_task_status(id=request_id)
        print("Task status =", status)
    
    print("Final result:", status)