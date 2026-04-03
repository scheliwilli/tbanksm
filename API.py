from fastapi import FastAPI


app = FastAPI()

@app.GET("/")
def get_path_list():
    return path_list

@app.PUT("/")
