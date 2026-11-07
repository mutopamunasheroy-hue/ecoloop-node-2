import streamlit as st
import uuid
import mimetypes
import re

from datetime import datetime, timezone


# =========================================================
# ECOLOOP NODE — CENTRAL ACCOUNT PROFILE SYSTEM
# Powered by Next Gen Impact Hub (NGIH)
# =========================================================

MEDIA_BUCKET = "community-media"


# =========================================================
# 1. GENERAL HELPERS
# =========================================================

def account_now():
    return datetime.now(timezone.utc)


def account_user_id():
    user_id = st.session_state.get("user_id")

    if user_id:
        return str(user_id)

    user = st.session_state.get("user")

    if isinstance(user, dict):
        return str(user.get("id") or "")

    return str(getattr(user, "id", "") or "")


def account_user_metadata(user=None):
    if user is None:
        user = st.session_state.get("user")

    if isinstance(user, dict):
        return user.get("user_metadata") or {}

    return getattr(user, "user_metadata", None) or {}


def account_profile(supabase, user_id):
    if not user_id:
        return {}

    try:
        response = (
            supabase.table("member_profiles")
            .select("*")
            .eq("user_id", str(user_id))
            .maybe_single()
            .execute()
        )

        return response.data or {}

    except Exception:
        return {}


def account_display_name(profile, user=None):
    metadata = account_user_metadata(user)

    return (
        profile.get("display_name")
        or metadata.get("full_name")
        or metadata.get("display_name")
        or "EcoLoop Member"
    )


def account_initials(name):
    words = str(name or "").strip().split()

    if not words:
        return "👤"

    return "".join(word[0].upper() for word in words[:2])


def account_escape(value):
    value = str(value or "")

    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


# =========================================================
# 2. PROFILE PHOTO STORAGE
# =========================================================

def account_signed_image(supabase, image_path):

    if not image_path:
        return None

    try:
        result = (
            supabase.storage
            .from_(MEDIA_BUCKET)
            .create_signed_url(image_path, 3600)
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
            )

        return (
            getattr(result, "signed_url", None)
            or getattr(result, "signedURL", None)
        )

    except Exception:
        return None


def upload_account_picture(supabase, user_id, uploaded_file):

    if uploaded_file is None:
        return None

    try:
        extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

        allowed = ["jpg", "jpeg", "png", "webp"]

        if extension not in allowed:
            st.error("Please upload a JPG, JPEG, PNG or WEBP image.")
            return None

        file_path = (
            f"profiles/{user_id}/"
            f"{uuid.uuid4().hex}.{extension}"
        )

        content_type = (
            uploaded_file.type
            or mimetypes.guess_type(uploaded_file.name)[0]
            or "application/octet-stream"
        )

        supabase.storage.from_(MEDIA_BUCKET).upload(
            file_path,
            uploaded_file.getvalue(),
            {
                "content-type": content_type,
                "upsert": "false"
            }
        )

        return file_path

    except Exception as error:
        st.error("Profile picture upload failed.")
        st.caption(str(error))
        return None


# =========================================================
# 3. USERNAME VALIDATION
# =========================================================

def validate_account_username(username):

    username = str(username or "").strip().lower()

    if len(username) < 3 or len(username) > 25:
        return False, "Username must contain 3–25 characters."

    if not re.fullmatch(r"[a-z0-9_.]+", username):
        return False, (
            "Use only lowercase letters, numbers, "
            "underscores and full stops."
        )

    return True, ""


def account_username_available(supabase, username, user_id):

    try:
        response = (
            supabase.table("member_profiles")
            .select("user_id")
            .eq("username", username)
            .execute()
        )

        for row in response.data or []:
            if str(row.get("user_id")) != str(user_id):
                return False

        return True

    except Exception:
        return False


# =========================================================
# 4. SAVE PROFILE
# =========================================================

