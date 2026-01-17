import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from prompt_butler.routers import groups, prompts, tags
from prompt_butler.services.storage import PromptNotFoundError, StorageError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting Prompt Butler API...')
    yield
    logger.info('Shutting down Prompt Butler API...')


app = FastAPI(
    title='Prompt Butler API',
    description='API for managing AI prompts with markdown frontmatter storage',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:5173', 'http://127.0.0.1:3000', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(prompts.router)
app.include_router(tags.router)
app.include_router(groups.router)


@app.exception_handler(PromptNotFoundError)
async def prompt_not_found_handler(request, exc: PromptNotFoundError):
    return JSONResponse(status_code=404, content={'detail': str(exc) or 'Prompt not found'})


@app.exception_handler(StorageError)
async def storage_error_handler(request, exc: StorageError):
    return JSONResponse(status_code=500, content={'detail': str(exc) or 'Storage operation failed'})


@app.get('/')
async def root():
    return {'status': 'healthy', 'service': 'Prompt Butler API', 'version': '1.0.0'}


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': 'Prompt Butler API'}


if __name__ == '__main__':
    import uvicorn

    host = os.getenv('HOST', '0.0.0.0')
    port_str = os.getenv('PORT', '8000')
    try:
        port = int(port_str)
    except ValueError as exc:
        raise ValueError(f'Invalid PORT value: {port_str!r}') from exc

    uvicorn.run('prompt_butler.main:app', host=host, port=port, reload=True, log_level='info')
