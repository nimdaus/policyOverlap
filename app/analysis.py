from typing import List, Dict, Any
from .models import CAPolicy

def normalize_policies_for_graph(policies: List[CAPolicy]) -> Dict[str, List[Dict[str, Any]]]:
    nodes = []
    edges = []
    
    for policy in policies:
        policy_node_id = f"policy_{policy.id}"
        nodes.append({
            "data": {
                "id": policy_node_id,
                "label": policy.display_name,
                "type": "policy",
                "state": policy.state
            }
        })
        
        # Conditions (Inputs)
        # Users/Groups
        if policy.conditions.users:
            users_inc = policy.conditions.users.get("includeUsers", []) + policy.conditions.users.get("includeGroups", [])
            for u in users_inc:
                # Handle "All" or specific GUIDs
                label = "All Users" if u == "All" else u 
                node_id = f"cond_user_{u}"
                # Check if node exists to avoid duplicates? Cytoscape handles this if ID is same.
                # But we might want to deduplicate here for cleanliness or just let frontend handle it.
                # For simplicity, we'll add unique nodes based on ID.
                # Actually, if multiple policies use the same group, we want one node for that group.
                # So we should track added nodes.
                
                # Let's just emit edges and let frontend/cytoscape handle node uniqueness if we provide consistent IDs.
                # But we need to emit the node definition at least once.
                nodes.append({
                    "data": {
                        "id": node_id,
                        "label": label,
                        "type": "condition"
                    }
                })
                edges.append({
                    "data": {
                        "source": node_id,
                        "target": policy_node_id,
                        "label": "Include"
                    }
                })

        # Controls (Outputs)
        if policy.grant_controls:
            for control in policy.grant_controls.built_in_controls:
                control_node_id = f"control_{control}"
                nodes.append({
                    "data": {
                        "id": control_node_id,
                        "label": control,
                        "type": "control"
                    }
                })
                edges.append({
                    "data": {
                        "source": policy_node_id,
                        "target": control_node_id,
                        "label": "Grant"
                    }
                })
                
    # Deduplicate nodes based on ID
    unique_nodes = {node['data']['id']: node for node in nodes}.values()
    
    return {
        "nodes": list(unique_nodes),
        "edges": edges
    }

def evaluate_policy_applicability(policy: CAPolicy, user_id: str, group_ids: List[str]) -> bool:
    """
    Determines if a policy applies to a specific user based on their ID and group memberships.
    Returns True if the policy applies, False otherwise.
    """
    if policy.state == "disabled":
        return False
        
    conditions = policy.conditions
    users_cond = conditions.users or {}
    
    include_users = users_cond.get("includeUsers", [])
    include_groups = users_cond.get("includeGroups", [])
    exclude_users = users_cond.get("excludeUsers", [])
    exclude_groups = users_cond.get("excludeGroups", [])
    
    # Check Exclusions first (Exclude overrides Include)
    if user_id in exclude_users:
        return False
    
    for gid in group_ids:
        if gid in exclude_groups:
            return False
            
    # Check Inclusions
    # "All" keyword handling
    if "All" in include_users:
        return True
        
    if user_id in include_users:
        return True
        
    for gid in group_ids:
        if gid in include_groups:
            return True
            
    return False

def get_applicable_policies(policies: List[CAPolicy], user_id: str, group_ids: List[str]) -> List[str]:
    """Returns a list of Policy IDs that apply to the user."""
    applicable_ids = []
    for policy in policies:
        if evaluate_policy_applicability(policy, user_id, group_ids):
            applicable_ids.append(policy.id)
    return applicable_ids
