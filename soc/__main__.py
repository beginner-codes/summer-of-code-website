if __name__ == "__main__":
    import uvicorn
    import yaml

    try:
        file = open("development.config.yaml")
    except FileNotFoundError:
        config = {}
    else:
        with file:
            config = yaml.safe_load(file)

    site = config.get("site", {})
    app = site.get("app", "soc.apps.site:site")
    host = site.get("host", "0.0.0.0")
    port = site.get("port", 8000)
    log_level = site.get("log_level", "debug")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
