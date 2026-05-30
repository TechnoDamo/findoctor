"""Маршруты AI-чата: диалоги и сообщения."""

from fastapi import APIRouter, Body, Form, Query, UploadFile

from app.api.dependencies import CurrentUser, DbConnection
from app.schemas.ai_chat import (
    AiChatConversation,
    AiChatConversationCreate,
    AiChatConversationPage,
    AiChatRequest,
    AiChatResponse,
)
from app.services import ai_chat as chat_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Сообщения
# ---------------------------------------------------------------------------
@router.post("/messages", response_model=AiChatResponse)
async def create_message(
    data: AiChatRequest,
    user: CurrentUser,
    conn: DbConnection,
) -> dict:
    """Отправка текстового или аудио (base64) сообщения AI-ассистенту."""
    return await chat_service.send_message(
        conn=conn,
        user=user,
        conversation_id=data.conversation_id,
        input_parts=[p.model_dump(exclude_none=True) for p in data.input],
        title=data.title,
        response_modalities=data.response_modalities,
        audio_response=data.audio_response.model_dump(exclude_none=True) if data.audio_response else None,
        context_options=data.context.model_dump(exclude_none=True) if data.context else None,
        agentic=data.agentic,
    )


@router.post("/audio", response_model=AiChatResponse)
async def create_voice_message(
    user: CurrentUser,
    conn: DbConnection,
    audio: UploadFile,
    conversation_id: str | None = Form(None, alias="conversationId"),
    title: str | None = Form(None, max_length=200),
    prompt: str | None = Form(None),
    response_modalities: str | None = Form(None, alias="responseModalities"),
    audio_format: str | None = Form(None, alias="audioFormat"),
    audio_response_voice: str | None = Form(None, alias="audioResponseVoice"),
    audio_response_format: str | None = Form(None, alias="audioResponseFormat"),
    audio_response_delivery: str = Form("temporary_url", alias="audioResponseDelivery"),
) -> dict:
    """Отправка голосового сообщения AI-ассистенту (multipart/form-data)."""
    import base64

    audio_bytes = await audio.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return await chat_service.send_voice_message(
        conn=conn,
        user=user,
        audio_data=audio_base64,
        audio_format=audio_format or (audio.content_type.split("/")[-1] if audio.content_type else "webm"),
        conversation_id=conversation_id,
        title=title,
        prompt=prompt,
        response_modalities=response_modalities.split(
            ",") if response_modalities else None,
        voice=audio_response_voice,
        response_format=audio_response_format,
        delivery=audio_response_delivery,
    )


# ---------------------------------------------------------------------------
# Диалоги
# ---------------------------------------------------------------------------
@router.get("/conversations", response_model=AiChatConversationPage)
async def list_conversations(
    user: CurrentUser,
    conn: DbConnection,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=250),
) -> dict:
    """Список диалогов AI-чата."""
    items, total = await chat_service.list_conversations_export(conn, user["id"], page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "meta": {"page": page, "page_size": page_size, "total_items": total, "total_pages": total_pages},
    }


@router.post("/conversations", response_model=AiChatConversation, status_code=201)
async def create_conversation(
    data: AiChatConversationCreate = Body(None),
    user: CurrentUser = None,
    conn: DbConnection = None,
) -> dict:
    """Создание нового диалога."""
    title = data.title if data else None
    conversation = await chat_service.create_conversation(conn, user["id"], title)
    conversation["messages"] = []
    return conversation


@router.get("/conversations/{conversation_id}", response_model=AiChatConversation)
async def get_conversation(
    conversation_id: str,
    user: CurrentUser,
    conn: DbConnection,
) -> dict:
    """Получение диалога с сообщениями."""
    return await chat_service.get_conversation(conn, user["id"], conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    user: CurrentUser,
    conn: DbConnection,
) -> None:
    """Удаление диалога."""
    await chat_service.delete_conversation(conn, user["id"], conversation_id)
