# http-rpc

**http-rpc** is a lightweight HTTP-based Remote Procedure Call (RPC) service for Python. It enables communication between clients and servers using simple HTTP requests, making it easy to expose Python functions over the network and invoke them remotely.

## Features

- Simple HTTP API for RPC calls
- Built with Flask for the server-side
- Uses Requests for client-side communication
- Easily extensible for custom RPC methods

## Project Structure

```
http-rpc/
├── LICENSE
├── main.py
├── pyproject.toml
├── README.md
└── src/
    ├── rpc_client.py
    └── rpc_server.py
```

## Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) dependency manager

### Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd http-rpc
   ```

2. **Install [uv](https://github.com/astral-sh/uv):**
   ```sh
   pip install uv
   ```
   Or follow instructions in the [uv documentation](https://github.com/astral-sh/uv#installation).

3. **Install project dependencies using uv:**
   ```sh
   uv sync
   ```
   Or, to install from `pyproject.toml`:
   ```sh
   uv pip install -e .
   ```
   This will install all required dependencies (Flask, Requests, etc.).

## Usage

### Running the RPC Server

Start the server to expose your RPC methods over HTTP:

```sh
uv run python src/rpc_server.py
```

### Making RPC Calls from the Client

You can use the client to call remote procedures exposed by the server:

```sh
uv run python src/rpc_client.py
```

Or, use the `rpc_client.py` directly in your Python code:

```python
from src.rpc_client import RpcClient

client = RpcClient("http://localhost:5000")
result = client.call("add", {"a": 1, "b": 2})
print(result)
```

## License

See [LICENSE](LICENSE) for details.

---

For more details, see the source files in [src/rpc_server.py](src/rpc_server.py) and [src/rpc_client.py](src/rpc_client.py).