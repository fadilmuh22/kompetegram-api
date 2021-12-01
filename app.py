import os
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse
from fastapi.openapi.utils import get_openapi

load_dotenv()
app = FastAPI()
client = AsyncIOMotorClient(os.environ["MONGODB_URL"])
collection = client.kompetegram_publicdb.fakultas_prodi


class ProdiModel(BaseModel):
    kode: str = Field(...)
    prodi: str = Field(...)
    fakultas: str = Field(...)


class ErrorModel():
    def __init__(self, status="404", title="Tidak ditemukan", detail="Kode prodi tidak ditemukan") -> None:
        self.status = status
        self.title = title
        self.detail = detail


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url='/docs')


async def fakultas_prodi(nama_fakultas):
    cursor = collection.find({'fakultas': nama_fakultas}, {
        'kode': 1, 'prodi': 1, '_id': 0})

    # if cursor.count() == 0:
    #     return None

    list_prodi = []
    for prodi in await cursor.to_list(None):
        data = {'kodeProdi': prodi['kode'], 'namaProdi': prodi['prodi']}
        print(prodi)
        list_prodi.append(data)

    return list_prodi


@app.get(
    "/fakultas-prodi", response_description="List atau daftar seluruh fakultas atau kampus daerah dan prod"
)
async def all_fakultas_prodi():
    base = {"universitas": "Universitas Pendidikan Indonesia"}
    cursor = await collection.distinct('fakultas')
    list_fakultas = []

    for f in cursor:
        list_fakultas.append({'namaFakultas': f, 'listProdi': await fakultas_prodi(f)})

    base['listFakultas'] = list_fakultas
    return {
        "data": base
    }


@app.get(
    "/fakultas", response_description="List atau daftar seluruh fakultas atau kampus daerah"
)
async def all_fakultas():
    cursor = await collection.distinct('fakultas')
    list_fakultas = []

    for f in cursor:
        list_fakultas.append({'namaFakultas': f})

    return {
        "data": list_fakultas
    }


@app.get(
    "/{namaFakultas}/prodi", response_description="List atau daftar seluruh fakultas atau kampus daerah"
)
async def all_fakultas(namaFakultas: str):
    if (fakultas := await collection.find_one({'fakultas': namaFakultas}, {'_id': 0})) is not None:
        return {"data": {'namaFakultas': fakultas['fakultas'], 'listProdi': await fakultas_prodi(fakultas['fakultas'])}}

    return {"errors": [vars(ErrorModel())]}


@app.get(
    "/prodi", response_description="List atau daftar berisi seluruh program studi"
)
async def prodi():
    prodis = await collection.find({}, {'_id': 0}).to_list(None)

    return {"data": prodis}


@app.get(
    "/prodi/{kodeProdi}", response_description="Program studi secara spesifik sesuai kode prodi"
)
async def single_prodi(kodeProdi: str):
    if (prodi := await collection.find_one({"kode": kodeProdi}, {'_id': 0})) is not None:
        return {"data": prodi}

    return {"errors": [vars(ErrorModel())]}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5049, reload=True)
