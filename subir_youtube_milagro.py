# -*- coding: utf-8 -*-
"""
Sube el video del Jueves Eucarístico (Milagro Eucarístico) a YouTube usando la YouTube Data API v3.

Reutiliza las MISMAS credenciales de Google que el Evangelio y el Santo
(client_secret.json / token.json en la raíz). Mismo canal, distinta playlist.

Uso:
    python subir_youtube_milagro.py output_milagro/milagro_2026-08-06.json
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
CLIENT_SECRET_PATH = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

PRIVACIDAD_DEFAULT = "public"
NOMBRE_PLAYLIST = "Jueves Eucarístico"


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
                    "Google Cloud Console (OAuth Desktop app) y ponelo aquí.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def buscar_o_crear_playlist(youtube, nombre):
    request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    while request is not None:
        response = request.execute()
        for item in response.get("items", []):
            if item["snippet"]["title"].strip().lower() == nombre.strip().lower():
                return item["id"]
        request = youtube.playlists().list_next(request, response)
    body = {
        "snippet": {"title": nombre, "description": "Milagros Eucarísticos reconocidos por la Iglesia, cada jueves."},
        "status": {"privacyStatus": PRIVACIDAD_DEFAULT},
    }
    resp = youtube.playlists().insert(part="snippet,status", body=body).execute()
    return resp["id"]


def agregar_a_playlist(youtube, playlist_id, video_id, intentos=3):
    body = {"snippet": {"playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
    for intento in range(1, intentos + 1):
        try:
            youtube.playlistItems().insert(part="snippet", body=body).execute()
            return True
        except HttpError as e:
            print(f"  [aviso] Intento {intento}/{intentos} falló: {e}")
            if intento < intentos:
                time.sleep(5)
    print("  [aviso] No se pudo agregar a la playlist; el video ya está subido igual.")
    return False


def ya_existe_video(youtube, titulo):
    """Revisa si YA existe un video con este título exacto en el canal.
    Evita subir dos veces el mismo video si el workflow corre dos veces el
    mismo día (reintento de GitHub, Run workflow manual, etc.)."""
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
        print(f"  [aviso] No se pudo verificar duplicados ({e}); se continúa.")
    return False


def subir_video(video_path, titulo, descripcion, tags):
    creds = obtener_credenciales()
    youtube = build("youtube", "v3", credentials=creds)

    # PROTECCIÓN ANTI-DUPLICADOS: si ya existe un video con este título,
    # no se sube de nuevo.
    if ya_existe_video(youtube, titulo):
        print(f"  ⚠️  YA EXISTE un video con el título '{titulo}'. No se sube de nuevo.")
        return None

    body = {
        "snippet": {"title": titulo, "description": descripcion,
                    "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": PRIVACIDAD_DEFAULT, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Subiendo... {int(status.progress() * 100)}%")
    video_id = response["id"]
    print(f"  Video subido: https://youtube.com/watch?v={video_id}")
    try:
        playlist_id = buscar_o_crear_playlist(youtube, NOMBRE_PLAYLIST)
        agregar_a_playlist(youtube, playlist_id, video_id)
    except HttpError as e:
        print(f"  [aviso] No se pudo procesar la playlist: {e}")
    return video_id


def main():
    if len(sys.argv) < 2:
        print("Uso: python subir_youtube_salmo.py output_milagro/milagro_<fecha>.json")
        sys.exit(1)
    json_path = sys.argv[1]
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    video_path = data.get("_video_path")
    if not video_path or not os.path.exists(video_path):
        print(f"[ERROR] No se encontró el video (_video_path: {video_path}). "
              f"¿Corriste generar_video_salmo.py?")
        sys.exit(1)
    for campo in ("titulo", "descripcion", "tags"):
        if campo not in data:
            print(f"[ERROR] Falta '{campo}'. ¿Corriste generar_metadata_salmo.py?")
            sys.exit(1)

    try:
        video_id = subir_video(video_path, data["titulo"], data["descripcion"], data["tags"])
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if video_id is None:
        print("No se subió nada (ya existía un video con ese título hoy).")
        sys.exit(0)

    print(f"Subido con éxito (estado: {PRIVACIDAD_DEFAULT})")
    print(f"https://youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
