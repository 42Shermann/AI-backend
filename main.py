from typing import Optional
from tempfile import NamedTemporaryFile
import base64
import datetime

from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
import cv2

from detection_and_crop import get_cropped_img, get_cropped_eye

app = FastAPI()
getTime = datetime.datetime.now()

imgUrl = None

class Item(BaseModel):
    url: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/")
async def root():
    return {"message": "Hi Mom"}    
 
@app.post("/api/uploadfile/")
async def create_upload_file(file: UploadFile):
    print("{} :File recived".format(getTime))
    contents = await file.read()
    with NamedTemporaryFile(suffix='.mp4', delete=False) as file_copy:
        try:
            cropped_img = None
            file_copy.write(contents);  # copy the received file data into a new temp file. 
            file_copy.seek(0)  # move to the beginning of the file
            print("{} :Begin extracting frames from video".format(getTime))
            cropped_img = await get_cropped_eye(str(file_copy.name))
            
            if cropped_img is None:
                print("{} :Extraction Error.".format(getTime))
                raise HTTPException(status_code=500, detail="Unable to extract image.")
            else:
                print("{} :Image extracted successfully".format(getTime))
                _, encoded_img = cv2.imencode('.jpg', cropped_img)
                encoded_img = base64.b64encode(encoded_img)
                print("{} :Image is encoded and ready to send".format(getTime))

        finally:
            file_copy.close()  # Remember to close any file instances before removing the temp file
    
    return {
        'filename': file.filename,
        'encoded_img': encoded_img,
    }

@app.get("/getCDN/")
async def get_cdn_data():
    data = {
        "url": "https://api.cloudinary.com/v1_1/dyfbbcvhc/upload",
        "upload_preset":"bxn5qztj",
        "cloud_preset":"dyfbbcvhc"
        }    
    return data    

@app.post("/getCropImg/")
async def create_item(item: Item):
    imgUrl = get_cropped_img(item.url)
    if imgUrl is None:
        raise HTTPException(status_code=404, detail="Could not process the input video.")
    return {"url": imgUrl}
     