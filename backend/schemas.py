from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    interests: List["TopicResponse"] = []
    groups: List["GroupResponse"] = []


class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GroupResourceCreate(BaseModel):
    title: str
    url: str
    resource_type: str


class GroupResourceResponse(GroupResourceCreate):
    id: int
    group_id: int
    shared_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class GroupBase(BaseModel):
    title: str
    description: Optional[str] = None
    topic_id: int


class GroupCreate(GroupBase):
    pass


class GroupResponse(GroupBase):
    id: int
    created_by: int
    created_at: datetime
    members: List[UserResponse] = []
    resources: List[GroupResourceResponse] = []

    class Config:
        from_attributes = True


class DoubtBase(BaseModel):
    topic: str
    title: str
    description: str


class DoubtCreate(DoubtBase):
    pass


class DoubtResponse(DoubtBase):
    id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class DoubtDetailResponse(DoubtResponse):
    created_by_user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class SearchHistoryResponse(BaseModel):
    topic: str
    searched_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    recent_searches: List[SearchHistoryResponse]
    joined_groups: List[GroupResponse]
    recommended_topics: List[TopicResponse]


class SearchResultsResponse(BaseModel):
    videos: List[dict]
    articles: List[dict]


class PostMediaResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    media_type: str
    mime_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    media: List[PostMediaResponse] = []

    class Config:
        from_attributes = True


class PostDetailResponse(PostResponse):
    author: UserResponse


class UserProfileResponse(UserResponse):
    posts: List[PostResponse] = []


from pydantic import BaseModel
from datetime import datetime


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    github_url: Optional[str] = None
    user_id: int


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    github_url: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class ProjectDetailResponse(BaseModel):
    id: int
    created_by: int
    created_at: datetime

    class Config:
        orm_mode = True
