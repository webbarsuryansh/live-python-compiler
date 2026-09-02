"""Authentication and authorization routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header

from ..auth import (
    create_access_token,
    create_refresh_token,
    extract_token_from_header,
    get_current_user,
    verify_token,
)
from ..models import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ShareCodeRequest,
    UpdateCodeRequest,
    UpdateProfileRequest,
    UserProfileResponse,
    UserSummary,
)
from ..storage import (
    authenticate_user,
    change_password,
    create_user,
    delete_saved_code,
    delete_user,
    get_public_codes,
    get_saved_code,
    get_shared_codes,
    list_saved_codes,
    revoke_code_access,
    save_user_code,
    share_code,
    update_saved_code,
    update_user,
    check_code_access,
)

router = APIRouter()


# ===== Authentication Endpoints =====

@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    """Register a new user."""
    try:
        user = create_user(payload.name, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    access_token = create_access_token(user["id"], role=user.get("role", "user"))
    refresh_token = create_refresh_token(user["id"])
    
    return AuthResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserSummary(**user),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    """Login with email and password."""
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(user["id"], role=user.get("role", "user"))
    refresh_token = create_refresh_token(user["id"])
    
    return AuthResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserSummary(**user),
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh_access_token(payload: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        payload_data = verify_token(payload.refresh_token)
        if payload_data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload_data.get("sub")
        access_token = create_access_token(user_id)
        
        # Return user info from token (don't need DB lookup for just token refresh)
        return AuthResponse(
            token=access_token,
            refresh_token=payload.refresh_token,
            user=UserSummary(
                id=user_id,
                name="",  # Will be populated if needed
                email="",
                role=payload_data.get("role", "user"),
            ),
        )
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserProfileResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        role=current_user.get("role", "user"),
        created_at=current_user.get("created_at", ""),
        updated_at=current_user.get("updated_at", ""),
        ai_plan=current_user.get("ai_plan", "free"),
        ai_subscription_status=current_user.get("ai_subscription_status", "active"),
    )


@router.post("/logout")
def logout():
    """Logout (client-side primarily, but confirms logout endpoint exists)."""
    return {"message": "Successfully logged out"}


# ===== User Profile Management =====

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update user profile (name, email)."""
    update_data = {}
    if payload.name is not None:
        update_data["name"] = payload.name
    if payload.email is not None:
        update_data["email"] = payload.email
    
    updated_user = update_user(current_user["id"], **update_data)
    if updated_user is None:
        raise HTTPException(status_code=400, detail="Could not update profile")
    
    # Re-fetch full user info
    from ..storage import get_user_by_id
    full_user = get_user_by_id(current_user["id"])
    
    return UserProfileResponse(
        id=full_user["id"],
        name=full_user["name"],
        email=full_user["email"],
        role=full_user.get("role", "user"),
        created_at=full_user.get("created_at", ""),
        updated_at=full_user.get("updated_at", ""),
        ai_plan=full_user.get("ai_plan", "free"),
        ai_subscription_status=full_user.get("ai_subscription_status", "active"),
    )


@router.get("/ai-subscription")
def get_ai_subscription(current_user: dict = Depends(get_current_user)):
    """Return the user's current no-cost AI subscription status."""
    return {
        "plan": current_user.get("ai_plan", "free"),
        "status": current_user.get("ai_subscription_status", "active"),
        "provider": "Google Gemini free tier",
        "billing_required": False,
    }


@router.post("/change-password")
def change_user_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """Change user password."""
    success = change_password(current_user["id"], payload.old_password, payload.new_password)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid current password")
    
    return {"message": "Password changed successfully"}


@router.delete("/account")
def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete user account and all data."""
    delete_user(current_user["id"])
    return {"message": "Account deleted successfully"}


# ===== Code Management Endpoints =====

@router.get("/saved-codes")
def get_saved_codes(current_user: dict = Depends(get_current_user)):
    """Get user's saved codes."""
    codes = list_saved_codes(current_user["id"])
    return codes


@router.post("/saved-codes")
def save_code(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """Save a new code."""
    try:
        code = save_user_code(
            current_user["id"],
            title=payload.get("title", "Untitled script"),
            code=payload.get("code", ""),
            language=payload.get("language", "python"),
            is_public=payload.get("is_public", False),
        )
        return code
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/saved-codes/{code_id}")
def get_code(
    code_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a saved code by ID."""
    code = get_saved_code(code_id, current_user["id"])
    if code is None:
        raise HTTPException(status_code=404, detail="Code not found")
    return code


@router.put("/saved-codes/{code_id}")
def update_code(
    code_id: str,
    payload: UpdateCodeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update a saved code."""
    update_data = {}
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.code is not None:
        update_data["code"] = payload.code
    if payload.is_public is not None:
        update_data["is_public"] = payload.is_public
    
    updated = update_saved_code(code_id, current_user["id"], **update_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Code not found or permission denied")
    
    return updated


@router.delete("/saved-codes/{code_id}")
def delete_code(
    code_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a saved code."""
    success = delete_saved_code(code_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Code not found or permission denied")
    
    return {"message": "Code deleted successfully"}


@router.get("/public-codes")
def get_public_codes_list():
    """Get all public codes (no auth required)."""
    codes = get_public_codes()
    return codes


# ===== Code Sharing/Permissions Endpoints =====

@router.post("/saved-codes/{code_id}/share")
def share_code_with_user(
    code_id: str,
    payload: ShareCodeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Share a code with another user."""
    from ..storage import list_users, get_user_by_id
    
    # Find target user by email
    target_user = None
    for user in list_users():
        if user["email"].lower() == payload.shared_with_email.lower():
            target_user = user
            break
    
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")
    
    perm = share_code(
        code_id,
        current_user["id"],
        target_user["id"],
        permission=payload.permission,
    )
    
    if perm is None:
        raise HTTPException(status_code=404, detail="Code not found or permission denied")
    
    return {
        "message": f"Code shared with {payload.shared_with_email}",
        "permission": perm,
    }


@router.get("/shared-codes")
def get_shared_codes_list(current_user: dict = Depends(get_current_user)):
    """Get codes shared with current user."""
    codes = get_shared_codes(current_user["id"])
    return codes


@router.delete("/saved-codes/{code_id}/share/{user_id}")
def revoke_code_share(
    code_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke shared access to a code."""
    success = revoke_code_access(code_id, current_user["id"], user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found or denied")
    
    return {"message": "Access revoked successfully"}


@router.get("/saved-codes/{code_id}/access")
def check_access(
    code_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Check if user has access to a code."""
    has_access, permission = check_code_access(code_id, current_user["id"])
    
    return {
        "has_access": has_access,
        "permission": permission,
    }
