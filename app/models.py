from typing import List, Optional, Any
from pydantic import BaseModel, Field

class Conditions(BaseModel):
    users: Optional[dict] = Field(default_factory=dict) # To hold include/exclude users/groups
    applications: Optional[dict] = Field(default_factory=dict)
    platforms: Optional[dict] = Field(default_factory=dict)
    locations: Optional[dict] = Field(default_factory=dict)
    client_app_types: Optional[List[str]] = Field(default_factory=list, alias="clientAppTypes")

class GrantControls(BaseModel):
    operator: Optional[str] = None # OR / AND
    built_in_controls: List[str] = Field(default_factory=list, alias="builtInControls")
    custom_authentication_factors: List[str] = Field(default_factory=list, alias="customAuthenticationFactors")
    terms_of_use: List[str] = Field(default_factory=list, alias="termsOfUse")

class CAPolicy(BaseModel):
    id: str
    display_name: str = Field(..., alias="displayName")
    state: str # enabled, disabled, enabledForReportingButNotEnforced
    conditions: Conditions
    grant_controls: Optional[GrantControls] = Field(None, alias="grantControls")
    
    class Config:
        populate_by_name = True

class GraphUser(BaseModel):
    id: str
    display_name: str = Field(..., alias="displayName")
    user_principal_name: str = Field(..., alias="userPrincipalName")
    
    class Config:
        populate_by_name = True

class GraphGroup(BaseModel):
    id: str
    display_name: str = Field(..., alias="displayName")
    
    class Config:
        populate_by_name = True
