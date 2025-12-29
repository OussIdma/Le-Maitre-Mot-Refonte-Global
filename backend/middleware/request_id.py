"""
Middleware pour générer et propager un request_id unique par requête
"""

import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.logger import get_logger

logger = get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui génère un request_id unique pour chaque requête
    et le propage dans les headers de réponse et les logs.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Récupérer ou générer le request_id
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Ajouter le request_id au state de la requête pour usage dans les routes
        request.state.request_id = request_id
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        try:
            # Appeler le handler suivant
            response = await call_next(request)
            
            # Calculer la durée
            duration = time.time() - start_time
            
            # Ajouter le request_id dans les headers de réponse
            response.headers["X-Request-Id"] = request_id
            
            # Logger la requête (seulement pour les routes API critiques)
            path = request.url.path
            if self._should_log(path):
                logger.info(
                    f"[REQUEST] method={request.method} path={path} "
                    f"status={response.status_code} duration={duration:.3f}s "
                    f"request_id={request_id}"
                )
            
            return response
            
        except Exception as e:
            # En cas d'exception, logger avec le request_id
            duration = time.time() - start_time
            path = request.url.path
            if self._should_log(path):
                logger.error(
                    f"[REQUEST_ERROR] method={request.method} path={path} "
                    f"duration={duration:.3f}s request_id={request_id} error={str(e)}",
                    exc_info=True
                )
            raise
    
    def _should_log(self, path: str) -> bool:
        """
        Détermine si cette route doit être loggée.
        On log seulement les routes critiques : /api/generate, /api/admin/*, /api/export*
        """
        if path.startswith("/api/generate"):
            return True
        if path.startswith("/api/admin/"):
            return True
        if path.startswith("/api/export"):
            return True
        if path.startswith("/api/v1/exercises/generate"):
            return True
        return False

