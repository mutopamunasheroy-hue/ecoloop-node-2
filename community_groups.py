
import streamlit as st
import uuid
import html
from datetime import datetime, timedelta, timezone


def render_community_groups_page(*args, **kwargs):
    supabase = (
        kwargs.get("supabase")
        or (args[0] if len(args) >= 1 else st.session_state.get("supabase_client"))
    )
    uid = (
        kwargs.get("user_id")
        or (args[1] if len(args) >= 2 else None)
        or st.session_state.get("uid")
        or st.session_state.get("user_id")
    )

    if not uid:
        try:
            user = supabase.auth.get_user().user
            uid = user.id if user else None
        except Exception:
            pass

    if not uid:
        st.warning("Please log in to access Community.")
        return

    BUCKET = "community-media"

    # --------------------------------------------------
    # STATE
    # --------------------------------------------------
    defaults = {
        "eco_new_nav": "Chats",
        "eco_new_chat_id": None,
        "eco_new_chat_user": None,
        "eco_new_profile": None,
        "eco_new_notice": None,
        "eco_new_story_user": None,
        "eco_new_search": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # --------------------------------------------------
    # STYLING
    # --------------------------------------------------
    st.markdown("""
    <style>
    .block-container {
        max-width: 650px !important;
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }
    .community-heading {
        background: #075E54;
        color: white;
        padding: 20px;
        border-radius: 16px;
        margin: 10px 0 16px 0;
    }
    .community-heading h1 {
        color: white !important;
        font-size: 27px;
        margin: 0;
    }
    .community-heading p {
        color: #D9FDD3;
        margin: 5px 0 0 0;
        font-size: 14px;
    }
    .community-card {
        background: white;
        padding: 14px;
        border-radius: 14px;
        border: 1px solid #e7e7e7;
        margin: 8px 0;
    }
    .message-mine {
        background: #D9FDD3;
        padding: 11px;
        border-radius: 13px 13px 0 13px;
        margin: 8px 0 8px 35px;
        overflow-wrap: anywhere;
    }
    .message-other {
        background: white;
        padding: 11px;
        border-radius: 13px 13px 13px 0;
        border: 1px solid #eeeeee;
        margin: 8px 35px 8px 0;
        overflow-wrap: anywhere;
    }
    .message-time {
        color: #667781;
        font-size: 10px;
        text-align: right;
        margin-top: 5px;
    }
    .community-muted {
        color: #667781;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------
    def esc(value):
        return html.escape(str(value or ""), quote=True)

    def get_profile(user_id):
        if not user_id:
            return {}
        try:
            result = (
                supabase.table("member_profiles")
                .select("*")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else {}
        except Exception:
            return {}

    def display_name(profile):
        username = (profile.get("username") or "").strip()
        if username:
            return "@" + username
        return profile.get("display_name") or "Community member"

    def storage_url(path):
        if not path:
            return ""
        if str(path).startswith("http"):
            return str(path)
        try:
            result = supabase.storage.from_(BUCKET).create_signed_url(
                str(path), 3600
            )
            if isinstance(result, dict):
                return result.get("signedURL") or result.get("signedUrl") or ""
            return ""
        except Exception:
            try:
                return supabase.storage.from_(BUCKET).get_public_url(str(path))
            except Exception:
                return ""

    def upload_media(file, folder):
        if file is None:
            return None

        try:
            extension = (
                file.name.rsplit(".", 1)[-1].lower()
                if "." in file.name else "jpg"
            )
            path = (
                f"{uid}/{folder}/"
                f"{uuid.uuid4().hex}.{extension}"
            )

            supabase.storage.from_(BUCKET).upload(
                path,
                file.getvalue(),
                {"content-type": file.type},
            )
            return path

        except Exception as error:
            st.error(f"Upload failed: {error}")
            return None

    def show_avatar(profile, width=65):
        path = profile.get("avatar_url")
        url = storage_url(path)

        if url:
            try:
                st.image(url, width=width)
                return
            except Exception:
                pass

        name = display_name(profile)
        initials = name.replace("@", "")[:2].upper() or "U"
        st.markdown(f"**{initials}**")

    def search_members(query, limit=25):
        query = (query or "").strip().replace("@", "")
        if not query:
            return []

        try:
            result = (
                supabase.table("member_profiles")
                .select("*")
                .ilike("username", f"%{query}%")
                .limit(limit)
                .execute()
            )
            profiles = result.data or []

            profiles.sort(
                key=lambda p: (
                    not (p.get("username") or "").lower().startswith(
                        query.lower()
                    ),
                    (p.get("username") or "").lower(),
                )
            )
            return profiles

        except Exception:
            return []

    def get_other_user(conversation):
        if str(conversation.get("user_one_id")) == str(uid):
            return conversation.get("user_two_id")
        return conversation.get("user_one_id")

    def open_chat(other_user_id):
        if not other_user_id or str(other_user_id) == str(uid):
            return

        try:
            existing = (
                supabase.table("direct_conversations")
                .select("*")
                .or_(
                    f"and(user_one_id.eq.{uid},user_two_id.eq.{other_user_id}),"
                    f"and(user_one_id.eq.{other_user_id},user_two_id.eq.{uid})"
                )
                .execute()
                .data or []
            )

            if existing:
                conversation_id = existing[0]["id"]
            else:
                created = (
                    supabase.table("direct_conversations")
                    .insert({
                        "user_one_id": uid,
                        "user_two_id": other_user_id,
                    })
                    .execute()
                )
                conversation_id = created.data[0]["id"]

            st.session_state["eco_new_chat_id"] = conversation_id
            st.session_state["eco_new_chat_user"] = other_user_id
            st.session_state["eco_new_profile"] = None
            st.session_state["eco_new_nav"] = "Chats"
            st.rerun()

        except Exception as error:
            st.error(f"Could not open chat: {error}")

    def back_to_chats():
        st.session_state["eco_new_chat_id"] = None
        st.session_state["eco_new_chat_user"] = None
        st.session_state["eco_new_profile"] = None
        st.rerun()

    def format_time(value):
        try:
            return datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            ).astimezone().strftime("%d %b, %H:%M")
        except Exception:
            return ""

    # --------------------------------------------------
    # TOP-LEVEL NAVIGATION
    # --------------------------------------------------
    st.button(
        "← Back to Dashboard",
        key="eco_new_back_dashboard",
        use_container_width=False,
        on_click=lambda: st.session_state.update({
            kwargs.get("dashboard_state_key", "page"):
                kwargs.get("dashboard_page", "Dashboard"),
            "eco_new_chat_id": None,
            "eco_new_chat_user": None,
            "eco_new_profile": None,
        }),
    )

    # If your main app uses a different dashboard state variable,
    # pass dashboard_state_key and dashboard_page when calling this function.

    st.markdown("""
    <div class="community-heading">
        <h1>Community</h1>
        <p>Connect. Communicate. Share.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("eco_new_notice"):
        st.success(st.session_state["eco_new_notice"])
        st.session_state["eco_new_notice"] = None

    # --------------------------------------------------
    # PROFILE SCREEN
    # --------------------------------------------------
    profile_target = st.session_state.get("eco_new_profile")

    if profile_target:
        profile = get_profile(profile_target)

        st.button(
            "← Back to Community",
            key="eco_new_profile_back",
            on_click=lambda: st.session_state.update({
                "eco_new_profile": None
            }),
        )

        st.divider()

        col1, col2 = st.columns([1, 3])

        with col1:
            show_avatar(profile, 100)

        with col2:
            st.subheader(display_name(profile))
            st.caption(profile.get("display_name") or "Community member")

            if profile.get("username"):
                st.caption("@" + profile["username"])

        st.divider()
        st.markdown("### About")

        st.write(profile.get("bio") or "No About information has been added yet.")

        if profile.get("location"):
            st.write(f"📍 Location: {profile['location']}")

        if profile.get("country_of_origin"):
            st.write(f"🌍 Country: {profile['country_of_origin']}")

        if profile.get("interests"):
            st.write(f"✨ Interests: {profile['interests']}")

        social_fields = {
            "Instagram": "instagram_handle",
            "Facebook": "facebook_handle",
            "TikTok": "tiktok_handle",
            "LinkedIn": "linkedin_handle",
        }

        for label, column in social_fields.items():
            if profile.get(column):
                st.write(f"**{label}:** {profile[column]}")

        if str(profile_target) != str(uid):
            st.divider()
            if st.button(
                "💬 Message",
                key="eco_new_profile_message",
                use_container_width=True,
            ):
                open_chat(profile_target)

        else:
            st.caption("This is your profile.")

            st.divider()
            st.markdown("### Edit your profile")

            avatar_file = st.file_uploader(
                "Upload profile picture",
                type=["jpg", "jpeg", "png", "webp"],
                key="eco_new_avatar_upload",
            )

            display_name_input = st.text_input(
                "Display name",
                value=profile.get("display_name") or "",
                key="eco_new_display_name",
            )

            bio_input = st.text_area(
                "About",
                value=profile.get("bio") or "",
                key="eco_new_bio",
            )

            location_input = st.text_input(
                "Location",
                value=profile.get("location") or "",
                key="eco_new_location",
            )

            interests_input = st.text_input(
                "Interests",
                value=profile.get("interests") or "",
                key="eco_new_interests",
            )

            if st.button(
                "Save Profile",
                key="eco_new_save_profile",
                use_container_width=True,
            ):
                update_data = {
                    "display_name": display_name_input.strip(),
                    "bio": bio_input.strip(),
                    "location": location_input.strip(),
                    "interests": interests_input.strip(),
                }

                if avatar_file:
                    avatar_path = upload_media(avatar_file, "avatars")
                    if avatar_path:
                        update_data["avatar_url"] = avatar_path

                try:
                    (
                        supabase.table("member_profiles")
                        .update(update_data)
                        .eq("user_id", uid)
                        .execute()
                    )
                    st.success("Profile updated.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not update profile: {error}")

        return

    # --------------------------------------------------
    # INDIVIDUAL CHAT SCREEN
    # --------------------------------------------------
    selected_chat = st.session_state.get("eco_new_chat_id")

    if selected_chat:
        other_id = st.session_state.get("eco_new_chat_user")
        other_profile = get_profile(other_id)

        st.button(
            "← Back to Chats",
            key="eco_new_chat_back",
            on_click=back_to_chats,
        )

        col1, col2 = st.columns([1, 4])

        with col1:
            show_avatar(other_profile, 55)

        with col2:
            st.markdown(f"**{esc(display_name(other_profile))}**")
            if st.button(
                "View Profile",
                key="eco_new_chat_view_profile",
            ):
                st.session_state["eco_new_profile"] = other_id
                st.rerun()

        st.divider()

        try:
            messages = (
                supabase.table("direct_messages")
                .select("*")
                .eq("conversation_id", selected_chat)
                .order("created_at")
                .execute()
                .data or []
            )
        except Exception as error:
            messages = []
            st.error(f"Could not load messages: {error}")

        for message in messages:
            mine = str(message.get("sender_id")) == str(uid)
            css_class = "message-mine" if mine else "message-other"

            sender_profile = (
                get_profile(message.get("sender_id"))
                if not mine else {}
            )

            sender_label = (
                f'<div><b>{esc(display_name(sender_profile))}</b></div>'
                if not mine else ""
            )

            st.markdown(
                f'<div class="{css_class}">'
                f'{sender_label}'
                f'{esc(message.get("message_text") or "")}'
                f'<div class="message-time">'
                f'{format_time(message.get("created_at"))}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            attachment = message.get("attachment_path")
            if attachment:
                media_url = storage_url(attachment)
                if media_url:
                    try:
                        if str(message.get("attachment_type") or "").startswith("video"):
                            st.video(media_url)
                        else:
                            st.image(media_url, width=280)
                    except Exception:
                        st.caption("Attachment unavailable.")

        st.divider()
        st.markdown("### Send a message")

        message_text = st.text_area(
            "Message",
            key=f"eco_new_message_{selected_chat}",
            placeholder="Write a message...",
            label_visibility="collapsed",
            height=90,
        )

        attachment_file = st.file_uploader(
            "Attach a picture or video",
            type=["jpg", "jpeg", "png", "webp", "mp4", "mov"],
            key=f"eco_new_attachment_{selected_chat}",
        )

        if st.button(
            "➤ Send",
            key=f"eco_new_send_{selected_chat}",
            use_container_width=True,
        ):
            attachment_path = None

            if attachment_file:
                attachment_path = upload_media(
                    attachment_file,
                    "direct-messages",
                )

            if message_text.strip() or attachment_path:
                try:
                    supabase.table("direct_messages").insert({
                        "conversation_id": selected_chat,
                        "sender_id": uid,
                        "message_text": message_text.strip(),
                        "attachment_path": attachment_path,
                        "attachment_type": (
                            attachment_file.type if attachment_file else None
                        ),
                        "attachment_name": (
                            attachment_file.name if attachment_file else None
                        ),
                    }).execute()

                    st.rerun()

                except Exception as error:
                    st.error(f"Message could not be sent: {error}")
            else:
                st.warning("Write a message or attach a file.")

        return

    # --------------------------------------------------
    # COMMUNITY NAVIGATION
    # --------------------------------------------------
    selected_nav = st.radio(
        "Community sections",
        ["Chats", "Stories"],
        horizontal=True,
        key="eco_new_nav",
        label_visibility="collapsed",
    )

    st.divider()

    # --------------------------------------------------
    # CHATS
    # --------------------------------------------------
    if selected_nav == "Chats":
        st.markdown("### 💬 Chats")

        search = st.text_input(
            "Search members by username",
            placeholder="Search using @username...",
            key="eco_new_member_search",
        )

        if search.strip():
            results = search_members(search)

            if not results:
                st.info("No matching members found.")

            for profile in results:
                member_id = profile.get("user_id")

                if str(member_id) == str(uid):
                    continue

                col1, col2, col3 = st.columns([1, 3, 2])

                with col1:
                    show_avatar(profile, 45)

                with col2:
                    st.write(f"**{display_name(profile)}**")
                    st.caption(profile.get("display_name") or "Community member")

                with col3:
                    if st.button(
                        "View Profile",
                        key=f"eco_new_search_profile_{member_id}",
                    ):
                        st.session_state["eco_new_profile"] = member_id
                        st.rerun()

                    if st.button(
                        "Message",
                        key=f"eco_new_search_message_{member_id}",
                    ):
                        open_chat(member_id)

                st.divider()

        st.markdown("### Your conversations")

        try:
            conversations = (
                supabase.table("direct_conversations")
                .select("*")
                .or_(f"user_one_id.eq.{uid},user_two_id.eq.{uid}")
                .execute()
                .data or []
            )
        except Exception as error:
            conversations = []
            st.error(f"Could not load chats: {error}")

        conversation_items = []

        for conversation in conversations:
            other_id = get_other_user(conversation)
            profile = get_profile(other_id)

            try:
                latest = (
                    supabase.table("direct_messages")
                    .select("message_text,created_at,attachment_path")
                    .eq("conversation_id", conversation.get("id"))
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                    .data or []
                )
            except Exception:
                latest = []

            last_message = latest[0] if latest else {}
            preview = (
                last_message.get("message_text")
                or ("📷 Attachment" if last_message.get("attachment_path") else "No messages yet")
            )

            conversation_items.append({
                "id": conversation.get("id"),
                "other_id": other_id,
                "profile": profile,
                "preview": preview,
                "created_at": last_message.get("created_at") or "",
            })

        conversation_items.sort(
            key=lambda item: item.get("created_at") or "",
            reverse=True,
        )

        if not conversation_items:
            st.info(
                "You haven't started any conversations yet. "
                "Search for a username above to find someone and start chatting."
            )

        for item in conversation_items:
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                show_avatar(item["profile"], 48)

            with col2:
                st.write(f"**{display_name(item['profile'])}**")
                st.caption(str(item["preview"])[:65])

            with col3:
                if st.button(
                    "Open Chat",
                    key=f"eco_new_open_{item['id']}",
                    use_container_width=True,
                ):
                    st.session_state["eco_new_chat_id"] = item["id"]
                    st.session_state["eco_new_chat_user"] = item["other_id"]
                    st.rerun()

                if st.button(
                    "Profile",
                    key=f"eco_new_open_profile_{item['id']}",
                    use_container_width=True,
                ):
                    st.session_state["eco_new_profile"] = item["other_id"]
                    st.rerun()

            st.divider()

        st.markdown("### Your profile")

        if st.button(
            "👤 View and edit my profile",
            key="eco_new_my_profile",
            use_container_width=True,
        ):
            st.session_state["eco_new_profile"] = uid
            st.rerun()

    # --------------------------------------------------
    # STORIES
    # --------------------------------------------------
    elif selected_nav == "Stories":
        st.markdown("### 📸 Stories")

        with st.expander("➕ Share a Story", expanded=False):
            story_file = st.file_uploader(
                "Choose a photo or video",
                type=["jpg", "jpeg", "png", "webp", "mp4", "mov"],
                key="eco_new_story_upload",
            )

            story_caption = st.text_input(
                "Add a caption",
                key="eco_new_story_caption",
            )

            if st.button(
                "Post Story",
                key="eco_new_post_story",
                use_container_width=True,
            ):
                if not story_file:
                    st.warning("Choose a photo or video first.")
                else:
                    media_path = upload_media(story_file, "stories")

                    if media_path:
                        try:
                            supabase.table("stories").insert({
                                "user_id": uid,
                                "media_url": media_path,
                                "media_type": (
                                    "video"
                                    if story_file.type.startswith("video")
                                    else "image"
                                ),
                                "caption": story_caption.strip(),
                                "expires_at": (
                                    datetime.now(timezone.utc)
                                    + timedelta(hours=24)
                                ).isoformat(),
                            }).execute()

                            st.success("Your Story has been posted.")
                            st.rerun()

                        except Exception as error:
                            st.error(f"Could not post Story: {error}")

        try:
            stories = (
                supabase.table("stories")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
                .data or []
            )
        except Exception as error:
            stories = []
            st.error(f"Could not load Stories: {error}")

        now = datetime.now(timezone.utc)
        active_stories = []

        for story in stories:
            try:
                expiry = datetime.fromisoformat(
                    str(story.get("expires_at")).replace("Z", "+00:00")
                )
                if expiry >= now:
                    active_stories.append(story)
            except Exception:
                continue

        story_users = []
        for story in active_stories:
            story_user = story.get("user_id")
            if story_user not in story_users:
                story_users.append(story_user)

        if not story_users:
            st.info("No active Stories yet. Share the first one!")

        for story_user in story_users:
            profile = get_profile(story_user)
            user_stories = [
                item for item in active_stories
                if str(item.get("user_id")) == str(story_user)
            ]

            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                show_avatar(profile, 50)

            with col2:
                st.write(f"**{display_name(profile)}**")
                st.caption(f"{len(user_stories)} active Story/Stories")

            with col3:
                if st.button(
                    "View Stories",
                    key=f"eco_new_view_stories_{story_user}",
                    use_container_width=True,
                ):
                    st.session_state["eco_new_story_user"] = story_user
                    st.rerun()

            st.divider()

        # Story viewer
        story_user = st.session_state.get("eco_new_story_user")

        if story_user:
            st.markdown("### Story viewer")

            if st.button(
                "← Close Stories",
                key="eco_new_close_stories",
            ):
                st.session_state["eco_new_story_user"] = None
                st.rerun()

            story_profile = get_profile(story_user)
            st.write(f"**{display_name(story_profile)}**")

            selected_stories = [
                item for item in active_stories
                if str(item.get("user_id")) == str(story_user)
            ]

            for story in selected_stories:
                if story.get("caption"):
                    st.write(story["caption"])

                media_url = storage_url(story.get("media_url"))

                if media_url:
                    try:
                        if story.get("media_type") == "video":
                            st.video(media_url)
                        else:
                            st.image(media_url, use_container_width=True)
                    except Exception:
                        st.caption("Story media could not be displayed.")

                if str(story_user) != str(uid):
                    try:
                        already_viewed = (
                            supabase.table("story_views")
                            .select("id")
                            .eq("story_id", story.get("id"))
                            .eq("viewer_id", uid)
                            .execute()
                            .data or []
                        )

                        if not already_viewed:
                            supabase.table("story_views").insert({
                                "story_id": story.get("id"),
                                "viewer_id": uid,
                            }).execute()
                    except Exception:
                        pass

                st.divider()