def save_account_profile(
    supabase,
    user_id,
    display_name,
    username,
    bio,
    location,
    country_of_origin,
    interests,
    instagram_handle="",
    facebook_handle="",
    tiktok_handle="",
    linkedin_handle="",
    avatar_path=""
):

    display_name = str(display_name or "").strip()
    username = str(username or "").strip().lower()

    if not display_name:
        st.error("Please enter your display name.")
        return False

    valid, message = validate_account_username(username)

    if not valid:
        st.error(message)
        return False

    if not account_username_available(
        supabase,
        username,
        user_id
    ):
        st.error(
            "That username is already taken or could not be checked."
        )
        return False

    current = account_profile(supabase, user_id)

    data = {
        "user_id": str(user_id),
        "display_name": display_name,
        "username": username,
        "bio": str(bio or "").strip(),
        "location": str(location or "").strip(),
        "interests": str(interests or "").strip(),
        "updated_at": account_now().isoformat()
    }

    if avatar_path:
        data["avatar_url"] = avatar_path
    elif current.get("avatar_url"):
        data["avatar_url"] = current["avatar_url"]

    # These fields require the additional database columns.
    data.update({
        "country_of_origin": str(country_of_origin or "").strip(),
        "instagram_handle": str(instagram_handle or "").strip(),
        "facebook_handle": str(facebook_handle or "").strip(),
        "tiktok_handle": str(tiktok_handle or "").strip(),
        "linkedin_handle": str(linkedin_handle or "").strip()
    })

    try:
        supabase.table("member_profiles").upsert(
            data,
            on_conflict="user_id"
        ).execute()

        return True

    except Exception as error:
        st.error("Could not save your profile.")
        st.caption(str(error))
        return False


# =========================================================
# 5. PROFILE EDITOR
# =========================================================

def render_account_profile_editor(supabase, user_id, user=None):

    profile = account_profile(supabase, user_id)

    metadata = account_user_metadata(user)

    st.subheader("Edit your profile")
    st.caption("Your public identity in the EcoLoop community.")

    avatar_path = profile.get("avatar_url") or ""
    avatar_url = account_signed_image(supabase, avatar_path)

    if avatar_url:
        st.image(avatar_url, width=120)
    else:
        st.markdown("### 👤")

    with st.form("ecoloop_account_profile_form"):

        uploaded_photo = st.file_uploader(
            "Profile picture",
            type=["jpg", "jpeg", "png", "webp"],
            key="account_profile_picture"
        )

        if uploaded_photo:
            st.image(uploaded_photo, width=120)

        display_name = st.text_input(
            "Display name",
            value=(
                profile.get("display_name")
                or metadata.get("full_name")
                or ""
            )
        )

        username = st.text_input(
            "Username",
            value=profile.get("username") or "",
            help="Other members can search for this username."
        )

        bio = st.text_area(
            "Bio",
            value=profile.get("bio") or "",
            max_chars=300,
            placeholder="Tell the community a little about yourself."
        )

        location = st.text_input(
            "Current location",
            value=profile.get("location") or "",
            placeholder="City, province or region"
        )

        country = st.text_input(
            "Country of origin",
            value=profile.get("country_of_origin") or ""
        )

        interests = st.text_input(
            "Interests",
            value=profile.get("interests") or "",
            placeholder="Climate action, technology, entrepreneurship..."
        )

        st.divider()
        st.markdown("**Social media (optional)**")

        instagram = st.text_input(
            "Instagram username",
            value=profile.get("instagram_handle") or ""
        )

        facebook = st.text_input(
            "Facebook profile",
            value=profile.get("facebook_handle") or ""
        )

        tiktok = st.text_input(
            "TikTok username",
            value=profile.get("tiktok_handle") or ""
        )

        linkedin = st.text_input(
            "LinkedIn profile",
            value=profile.get("linkedin_handle") or ""
        )

        submitted = st.form_submit_button(
            "Save Profile",
            use_container_width=True
        )

        if submitted:

            new_avatar_path = ""

            if uploaded_photo:
                new_avatar_path = upload_account_picture(
                    supabase,
                    user_id,
                    uploaded_photo
                )

                if not new_avatar_path:
                    st.error("Profile was not saved.")
                    return

            saved = save_account_profile(
                supabase=supabase,
                user_id=user_id,
                display_name=display_name,
                username=username,
                bio=bio,
                location=location,
                country_of_origin=country,
                interests=interests,
                instagram_handle=instagram,
                facebook_handle=facebook,
                tiktok_handle=tiktok,
                linkedin_handle=linkedin,
                avatar_path=new_avatar_path
            )

            if saved:
                st.success("Your profile has been updated!")
                st.rerun()


