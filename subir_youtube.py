# -*- coding: utf-8 -*-
"""
Sube el video del Evangelio del Día a YouTube usando la YouTube Data API v3.

Requiere, UNA SOLA VEZ:
1) Un proyecto en Google Cloud Console con la "YouTube Data API v3" habilitada.
2) Credenciales OAuth 2.0 tipo "Desktop app", descargadas como
   client_secret.json y puestas en esta misma carpeta.
3) La primera vez que corras este script, se va a abrir el navegador para
   que autorices el acceso a tu canal (una sola vez). Después queda
   guardado un token.json local y no te va a volver a pedir nada.

Instalación:
    pip install google-auth-oauthlib google-api-python-client

Uso:
    python subir_youtube.py output/evangelio_2026-07-05.json

Sube el video como PRIVADO por defecto (para que lo revises antes de
publicarlo). Cambiá PRIVACIDAD_DEFAULT más abajo cuando quieras que sea
100% automático y público.
"""

import json
import os
import sys
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

CLIENT_SECRET_PATH = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

# "private", "unlisted" o "public". Ahora en "public": el video se publica
# directo, sin revisión manual previa.
PRIVACIDAD_DEFAULT = "public"

# Nombre EXACTO de tu playlist en YouTube (la que ya creaste)
NOMBRE_PLAYLIST = "Evangelio del Día"


def obtener_credenciales():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_PATH):
                raise RuntimeError(
                    f"No se encontró {CLIENT_SECRET_PATH}. Descargalo desde "
                    "Google Cloud Console (credenciales OAuth tipo Desktop app) "
                    "y ponelo en esta carpeta."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def buscar_o_crear_playlist(youtube, nombre_playlist):
    # Buscar entre las playlists del canal autenticado
    request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    while request is not None:
        response = request.execute()
        for item in response.get("items", []):
            if item["snippet"]["title"].strip().lower() == nombre_playlist.strip().lower():
                return item["id"]
        request = youtube.playlists().list_next(request, response)

    # No existe -> la creamos
    body = {
        "snippet": {
            "title": nombre_playlist,
            "description": "Evangelio del día, con reflexión.",
        },
        "status": {"privacyStatus": PRIVACIDAD_DEFAULT},
    }
    resp = youtube.playlists().insert(part="snippet,status", body=body).execute()
    return resp["id"]


def agregar_a_playlist(youtube, playlist_id, video_id, intentos=3):
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id},
        }
    }
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            youtube.playlistItems().insert(part="snippet", body=body).execute()
            return True
        except HttpError as e:
            ultimo_error = e
            print(f"  [aviso] Intento {intento}/{intentos} de agregar a la playlist falló: {e}")
            if intento < intentos:
                time.sleep(5)
    print(f"  [aviso] No se pudo agregar a la playlist tras {intentos} intentos. "
          f"El video ya está subido igual, agregalo a mano a la playlist si querés.")
    return False


def subir_video(video_path, metadata):
    creds = obtener_credenciales()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": metadata["titulo"],
            "description": metadata["descripcion"],
            "tags": metadata["tags"],
            "categoryId": "22",  # People & Blogs (podés ajustarlo)
        },
        "status": {
            "privacyStatus": PRIVACIDAD_DEFAULT,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Subiendo... {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"  Video subido con éxito: https://youtube.com/watch?v={video_id}")

    try:
        playlist_id = buscar_o_crear_playlist(youtube, NOMBRE_PLAYLIST)
        agregar_a_playlist(youtube, playlist_id, video_id)
    except HttpError as e:
        print(f"  [aviso] No se pudo procesar la playlist (el video ya está subido igual): {e}")

    return video_id


def main():
    if len(sys.argv) < 2:
        print("Uso: python subir_youtube.py output/evangelio_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fecha = data["fecha"]
    video_path = os.path.join(OUTPUT_DIR, f"video_{fecha}.mp4")
    metadata_path = os.path.join(OUTPUT_DIR, f"metadata_{fecha}.json")

    if not os.path.exists(video_path):
        print(f"[ERROR] No se encontró el video: {video_path}")
        sys.exit(1)
    if not os.path.exists(metadata_path):
        print(f"[ERROR] No se encontró la metadata: {metadata_path}")
        sys.exit(1)

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    try:
        video_id = subir_video(video_path, metadata)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"Subido con éxito (estado: {PRIVACIDAD_DEFAULT})")
    print(f"https://youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
