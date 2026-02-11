from fastapi import APIRouter

router = APIRouter()

# Placeholder for auth routes
@router.post("/login")
async def login():
    return {"token": "msg_not_implemented_yet"}