# =========================================================
# 6. FOLLOW SYSTEM — TEMPORARY SESSION VERSION
# =========================================================

def account_init_follow_state():

    if "account_following" not in st.session_state:
        st.session_state["account_following"] = set()


def render_account_follow_controls(member_id):

    account_init_follow_state()

    current_user_id = account_user_id()

    if not current_user_id or str(member_id) == current_user_id:
        return

    following = st.session_state["account_following"]
    member_id = str(member_id)

    if member_id in following:

        if st.button(
            "Following ✓",
            key=f"account_unfollow_{member_id}"
        ):
            following.discard(member_id)
            st.rerun()

    else:

        if st.button(
            "＋ Follow",
            key=f"account_follow_{member_id}"
        ):
            following.add(member_id)
            st.rerun()


# =========================================================
# 7. PUBLIC PROFILE DISPLAY
# =========================================================

def render_account_public_profile(supabase, member):

    if not member:
        st.info("Profile not found.")
        return

    member_id = str(member.get("user_id") or "")

    avatar_url = account_signed_image(
        supabase,
        member.get("avatar_url")
    )

    name = account_escape(
        member.get("display_name") or "EcoLoop Member"
    )

    username = account_escape(
        member.get("username") or "member"
    )

    if avatar_url:
        st.image(avatar_url, width=140)
    else:
        st.markdown("## 👤")

    st.subheader(name)
    st.caption(f"@{username}")

    if member.get("location"):
        st.write(f"📍 {member['location']}")

    if member.get("country_of_origin"):
        st.write(
            f"🌍 From {member['country_of_origin']}"
        )

    if member.get("bio"):
        st.write(member["bio"])

    if member.get("interests"):
        st.caption(
            f"Interests: {member['interests']}"
        )

    st.divider()

    st.markdown("**Social links**")

    social_fields = [
        ("Instagram", "instagram_handle"),
        ("Facebook", "facebook_handle"),
        ("TikTok", "tiktok_handle"),
        ("LinkedIn", "linkedin_handle")
    ]

    social_found = False

    for label, field in social_fields:

        value = member.get(field)

        if value:
            social_found = True
            st.write(f"**{label}:** {value}")

    if not social_found:
        st.caption("No social links added.")

    current_user_id = account_user_id()

    if member_id and member_id != current_user_id:

        render_account_follow_controls(member_id)

        if st.button(
            "Message",
            key=f"account_public_message_{member_id}",
            use_container_width=True
        ):
            open_account_direct_chat(member_id, supabase)


# =========================================================
# 8. OPEN EXISTING PRIVATE CHAT
# =========================================================

def open_account_direct_chat(member_id, supabase):

    current_user_id = account_user_id()

    if not current_user_id:
        st.warning("Please log in first.")
        return

    try:
        from community_groups import get_or_create_direct_conversation

        conversation_id = get_or_create_direct_conversation(
            supabase,
            current_user_id,
            str(member_id)
        )

        st.session_state["eco_active_conversation"] = conversation_id
        st.session_state["eco_community_section"] = "Chats"
        st.session_state["current_page"] = "Community Groups"

        st.rerun()

    except Exception as error:

        st.error("Could not open this conversation.")
        st.caption(str(error))


# =========================================================
# 9. SEARCH MEMBER DIRECTORY
# =========================================================

