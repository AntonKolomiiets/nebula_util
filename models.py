# models.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Product(BaseModel):
    productId: str

class UserRef(BaseModel):
    userId: str

class Task(BaseModel):
    taskId: str
    name: str
    creatingTime: datetime
    finishTime: Optional[datetime]
    statusChangeTime: Optional[datetime] = None
    launchIllustration: bool
    launchMotion: bool
    needIllustrator: Optional[bool] = None
    referenceLink: Optional[str] = None
    description: Optional[str] = None
    adPlatforms: List[str]
    localizations: List[str]
    priority: int
    status: str
    imageResultLink: Optional[str] = None
    motionResultLink: Optional[str] = None
    accountId: str
    hypothesisId: Optional[str] = None
    creatorId: str
    illustratorId: Optional[str] = None
    motionerId: Optional[str] = None  # sometimes this is null if there are multiple motioners
    illustrationReviewerId: Optional[str] = None
    motionReviewerId: Optional[str] = None
    childTaskId: Optional[str] = None
    products: List[Product]
    motioners: List[UserRef]
    illustrators: List[UserRef]
