# ============================================================
# ECOLOOP NODE — ACTION GALLERY 2.0
# Next Gen Impact Hub (NGIH)
# Modern Community Social Feed
# ============================================================

ACTION_GALLERY_BUILD = "NOV06_V4"

import streamlit as st
import uuid
import mimetypes
import re
import os
import html

from datetime import datetime, timezone
from urllib.parse import quote


BUCKET = "action-gallery"

PUBLIC_APP_URL = (
    "https://ecoloop-node-2-g2jtmgyszhvgynvmnzuo7d.streamlit.app"
)

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

ALL_REACTIONS = list(REACTIONS.values()) + EXTRA_REACTIONS

MODERATOR_ROLES = (
    "coordinator",
    "admin",
    "super_admin",
)


# ============================================================
# MODERN GALLERY DESIGN
# ============================================================

def _inject_gallery_styles():
    st.markdown(
        """
        <style>
        .gallery-intro {
            color: var(--text-color);
            opacity: 0.78;
            font-size: 0.94rem;
            margin-top: -8px;
            margin-bottom: 12px;
        }

        .gallery-brand {
            font-size: 0.76rem;
            opacity: 0.65;
            letter-spacing: 0.5px;
            margin-bottom: 14px;
        }

        .gallery-author {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 2px;
        }

        .gallery-meta {
            font-size: 0.78rem;
            opacity: 0.65;
            margin-bottom: 9px;
        }

        .gallery-caption {
            font-size: 0.96rem;
            line-height: 1.6;
            margin-top: 8px;
            margin-bottom: 12px;
            overflow-wrap: anywhere;
        }

        .gallery-reaction-summary {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            align-items: center;
            margin-top: 7px;
            margin-bottom: 8px;
            font-size: 0.82rem;
            opacity: 0.82;
        }

        .gallery-comment {
            padding: 9px 0;
            border-bottom: 1px solid rgba(128,128,128,0.16);
        }

        .gallery-comment-author {
            font-size: 0.88rem;
            font-weight: 700;
        }

        .gallery-comment-time {
            font-size: 0.72rem;
            opacity: 0.60;
        }

        .gallery-comment-text {
            font-size: 0.9rem;
            line-height: 1.5;
            overflow-wrap: anywhere;
            margin-top: 3px;
        }

        .gallery-reply {
            margin-left: 22px;
            padding-left: 12px;
            border-left: 2px solid rgba(128,128,128,0.25);
        }

        .gallery-section-label {
            font-size: 0.95rem;
            font-weight: 700;
            margin-top: 12px;
            margin-bottom: 4px;
        }

        div[data-testid="stPopover"] button {
            border-radius: 18px;
        }

        div[data-testid="stExpander"] {
            border-radius: 12px;
        }

        div[data-testid="stFileUploader"] {
            border-radius: 12px;
        }

        div[data-testid="stForm"] {
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# GENERAL HELPERS
# ============================================================

def _data(response):
    return getattr(response, "data", response)


def _rows(response):
    result = _data(response)

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        return [result]

    return []


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

    author_type = (
        "group"
        if author_type.lower() in ("group", "community group")
        else "individual"
    )

    if author_type == "group" and not group_id:
        st.error("Please select an approved community group.")
        return

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

        st.markdown("**Tell your community what you've done.**")

        caption = st.text_area(
            "Your story",
            placeholder=(
                "Share your environmental action, "
                "community initiative or achievement..."
            ),
            key="gallery_new_caption",
        )

        category = st.selectbox(
            "Action category",
            CATEGORIES,
            key="gallery_new_category",
        )

        uploaded_file = st.file_uploader(
            "Add a photo or video",
            type=[
                "jpg", "jpeg", "png", "webp",
                "mp4", "mov", "webm",
            ],
            key="gallery_new_media",
        )

        groups = _get_groups(supabase, user_id)

        author_type = st.radio(
            "Publish as",
            ["Individual", "Community group"],
            horizontal=True,
            key="gallery_author_type",
        )

        group_id = None

        if author_type == "Community group":
            if not groups:
                st.warning(
                    "You need approved membership in a group "
                    "before publishing as a group."
                )
            else:
                selected_group = st.selectbox(
                    "Choose your group",
                    groups,
                    format_func=lambda item: item.get(
                        "name", "Community Group"
                    ),
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
                    author_type,
                    group_id,
                    location,
                    social_handle,
                )


# ============================================================
# REACTIONS — COMPACT SOCIAL MEDIA STYLE
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


def _get_my_reaction(supabase, post_id, user_id):
    try:
        result = (
            supabase.table("action_post_reactions")
            .select("reaction")
            .eq("post_id", post_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        rows = _rows(result)

        return rows[0].get("reaction") if rows else None

    except Exception:
        return None


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
                (
                    supabase.table("action_post_reactions")
                    .delete()
                    .eq("id", old["id"])
                    .execute()
                )

            else:
                (
                    supabase.table("action_post_reactions")
                    .update({"reaction": reaction})
                    .eq("id", old["id"])
                    .execute()
                )

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

    current = _get_my_reaction(
        supabase,
        post_id,
        user_id,
    )

    total = sum(counts.values())

    label = (
        f"{current} Reacted"
        if current
        else "😊 React"
    )

    with st.popover(label):
        st.markdown("**Choose a reaction**")

        cols = st.columns(5)

        for index, emoji in enumerate(ALL_REACTIONS):
            with cols[index % 5]:
                count = counts.get(emoji, 0)

                if st.button(
                    f"{emoji} {count}",
                    key=f"reaction_{post_id}_{index}",
                    type=(
                        "primary"
                        if current == emoji
                        else "secondary"
                    ),
                    use_container_width=True,
                ):
                    _set_reaction(
                        supabase,
                        post_id,
                        user_id,
                        emoji,
                    )

    active_reactions = [
        (emoji, count)
        for emoji, count in counts.items()
        if count > 0
    ]

    if active_reactions:
        summary = "  ".join(
            f"{emoji} {count}"
            for emoji, count in active_reactions
        )

        st.markdown(
            f'<div class="gallery-reaction-summary">'
            f'{summary} · {total} reactions'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("Be the first to react.")


# ============================================================
# UNIVERSAL SHARING
# ============================================================

def _share_post(supabase, post, user_id):
    post_id = post["id"]

    public_url = os.environ.get(
        "ECLOOP_PUBLIC_URL",
        PUBLIC_APP_URL,
    ).strip()

    share_url = (
        f"{public_url.rstrip('/')}/?post={post_id}"
    )

    caption = post.get("caption", "").strip()

    share_text = (
        f"{caption}\n\n"
        f"Shared from EcoLoop Node — NGIH\n\n"
        f"Community Action ID: {post_id}\n\n"
        f"Open EcoLoop Node:\n{share_url}"
    )

    encoded_url = quote(share_url, safe="")
    encoded_text = quote(share_text, safe="")
    encoded_caption = quote(caption, safe="")

    whatsapp_url = (
        f"https://wa.me/?text={encoded_text}"
    )

    facebook_url = (
        "https://www.facebook.com/sharer/sharer.php"
        f"?u={encoded_url}"
    )

    telegram_url = (
        "https://t.me/share/url"
        f"?url={encoded_url}"
        f"&text={encoded_caption}"
    )

    x_url = (
        "https://twitter.com/intent/tweet"
        f"?text={encoded_caption}"
        f"&url={encoded_url}"
    )

    email_url = (
        "mailto:?subject="
        f"{quote('EcoLoop Node Community Action')}"
        f"&body={encoded_text}"
    )

    st.markdown("### ↗ Share this community action")

    st.caption(
        "Choose a platform or copy the EcoLoop link to share anywhere."
    )

    # First row
    col1, col2 = st.columns(2)

    with col1:
        st.link_button(
            "🟢 WhatsApp",
            whatsapp_url,
            use_container_width=True,
        )

    with col2:
        st.link_button(
            "🔵 Facebook",
            facebook_url,
            use_container_width=True,
        )

    # Second row
    col3, col4 = st.columns(2)

    with col3:
        st.link_button(
            "✈️ Telegram",
            telegram_url,
            use_container_width=True,
        )

    with col4:
        st.link_button(
            "𝕏 Share on X",
            x_url,
            use_container_width=True,
        )

    # Third row
    col5, col6 = st.columns(2)

    with col5:
        st.link_button(
            "✉️ Email",
            email_url,
            use_container_width=True,
        )

    with col6:
        st.link_button(
            "🌍 Open EcoLoop",
            share_url,
            use_container_width=True,
        )

    st.divider()

    st.markdown("**Direct link to this action**")

    st.markdown(
        f"[Open this action in EcoLoop Node]({share_url})"
    )

    st.text_input(
        "Copy this link and share it in any other app",
        value=share_url,
        key=f"share_link_{post_id}",
    )

    st.caption(
        f"Community Action ID: {post_id}"
    )

    if st.button(
        "Record share",
        key=f"record_share_{post_id}",
        use_container_width=True,
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

def _has_reposted(supabase, post_id, user_id):
    try:
        result = (
            supabase.table("action_posts")
            .select("id")
            .eq("user_id", user_id)
            .eq("original_post_id", post_id)
            .limit(1)
            .execute()
        )

        return bool(_rows(result))

    except Exception:
        return False


def _repost_post(supabase, post, user_id, user_name):
    post_id = post.get("id")

    if not post_id:
        st.error("This action could not be identified.")
        return

    if post.get("is_repost"):
        st.info("You cannot repost an action that is already a repost.")
        return

    try:
        if _has_reposted(supabase, post_id, user_id):
            st.info("You have already reposted this action.")
            return

        original_author = post.get("user_id")
        names = _profile_names(supabase, [original_author])

        handles = {
            "original_author_name": names.get(
                original_author,
                "EcoLoop Member",
            ),
            "reposted_by": user_name,
        }

        result = (
            supabase.table("action_posts")
            .insert({
                "user_id": user_id,
                "group_id": None,
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
            })
            .execute()
        )

        if not _rows(result):
            st.error(
                "The repost could not be confirmed. Please try again."
            )
            return

        st.success("Successfully reposted to your feed!")
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
        content.lower(),
    )

    if len(links) >= 3:
        return "Multiple links detected"

    if re.search(r"(.)\1{9,}", content):
        return "Repeated characters detected"

    for row in recent_comments:
        if (
            row.get("comment", "").strip().lower()
            == content.lower()
        ):
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


def _report_form(
    supabase,
    user_id,
    post_id=None,
    comment_id=None,
    key="report",
):
    reason = st.selectbox(
        "Reason for reporting",
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
# SUBMIT COMMENTS AND REPLIES
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
            comment,
            _rows(recent),
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
                "Your comment was submitted and flagged "
                "for moderator review."
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


# ============================================================
# COMMENT OPTIONS
# ============================================================

def _comment_options(
    supabase,
    comment,
    user_id,
    user_role,
):
    comment_id = comment["id"]
    author_id = comment.get("user_id")

    with st.popover("⋯"):
        st.caption("Comment options")

        if str(author_id) == str(user_id):
            if st.button(
                "🗑️ Delete comment",
                key=f"delete_comment_{comment_id}",
                use_container_width=True,
            ):
                _delete_own_comment(
                    supabase,
                    comment_id,
                    user_id,
                )

        else:
            if st.button(
                "Hide comment",
                key=f"hide_comment_{comment_id}",
                use_container_width=True,
            ):
                _hide_comment(
                    supabase,
                    comment_id,
                    user_id,
                )

        st.divider()

        st.markdown("**Report comment**")

        _report_form(
            supabase,
            user_id,
            comment_id=comment_id,
            key=f"comment_report_{comment_id}",
        )

        if _is_moderator(user_role):
            st.divider()

            if st.button(
                "🛡️ Moderator: remove comment",
                key=f"moderator_remove_{comment_id}",
                use_container_width=True,
            ):
                _moderator_remove_comment(
                    supabase,
                    comment_id,
                )


# ============================================================
# DISPLAY ONE COMMENT
# ============================================================

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
        st.caption("You have hidden this comment.")

        if st.button(
            "Show comment",
            key=f"unhide_{comment_id}",
        ):
            _unhide_comment(
                supabase,
                comment_id,
                user_id,
            )

        return

    if comment.get("moderation_status") != "visible":
        return

    author_col, menu_col = st.columns([0.88, 0.12])

    with author_col:
        st.markdown(
            f'<div class="gallery-comment-author">'
            f'{html.escape(names.get(author_id, "EcoLoop Member"))}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="gallery-comment-time">'
            f'{_format_timestamp(comment.get("created_at"))}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with menu_col:
        _comment_options(
            supabase,
            comment,
            user_id,
            user_role,
        )

    st.markdown(
        '<div class="gallery-comment-text">',
        unsafe_allow_html=True,
    )

    st.write(comment.get("comment", ""))

    st.markdown("</div>", unsafe_allow_html=True)

    # Replies
    if replies:
        st.caption(f"↳ {len(replies)} replies")

        for reply in replies:
            if reply["id"] in hidden_ids:
                continue

            if reply.get("moderation_status") != "visible":
                continue

            reply_author = reply.get("user_id")

            with st.container():
                st.markdown(
                    '<div class="gallery-reply">',
                    unsafe_allow_html=True,
                )

                reply_cols = st.columns([0.88, 0.12])

                with reply_cols[0]:
                    st.markdown(
                        f"**{html.escape(names.get(reply_author, 'EcoLoop Member'))}**"
                    )

                    st.caption(
                        _format_timestamp(
                            reply.get("created_at")
                        )
                    )

                with reply_cols[1]:
                    _comment_options(
                        supabase,
                        reply,
                        user_id,
                        user_role,
                    )

                st.write(reply.get("comment", ""))

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )

    # Reply control
    with st.expander("↩ Reply"):
        reply_text = st.text_area(
            "Write a reply",
            key=f"reply_text_{comment_id}",
            label_visibility="collapsed",
            placeholder="Write your reply...",
        )

        if st.button(
            "Send reply",
            key=f"send_reply_{comment_id}",
            type="primary",
        ):
            _submit_comment(
                supabase,
                comment.get("post_id"),
                user_id,
                reply_text,
                parent_comment_id=comment_id,
            )


# ============================================================
# COMMENTS SECTION
# ============================================================

def _show_comments(
    supabase,
    post_id,
    user_id,
    user_role,
):
    st.markdown(
        '<div class="gallery-section-label">💬 Comments</div>',
        unsafe_allow_html=True,
    )

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
            replies_by_parent.setdefault(
                parent, []
            ).append(row)

    all_user_ids = [
        row.get("user_id")
        for row in comments
    ]

    names = _profile_names(
        supabase,
        all_user_ids,
    )

    hidden_ids = _hidden_comment_ids(
        supabase,
        user_id,
    )

    if not root_comments:
        st.caption(
            "No comments yet. Start the conversation."
        )

    else:
        preview = root_comments[:2]

        for comment in preview:
            _show_one_comment(
                supabase,
                comment,
                replies_by_parent.get(
                    comment["id"], []
                ),
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
                        replies_by_parent.get(
                            comment["id"], []
                        ),
                        names,
                        user_id,
                        user_role,
                        hidden_ids,
                    )

    with st.form(
        f"new_comment_form_{post_id}",
        clear_on_submit=True,
    ):
        new_comment = st.text_input(
            "Add a comment",
            key=f"new_comment_{post_id}",
            placeholder="Write a comment...",
        )

        submitted = st.form_submit_button(
            "Post comment",
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
# POST DELETION
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


# ============================================================
# POST OPTIONS
# ============================================================

def _post_tools(
    supabase,
    post,
    user_id,
    user_role,
):
    post_id = post["id"]
    owner = str(post.get("user_id")) == str(user_id)
    moderator = _is_moderator(user_role)

    with st.popover("⋯ Post options"):

        st.caption("Post options")

        st.markdown("**Report this post**")

        _report_form(
            supabase,
            user_id,
            post_id=post_id,
            key=f"post_report_{post_id}",
        )

        if owner:
            st.divider()
            st.markdown("**Edit your post**")

            new_caption = st.text_area(
                "Edit caption",
                value=post.get("caption", ""),
                key=f"edit_caption_{post_id}",
            )

            if st.button(
                "Save caption",
                key=f"save_caption_{post_id}",
                use_container_width=True,
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
                    st.error(
                        f"Could not update caption: {error}"
                    )

            st.divider()

            public_preview = st.checkbox(
                "Allow public preview",
                value=bool(post.get("public_preview")),
                key=f"preview_{post_id}",
            )

            if st.button(
                "Save preview setting",
                key=f"save_preview_{post_id}",
                use_container_width=True,
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
                    st.error(
                        f"Could not update setting: {error}"
                    )

        if moderator:
            st.divider()

            if st.button(
                "🛡️ Remove post from public feed",
                key=f"remove_post_{post_id}",
                use_container_width=True,
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
                    st.error(
                        f"Could not remove post: {error}"
                    )

        if owner or moderator:
            st.divider()
            st.markdown("**Delete post**")

            confirm_delete = st.checkbox(
                "I understand this permanently deletes the post.",
                key=f"confirm_delete_{post_id}",
            )

            if st.button(
                "🗑️ Delete post",
                key=f"delete_post_{post_id}",
                disabled=not confirm_delete,
                use_container_width=True,
            ):
                _delete_post(
                    supabase,
                    post,
                    user_id,
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
                    report.get("details")
                    or "No extra details."
                )

                st.caption(
                    _format_timestamp(
                        report.get("created_at")
                    )
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
                                "reviewed_by": st.session_state.get(
                                    "user_id"
                                ),
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
                                "reviewed_by": st.session_state.get(
                                    "user_id"
                                ),
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
                                    "reviewed_by": st.session_state.get(
                                        "user_id"
                                    ),
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
                                    "reviewed_by": st.session_state.get(
                                        "user_id"
                                    ),
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
# POST DISPLAY — MODERN SOCIAL FEED
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

    author_name = names.get(
        author_id,
        "EcoLoop Member",
    )

    if post.get("author_type") == "group":
        author_name = group_names.get(
            post.get("group_id"),
            "Community Group",
        )

    is_repost = bool(post.get("is_repost"))

    # Check if this user has already reposted this original post.
    already_reposted = False

    if not is_repost:
        already_reposted = _has_reposted(
            supabase,
            post_id,
            user_id,
        )

    # POST HEADER
    header_cols = st.columns([0.84, 0.16])

    with header_cols[0]:
        st.markdown(
            f'<div class="gallery-author">'
            f'🌿 {html.escape(author_name)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="gallery-meta">'
            f'{html.escape(post.get("category", "Community action"))} '
            f'· {_format_timestamp(post.get("created_at"))}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with header_cols[1]:
        _post_tools(
            supabase,
            post,
            user_id,
            user_role,
        )

    # REPOST INFORMATION
    if is_repost:
        original_author = (
            (post.get("social_handles") or {})
            .get(
                "original_author_name",
                "EcoLoop Member",
            )
        )

        st.caption(
            f"🔁 Reposted from {original_author}"
        )

    if post.get("location"):
        st.caption(f"📍 {post['location']}")

    # CAPTION
    st.markdown(
        f'<div class="gallery-caption">'
        f'{html.escape(post.get("caption", ""))}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # MEDIA
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

    # RECORD VIEW
    _record_view(
        supabase,
        post_id,
        user_id,
    )

    # REACTIONS
    _show_reactions(
        supabase,
        post_id,
        user_id,
    )

    counts = _reaction_counts(
        supabase,
        post_id,
    )

    total_reactions = sum(counts.values())

    # SOCIAL ACTIONS
    action_cols = st.columns([1.2, 1, 1])

    # REPOST — AVAILABLE ON EVERY ORIGINAL POST
    with action_cols[0]:
        if is_repost:
            st.button(
                "Repost unavailable",
                key=f"repost_{post_id}",
                disabled=True,
                use_container_width=True,
            )

        elif already_reposted:
            st.button(
                "✓ Reposted",
                key=f"repost_{post_id}",
                disabled=True,
                use_container_width=True,
            )

        else:
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

    # SHARE
    with action_cols[1]:
        with st.popover(
            "↗ Share",
            use_container_width=True,
        ):
            _share_post(
                supabase,
                post,
                user_id,
            )

    # REACTION COUNT
    with action_cols[2]:
        st.caption(
            f"💬 {total_reactions} reactions"
        )

    # COMMENTS
    _show_comments(
        supabase,
        post_id,
        user_id,
        user_role,
    )

    st.divider()


# ============================================================
# MAIN ACTION GALLERY
# ============================================================

def render_action_gallery(
    supabase,
    user_id,
    user_name="EcoLoop Member",
    user_role="member",
):
    _inject_gallery_styles()

    st.caption(
        f"Action Gallery Build: {ACTION_GALLERY_BUILD}"
    )

    st.title("🌍 Action Gallery")

    st.markdown(
        '<div class="gallery-intro">'
        'Discover community environmental action, '
        'share your impact and celebrate positive change.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="gallery-brand">'
        'Powered by Next Gen Impact Hub (NGIH)'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # CREATE A POST
    _post_creation_form(
        supabase,
        user_id,
    )

    st.divider()

    # FEED FILTERS
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

    # LOAD POSTS
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
        st.error(
            f"Could not load the Action Gallery: {error}"
        )
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
                    row["id"]: row.get(
                        "name",
                        "Community Group",
                    )
                    for row in _rows(groups)
                }

            except Exception:
                pass

        for index, post in enumerate(posts):
            _display_post(
                supabase,
                post,
                user_id,
                user_name,
                user_role,
                names,
                group_names,
            )

            if index < len(posts) - 1:
                st.divider()

    # MODERATOR TOOLS
    if _is_moderator(user_role):
        st.divider()

        _moderator_report_queue(
            supabase,
            user_role,
        )

    st.divider()

    st.caption(
        "EcoLoop Node • Next Gen Impact Hub (NGIH)"
        )
