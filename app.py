"""Run the full NSS Word Master app: `python app.py` or `uvicorn backend.main:app --reload`."""

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
