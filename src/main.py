from fastapi import FastAPI
from .routes.api_router import api_router

app = FastAPI(title="Inteligencia Juridica API")
app.include_router(api_router)


def lambda_handler(event, context):  
    from mangum import Mangum
    handler = Mangum(app)
    return handler(event, context)
