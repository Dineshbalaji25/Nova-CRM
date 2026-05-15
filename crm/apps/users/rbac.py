from django.core.cache import cache

def get_visible_user_ids(user, organization_id):
    """
    Returns a set of user IDs whose records this user is allowed to see,
    based on the Role hierarchy.
    
    Rules:
      - A user with no rbac_role can only see their own records.
      - A user sees their own records + records owned by all subordinate role members.
      - share_with_peers=True means the user also sees peer records (same role).
      - Admins and owners (OrganizationMember.role in ['admin', 'owner']) see everything.
    """
    cache_key = f"rbac_visible:{user.id}:{organization_id}"
    try:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    except Exception:
        # Fallback if Redis is down
        pass

    from apps.users.models import OrganizationMember, Role

    membership = OrganizationMember.objects.select_related('rbac_role').filter(
        user=user, organization_id=organization_id, is_active=True
    ).first()

    if not membership:
        result = {user.id}
        try:
            cache.set(cache_key, result, 120)
        except Exception: pass
        return result

    # Admins and owners see everything — return None as a signal for "no filter"
    if membership.role in ('admin', 'owner'):
        try:
            cache.set(cache_key, None, 120)
        except Exception: pass
        return None  # None means: no owner filter, show all tenant records

    user_role = membership.rbac_role
    if not user_role:
        result = {user.id}
        try:
            cache.set(cache_key, result, 120)
        except Exception: pass
        return result

    # Collect all subordinate role IDs via BFS on the role adjacency list
    visible_role_ids = set()
    queue = [user_role.id]
    while queue:
        current_id = queue.pop()
        if current_id in visible_role_ids:
            continue
        visible_role_ids.add(current_id)
        children = Role.objects.filter(
            parent_id=current_id, organization_id=organization_id
        ).values_list('id', flat=True)
        queue.extend(children)

    # Add peers if share_with_peers is True
    if user_role.share_with_peers:
        peer_ids = Role.objects.filter(
            parent=user_role.parent, organization_id=organization_id
        ).values_list('id', flat=True)
        visible_role_ids.update(peer_ids)

    # Fetch users belonging to visible roles
    visible_user_ids = set(
        OrganizationMember.objects.filter(
            organization_id=organization_id,
            rbac_role_id__in=visible_role_ids,
            is_active=True
        ).values_list('user_id', flat=True)
    )
    visible_user_ids.add(user.id)  # Always include self

    try:
        cache.set(cache_key, visible_user_ids, 120)
    except Exception: pass
    return visible_user_ids
