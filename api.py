from fastapi import FastAPI, File, UploadFile
import pandas as pd
import uvicorn
from io import BytesIO

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    file_extension = file.filename.split(".")[-1]

    if file_extension == "csv":
        df = pd.read_csv(BytesIO(contents))
    elif file_extension in ["xls", "xlsx"]:
        df = pd.read_excel(BytesIO(contents))
    else:
        return {"error": "Formato de arquivo não suportado"}

    return {"columns": df.columns.tolist(), "data": df.head().to_dict(orient="records")}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
