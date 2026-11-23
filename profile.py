
import streamlit as st
import uuid
from datetime import datetime, timezone


BUCKET = "community-media"


# =========================================================
# PROFILE DATA
# =========================================================

def get_member_profile(supabase, user_id):
    """Retrieve a member profile from Supabase."""

    if not supabase or not user_id:
        return {}

    try:
        response = (
            supabase.table("member_profiles")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

    except Exception as error:
        st.error(f"Could not load profile: {error}")

    return {}


def get_display_name(profile):
    """Return the best available display name."""

    if not profile:
        return "EcoLoop Member"

    return (
        profile.get("display_name")
        or profile.get("username")
        or "EcoLoop Member"
    )


def get_avatar_url(supabase, profile):
    """Resolve profile avatar URL."""

    if not profile:
        return None

    avatar = profile.get("avatar_url")

    if not avatar:
        return None

    # Already a complete URL
    if str(avatar).startswith("http"):
        return avatar

    try:
        return (
            supabase.storage
            .from_(BUCKET)
            .get_public_url(str(avatar))
        )
    except Exception:
        return None


# =========================================================
# PROFILE PHOTO UPLOAD
# =========================================================

def upload_profile_photo(supabase, user_id, uploaded_file):
    """Upload a profile photo to the community-media bucket."""

    if uploaded_file is None:
        return None

    try:
        current_user = supabase.auth.get_user().user

        authenticated_uid = (
            str(current_user.id) if current_user else None
        )

        if not authenticated_uid or authenticated_uid != str(user_id):
            st.error("Your login session could not be verified.")
            return None

        extension = (
            uploaded_file.name.rsplit(".", 1)[-1].lower()
            if "." in uploaded_file.name
            else "jpg"
            )

        path = (
            f"{authenticated_uid}/avatars/"
            f"{uuid.uuid4().hex}.{extension}"
        )

        supabase.storage.from_(BUCKET).upload(
            path,
            uploaded_file.getvalue(),
            {
                "content-type": uploaded_file.type
                or "application/octet-stream",
                "upsert": "false",
            },
        )

        return path

    except Exception as error:
        st.error(f"Profile picture upload failed: {error}")
        return None


# =========================================================
# PROFILE SAVE
# =========================================================

def save_member_profile(
    supabase,
    user_id,
    display_name,
    username,
    bio,
    location,
    interests,
    avatar_url=None,
):
    """Save profile details using the existing member_profiles table."""

    if not supabase or not user_id:
        return False

    try:
        profile_data = {
            "user_id": str(user_id),
            "display_name": display_name.strip(),
            "username": username.strip().lstrip("@"),
            "bio": bio.strip(),
            "location": location.strip(),
            "interests": interests.strip(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if avatar_url:
            profile_data["avatar_url"] = avatar_url

        (
            supabase.table("member_profiles")
            .upsert(profile_data, on_conflict="user_id")
            .execute()
        )

        return True

    except Exception as error:
        st.error(f"Profile could not be saved: {error}")
        return False


# =========================================================
# PROFILE CARD
# =========================================================

def render_profile_card(
    supabase,
    profile,
    key=None,
    show_button=True,
):
    """Display a clean member card.

    Returns True when the View Profile button is clicked.
    """

    if not profile:
        return False

    name = get_display_name(profile)
    username = profile.get("username", "")
    bio = profile.get("bio", "")
    location = profile.get("location", "")
    avatar = get_avatar_url(supabase, profile)

    with st.container(border=True):

        col1, col2 = st.columns([1, 3])

        with col1:
            if avatar:
                st.image(avatar, width=90)
            else:
                st.markdown("### 👤")

        with col2:
            st.markdown(f"**{name}**")

            if username:
                st.caption(f"@{username}")

            if location:
                st.caption(f"📍 {location}")

        if bio:
            st.write(bio[:120] + ("..." if len(bio) > 120 else ""))

        if show_button:
            button_key = key or str(profile.get("user_id", uuid.uuid4()))

            return st.button(
                "View Profile",
                key=f"profile_view_{button_key}",
                use_container_width=True,
            )

    return False


# =========================================================
# FULL PROFILE VIEW
# =========================================================

def render_profile_view(supabase, profile):
    """Display the full profile of a selected member."""

    if not profile:
        st.info("Profile not found.")
        return

    name = get_display_name(profile)
    username = profile.get("username", "")
    bio = profile.get("bio", "")
    location = profile.get("location", "")
    interests = profile.get("interests", "")
    avatar = get_avatar_url(supabase, profile)

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        if avatar:
            st.image(avatar, width=160)
        else:
            st.markdown("## 👤")

    with col2:
        st.markdown(f"# {name}")

        if username:
            st.markdown(f"**@{username}**")

        if location:
            st.markdown(f"📍 {location}")

    st.markdown("### About")

    if bio:
        st.write(bio)
    else:
        st.caption("This member hasn't added a bio yet.")

    st.markdown("### Interests")

    if interests:
        st.write(interests)
    else:
        st.caption("No interests added yet.")

    st.markdown("---")


# =========================================================
# MY PROFILE PAGE
# =========================================================

def render_profile_page(supabase, user_id):
    """Render the member's own profile and profile editor."""

    st.markdown("## 👤 My Profile")
    st.caption("Your identity and presence in the EcoLoop community.")

    if not user_id:
        st.warning("Please sign in to view your profile.")
        return

    profile = get_member_profile(supabase, user_id)

    name = profile.get("display_name", "")
    username = profile.get("username", "")
    bio = profile.get("bio", "")
    location = profile.get("location", "")
    interests = profile.get("interests", "")

    avatar = get_avatar_url(supabase, profile)

    # Current profile preview
    with st.container(border=True):

        col1, col2 = st.columns([1, 2])

        with col1:
            if avatar:
                st.image(avatar, width=110)
            else:
                st.markdown("### 👤")

        with col2:
            st.markdown(f"### {name or 'Your Name'}")

            if username:
                st.caption(f"@{username}")

            if location:
                st.caption(f"📍 {location}")

        if bio:
            st.write(bio)

    st.markdown("### Edit Profile")

    with st.form("ecoloop_profile_form", clear_on_submit=False):

        display_name = st.text_input(
            "Display name",
            value=name,
            max_chars=60,
            placeholder="What should people call you?",
        )

        new_username = st.text_input(
            "Username",
            value=username,
            max_chars=30,
            placeholder="Choose a username",
        )

        new_location = st.text_input(
            "Location",
            value=location,
            max_chars=100,
            placeholder="City or community",
        )

        new_bio = st.text_area(
            "About me",
            value=bio,
            max_chars=500,
            height=120,
            placeholder="Tell the community a little about yourself...",
        )

        new_interests = st.text_area(
            "Interests",
            value=interests,
            max_chars=300,
            height=100,
            placeholder="Environment, technology, innovation, community...",
        )

        uploaded_photo = st.file_uploader(
            "Profile photo",
            type=["jpg", "jpeg", "png", "webp"],
            key="ecoloop_profile_photo",
        )

        save_button = st.form_submit_button(
            "Save Profile",
            use_container_width=True,
        )

    if save_button:

        new_avatar_url = profile.get("avatar_url")

        if uploaded_photo is not None:
            uploaded_path = upload_profile_photo(
                supabase,
                user_id,
                uploaded_photo,
            )

            if uploaded_path:
                new_avatar_url = uploaded_path

        saved = save_member_profile(
            supabase=supabase,
            user_id=user_id,
            display_name=display_name,
            username=new_username,
            bio=new_bio,
            location=new_location,
            interests=new_interests,
            avatar_url=new_avatar_url,
        )

        if saved:
            st.success("Profile saved successfully!")
            st.rerun()


# =========================================================
# PROFILE LOOKUP
# =========================================================

def render_member_profile(supabase, user_id):
    """Retrieve and display another member's full profile."""

    profile = get_member_profile(supabase, user_id)

    if profile:
        render_profile_view(supabase, profile)
    else:
        st.info("This member has not created a profile yet.")
