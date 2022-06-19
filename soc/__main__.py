if __name__ == "__main__":
    import uvicorn

    uvicorn.run("soc.site:site", port=8000, log_level="debug")
