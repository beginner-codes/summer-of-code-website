if __name__ == "__main__":
    import uvicorn

    uvicorn.run("soc.site:site", host="0.0.0.0", port=8000, log_level="debug")
