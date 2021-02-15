from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def read_root():
    return "hello world"


if __name__ == "__main__":
    uvicorn.run(app)
