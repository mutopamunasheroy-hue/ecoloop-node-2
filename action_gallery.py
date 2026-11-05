# ============================================================
# ECOLOOP NODE — ACTION GALLERY
# Separate module: action_gallery.py
# ============================================================

import streamlit as st
import uuid
import mimetypes
from datetime import datetime, timezone

BUCKET = "action-gallery"

CATEGORIES = [
    "Clean-up",
    "Recycling",
    "Tree Planting",
    "Conservation",
    "Climate Action",
    "Environmental Innovation",
    "Community Initiative",
    "Other",
]

REACTIONS = {
    "like": "👍",
    "love": "❤️",
    "laugh": "😂",
    "wow": "😮",
    "clap": "👏",
    "green": "🌱",
}


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def _data(response):
    return getattr(response, "data", response)


def _profile_names(supabase, user_ids):
    user_ids = list(set(user_ids))

    if not user_ids:
        return {}

    response = (
        supabase.table("profiles")
        .select("id, full_name")
        .in_("id", user_ids)
        .execute()
    )

    rows = _data(response) or []

    return {
        row["id"]: row.get("full_name") or "EcoLoop Member"
        for row in rows
    }


def _signed_media_url(supabase, path):
    if not path:
        return None

    try:
        result = (
            supabase.storage
            .from_(BUCKET)
            .create_signed_url(path, 3600)
        )

        result = _data(result)

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
            )

    except Exception:
        return None

    return None


def _get_groups(supabase, user_id):
    memberships = (
        supabase.table("group_memberships")
        .select("group_id")
        .eq("user_id", user_id)
        .eq("status", "approved")
        .execute()
    )

    membership_rows = _data(memberships) or []
    group_ids = list({
        row["group_id"] for row in membership_rows
        if row.get("group_id")
    })

    if not group_ids:
        return []

    groups = (
        supabase.table("community_groups")
        .select("id, name")
        .in_("id", group_ids)
        .order("name")
        .execute()
    )

    return _data(groups) or []


def _record_view(supabase, post_id, user_id):
    try:
        existing = (
            supabase.table("action_post_views")
            .select("id")
            .eq("post_id", post_id)
            .eq("viewer_id", user_id)
            .limit(1)
            .execute()
        )

        if not (_data(existing) or []):
            supabase.table("action_post_views").insert({
                "post_id": post_id,
                "viewer_id": user_id,
            }).execute()

    except Exception:
        pass


def _reaction_counts(supabase, post_id):
    result = (
        supabase.table("action_post_reactions")
        .select("reaction")
        .eq("post_id", post_id)
        .execute()
    )

    counts = {key: 0 for key in REACTIONS}

    for row in (_data(result) or []):
        reaction = row.get("reaction")

        if reaction in counts:
            counts[reaction] += 1

    return counts


# ------------------------------------------------------------
# CREATE A POST
# ------------------------------------------------------------

def _create_post(
    supabase,
    user_id,
    caption,
    category,
    uploaded_file,
    author_type,
    group_id,
    location,
    social_handle,
):
    if not caption.strip():
        st.error("Please write a caption before publishing.")
        return

    if uploaded_file is None:
        st.error("Please select a photo or video.")
        return

    file_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "application/octet-stream"

    if not (
        mime_type.startswith("image/")
        or mime_type.startswith("video/")
    ):
        st.error("Please select a supported photo or video.")
        return

    media_type = "video" if mime_type.startswith("video/") else "image"

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    safe_name = f"{uuid.uuid4().hex}.{extension}"
    storage_path = f"{user_id}/{safe_name}"

    try:
        supabase.storage.from_(BUCKET).upload(
            storage_path,
            file_bytes,
            file_options={
                "content-type": mime_type,
                "upsert": "false",
            },
        )

        handles = {}

        if social_handle.strip():
            handles["social"] = social_handle.strip()

        post_data = {
            "user_id": user_id,
            "group_id": group_id,
            "author_type": author_type,
            "caption": caption.strip(),
            "category": category,
            "image_path": storage_path,
            "media_type": media_type,
            "location": location.strip() or None,
            "social_handles": handles,
            "status": "published",
            "public_preview": False,
        }

        supabase.table("action_posts").insert(post_data).execute()

        st.success("Your action has been published!")
        st.rerun()

    except Exception as error:
        st.error(f"Could not publish your post: {error}")


