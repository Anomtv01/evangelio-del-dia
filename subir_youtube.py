# -*- coding: utf-8 -*-
"""
Sube el video del Evangelio del Día a YouTube usando la YouTube Data API v3.

PROTECCIÓN ANTI-DUPLICADOS: antes de subir, revisa si ya existe un video
con el mismo título en el canal. Si existe, no sube de nuevo (evita dos
videos el mismo día si el workflow corre dos veces).

Uso:
    python subir_youtube.py output/evangelio_2026-07-05.json
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

PRIVACIDAD_DEFAULT = "public"
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


def ya_existe_video(youtube, titulo):
    """Revisa si YA existe un video con este título exacto en el canal.
    Evita subir dos veces el mismo video el mismo día."""
    try:
        canal = youtube.channels().list(part="contentDetails", mine=True).execute()
        uploads_id = canal["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        resp = youtube.playlistItems().list(
            part="snippet", playlistId=uploads_id, maxResults=50
        ).execute()
        titulo_norm = titulo.strip().lower()
        for item in resp.get("items", []):
            if item["snippet"]["title"].strip().lower() == titulo_norm:
                return True
    except Exception as e:
        print(f"  [aviso] No se pudo verificar duplicados ({e}); se continua.")
    return False


def buscar_o_crear_playlist(youtube, nombre_playlist):
    request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    while request is not None:
        response = request.execute()
        for item in response.get("items", []):
            if item["snippet"]["title"].strip().lower() == nombre_playlist.strip().lower():
                return item["id"]
        request = youtube.playlists().list_next(request, response)

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
    for intento in range(1, intentos + 1):
        try:
            youtube.playlistItems().insert(part="snippet", body=body).execute()
            return True
        except HttpError as e:
            print(f"  [aviso] Intento {intento}/{intentos} de agregar a la playlist falló: {e}")
            if intento < intentos:
                time.sleep(5)
    print(f"  [aviso] No se pudo agregar a la playlist tras {intentos} intentos. "
          f"El video ya está subido igual.")
    return False


def subir_video(video_path, metadata):
    creds = obtener_credenciales()
    youtube = build("youtube", "v3", credentials=creds)

    # PROTECCION ANTI-DUPLICADOS
    if ya_existe_video(youtube, metadata["titulo"]):
        print(f"  [!] YA EXISTE un video con el titulo '{metadata['titulo']}'. "
              f"No se sube de nuevo.")
        return None

    body = {
        "snippet": {
            "title": metadata["titulo"],
            "description": metadata["descripcion"],
            "tags": metadata["tags"],
            "categoryId": "22",
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
        print(f"  [aviso] No se pudo procesar la playlist: {e}")

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

    if video_id is None:
        print("No se subio nada (ya existia un video con ese titulo hoy).")
        sys.exit(0)

    print(f"Subido con éxito (estado: {PRIVACIDAD_DEFAULT})")
    print(f"https://youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
