if __name__ == "__main__":
    import uvicorn

    uvicorn.run("soc.apps.site:site", host="127.0.0.1", port=8000, log_level="debug")