# ------------------------------------------------------------
# REACTIONS
# ------------------------------------------------------------

def _show_reactions(supabase, post_id, user_id):
    counts = _reaction_counts(supabase, post_id)

    existing = (
        supabase.table("action_post_reactions")
        .select("reaction")
        .eq("post_id", post_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    existing_rows = _data(existing) or []
    current_reaction = (
        existing_rows[0]["reaction"] if existing_rows else None
    )

    st.caption("React to this action")

    columns = st.columns(6)

    for index, (reaction, emoji) in enumerate(REACTIONS.items()):
        with columns[index]:
            label = f"{emoji} {counts[reaction]}"

            if current_reaction == reaction:
                label = f"✓ {emoji} {counts[reaction]}"

            if st.button(
                label,
                key=f"reaction_{post_id}_{reaction}",
                use_container_width=True,
            ):
                try:
                    if current_reaction == reaction:
                        (
                            supabase.table("action_post_reactions")
                            .delete()
                            .eq("post_id", post_id)
                            .eq("user_id", user_id)
                            .execute()
                        )
                    elif current_reaction:
                        (
                            supabase.table("action_post_reactions")
                            .update({"reaction": reaction})
                            .eq("post_id", post_id)
                            .eq("user_id", user_id)
                            .execute()
                        )
                    else:
                        (
                            supabase.table("action_post_reactions")
                            .insert({
                                "post_id": post_id,
                                "user_id": user_id,
                                "reaction": reaction,
                            })
                            .execute()
                        )

                    st.rerun()

                except Exception as error:
                    st.error(f"Reaction failed: {error}")


# ------------------------------------------------------------
# COMMENTS AND REPLIES
# ------------------------------------------------------------

def _show_comments(supabase, post_id, user_id, names):
    st.markdown("**Comments and replies**")

    result = (
        supabase.table("action_post_comments")
        .select("*")
        .eq("post_id", post_id)
        .order("created_at")
        .execute()
    )

    comments = _data(result) or []

    roots = [
        comment for comment in comments
        if not comment.get("parent_comment_id")
    ]

    replies = [
        comment for comment in comments
        if comment.get("parent_comment_id")
    ]

    new_comment = st.text_input(
        "Write a comment",
        key=f"new_comment_{post_id}",
        placeholder="Share your thoughts... 🌱",
    )

    if st.button(
        "Post comment",
        key=f"send_comment_{post_id}",
    ):
        if new_comment.strip():
            try:
                supabase.table("action_post_comments").insert({
                    "post_id": post_id,
                    "user_id": user_id,
                    "comment": new_comment.strip(),
                }).execute()

                st.rerun()

            except Exception as error:
                st.error(f"Comment failed: {error}")

    for comment in roots:
        comment_id = comment["id"]
        owner_name = names.get(
            comment["user_id"], "EcoLoop Member"
        )

        st.markdown(
            f"**{owner_name}:** {comment['comment']}"
        )

        if comment["user_id"] == user_id:
            if st.button(
                "Delete comment",
                key=f"delete_comment_{comment_id}",
            ):
                (
                    supabase.table("action_post_comments")
                    .delete()
                    .eq("id", comment_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                st.rerun()

        for reply in replies:
            if reply.get("parent_comment_id") == comment_id:
                reply_name = names.get(
                    reply["user_id"], "EcoLoop Member"
                )

                st.markdown(
                    f"&nbsp;&nbsp;↳ **{reply_name}:** "
                    f"{reply['comment']}"
                )

                if reply["user_id"] == user_id:
                    if st.button(
                        "Delete reply",
                        key=f"delete_reply_{reply['id']}",
                    ):
                        (
                            supabase.table("action_post_comments")
                            .delete()
                            .eq("id", reply["id"])
                            .eq("user_id", user_id)
                            .execute()
                        )
                        st.rerun()

        with st.expander("Reply"):
            reply_text = st.text_input(
                "Write a reply",
                key=f"reply_text_{comment_id}",
            )

            if st.button(
                "Send reply",
                key=f"send_reply_{comment_id}",
            ):
                if reply_text.strip():
                    try:
                        supabase.table(
                            "action_post_comments"
                        ).insert({
                            "post_id": post_id,
                            "user_id": user_id,
                            "comment": reply_text.strip(),
                            "parent_comment_id": comment_id,
                        }).execute()

                        st.rerun()

                    except Exception as error:
                        st.error(f"Reply failed: {error}")


# ------------------------------------------------------------
# SHARE
# ------------------------------------------------------------

def _share_post(supabase, post_id, user_id):
    if st.button(
        "↗ Share",
        key=f"share_{post_id}",
    ):
        try:
            supabase.table("action_post_shares").insert({
                "post_id": post_id,
                "user_id": user_id,
                "share_type": "internal",
            }).execute()

            st.success("Post shared inside EcoLoop!")
            st.rerun()

        except Exception as error:
            st.error(f"Could not share post: {error}")


# ------------------------------------------------------------
# POST OWNER AND MODERATOR TOOLS
# ------------------------------------------------------------

def _post_tools(
    supabase,
    post,
    user_id,
    user_role,
):
    post_id = post["id"]
    is_owner = post["user_id"] == user_id
    is_moderator = user_role in (
        "coordinator",
        "admin",
        "super_admin",
    )

    if not (is_owner or is_moderator):
        return

    with st.expander("Post management"):
        if is_owner:
            new_caption = st.text_area(
                "Edit your caption",
                value=post.get("caption", ""),
                key=f"edit_caption_{post_id}",
            )

            if st.button(
                "Save caption",
                key=f"save_caption_{post_id}",
            ):
                try:
                    supabase.table("action_posts").update({
                        "caption": new_caption.strip(),
                    }).eq("id", post_id).execute()

                    st.success("Caption updated.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Update failed: {error}")

            public_preview = st.checkbox(
                "Allow this post to appear in public previews",
                value=bool(post.get("public_preview")),
                key=f"preview_{post_id}",
            )

            if st.button(
                "Save preview setting",
                key=f"save_preview_{post_id}",
            ):
                (
                    supabase.table("action_posts")
                    .update({
                        "public_preview": public_preview,
                    })
                    .eq("id", post_id)
                    .execute()
                )
                st.success("Preview setting saved.")
                st.rerun()

        if is_moderator:
            if post.get("status") == "published":
                if st.button(
                    "Hide post",
                    key=f"hide_{post_id}",
                ):
                    (
                        supabase.table("action_posts")
                        .update({"status": "hidden"})
                        .eq("id", post_id)
                        .execute()
                    )
                    st.rerun()

            else:
                if st.button(
                    "Restore post",
                    key=f"restore_{post_id}",
                ):
                    (
                        supabase.table("action_posts")
                        .update({"status": "published"})
                        .eq("id", post_id)
                        .execute()
                    )
                    st.rerun()

        if is_owner or is_moderator:
            if st.button(
                "Delete post",
                key=f"delete_post_{post_id}",
            ):
                try:
                    media_path = post.get("image_path")

                    if media_path:
                        supabase.storage.from_(BUCKET).remove(
                            [media_path]
                        )

                    (
                        supabase.table("action_posts")
                        .delete()
                        .eq("id", post_id)
                        .execute()
                    )

                    st.success("Post deleted.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not delete post: {error}")


# ------------------------------------------------------------
# MAIN GALLERY PAGE
# ------------------------------------------------------------

def render_action_gallery(
    supabase,
    user_id,
    user_name="EcoLoop Member",
    user_role="member",
):
    st.title("🌍 Action Gallery")
    st.caption(
        "Discover Environmental Actions & Community Initiatives"
    )

    st.markdown(
        "Share the positive change happening in your community. "
        "Post photos and videos, celebrate other members, "
        "and inspire more environmental action."
    )

    # CREATE POST
    with st.expander("➕ Share an environmental action", expanded=True):
        author_type = st.radio(
            "Who is publishing?",
            ["Individual", "Community Group"],
            horizontal=True,
        )

        group_id = None

        if author_type == "Community Group":
            groups = _get_groups(supabase, user_id)

            if not groups:
                st.warning(
                    "You need approved membership in a community "
                    "group before publishing as that group."
                )
            else:
                group_options = {
                    group["name"]: group["id"]
                    for group in groups
                }

                selected_group = st.selectbox(
                    "Choose your group",
                    list(group_options.keys()),
                )

                group_id = group_options[selected_group]

        caption = st.text_area(
            "Describe your action",
            placeholder="Tell the community what happened...",
        )

        category = st.selectbox(
            "Action category",
            CATEGORIES,
        )

        uploaded_file = st.file_uploader(
            "Upload a photo or video",
            type=[
                "jpg", "jpeg", "png", "webp", "gif",
                "mp4", "webm", "mov",
            ],
            help="Maximum file size: 250 MB per file.",
        )

        location = st.text_input(
            "Location (optional)",
            placeholder="e.g. Bulawayo, Zimbabwe",
        )

        social_handle = st.text_input(
            "Public project or organisation handle (optional)",
            placeholder="e.g. @YourProject",
        )

        if uploaded_file:
            if uploaded_file.type.startswith("video/"):
                st.video(uploaded_file)
            else:
                st.image(uploaded_file, use_container_width=True)

        cannot_post_as_group = (
            author_type == "Community Group"
            and group_id is None
        )

        if st.button(
            "🚀 Publish action",
            type="primary",
            disabled=cannot_post_as_group,
            use_container_width=True,
        ):
            _create_post(
                supabase=supabase,
                user_id=user_id,
                caption=caption,
                category=category,
                uploaded_file=uploaded_file,
                author_type=(
                    "group"
                    if author_type == "Community Group"
                    else "individual"
                ),
                group_id=group_id,
                location=location,
                social_handle=social_handle,
            )

    st.divider()

    # FEED FILTERS
    st.subheader("🌱 Community Feed")

    selected_category = st.selectbox(
        "Filter by category",
        ["All categories"] + CATEGORIES,
    )

    try:
        query = (
            supabase.table("action_posts")
            .select("*")
            .eq("status", "published")
            .order("created_at", desc=True)
        )

        if selected_category != "All categories":
            query = query.eq("category", selected_category)

        response = query.execute()
        posts = _data(response) or []

    except Exception as error:
        st.error(f"Could not load the gallery: {error}")
        return

    if not posts:
        st.info(
            "No published actions yet. Be the first to share "
            "a positive environmental action!"
        )
        return

    # NAMES FOR POSTS
    user_ids = [post["user_id"] for post in posts]
    names = _profile_names(supabase, user_ids)

    # DISPLAY FEED
    for post in posts:
        post_id = post["id"]
        author_id = post["user_id"]

        author_name = names.get(author_id, "EcoLoop Member")

        st.divider()

        if post.get("author_type") == "group" and post.get("group_id"):
            try:
                group_result = (
                    supabase.table("community_groups")
                    .select("name")
                    .eq("id", post["group_id"])
                    .limit(1)
                    .execute()
                )

                group_rows = _data(group_result) or []

                if group_rows:
                    author_name = group_rows[0]["name"]

            except Exception:
                pass

        st.markdown(f"### {author_name}")
        st.caption(
            f"{post.get('category', 'Community action')} "
            f"• {post.get('location') or 'Location not provided'}"
        )

        created_at = post.get("created_at")

        if created_at:
            st.caption(f"Posted: {created_at}")

        st.write(post.get("caption", ""))

        if post.get("social_handles"):
            handle = post["social_handles"].get("social")

            if handle:
                st.caption(f"Project handle: {handle}")

        media_url = _signed_media_url(
            supabase,
            post.get("image_path"),
        )

        if media_url:
            if post.get("media_type") == "video":
                st.video(media_url)
            else:
                st.image(media_url, use_container_width=True)
        else:
            st.warning("The media for this post could not be loaded.")

        _record_view(supabase, post_id, user_id)

        _show_reactions(supabase, post_id, user_id)

        _share_post(supabase, post_id, user_id)

        _show_comments(
            supabase,
            post_id,
            user_id,
            names,
        )

        _post_tools(
            supabase,
            post,
            user_id,
            user_role,
        )

    st.divider()

    st.caption(
        "Powered by Next Gen Impact Hub (NGIH) • EcoLoop Node 2.0"
  )
