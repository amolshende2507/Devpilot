from pydantic import BaseModel, HttpUrl


class ProjectImportRequest(BaseModel):
    name: str
    github_url: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    github_url: str
    status: str

    class Config:
        from_attributes = True