from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Group, User, Topic, GroupResource, GroupMessage
from schemas import GroupCreate, GroupResponse, GroupResourceCreate, GroupMessageCreate, GroupMessageResponse
from dependencies import get_current_user
from websocket_manager import manager
from auth import decode_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.post("/create", response_model=GroupResponse)
def create_group(
        group_data: GroupCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    print(group_data)
    topic = db.query(Topic).filter(Topic.id == group_data.topic_id).first()
    print(topic)
    # if not topic:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Topic not found",
    #     )

    new_group = Group(
        title=group_data.title,
        description=group_data.description,
        topic_id=group_data.topic_id,
        created_by=current_user.id,
    )
    new_group.members.append(current_user)

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return GroupResponse.model_validate(new_group)


@router.get("", response_model=list[GroupResponse])
def list_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    arr = []
    for i in groups:
        try:
            x = GroupResponse.model_validate(i)
            arr.append(x)
        except:
            continue
    return arr


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return GroupResponse.model_validate(group)


@router.post("/{group_id}/join")
def join_group(
        group_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    print(group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if current_user in group.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this group",
        )

    group.members.append(current_user)
    db.commit()
    db.refresh(group)

    return GroupResponse.model_validate(group)


@router.post("/{group_id}/leave")
def leave_group(
        group_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    print(group_id)
    print(group)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if current_user not in group.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a member of this group",
        )

    group.members.remove(current_user)
    db.commit()
    db.refresh(group)

    return {"message": "Left group successfully"}


@router.post("/{group_id}/resources", response_model=dict)
def add_resource(
        group_id: int,
        resource_data: GroupResourceCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if current_user not in group.members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group members can add resources",
        )

    new_resource = GroupResource(
        group_id=group_id,
        title=resource_data.title,
        url=resource_data.url,
        resource_type=resource_data.resource_type,
        shared_by=current_user.id,
    )

    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)

    return {"message": "Resource added successfully"}


@router.post("/{group_id}/messages", response_model=GroupMessageResponse)
def create_message(
        group_id: int,
        message_data: GroupMessageCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if current_user not in group.members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group members can send messages",
        )

    new_message = GroupMessage(
        group_id=group_id,
        user_id=current_user.id,
        content=message_data.content,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return GroupMessageResponse.model_validate(new_message)


@router.get("/{group_id}/messages", response_model=list[GroupMessageResponse])
def get_messages(
        group_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if current_user not in group.members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group members can view messages",
        )

    messages = db.query(GroupMessage).filter(GroupMessage.group_id == group_id).order_by(
        GroupMessage.created_at.asc()).all()
    return [GroupMessageResponse.model_validate(m) for m in messages]


@router.websocket("/{group_id}/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        group_id: int,
        token: str = Query(...),
        db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time group chat messaging.
    Clients connect with their auth token and can send/receive messages instantly.
    """
    # Authenticate user from token
    try:
        dec_tok = decode_token(token)
        print(dec_tok)
        if not dec_tok:
            await websocket.close(code=1008, reason="Invalid token")
            return
        print(dec_tok)
        email = dec_tok.get("sub")
        print(email)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Verify group exists and user is a member
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        await websocket.close(code=1008, reason="Group not found")
        return

    if user not in group.members:
        await websocket.close(code=1008, reason="Not a group member")
        return

    # Accept connection and add to manager
    await manager.connect(websocket, group_id)
    logger.info(f"User {user.email} connected to group {group_id} via WebSocket")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Create and save message to database
            new_message = GroupMessage(
                group_id=group_id,
                user_id=user.id,
                content=data.get("content", ""),
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            # Prepare message response
            message_response = GroupMessageResponse.model_validate(new_message)

            # Broadcast to all connected clients in this group
            await manager.broadcast_to_group(
                group_id,
                message_response.model_dump(mode="json")
            )

            logger.info(f"Message from {user.email} broadcasted to group {group_id}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, group_id)
        logger.info(f"User {user.email} disconnected from group {group_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, group_id)
