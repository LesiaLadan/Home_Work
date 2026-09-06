from django.db import connection
from django.db.utils import Error as DatabaseError
from django.http import JsonResponse


def health_check(request):
    try:
        connection.ensure_connection()
        database_ok = True
    except DatabaseError:
        database_ok = False

    payload = {
        "status": "ok" if database_ok else "error",
        "database": database_ok,
    }
    return JsonResponse(payload, status=200 if database_ok else 503)
