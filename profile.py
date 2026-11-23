
import streamlit as st
import uuid
from datetime import datetime, timezone

BUCKET = "community-media"


# =====================================================
# PROFILE DATA
# =====================================================

def get_member_profile(supabase, user_id):
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
        return response.data[0] if response.data else {}
    except Exception as error:
        st.error(f"Could not load profile: {error}")
        return {}


def get_display_name(profile):
    return (
        (profile or {}).get("display_name")
        or (profile or {}).get("username")
        or "EcoLoop Member"
    )


def get_avatar_url(supabase, profile):
    avatar = (profile or {}).get("avatar_url")

    if not avatar:
        return None

    if str(avatar).startswith("http"):
        return avatar

    try:
        return supabase.storage.from_(BUCKET).get_public_url(str(avatar))
    except Exception:
        return None


def clean_social(value):
    value = (value or "").strip()
    if not value:
        return ""

    if value.startswith("@"):
        return value[1:]

    return value


def social_link(platform, value):
    value = clean_social(value)

    if not value:
        return

    if value.startswith("http"):
        url = value
        label = value
    else:
        handles = {
            "Instagram": f"https://instagram.com/{value}",
            "Facebook": f"https://facebook.com/{value}",
            "TikTok": f"https://tiktok.com/@{value}",
            "LinkedIn": (
                value if "/" in value
                else f"https://linkedin.com/in/{value}"
            ),
        }

        url = handles.get(platform, value)
        label = f"@{value}" if platform != "LinkedIn" else value

    st.markdown(f"**{platform}:** [{label}]({url})")


# =====================================================
# PROFILE PHOTO UPLOAD
# =====================================================

