def main() -> None:
    import uvicorn

    uvicorn.run("mnemosyne.app:app", host="127.0.0.1", port=8000)


def dev() -> None:
    import uvicorn

    uvicorn.run("mnemosyne.app:app", host="127.0.0.1", port=8000, reload=True)
