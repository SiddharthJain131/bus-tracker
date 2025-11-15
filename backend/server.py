# PATCH: Update Notification model to include title field
# Search for:
class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    timestamp: str
    read: bool = False
    type: str  # mismatch, missed_boarding, update

# Replace with:
class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: Optional[str] = None
    timestamp: str
    read: bool = False
    type: str  # mismatch, missed_boarding, update
