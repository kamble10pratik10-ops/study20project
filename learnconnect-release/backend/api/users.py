from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from database import get_db
from models import User, Connection, Group
from schemas import (
    UserSearchResponse,
    ConnectionCreate,
    ConnectionResponse,
    ConnectionUpdate,
    UserResponse,
)
from dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search", response_model=list[UserSearchResponse])
def search_users(
    q: str = Query(..., min_length=1, description="Search query for user name or email"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search for users by name or email.
    Returns users with their connection status relative to the current user.
    """
    try:
        # Search users by name or email (case-insensitive)
        search_term = f"%{q.lower()}%"
        users = (
            db.query(User)
            .filter(
                or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term),
                )
            )
            .filter(User.id != current_user.id)  # Exclude current user
            .limit(50)
            .all()
        )

        # Get all connections involving current user
        connections = (
            db.query(Connection)
            .filter(
                or_(
                    Connection.requester_id == current_user.id,
                    Connection.addressee_id == current_user.id,
                )
            )
            .all()
        )

        # Create a mapping of user_id -> connection status
        connection_map = {}
        for conn in connections:
            other_user_id = (
                conn.addressee_id
                if conn.requester_id == current_user.id
                else conn.requester_id
            )
            connection_map[other_user_id] = conn.status

        # Build response with connection status
        result = []
        for user in users:
            user_dict = UserSearchResponse.model_validate(user).model_dump()
            user_dict["connection_status"] = connection_map.get(user.id, "none")
            result.append(UserSearchResponse(**user_dict))

        return result
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users",
        )


@router.get("/group/{group_id}/members", response_model=list[UserSearchResponse])
def get_group_members(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all members of a specific group with their connection status relative to the current user.
    """
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )

        # Check if current user is a member
        if current_user not in group.members:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of this group to view its members",
            )

        # Get all connections involving current user
        connections = (
            db.query(Connection)
            .filter(
                or_(
                    Connection.requester_id == current_user.id,
                    Connection.addressee_id == current_user.id,
                )
            )
            .all()
        )

        # Create a mapping of user_id -> connection status
        connection_map = {}
        for conn in connections:
            other_user_id = (
                conn.addressee_id
                if conn.requester_id == current_user.id
                else conn.requester_id
            )
            connection_map[other_user_id] = conn.status

        # Build response with connection status
        result = []
        for member in group.members:
            if member.id == current_user.id:
                continue  # Skip current user
            user_dict = UserSearchResponse.model_validate(member).model_dump()
            user_dict["connection_status"] = connection_map.get(member.id, "none")
            result.append(UserSearchResponse(**user_dict))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching group members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch group members",
        )


@router.post("/connections", response_model=ConnectionResponse)
def create_connection(
    connection_data: ConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a connection request to another user.
    """
    try:
        # Check if addressee exists
        addressee = db.query(User).filter(User.id == connection_data.addressee_id).first()
        if not addressee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Can't send connection to yourself
        if addressee.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send connection request to yourself",
            )

        # Check if connection already exists
        existing_connection = (
            db.query(Connection)
            .filter(
                or_(
                    and_(
                        Connection.requester_id == current_user.id,
                        Connection.addressee_id == addressee.id,
                    ),
                    and_(
                        Connection.requester_id == addressee.id,
                        Connection.addressee_id == current_user.id,
                    ),
                )
            )
            .first()
        )

        if existing_connection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection already exists with status: {existing_connection.status}",
            )

        # Create new connection
        new_connection = Connection(
            requester_id=current_user.id,
            addressee_id=addressee.id,
            status="pending",
        )

        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)

        # Load relationships
        db.refresh(new_connection, ["requester", "addressee"])

        return ConnectionResponse.model_validate(new_connection)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating connection: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create connection",
        )


@router.get("/connections", response_model=list[ConnectionResponse])
def get_connections(
    status_filter: str = Query(None, description="Filter by status: pending, accepted, rejected, blocked"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all connections for the current user (both sent and received).
    """
    try:
        query = db.query(Connection).filter(
            or_(
                Connection.requester_id == current_user.id,
                Connection.addressee_id == current_user.id,
            )
        )

        if status_filter:
            query = query.filter(Connection.status == status_filter)

        connections = query.order_by(Connection.created_at.desc()).all()

        # Load relationships
        for conn in connections:
            db.refresh(conn, ["requester", "addressee"])

        return [ConnectionResponse.model_validate(conn) for conn in connections]
    except Exception as e:
        logger.error(f"Error fetching connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch connections",
        )


@router.put("/connections/{connection_id}", response_model=ConnectionResponse)
def update_connection(
    connection_id: int,
    connection_update: ConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update connection status (accept, reject, or block).
    Only the addressee can accept/reject pending requests.
    """
    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        # Check if current user is involved in this connection
        if (
            connection.requester_id != current_user.id
            and connection.addressee_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this connection",
            )

        # Validate status
        valid_statuses = ["pending", "accepted", "rejected", "blocked"]
        if connection_update.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        # Only addressee can accept/reject pending requests
        if connection.status == "pending" and connection_update.status in ["accepted", "rejected"]:
            if connection.addressee_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the recipient can accept or reject connection requests",
                )

        connection.status = connection_update.status
        db.commit()
        db.refresh(connection)

        # Load relationships
        db.refresh(connection, ["requester", "addressee"])

        return ConnectionResponse.model_validate(connection)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating connection: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update connection",
        )


@router.delete("/connections/{connection_id}")
def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a connection (cancel request or remove connection).
    """
    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        # Check if current user is involved in this connection
        if (
            connection.requester_id != current_user.id
            and connection.addressee_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this connection",
            )

        db.delete(connection)
        db.commit()

        return {"message": "Connection deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting connection: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete connection",
        )

