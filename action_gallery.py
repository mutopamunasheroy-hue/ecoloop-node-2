ACTION_GALLERY_BUILD = "NOV06_V2"
# ============================================================
# ECOLOOP NODE — ACTION GALLERY
# Next Gen Impact Hub (NGIH)
# Complete Community Action Feed
# ============================================================

import streamlit as st
import uuid
import mimetypes
import re
import os

from datetime import datetime, timezone
from urllib.parse import quote


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

EXTRA_REACTIONS = [
    "🔥", "💚", "🌍", "♻️", "💯",
    "🙌", "😍", "🤔", "😢", "🌳",
    "🌿", "💪", "✨",
]

MODERATOR_ROLES = (
    "coordinator",
    "admin",
    "super_admin",
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def _data(response):
    return getattr(response, "data", response)


def _rows(response):
    return _data(response) or []


def _profile_names(supabase, user_ids):
    user_ids = list(set(uid for uid in user_ids if uid))

    if not user_ids:
        return {}

    try:
        result = (
            supabase.table("profiles")
            .select("id, full_name")
            .in_("id", user_ids)
            .execute()
        )

        return {
            row["id"]: row.get("full_name") or "EcoLoop Member"
            for row in _rows(result)
        }

    except Exception:
        return {}


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


def _format_timestamp(value):
    if not value:
        return ""

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).strftime(
            "%d %b %Y, %H:%M UTC"
        )

    except Exception:
        return str(value)


def _is_moderator(user_role):
    return str(user_role or "").lower() in MODERATOR_ROLES


def _get_groups(supabase, user_id):
    try:
        memberships = (
            supabase.table("group_memberships")
            .select("group_id")
            .eq("user_id", user_id)
            .eq("status", "approved")
            .execute()
        )

        group_ids = list({
            row["group_id"]
            for row in _rows(memberships)
            if row.get("group_id")
        })

        if not group_ids:
            return []

        result = (
            supabase.table("community_groups")
            .select("id, name")
            .in_("id", group_ids)
            .order("name")
            .execute()
        )

        return _rows(result)

    except Exception:
        return []


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

        if not _rows(existing):
            supabase.table("action_post_views").insert({
                "post_id": post_id,
                "viewer_id": user_id,
            }).execute()

    except Exception:
        pass


