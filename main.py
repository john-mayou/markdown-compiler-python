from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from compiler import Compiler

app = FastAPI()

@app.get('/', response_class=HTMLResponse)
async def read_root():
    with open('testdata/example.text', 'r') as f:
        markdown = f.read()

    return wrap_html(Compiler().compile(markdown))

def wrap_html(body: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Markdown Preview</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        blockquote {{ color: gray; border-left: 4px solid #ccc; padding-left: 10px; }}
        strong {{ font-weight: bold; }}
    </style>
</head>
<body>
    {body}
</body>
</html>
"""