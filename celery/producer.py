
from app import app


def push(file_path: str) -> str:

    result = app.send_task('process_file', args=[file_path])
    print(f"➤ Task sent: id={result.id}")


    out = result.get(timeout=60)
    return out