# ============================================================
# CREATE POSTS
# ============================================================

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
        st.error("Please write something about your action.")
        return

    if uploaded_file is None:
        st.error("Please upload a photo or video.")
        return

    mime_type = (
        uploaded_file.type
        or mimetypes.guess_type(uploaded_file.name)[0]
        or "application/octet-stream"
    )

    if not (
        mime_type.startswith("image/")
        or mime_type.startswith("video/")
    ):
        st.error("Please upload a supported image or video.")
        return

    media_type = (
        "video" if mime_type.startswith("video/") else "image"
    )

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    storage_path = f"{user_id}/{uuid.uuid4().hex}.{extension}"

    try:
        supabase.storage.from_(BUCKET).upload(
            storage_path,
            uploaded_file.getvalue(),
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

        supabase.table("action_posts").insert(
            post_data
        ).execute()

        st.success("Your action has been published!")
        st.rerun()

    except Exception as error:
        st.error(f"Could not publish your post: {error}")


def _post_creation_form(supabase, user_id):
    with st.expander("➕ Share a community action", expanded=False):

        caption = st.text_area(
            "Tell the community about your action",
            placeholder="What have you done for your community or environment?",
            key="gallery_new_caption",
        )

        category = st.selectbox(
            "Action category",
            CATEGORIES,
            key="gallery_new_category",
        )

        uploaded_file = st.file_uploader(
            "Upload a photo or video",
            type=[
                "jpg", "jpeg", "png", "webp",
                "mp4", "mov", "webm",
            ],
            key="gallery_new_media",
        )

        groups = _get_groups(supabase, user_id)

        author_type = st.radio(
            "Who is sharing this action?",
            ["Individual", "Community group"],
            horizontal=True,
            key="gallery_author_type",
        )

        group_id = None

        if author_type == "Community group":
            if not groups:
                st.warning(
                    "You need to be an approved member of a group "
                    "before publishing as a group."
                )
            else:
                selected_group = st.selectbox(
                    "Choose your group",
                    groups,
                    format_func=lambda item: item.get("name", "Group"),
                    key="gallery_selected_group",
                )

                group_id = selected_group["id"]

        location = st.text_input(
            "Location (optional)",
            key="gallery_location",
        )

        social_handle = st.text_input(
            "Social media handle (optional)",
            key="gallery_social",
        )

        if st.button(
            "Publish action",
            type="primary",
            use_container_width=True,
            key="gallery_publish_button",
        ):
            if author_type == "Community group" and not group_id:
                st.error("Please select an approved group.")
            else:
                _create_post(
                    supabase,
                    user_id,
                    caption,
                    category,
                    uploaded_file,
                    author_type.lower(),
                    group_id,
                    location,
                    social_handle,
                )


# ============================================================
# REACTIONS
# ============================================================

def _reaction_counts(supabase, post_id):
    try:
        result = (
            supabase.table("action_post_reactions")
            .select("reaction")
            .eq("post_id", post_id)
            .execute()
        )

        counts = {}

        for row in _rows(result):
            reaction = row.get("reaction")
            if reaction:
                counts[reaction] = counts.get(reaction, 0) + 1

        return counts

    except Exception:
        return {}


def _set_reaction(supabase, post_id, user_id, reaction):
    try:
        existing = (
            supabase.table("action_post_reactions")
            .select("id, reaction")
            .eq("post_id", post_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        existing_rows = _rows(existing)

        if existing_rows:
            old = existing_rows[0]

            if old.get("reaction") == reaction:
                supabase.table("action_post_reactions").delete().eq(
                    "id", old["id"]
                ).execute()
            else:
                supabase.table("action_post_reactions").update({
                    "reaction": reaction
                }).eq("id", old["id"]).execute()

        else:
            supabase.table("action_post_reactions").insert({
                "post_id": post_id,
                "user_id": user_id,
                "reaction": reaction,
            }).execute()

        st.rerun()

    except Exception as error:
        st.error(f"Could not save reaction: {error}")


def _show_reactions(supabase, post_id, user_id):
    counts = _reaction_counts(supabase, post_id)

    try:
        mine = (
            supabase.table("action_post_reactions")
            .select("reaction")
            .eq("post_id", post_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        mine_rows = _rows(mine)
        current = mine_rows[0]["reaction"] if mine_rows else None

    except Exception:
        current = None

    st.caption("React to this action")

    cols = st.columns(6)

    for index, (key, emoji) in enumerate(REACTIONS.items()):
        with cols[index]:
            label = f"{emoji} {counts.get(emoji, 0)}"

            if st.button(
                label,
                key=f"reaction_{post_id}_{key}",
                type="primary" if current == emoji else "secondary",
                use_container_width=True,
            ):
                _set_reaction(
                    supabase, post_id, user_id, emoji
                )

    with st.popover("More reactions"):
        extra_cols = st.columns(4)

        for index, emoji in enumerate(EXTRA_REACTIONS):
            with extra_cols[index % 4]:
                if st.button(
                    f"{emoji} {counts.get(emoji, 0)}",
                    key=f"extra_reaction_{post_id}_{index}",
                    use_container_width=True,
                ):
                    _set_reaction(
                        supabase, post_id, user_id, emoji
                    )


# ============================================================
# SHARING
# ============================================================

def _share_post(supabase, post, user_id):
    post_id = post["id"]

    st.caption("Share this community action")

    public_url = os.environ.get("ECLOOP_PUBLIC_URL", "").strip()

    if public_url:
        share_url = f"{public_url.rstrip('/')}/?post={post_id}"
    else:
        share_url = f"EcoLoop Node — Community Action ID: {post_id}"

    share_text = (
        f"{post.get('caption', '')}\n\n"
        f"Shared from EcoLoop Node — NGIH\n"
        f"{share_url}"
    )

    whatsapp_url = (
        "https://wa.me/?text=" + quote(share_text)
    )

    st.markdown(
        f"[<icon name='message-circle' /> Share using WhatsApp]({whatsapp_url})"
    )

    st.code(share_text, language="text")

    if st.button(
        "Record share",
        key=f"record_share_{post_id}",
    ):
        try:
            supabase.table("action_post_shares").insert({
                "post_id": post_id,
                "user_id": user_id,
            }).execute()

            st.success("Share recorded.")

        except Exception as error:
            st.error(f"Could not record share: {error}")


# ============================================================
# REPOSTING
# ============================================================

def _repost_post(supabase, post, user_id, user_name):
    post_id = post["id"]

    if post.get("is_repost"):
        st.info("This is already a repost.")
        return

    try:
        existing = (
            supabase.table("action_posts")
            .select("id")
            .eq("user_id", user_id)
            .eq("original_post_id", post_id)
            .limit(1)
            .execute()
        )

        if _rows(existing):
            st.info("You have already reposted this action.")
            return

        original_author = post.get("user_id")
        names = _profile_names(supabase, [original_author])

        handles = {
            "original_author_name": names.get(
                original_author, "EcoLoop Member"
            )
        }

        supabase.table("action_posts").insert({
            "user_id": user_id,
            "author_type": "individual",
            "caption": post.get("caption", ""),
            "category": post.get("category", "Other"),
            "image_path": post.get("image_path"),
            "media_type": post.get("media_type"),
            "location": post.get("location"),
            "social_handles": handles,
            "status": "published",
            "public_preview": False,
            "is_repost": True,
            "original_post_id": post_id,
        }).execute()

        st.success("Action reposted to your feed.")
        st.rerun()

    except Exception as error:
        st.error(f"Could not repost: {error}")


# ============================================================
# COMMENT SPAM CHECK
# ============================================================

def _spam_reason(text, recent_comments):
    content = text.strip()

    if len(content) > 2000:
        return "Unusually long comment"

    links = re.findall(
        r"https?://|www\.",
        content.lower()
    )

    if len(links) >= 3:
        return "Multiple links detected"

    if re.search(r"(.)\1{9,}", content):
        return "Repeated characters detected"

    for row in recent_comments:
        if row.get("comment", "").strip().lower() == content.lower():
            return "Repeated comment detected"

    return None


# ============================================================
# REPORTING
# ============================================================

def _report_item(
    supabase,
    user_id,
    reason,
    post_id=None,
    comment_id=None,
    details="",
):
    try:
        supabase.table("action_gallery_reports").insert({
            "reporter_id": user_id,
            "post_id": post_id,
            "comment_id": comment_id,
            "reason": reason,
            "details": details.strip() or None,
            "status": "pending",
        }).execute()

        st.success("Report submitted for moderator review.")

    except Exception as error:
        message = str(error).lower()

        if "duplicate" in message or "unique" in message:
            st.info("You have already reported this item.")
        else:
            st.error(f"Could not submit report: {error}")


def _report_controls(
    supabase,
    user_id,
    post_id=None,
    comment_id=None,
    key="report",
):
    with st.popover("🚩 Report"):
        reason = st.selectbox(
            "Why are you reporting this?",
            [
                "Spam",
                "Harassment or bullying",
                "Inappropriate content",
                "False or misleading information",
                "Hate or harmful language",
                "Other",
            ],
            key=f"{key}_reason",
        )

        details = st.text_area(
            "Additional details (optional)",
            key=f"{key}_details",
        )

        if st.button(
            "Submit report",
            key=f"{key}_submit",
            use_container_width=True,
        ):
            _report_item(
                supabase,
                user_id,
                reason,
                post_id=post_id,
                comment_id=comment_id,
                details=details,
            )


# ============================================================
# COMMENT HIDING
# ============================================================

def _hidden_comment_ids(supabase, user_id):
    try:
        result = (
            supabase.table("action_hidden_comments")
            .select("comment_id")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            row["comment_id"]
            for row in _rows(result)
        }

    except Exception:
        return set()


def _hide_comment(supabase, comment_id, user_id):
    try:
        supabase.table("action_hidden_comments").insert({
            "comment_id": comment_id,
            "user_id": user_id,
        }).execute()

        st.rerun()

    except Exception as error:
        st.error(f"Could not hide comment: {error}")


def _unhide_comment(supabase, comment_id, user_id):
    try:
        (
            supabase.table("action_hidden_comments")
            .delete()
            .eq("comment_id", comment_id)
            .eq("user_id", user_id)
            .execute()
        )

        st.rerun()

    except Exception as error:
        st.error(f"Could not restore comment: {error}")


# ============================================================
# COMMENTS AND REPLIES
# ============================================================

def _submit_comment(
    supabase,
    post_id,
    user_id,
    comment,
    parent_comment_id=None,
):
    comment = comment.strip()

    if not comment:
        st.warning("Please write a comment first.")
        return

    if len(comment) > 2000:
        st.warning("Your comment is too long.")
        return

    try:
        recent = (
            supabase.table("action_post_comments")
            .select("comment")
            .eq("post_id", post_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        spam_reason = _spam_reason(
            comment, _rows(recent)
        )

        comment_data = {
            "post_id": post_id,
            "user_id": user_id,
            "comment": comment,
            "parent_comment_id": parent_comment_id,
            "is_flagged": bool(spam_reason),
            "flag_reason": spam_reason,
            "moderation_status": "visible",
        }

        supabase.table("action_post_comments").insert(
            comment_data
        ).execute()

        if spam_reason:
            st.info(
                "Your comment was submitted and flagged for moderator review."
            )
        else:
            st.success("Comment added.")

        st.rerun()

    except Exception as error:
        st.error(f"Could not add comment: {error}")


def _delete_own_comment(supabase, comment_id, user_id):
    try:
        (
            supabase.table("action_post_comments")
            .delete()
            .eq("id", comment_id)
            .eq("user_id", user_id)
            .execute()
        )

        st.rerun()

    except Exception as error:
        st.error(f"Could not delete comment: {error}")


def _moderator_remove_comment(supabase, comment_id):
    try:
        (
            supabase.table("action_post_comments")
            .update({
                "moderation_status": "removed",
            })
            .eq("id", comment_id)
            .execute()
        )

        st.success("Comment removed.")
        st.rerun()

    except Exception as error:
        st.error(f"Could not remove comment: {error}")


def _show_one_comment(
    supabase,
    comment,
    replies,
    names,
    user_id,
    user_role,
    hidden_ids,
):
    comment_id = comment["id"]
    author_id = comment.get("user_id")

    if comment_id in hidden_ids:
        with st.container(border=True):
            st.caption("You have hidden this comment.")

            if st.button(
                "Show comment",
                key=f"unhide_{comment_id}",
            ):
                _unhide_comment(
                    supabase, comment_id, user_id
                )

        return

    if comment.get("moderation_status") != "visible":
        return

    with st.container(border=True):
        st.markdown(
            f"**{names.get(author_id, 'EcoLoop Member')}**"
        )

        st.write(comment.get("comment", ""))

        st.caption(
            _format_timestamp(comment.get("created_at"))
        )

        action_cols = st.columns(3)

        with action_cols[0]:
            if author_id == user_id:
                if st.button(
                    "Delete",
                    key=f"delete_comment_{comment_id}",
                ):
                    _delete_own_comment(
                        supabase, comment_id, user_id
                    )

        with action_cols[1]:
            if author_id != user_id:
                if st.button(
                    "Hide",
                    key=f"hide_comment_{comment_id}",
                ):
                    _hide_comment(
                        supabase, comment_id, user_id
                    )

        with action_cols[2]:
            _report_controls(
                supabase,
                user_id,
                comment_id=comment_id,
                key=f"comment_report_{comment_id}",
            )

        if _is_moderator(user_role):
            if st.button(
                "Moderator: remove comment",
                key=f"moderator_remove_{comment_id}",
            ):
                _moderator_remove_comment(
                    supabase, comment_id
                )

        if replies:
            with st.expander(
                f"View {len(replies)} replies"
            ):
                for reply in replies:
                    if reply.get("moderation_status") != "visible":
                        continue

                    reply_author = reply.get("user_id")

                    st.markdown(
                        f"**{names.get(reply_author, 'EcoLoop Member')}**"
                    )

                    st.write(reply.get("comment", ""))

                    st.caption(
                        _format_timestamp(
                            reply.get("created_at")
                        )
                    )

                    reply_cols = st.columns(2)

                    with reply_cols[0]:
                        if reply_author == user_id:
                            if st.button(
                                "Delete reply",
                                key=f"delete_reply_{reply['id']}",
                            ):
                                _delete_own_comment(
                                    supabase,
                                    reply["id"],
                                    user_id,
                                )

                    with reply_cols[1]:
                        _report_controls(
                            supabase,
                            user_id,
                            comment_id=reply["id"],
                            key=f"reply_report_{reply['id']}",
                        )

        with st.expander("Reply"):
            reply_text = st.text_area(
                "Write a reply",
                key=f"reply_text_{comment_id}",
            )

            if st.button(
                "Send reply",
                key=f"send_reply_{comment_id}",
            ):
                _submit_comment(
                    supabase,
                    comment.get("post_id"),
                    user_id,
                    reply_text,
                    parent_comment_id=comment_id,
                )


def _show_comments(
    supabase,
    post_id,
    user_id,
    user_role,
):
    st.markdown("#### 💬 Comments")

    try:
        result = (
            supabase.table("action_post_comments")
            .select("*")
            .eq("post_id", post_id)
            .order("created_at", desc=False)
            .execute()
        )

        comments = [
            row for row in _rows(result)
            if row.get("moderation_status") == "visible"
        ]

    except Exception as error:
        st.error(f"Could not load comments: {error}")
        comments = []

    root_comments = [
        row for row in comments
        if not row.get("parent_comment_id")
    ]

    replies_by_parent = {}

    for row in comments:
        parent = row.get("parent_comment_id")

        if parent:
            replies_by_parent.setdefault(parent, []).append(row)

    all_user_ids = [
        row.get("user_id") for row in comments
    ]

    names = _profile_names(supabase, all_user_ids)
    hidden_ids = _hidden_comment_ids(supabase, user_id)

    if not root_comments:
        st.caption("No comments yet. Start the conversation.")

    else:
        preview = root_comments[:2]

        for comment in preview:
            _show_one_comment(
                supabase,
                comment,
                replies_by_parent.get(comment["id"], []),
                names,
                user_id,
                user_role,
                hidden_ids,
            )

        if len(root_comments) > 2:
            with st.expander(
                f"View all {len(root_comments)} comments"
            ):
                for comment in root_comments[2:]:
                    _show_one_comment(
                        supabase,
                        comment,
                        replies_by_parent.get(comment["id"], []),
                        names,
                        user_id,
                        user_role,
                        hidden_ids,
                    )

    with st.form(f"new_comment_form_{post_id}"):
        new_comment = st.text_input(
            "Write a comment...",
            key=f"new_comment_{post_id}",
        )

        submitted = st.form_submit_button(
            "Comment",
            use_container_width=True,
        )

        if submitted:
            _submit_comment(
                supabase,
                post_id,
                user_id,
                new_comment,
            )


# ============================================================
# POST MANAGEMENT
# ============================================================

def _delete_post(supabase, post, user_id):
    post_id = post["id"]

    try:
        media_path = post.get("image_path")

        if media_path:
            other_posts = (
                supabase.table("action_posts")
                .select("id")
                .eq("image_path", media_path)
                .neq("id", post_id)
                .limit(1)
                .execute()
            )

            if not _rows(other_posts):
                try:
                    supabase.storage.from_(BUCKET).remove(
                        [media_path]
                    )
                except Exception:
                    pass

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


def _post_tools(
    supabase,
    post,
    user_id,
    user_role,
):
    post_id = post["id"]
    owner = post.get("user_id") == user_id
    moderator = _is_moderator(user_role)

    if not owner and not moderator:
        return

    with st.expander("⚙️ Manage post"):

        if owner:
            new_caption = st.text_area(
                "Edit caption",
                value=post.get("caption", ""),
                key=f"edit_caption_{post_id}",
            )

            if st.button(
                "Save caption",
                key=f"save_caption_{post_id}",
            ):
                try:
                    (
                        supabase.table("action_posts")
                        .update({
                            "caption": new_caption.strip()
                        })
                        .eq("id", post_id)
                        .eq("user_id", user_id)
                        .execute()
                    )

                    st.success("Caption updated.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not update caption: {error}")

        if moderator:
            if st.button(
                "Remove post from public feed",
                key=f"remove_post_{post_id}",
            ):
                try:
                    (
                        supabase.table("action_posts")
                        .update({"status": "removed"})
                        .eq("id", post_id)
                        .execute()
                    )

                    st.success("Post removed.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not remove post: {error}")

        if owner:
            public_preview = st.checkbox(
                "Allow public preview",
                value=bool(post.get("public_preview")),
                key=f"preview_{post_id}",
            )

            if st.button(
                "Save preview setting",
                key=f"save_preview_{post_id}",
            ):
                try:
                    (
                        supabase.table("action_posts")
                        .update({
                            "public_preview": public_preview
                        })
                        .eq("id", post_id)
                        .eq("user_id", user_id)
                        .execute()
                    )

                    st.success("Preview setting updated.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not update setting: {error}")

        st.divider()

        confirm_delete = st.checkbox(
            "I understand this will permanently delete the post.",
            key=f"confirm_delete_{post_id}",
        )

        if st.button(
            "Delete post",
            key=f"delete_post_{post_id}",
            disabled=not confirm_delete,
        ):
            if owner or moderator:
                _delete_post(
                    supabase, post, user_id
                )


# ============================================================
# MODERATOR REPORT QUEUE
# ============================================================

def _moderator_report_queue(
    supabase,
    user_role,
):
    if not _is_moderator(user_role):
        return

    with st.expander("🛡️ Community moderation reports"):

        try:
            result = (
                supabase.table("action_gallery_reports")
                .select("*")
                .eq("status", "pending")
                .order("created_at", desc=True)
                .execute()
            )

            reports = _rows(result)

        except Exception as error:
            st.error(f"Could not load reports: {error}")
            return

        if not reports:
            st.success("There are no pending reports.")
            return

        for report in reports:
            with st.container(border=True):
                st.markdown(
                    f"**Report reason:** {report.get('reason')}"
                )

                st.write(
                    report.get("details") or "No extra details."
                )

                st.caption(
                    _format_timestamp(report.get("created_at"))
                )

                if report.get("post_id"):
                    st.caption(
                        f"Reported post: {report['post_id']}"
                    )

                if report.get("comment_id"):
                    st.caption(
                        f"Reported comment: {report['comment_id']}"
                    )

                if st.button(
                    "Mark as reviewed",
                    key=f"review_report_{report['id']}",
                ):
                    try:
                        (
                            supabase.table("action_gallery_reports")
                            .update({
                                "status": "reviewed",
                                "reviewed_at": datetime.now(
                                    timezone.utc
                                ).isoformat(),
                            })
                            .eq("id", report["id"])
                            .execute()
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(str(error))

                if st.button(
                    "Dismiss report",
                    key=f"dismiss_report_{report['id']}",
                ):
                    try:
                        (
                            supabase.table("action_gallery_reports")
                            .update({
                                "status": "dismissed",
                                "reviewed_at": datetime.now(
                                    timezone.utc
                                ).isoformat(),
                            })
                            .eq("id", report["id"])
                            .execute()
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(str(error))

                if report.get("post_id"):
                    if st.button(
                        "Remove reported post",
                        key=f"remove_reported_post_{report['id']}",
                    ):
                        try:
                            (
                                supabase.table("action_posts")
                                .update({"status": "removed"})
                                .eq("id", report["post_id"])
                                .execute()
                            )

                            (
                                supabase.table("action_gallery_reports")
                                .update({
                                    "status": "action_taken",
                                    "reviewed_at": datetime.now(
                                        timezone.utc
                                    ).isoformat(),
                                })
                                .eq("id", report["id"])
                                .execute()
                            )

                            st.success("Post removed.")
                            st.rerun()

                        except Exception as error:
                            st.error(str(error))

                if report.get("comment_id"):
                    if st.button(
                        "Remove reported comment",
                        key=f"remove_reported_comment_{report['id']}",
                    ):
                        try:
                            (
                                supabase.table("action_post_comments")
                                .update({
                                    "moderation_status": "removed"
                                })
                                .eq("id", report["comment_id"])
                                .execute()
                            )

                            (
                                supabase.table("action_gallery_reports")
                                .update({
                                    "status": "action_taken",
                                    "reviewed_at": datetime.now(
                                        timezone.utc
                                    ).isoformat(),
                                })
                                .eq("id", report["id"])
                                .execute()
                            )

                            st.success("Comment removed.")
                            st.rerun()

                        except Exception as error:
                            st.error(str(error))


# ============================================================
# POST DISPLAY
# ============================================================

def _display_post(
    supabase,
    post,
    user_id,
    user_name,
    user_role,
    names,
    group_names,
):
    post_id = post["id"]
    author_id = post.get("user_id")

    with st.container(border=True):

        author_name = names.get(
            author_id,
            "EcoLoop Member"
        )

        if post.get("author_type") == "group":
            author_name = group_names.get(
                post.get("group_id"),
                "Community Group"
            )

        st.markdown(f"### {author_name}")

        if post.get("is_repost"):
            original_author = (
                (post.get("social_handles") or {})
                .get("original_author_name", "EcoLoop Member")
            )

            st.caption(
                f"🔁 Reposted from {original_author}"
            )

        st.caption(
            f"{post.get('category', 'Community action')} "
            f"• {_format_timestamp(post.get('created_at'))}"
        )

        if post.get("location"):
            st.caption(f"📍 {post['location']}")

        st.write(post.get("caption", ""))

        media_url = _signed_media_url(
            supabase,
            post.get("image_path"),
        )

        if media_url:
            if post.get("media_type") == "video":
                st.video(media_url)
            else:
                st.image(
                    media_url,
                    use_container_width=True,
                )

        elif post.get("image_path"):
            st.caption("Media is currently unavailable.")

        _record_view(
            supabase,
            post_id,
            user_id,
        )

        _show_reactions(
            supabase,
            post_id,
            user_id,
        )

        counts = _reaction_counts(
            supabase,
            post_id,
        )

        st.caption(
            f"💬 Community reactions: "
            f"{sum(counts.values())}"
        )

        action_cols = st.columns(3)

        with action_cols[0]:
            if post.get("user_id") != user_id:
                if st.button(
                    "🔁 Repost",
                    key=f"repost_{post_id}",
                    use_container_width=True,
                ):
                    _repost_post(
                        supabase,
                        post,
                        user_id,
                        user_name,
                    )

        with action_cols[1]:
            _report_controls(
                supabase,
                user_id,
                post_id=post_id,
                key=f"post_report_{post_id}",
            )

        with action_cols[2]:
            if st.button(
                "↗ Share",
                key=f"share_toggle_{post_id}",
                use_container_width=True,
            ):
                st.session_state[
                    f"show_share_{post_id}"
                ] = not st.session_state.get(
                    f"show_share_{post_id}", False
                )

        if st.session_state.get(
            f"show_share_{post_id}", False
        ):
            _share_post(
                supabase,
                post,
                user_id,
            )

        _show_comments(
            supabase,
            post_id,
            user_id,
            user_role,
        )

        _post_tools(
            supabase,
            post,
            user_id,
            user_role,
        )


# ============================================================
# MAIN ACTION GALLERY
# ============================================================

def render_action_gallery(
    supabase,
    user_id,
    user_name="EcoLoop Member",
    user_role="member",
):
    st.title("🌍 Action Gallery")

    st.write(
        "Discover community environmental action, "
        "share your impact and celebrate positive change."
    )

    st.caption(
        "Powered by Next Gen Impact Hub (NGIH)"
    )

    st.divider()

    _post_creation_form(
        supabase,
        user_id,
    )

    st.divider()

    filter_cols = st.columns(2)

    with filter_cols[0]:
        selected_category = st.selectbox(
            "Filter by action",
            ["All categories"] + CATEGORIES,
            key="gallery_category_filter",
        )

    with filter_cols[1]:
        feed_filter = st.selectbox(
            "Show posts",
            [
                "All community posts",
                "Individual actions",
                "Group actions",
            ],
            key="gallery_type_filter",
        )

    try:
        query = (
            supabase.table("action_posts")
            .select("*")
            .eq("status", "published")
            .order("created_at", desc=True)
        )

        if selected_category != "All categories":
            query = query.eq(
                "category",
                selected_category,
            )

        if feed_filter == "Individual actions":
            query = query.eq(
                "author_type",
                "individual",
            )

        elif feed_filter == "Group actions":
            query = query.eq(
                "author_type",
                "group",
            )

        result = query.execute()
        posts = _rows(result)

    except Exception as error:
        st.error(f"Could not load the Action Gallery: {error}")
        return

    if not posts:
        st.info(
            "No community actions have been published here yet. "
            "Be the first to share one!"
        )

    else:
        user_ids = [
            post.get("user_id")
            for post in posts
        ]

        names = _profile_names(
            supabase,
            user_ids,
        )

        group_ids = list({
            post.get("group_id")
            for post in posts
            if post.get("group_id")
        })

        group_names = {}

        if group_ids:
            try:
                groups = (
                    supabase.table("community_groups")
                    .select("id, name")
                    .in_("id", group_ids)
                    .execute()
                )

                group_names = {
                    row["id"]: row.get("name", "Community Group")
                    for row in _rows(groups)
                }

            except Exception:
                pass

        for post in posts:
            _display_post(
                supabase,
                post,
                user_id,
                user_name,
                user_role,
                names,
                group_names,
            )

    st.divider()

    _moderator_report_queue(
        supabase,
        user_role,
    )

    st.divider()

    st.caption(
        "EcoLoop Node • Next Gen Impact Hub (NGIH)"
)
