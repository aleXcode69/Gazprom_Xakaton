from app import app

@app.task(name='process_file')
def process_file(input_path: str):

    import time
    time.sleep(5)

    return f"Processed file: {input_path}"