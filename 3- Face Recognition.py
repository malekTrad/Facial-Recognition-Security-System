''''
Real Time Face Recogition
	==> Each face stored on dataset/ dir, should have a unique numeric integer ID as 1, 2, 3, etc                       
	==> LBPH computed model (trained faces) should be on trainer/ dir
'''

import cv2
import numpy as np
import os 
import winsound
from datetime import datetime
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twilio.rest import Client

#setting twilio from twilio account 
account_sid = 'your_account_sid'
auth_token = 'your_account_auth_token'
client = Client(account_sid, auth_token)

#setting LBPH and HAAR (viola and jones) alogorithms 
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

font = cv2.FONT_HERSHEY_SIMPLEX

#iniciate counters
id = 0
count = 0

# names related to ids: example ==> LINDA: id=1,  etc
names = ['None', 'LINDA', 'CARMEN'] 

# Initialize and start realtime video capture
cam = cv2.VideoCapture('video/usersF.mkv')
cam.set(3, 640) # set video widht
cam.set(4, 480) # set video height

# Define min window size to be recognized as a face
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)
nowT=''
now =''

while True:

    ret, img =cam.read()
    img = cv2.flip(img, 1) # Flip vertically

    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale( 
        gray,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
       )

    for(x,y,w,h) in faces:
        id, confidence = recognizer.predict(gray[y:y+h,x:x+w])

        # Check if confidence is less them 100 ==> "0" is perfect match 
        if (confidence < 45):
            winsound.PlaySound(None, winsound.SND_PURGE)
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            id = names[id]
            confidence = "  {0}%".format(round(100 - confidence + 9))
        else:
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,0,255), 2)
            id = "NOT AUTHORIZED"
            confidence = "  {0}%".format(round(100 - confidence - 30))

             # Save the captured image from the non authorized into a folder
            count += 1
            if count == 1:
                winsound.PlaySound('Sound.wav',winsound.SND_ASYNC)
                nowT = datetime.now()
                cv2.imwrite("notAuthorized/notAuth." + str(nowT.strftime("%d%m%y,%H%M%S")) +  ".jpg", img)

            #create a dataset of the unauthorized person
            now = datetime.now()
            nowStr = now.strftime("%d%m%y,%H%M%S")
            cv2.imwrite("notAuthorizedFaces/notAuth." + str(nowStr)  + ".jpg", gray[y:y+h,x:x+w])
        
        cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  
    
    cv2.imshow('vid',img) 

    #if the video ends the program stop
    if cam.get(cv2.CAP_PROP_POS_FRAMES) == cam.get(cv2.CAP_PROP_FRAME_COUNT):
            winsound.PlaySound(None, winsound.SND_PURGE)
            cv2.destroyAllWindows()
            # If the number of captured frames is equal to the total number of frames,
            # we stop
            break

    k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        winsound.PlaySound(None, winsound.SND_PURGE)
        cv2.destroyAllWindows()
        break

#send an email 
if count>1 :
    subject = "Car alert" +" at " + str(nowT.strftime("%d-%m-%Y %H:%M:%S"))
    body = """\
    Unauthorized driver got into your car """+ "at " + str(nowT.strftime("%d-%m-%Y %H:%M:%S")) +"""
    An image of the unauthorized driver is attached to this email.
    If you like to add this driver to the green list y can find a dataset ready for use in the folder: notAuthorizedFaces.
    """
    sender_email = "e-mail_of_the_system"
    receiver_email = "e-mail_of_the_system_owner"
    password = 'password_of_sender_email'

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = 'Secured Car System'
    message["To"] = receiver_email
    message["Subject"] = subject
    #message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    filename = "notAuthorized/notAuth." + str(nowT.strftime("%d%m%y,%H%M%S")) +  ".jpg"  # the file with the last datetime

    # Open image file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
        print ('Email Sent')

    #send sms using twilio
    message = client.messages \
                    .create(
                        body="Unauthorized person got into your car",
                        from_='twilio_phone_number',
                        to='the_owner_of_the_system_number'
                    )

    # #make a phone call using twilio
    print(message.sid)
    call = client.calls.create(
                        twiml='<Response><Say>attention  unauthorized person got into your car</Say></Response>',
                        to='the_owner_of_the_system_number',
                        from_='twilio_phone_number'
                    )

    print(call.sid)
        
# Do a bit of cleanup
print("\n [INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()





