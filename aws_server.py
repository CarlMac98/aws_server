import boto3
import logging
import time
import requests
import settings as s

#enable console logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

#initialize s3, transcribe server and comprehend clients
s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')
comp = boto3.client('comprehend')
translate = boto3.client('translate')


#auxiliary function for s3 bucket selection
def select_bucket():
    resp = s3.list_buckets()

    
    print("\nHere's a list of buckets for you: \n")
    i = 0 
    buckets = [bucket['Name'] for bucket in resp['Buckets']]
    for x in buckets:
        print("  " + str(i) + "--> " + x + "\n") 
        i += 1
    print("  " + str(i) + "--> exit\n" )
    print("\nWhich one do you want? Type corresponding number\n")
    while True:
            sel = input()
            if int(sel) < i:
                bucketname = buckets[int(sel)]
                return bucketname
                break
            elif int(sel) == i:
                return False
                break
            else:
                print("C'mon, it's just a number. I believe in you\n")
    

#auxiliary function to select a file in an s3 bucket 
def select_file(bucketname, ret):
    #bucketname = select_bucket()
    resp = s3.list_objects(Bucket = bucketname)    

    if "Contents" in str(resp):    
        objects = [obj['Key'] for obj in resp['Contents']]
        i = 0
        for x in objects:
            print("  " + str(i) + "--> " + x + "\n") 
            i += 1
        
        
        if ret == True:
            print("  " + str(i) + "--> exit\n" )
            while True:
                print("\nWhich one do you want? Type corresponding number\n")
                sel = input()
                if int(sel) < i:
                    filename = objects[int(sel)]
                    return filename
                    break
                elif int(sel) == i:
                    return "-1"
                    break
                else:
                    print("C'mon, it's just a number. I believe in you\n")
                
            
    else:
        print("This is an empty bucket\n")
        return False

#conversion of an audio file via lambda function    
def convert(src):
    print("\nInput the destination name (Don't forget the desired format!)\n")
    dst = input()
    dst_format = dst.split(".")[1]

    src_ext = dst_format + "." + src #escamotage to pass the desired format of conversion to lambda function
    #if dst_format == "mp3":
    bucketname = s.TRIGGER #the s3 bucket with the trigger to lambda function
    s3.upload_file(src, bucketname, src_ext)

    converted = False
    name = src.split(".")[0] + "." + dst_format 

    while converted != True:
        resp = s3.list_objects(Bucket = s.OUTPUT)
        objects = [obj['Key'] for obj in resp['Contents']]

        print("Wait: our system is converting the file for you, but it could take a while!")
        for x in objects:
            if x == name:
                converted = True
        time.sleep(5)

    s3.download_file(s.OUTPUT, name, dst) #the converted file is downloaded
    print("Your file has been converted and downloaded!")
    s3.delete_object(Bucket = bucketname, Key = src_ext) #the file initially uploaded is deleted from bucket    
   

#transcribe an audio in text
def gettext(filename):
    bucketname = s.TRANSCRIBE
    upload(filename, bucketname)
    job_name = "job_name"
    job_uri = "s3://" + bucketname + "/" +filename
    check = transcribe.list_transcription_jobs()

    if check['TranscriptionJobSummaries'] != []:
        try:
            transcribe.delete_transcription_job(TranscriptionJobName = job_name)
        except BadRequestException:
            pass
        
    print("There are several supported languages for this service: choose the one you need by typing the corrisponding number!\n"
          "  1. English\n  2. Italian\n  3. French\n  4. Spanish\n  5. German\n")
    lang = input()
    while True:
        if lang == "1":
            lcode = 'en-US'
            break
        elif lang == "2":
            lcode = 'it-IT'
            break
        elif lang == "3":
            lcode = 'fr-FR'
            break
        elif lang == "4":
            lcode = 'es-ES'
            break
        elif lang == "5":
            lcode = 'de-DE'
            break
        else:
            print("C'mon, it's just a number. I believe in you\n")
            lang = input()
            continue
            
    transcribe.start_transcription_job(
        TranscriptionJobName= job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat= filename.split(".")[1],
        LanguageCode = lcode
    )

    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        print("Not ready yet...")
        time.sleep(5)
    
    url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
    myfile = requests.get(url)
    text = (str(myfile.content).split('"transcript":')[1]).split('}],"items"')[0]
    
    open(r'C:\Users\Utente\Desktop\Karl\Uni\Tirocinio\Python\transcribed.json', 'wb').write(myfile.content)
    print("\nHere's the transcribed text from the audio " + filename + ":\n\n" + text)
    

    print("\nIf you could wait just a second, we can guess the general sentiment of the text (Really!)\n" )
    lg = lcode.split("-")[0]
    response = comp.detect_sentiment(
        LanguageCode= lg,
        Text=text)
    print("Your text seems to have a rather " + str(response['Sentiment'])+ " sentiment.\n\n"
          "Here follows the scores we obtained:\n" + str(response['SentimentScore']))

    try:
        transcribe.delete_transcription_job(TranscriptionJobName = job_name)
    except BadRequestException:
        pass

    print("Do you want to translate your text in another language? (Y/N)")
    yn = input()
    if yn == ("y" or "Y"):
        gettranslation(text, lg)
    else:
        print("Ok then! My job here is done")

