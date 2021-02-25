from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image, ImageDraw
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person


app = Flask(__name__)
keyAT = "" 
keyDF = ""
endpoint = ""


def authenticate_client():
    ta_credential = AzureKeyCredential(keyAT)
    text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, 
            credential=ta_credential)
    return text_analytics_client


@app.route('/bot', methods=['POST'])
def bot():
    resp = MessagingResponse()
    msg = resp.message()
    if request.values.get('Body', '').lower() != '':
        #autenticação
        client = authenticate_client()
        #frases
        documents = [request.values.get('Body', '').lower()]
        #sentimento
        sentimento = client.analyze_sentiment(documents=documents)[0].sentiment
        #idioma
        idioma = client.detect_language(documents = documents, country_hint = '')[0].primary_language.name
        #configurações
        resposta = 'Sentimento: ' + sentimento + '\nIdioma: ' + idioma
        if sentimento == "positive":
            resposta = resposta + '\n\nQue bom que gostou! :)'
        elif sentimento == 'negative':
            resposta = resposta + '\n\nPrometo melhorar! :('
        else:
            resposta = resposta + '\n\nÓtimo! :)'
        msg.body(resposta)
    else:
        img_url = request.values.get('MediaUrl0')
        face_client = FaceClient(endpoint, CognitiveServicesCredentials(keyDF))
        single_face_image_url = img_url
        single_image_name = os.path.basename(single_face_image_url)
        detected_faces = face_client.face.detect_with_url(url=single_face_image_url, return_face_id=False, return_face_landmarks=False, return_face_attributes=["hair","gender","age","emotion","accessories"], recognition_model='recognition_01', return_recognition_model=False, detection_model='detection_01', custom_headers=None, raw=False)

        if not detected_faces:
            raise Exception('No face detected from image {}'.format(single_image_name))

        

        else:
            for face in detected_faces:
                cor_do_cabelo = face.face_attributes.hair.hair_color[0].color
                genero = face.face_attributes.gender
                idade_estipulada = str(face.face_attributes.age)
                emocoes = ""
                if face.face_attributes.emotion.anger > 0:
                    emocoes = "Raiva"
                if face.face_attributes.emotion.contempt > 0:
                    emocoes = emocoes + " Desprezo"
                if face.face_attributes.emotion.disgust > 0:
                    emocoes = emocoes + " Desgosto"
                if face.face_attributes.emotion.fear > 0:
                    emocoes = emocoes + " Medo"
                if face.face_attributes.emotion.happiness > 0:
                    emocoes = emocoes + " Feliz"
                if face.face_attributes.emotion.neutral > 0:
                    emocoes = emocoes + " Nêutro"
                if face.face_attributes.emotion.sadness > 0:
                    emocoes = emocoes + " Triste"
                if face.face_attributes.emotion.surprise > 0:
                    emocoes = emocoes + " Surpreso"
                acessorios = "Nenhum"
                if len(face.face_attributes.accessories) != 0:
                    acessorios = ""
                    for acessorio in face.face_attributes.accessories:
                        acessorios = acessorios + acessorio.type + "\n"
                msg.media(img_url)
                resposta = 'Cor do cabelo: ' + cor_do_cabelo + "\nGênero: " + genero + "\nIdade estipulada: " + idade_estipulada + "\nEmoções: " + emocoes + "\nAcessórios: " + acessorios
                msg.body(resposta)

    return str(resp)


if __name__ == '__main__':
   app.run()