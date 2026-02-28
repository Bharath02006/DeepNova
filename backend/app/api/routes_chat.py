from fastapi import APIRouter, File, UploadFile

from app.models.schemas import (
    AutofixRequest,
    AutofixResponse,
    ChatRequest,
    ChatResponse,
    ExtractCodeResponse,
)
from app.services import ai_service


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    reply = await ai_service.chat_with_ai(payload)
    return ChatResponse(messages=[*payload.messages, reply])


@router.post("/autofix", response_model=AutofixResponse)
async def autofix(payload: AutofixRequest) -> AutofixResponse:
    result = await ai_service.autofix_code(payload.code)
    return AutofixResponse(**result)


@router.post("/extract-code", response_model=ExtractCodeResponse)
async def extract_code(image: UploadFile = File(...)) -> ExtractCodeResponse:
    # Frontend runs OCR (Tesseract.js). Backend only formats a placeholder.
    filename = image.filename
    formatted = (
        "```text\n"
        "[OCR happens in the frontend via Tesseract.js]\n"
        f"uploaded_file: {filename}\n"
        "extracted_code: <placeholder>\n"
        "```\n"
    )
    return ExtractCodeResponse(
        formatted_code=formatted,
        filename=filename,
        note="Backend returns placeholder formatting only. Run OCR in frontend.",
    )