def upload_profile_photo(supabase, user_id, uploaded_file):
    if uploaded_file is None:
        return None

    try:
        current_user = supabase.auth.get_user().user
        authenticated_uid = str(current_user.id) if current_user else None

        if authenticated_uid != str(user_id):
            st.error("Your login session could not be verified.")
            return None

        extension = (
            uploaded_file.name.rsplit(".", 1)[-1].lower()
            if "." in uploaded_file.name else "jpg"
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


# =====================================================
# SAVE PROFILE
# =====================================================

def save_member_profile(
    supabase,
    user_id,
    display_name,
    username,
    bio,
    location,
    interests,
    avatar_url=None,
    instagram="",
    facebook="",
    tiktok="",
    linkedin="",
):
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
            "instagram": instagram.strip(),
            "facebook": facebook.strip(),
            "tiktok": tiktok.strip(),
            "linkedin": linkedin.strip(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if avatar_url:
            profile_data["avatar_url"] = avatar_url

        supabase.table("member_profiles").upsert(
            profile_data,
            on_conflict="user_id"
        ).execute()

        return True

    except Exception as error:
        st.error(f"Profile could not be saved: {error}")
        return False


# =====================================================
# PROFILE CARD
# =====================================================

def render_profile_card(supabase, profile, key=None, show_button=True):
    if not profile:
        return False

    avatar = get_avatar_url(supabase, profile)
    name = get_display_name(profile)

    with st.container(border=True):
        col1, col2 = st.columns([1, 3])

        with col1:
            if avatar:
                st.image(avatar, width=90)
            else:
                st.markdown("### 👤")

        with col2:
            st.markdown(f"**{name}**")

            if profile.get("username"):
                st.caption(f"@{profile['username']}")

            if profile.get("location"):
                st.caption(f"📍 {profile['location']}")

        bio = profile.get("bio", "")
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


# =====================================================
# FULL PROFILE VIEW
# =====================================================

def render_profile_view(supabase, profile):
    if not profile:
        st.info("Profile not found.")
        return

    name = get_display_name(profile)
    avatar = get_avatar_url(supabase, profile)

    st.markdown("---")

    with st.container(border=True):
        col1, col2 = st.columns([1, 2])

        with col1:
            if avatar:
                st.image(avatar, width=160)
            else:
                st.markdown("## 👤")

        with col2:
            st.markdown(f"# {name}")

            if profile.get("username"):
                st.markdown(f"**@{profile['username']}**")

            if profile.get("location"):
                st.write(f"📍 {profile['location']}")

            if profile.get("country"):
                st.write(f"🌍 From {profile['country']}")

        st.markdown("### About")
        st.write(profile.get("bio") or "No bio added yet.")

        st.markdown("### Interests")
        st.write(profile.get("interests") or "No interests added yet.")

        st.divider()

        st.markdown("### Social links")

        found_social = False

        for platform, field in [
            ("Instagram", "instagram"),
            ("Facebook", "facebook"),
            ("TikTok", "tiktok"),
            ("LinkedIn", "linkedin"),
        ]:
            if profile.get(field):
                social_link(platform, profile[field])
                found_social = True

        if not found_social:
            st.caption("No social links added yet.")

    st.markdown("---")


# =====================================================
# MY PROFILE + EDIT PROFILE
# =====================================================

def render_profile_page(supabase, user_id):
    st.markdown("## 👤 My EcoLoop Profile")
    st.caption("Manage your identity and connections in EcoLoop Node.")

    # Display confirmation after saving
    if st.session_state.pop("profile_saved", False):
        st.success("Profile saved successfully!")

    if not user_id:
        st.warning("Please sign in to view your profile.")
        return

    profile = get_member_profile(supabase, user_id)

    name = profile.get("display_name", "")
    username = profile.get("username", "")
    bio = profile.get("bio", "")
    location = profile.get("location", "")
    country = profile.get("country", "")
    interests = profile.get("interests", "")
    instagram = profile.get("instagram", "")
    facebook = profile.get("facebook", "")
    tiktok = profile.get("tiktok", "")
    linkedin = profile.get("linkedin", "")
    avatar = get_avatar_url(supabase, profile)

    tab1, tab2 = st.tabs(["My Profile", "Edit Profile"])


    # -------------------------------------------------
    # MY PROFILE
    # -------------------------------------------------

    with tab1:
        with st.container(border=True):

            if avatar:
                st.image(avatar, width=160)
            else:
                st.markdown("## 👤")

            st.markdown(f"# {name or 'Your Name'}")

            if username:
                st.markdown(f"**@{username}**")

            if location:
                st.write(f"📍 {location}")

            if country:
                st.write(f"🌍 From {country}")

            st.markdown("### About")
            st.write(bio or "Tell the community about yourself.")

            st.markdown("### Interests")
            st.write(interests or "No interests added yet.")

            st.divider()

            st.markdown("### Social links")

            has_social = False

            for platform, field in [
                ("Instagram", "instagram"),
                ("Facebook", "facebook"),
                ("TikTok", "tiktok"),
                ("LinkedIn", "linkedin"),
            ]:
                if profile.get(field):
                    social_link(platform, profile[field])
                    has_social = True

            if not has_social:
                st.caption("Add your social media accounts in Edit Profile.")

    # -------------------------------------------------
    # EDIT PROFILE
    # -------------------------------------------------

    with tab2:
        st.markdown("### Edit your profile")
        st.caption("Your public identity in the EcoLoop community.")

        if avatar:
            st.image(avatar, width=120)

        with st.form("ecoloop_profile_form", clear_on_submit=False):

            display_name = st.text_input(
                "Display name",
                value=name,
                max_chars=60,
            )

            new_username = st.text_input(
                "Username",
                value=username,
                max_chars=30,
            )

            new_location = st.text_input(
                "Current location",
                value=location,
                max_chars=100,
            )

            new_country = st.text_input(
                "Country of origin",
                value=country,
                max_chars=100,
            )

            new_bio = st.text_area(
                "Bio",
                value=bio,
                max_chars=500,
                height=120,
            )

            new_interests = st.text_area(
                "Interests",
                value=interests,
                max_chars=300,
                height=100,
            )

            st.markdown("### Social media")

            new_instagram = st.text_input(
                "Instagram",
                value=instagram,
                placeholder="@username or profile link",
            )

            new_facebook = st.text_input(
                "Facebook",
                value=facebook,
                placeholder="Username or profile link",
            )

            new_tiktok = st.text_input(
                "TikTok",
                value=tiktok,
                placeholder="@username or profile link",
            )

            new_linkedin = st.text_input(
                "LinkedIn",
                value=linkedin,
                placeholder="Username or profile link",
            )

            uploaded_photo = st.file_uploader(
                "Profile picture",
                type=["jpg", "jpeg", "png", "webp"],
                key="ecoloop_profile_photo",
            )

            save_button = st.form_submit_button(
                "Save Profile",
                use_container_width=True,
            )

        if save_button:

            new_avatar = profile.get("avatar_url")

            if uploaded_photo is not None:
                uploaded_path = upload_profile_photo(
                    supabase,
                    user_id,
                    uploaded_photo,
                )

                if uploaded_path:
                    new_avatar = uploaded_path
                else:
                    st.warning("Photo upload failed. Other changes were not saved.")
                    st.stop()

            saved = save_member_profile(
                supabase=supabase,
                user_id=user_id,
                display_name=display_name,
                username=new_username,
                bio=new_bio,
                location=new_location,
                interests=new_interests,
                avatar_url=new_avatar,
                instagram=new_instagram,
                facebook=new_facebook,
                tiktok=new_tiktok,
                linkedin=new_linkedin,
            )

            
            if saved:
                st.session_state["profile_saved"] = True
                st.rerun()
            else:
                st.error("Profile could not be saved. Please try again.")



# =====================================================
# PROFILE LOOKUP
# =====================================================

def render_member_profile(supabase, user_id):
    profile = get_member_profile(supabase, user_id)

    if profile:
        render_profile_view(supabase, profile)
    else:
        st.info("This member has not created a profile yet.")
