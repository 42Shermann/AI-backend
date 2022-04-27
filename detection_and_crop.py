import numpy as np
import cv2
from tempfile import NamedTemporaryFile
import cloudinary
import cloudinary.uploader
import cloudinary.api
from decouple import config


cloudinary.config( 
  cloud_name = config('cloud_name'), 
  api_key = config('api_key'), 
  api_secret = config('api_secret')
)

# multiple cascades: https://github.com/Itseez/opencv/tree/master/data/haarcascades

#https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
#https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_eye.xml
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')    

def detect_face(image):
    gray_picture = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)#make picture gray
    faces = face_cascade.detectMultiScale(gray_picture, 1.3, 5)
    face = None
    for (x,y,w,h) in faces:
        face = image[y:y+h, x:x+w] # cut the face frame out
        return face


def detect_eye(image):
    height = np.size(image, 0) # get face frame height
    width = np.size(image, 1) # get face frame height
    gray_face = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)#make picture gray
    eyes = eye_cascade.detectMultiScale(gray_face, 1.3, 5)
    left_eye = None
    for (ex,ey,ew,eh) in eyes:
        if ey+eh > height/2: # pass if the eye is at the bottom
            pass
        eyecenter = ex + ew / 2  # get the eye center
        if eyecenter < width * 0.5:
            left_eye = image[ey:ey + eh, ex:ex + ew]
            return left_eye 
        else:
            pass  


#For upload directly to the server without using third-party services 
async def get_cropped_eye(vid_file):
    vidcap = cv2.VideoCapture(vid_file)
    success,image = vidcap.read()
    count = 0
    while success:
        cropped_face = detect_face(image)
        if cropped_face is not None:
            cropped_eye = detect_eye(cropped_face)
            if cropped_eye is not None:
                cropped_height = np.size(cropped_eye, 0)
                if cropped_height > 100:
                    if count == 64:
                        return cropped_eye
                    success,image = vidcap.read()
                    count += 1
                else:
                    success,image = vidcap.read()
            else:
                success,image = vidcap.read()        
        else:
            success,image = vidcap.read()


#For using with Cloudninary
def get_cropped_img(vid_url):
    vidcap = cv2.VideoCapture(vid_url)
    success,image = vidcap.read()
    img_url = None
    count = 0
    while success:
        cropped_face = detect_face(image)
        if cropped_face is not None:
            cropped_eye = detect_eye(cropped_face)
            if cropped_eye is not None:
                cropped_height = np.size(cropped_eye, 0)
                if cropped_height > 100:
                    if count == 64:
                        with NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                            cv2.imwrite(str(temp.name),cropped_eye)
                            print('Begin uploading') 
                            upload_response = cloudinary.uploader.upload(str(temp.name))
                            img_url = upload_response['secure_url']
                            print('Upload completed')
                            print(upload_response['secure_url'])
                            break
                    success,image = vidcap.read()
                    count += 1
                else:
                    success,image = vidcap.read()
            else:
                success,image = vidcap.read()        
        else:
            success,image = vidcap.read()
    fileName = vid_url.split('/')
    public_id = fileName[7].split('.')[0]
    cloudinary.uploader.destroy(public_id, resource_type = 'video')
    print('File deleted')
    return img_url