def search_account_profiles(supabase, search_text=""):

    try:
        response = (
            supabase.table("member_profiles")
            .select("*")
            .not_.is_("username", "null")
            .order("username")
            .limit(200)
            .execute()
        )

        members = response.data or []

        term = str(search_text or "").strip().lower()

        if not term:
            return members

        return [
            member for member in members
            if term in str(member.get("username") or "").lower()
            or term in str(member.get("display_name") or "").lower()
        ]

    except Exception as error:
        st.error("Could not load the member directory.")
        st.caption(str(error))
        return []


# =========================================================
# 10. PEOPLE DIRECTORY
# =========================================================

def render_account_people_directory(supabase):

    st.title("Discover People")
    st.caption(
        "Find members, explore profiles and connect with the community."
    )

    search_text = st.text_input(
        "🔍 Search members",
        placeholder="Search username or display name...",
        key="account_people_search"
    )

    current_user_id = account_user_id()

    members = search_account_profiles(
        supabase,
        search_text
    )

    members = [
        member for member in members
        if str(member.get("user_id")) != current_user_id
    ]

    if not members:
        st.info("No matching members found.")
        return

    selected_id = st.session_state.get(
        "account_selected_public_profile"
    )

    if selected_id:

        selected = next(
            (
                member for member in members
                if str(member.get("user_id")) == str(selected_id)
            ),
            None
        )

        if selected:
            if st.button("← Back to people"):
                st.session_state["account_selected_public_profile"] = None
                st.rerun()

            st.divider()
            render_account_public_profile(supabase, selected)
            return

    for member in members:

        member_id = str(member.get("user_id"))

        with st.container(border=True):

            col1, col2, col3 = st.columns([1, 3, 1])

            avatar_url = account_signed_image(
                supabase,
                member.get("avatar_url")
            )

            with col1:

                if avatar_url:
                    st.image(avatar_url, width=65)
                else:
                    st.markdown("### 👤")

            with col2:

                st.markdown(
                    f"**{account_escape(member.get('display_name') or 'EcoLoop Member')}**"
                )

                st.caption(
                    f"@{account_escape(member.get('username') or '')}"
                )

                if member.get("location"):
                    st.caption(f"📍 {member['location']}")

                if member.get("bio"):
                    st.caption(member["bio"][:120])

            with col3:

                if st.button(
                    "View",
                    key=f"account_directory_view_{member_id}"
                ):
                    st.session_state[
                        "account_selected_public_profile"
                    ] = member_id

                    st.rerun()


# =========================================================
# 11. MY PROFILE PAGE
# =========================================================

def render_account_profile_page(supabase):

    user_id = account_user_id()
    user = st.session_state.get("user")

    if not user_id:
        st.warning("Please log in to view your profile.")
        return

    profile = account_profile(supabase, user_id)

    st.title("My EcoLoop Profile")
    st.caption(
        "Manage your identity and connections in EcoLoop Node."
    )

    tab1, tab2 = st.tabs([
        "My Profile",
        "Edit Profile"
    ])

    with tab1:

        if profile.get("username"):
            render_account_public_profile(supabase, profile)
        else:
            st.info(
                "Your community profile is not complete yet."
            )

            st.write(
                "Add a username and profile details so other members can discover you."
            )

        st.divider()

        if st.button(
            "Discover People",
            use_container_width=True
        ):
            st.session_state["eco_community_section"] = "Discover People"
            st.session_state["current_page"] = "Community Groups"
            st.rerun()

    with tab2:

        render_account_profile_editor(
            supabase,
            user_id,
            user
        )


# =========================================================
# 12. COMMUNITY PROFILE PAGE
# =========================================================

def render_account_community_profiles_page(supabase):

    user_id = account_user_id()

    if not user_id:
        st.warning("Please log in first.")
        return

    render_account_people_directory(supabase)


# =========================================================
# 13. MODULE ENTRY POINT
# =========================================================

def render_account_profiles(supabase, page="profile"):

    if page == "people":
        render_account_people_directory(supabase)

    else:
        render_account_profile_page(supabase)
