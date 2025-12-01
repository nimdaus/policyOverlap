import httpx
from typing import List, Optional
from .models import CAPolicy, GraphUser, GraphGroup

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

class GraphClient:
    def __init__(self, access_token: str):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def get_policies(self) -> List[CAPolicy]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GRAPH_BASE_URL}/identity/conditionalAccess/policies", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return [CAPolicy(**policy) for policy in data.get("value", [])]

    async def search_users(self, query: str) -> List[GraphUser]:
        async with httpx.AsyncClient() as client:
            # Search for users by displayName or userPrincipalName
            url = f"{GRAPH_BASE_URL}/users?$filter=startswith(displayName,'{query}') or startswith(userPrincipalName,'{query}')&$top=10"
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return [GraphUser(**user) for user in data.get("value", [])]

    async def get_transitive_member_of(self, user_id: str) -> List[str]:
        """Returns a list of Group IDs that the user is a member of (transitively)."""
        async with httpx.AsyncClient() as client:
            url = f"{GRAPH_BASE_URL}/users/{user_id}/transitiveMemberOf?$select=id"
            group_ids = []
            while url:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                group_ids.extend([item['id'] for item in data.get("value", []) if '@odata.type' in item and '#microsoft.graph.group' in item['@odata.type']])
                url = data.get("@odata.nextLink")
            return group_ids
