from fastapi import FastAPI


api_app = FastAPI()


@api_app.get("/")
async def hello():
    return {"message": "Hello World!"}