#translate a text in another language
def gettranslation(text):
    print("\nWhich is the language of the text?\n"
          "  1. English\n  2. Italian\n  3. French\n  4. Spanish\n  5. German\n")
    lang = input()
    while True:
        if lang == "1":
            lg = 'en'
            break
        elif lang == "2":
            lg = 'it'
            break
        elif lang == "3":
            lg = 'fr'
            break
        elif lang == "4":
            lg = 'es'
            break
        elif lang == "5":
            lg = 'de'
            break
        else:
            print("C'mon, it's just a number. I believe in you\n")
            lang = input()
            continue

    
    print("\nIn which language do you want to translate it?\n"
          "  1. English\n  2. Italian\n  3. French\n  4. Spanish\n  5. German\n")
    lang = input()
    while True:
        if lang == "1":
            lcode = 'en'
            break
        elif lang == "2":
            lcode = 'it'
            break
        elif lang == "3":
            lcode = 'fr'
            break
        elif lang == "4":
            lcode = 'es'
            break
        elif lang == "5":
            lcode = 'de'
            break
        else:
            print("C'mon, it's just a number. I believe in you\n")
            lang = input()
            continue


    result = translate.translate_text(Text=text, 
            SourceLanguageCode=lg, TargetLanguageCode=lcode)
    print('TranslatedText: ' + result.get('TranslatedText'))
    #print('SourceLanguageCode: ' + result.get('SourceLanguageCode'))
    #print('TargetLanguageCode: ' + result.get('TargetLanguageCode'))
    

#upload a file to an s3 bucket
def upload(filename, bucketname):
    s3.upload_file(filename, bucketname, filename)
    print("File uploaded! (" + filename +" in bucket " + bucketname + ")")

#download a certain file
def download():
    print("Select the bucket from which you want to download stuff\n")
    bucketname = select_bucket()
    if bucketname != False:
        print("Now select the file\n")
        filename = select_file(bucketname, True)
        if filename != False and filename != "-1":
            print("Do you want to assign a new name to the file? (Y/N)\n")
            yn = input()
            
            while True:
                if yn == ("y" or "Y"):
                    ext = filename.split(".")[1]
                    print("\nGive me a new name then: ")
                    newname = input() + "." + ext
                    break
                elif yn == ("n" or "N"):
                    newname = filename
                    break
                else:
                    print("Invalid input; type 'Y' or 'N'\n")
                    yn = input()
                    continue
            s3.download_file(bucketname, filename, newname)
            print("file " + filename + "downloaded as " + newname + "from " + bucketname)
        elif filename == "-1":
            print("Ok, not a good time for downloads...")
        else:
            print("No file to download here. Sorry")
    else:
        print("Ok, not a good time for downloads...")

        
    

#read the content of a bucket
def read():
    print("Select the bucket to read\n")
    bucketname = select_bucket()
    if bucketname != False:
        print("Here are the files in this bucket\n")
        filename = select_file(bucketname, False)
    else:
        print("Ok")
    

#instructions of this server
def help():
    print("Here's a list of avilable functions:\n\n"
          +"--> upload(): this function uploads a file on a s3 bucket;\n\n"+
          "--> download(): download one of the available files from a bucket\n\n"+
          "--> convert(): convert an audio file in another format;\n"+
          "    When you will be asked to specify a destination name, please don't forget to include the desired format!\n" +
          "    (e.g.: if you want a file to be named 'sample' and to be in mp3 format, type 'sample.mp3'\n\n"+
          "--> read(): read the content of a bucket\n\n"+
          "--> gettext(): get the transcription of specified audio file\n\n"
          "--> translate(): get the translation of a text file in another language")

    
def main():
    print("Hello folks! This is a tool for audio conversion/transcription/translation\n" +
          "For further information read the README file or type 'help()'")
    while True:
        sel = input()
        if sel == "help()":
            help()
        elif sel == "read()":
            read()
        elif sel == "download()":
            download()
        elif sel == "upload()":
            print("Select a file to upload")
            file = input()
            print("Now select a Bucket")
            bck = select_bucket()
            while True:
                if bck == s.TRIGGER or s.TRANSCRIBE:
                    print("Permission denied to upload here")
                else:
                    upload(file, bck)
                    break                
        elif sel == "convert()":
            print("Select a file to convert")
            file = input()
            convert(file)
        elif sel == "gettext()":
            print("Select a file to transcribe")
            while True:
                file = input()
                if file.split(".")[1] in {"flac", "mp3", "wav", "mp4"}:
                    gettext(file)
                    break
                else:
                    print("This format is not supported; choose a file in one of the following:\n"
                          "-mp3\n-mp4\n-wav\n-flac\n")
            
        elif sel == "translate()":
            print("Trascribe from file? (Y/N)")
            yn = input()
            while True:
                if yn == ("y" or "Y"):
                    print("Select a file to translate")
                    file = input()
                    text = open(file, "r")
                    tx = text.read()
                    gettranslation(tx)
                    text.close()
                    break
                elif yn == ("n" or "N"):
                    print("Then write the text to convert")
                    text = input()
                    gettranslation(text)
                    break
                else:
                    print("Invalid input; type 'Y' or 'N'\n")
                    yn = input()
                    
            
        elif sel == "exit()":
            exit()
        else:
            print("There's no function with that name, man. If you need help type 'help()'")
        
if __name__ == "__main__":
    main()
