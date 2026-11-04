
import streamlit as st
from datetime import date, timedelta
from uuid import uuid4
import re


# =====================================================
# ECOLOOP NODE — ENVIRONMENTAL CHALLENGES
# =====================================================

EVIDENCE_BUCKET = "challenge-evidence"

STARTER_CHALLENGES = [
    {
        "title": "7-Day Recycling Challenge",
        "description": "Sort recyclable materials for seven days. Record your contributions and help reduce waste.",
        "challenge_type": "both",
        "target_quantity": 7,
        "points_reward": 100,
    },
    {
        "title": "Green Neighbourhood Challenge",
        "description": "Plant and care for suitable indigenous trees with permission and community support.",
        "challenge_type": "both",
        "target_quantity": 1,
        "points_reward": 150,
    },
    {
        "title": "Plastic-Free Week",
        "description": "Reduce your use of single-use plastics and record reusable alternatives.",
        "challenge_type": "individual",
        "target_quantity": 7,
        "points_reward": 100,
    },
    {
        "title": "Clean Community Challenge",
        "description": "Participate in a supervised community cleanup. Avoid hazardous waste.",
        "challenge_type": "both",
        "target_quantity": 1,
        "points_reward": 150,
    },
    {
        "title": "Eco-Education Challenge",
        "description": "Spread environmental awareness through posters, presentations and educational activities.",
        "challenge_type": "both",
        "target_quantity": 1,
        "points_reward": 100,
    },
    {
        "title": "Water Conservation Challenge",
        "description": "Practise responsible water use and identify everyday ways to reduce unnecessary waste.",
        "challenge_type": "individual",
        "target_quantity": 7,
        "points_reward": 100,
    },
    {
        "title": "Waste-to-Value Challenge",
        "description": "Explore safe and creative ways to reuse materials or turn organic waste into compost.",
        "challenge_type": "both",
        "target_quantity": 1,
        "points_reward": 120,
    },
]


# =====================================================
# DATABASE HELPERS
# =====================================================

def get_challenges(supabase):
    response = (
        supabase.table("community_challenges")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_my_participation(supabase, user_id):
    if not user_id:
        return []

    response = (
        supabase.table("challenge_participants")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return response.data or []


def get_my_submissions(supabase, user_id):
    if not user_id:
        return []

    response = (
        supabase.table("challenge_submissions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


# =====================================================
# PUBLISH STARTER CHALLENGES
# =====================================================

def publish_starter_challenges(supabase, user_id, challenges):
    existing_titles = {
        item.get("title", "").strip().lower()
        for item in challenges
    }

    today = date.today()
    end_date = today + timedelta(days=30)
    added = 0

    for item in STARTER_CHALLENGES:
        if item["title"].strip().lower() in existing_titles:
            continue

        record = {
            "title": item["title"],
            "description": item["description"],
            "challenge_type": item["challenge_type"],
            "target_quantity": item["target_quantity"],
            "points_reward": item["points_reward"],
            "start_date": today.isoformat(),
            "end_date": end_date.isoformat(),
            "is_active": True,
        }

        supabase.table("community_challenges").insert(
            record
        ).execute()

        added += 1

    return added


# =====================================================
# JOIN CHALLENGE
# =====================================================

def join_challenge(supabase, challenge_id, user_id):
    existing = (
        supabase.table("challenge_participants")
        .select("id")
        .eq("challenge_id", challenge_id)
        .eq("user_id", user_id)
        .execute()
    )

    if existing.data:
        return False, "You have already joined this challenge."

    supabase.table("challenge_participants").insert({
        "challenge_id": challenge_id,
        "user_id": user_id,
        "group_id": None,
        "progress": 0,
        "completed": False,
    }).execute()

    return True, "You have successfully joined the challenge!"


# =====================================================
# SUBMIT CHALLENGE PROGRESS
# =====================================================

def submit_challenge_progress(
    supabase,
    participant_id,
    user_id,
    progress_amount,
    description,
    uploaded_file=None
):
    evidence_path = None

    if uploaded_file is not None:
        safe_name = re.sub(
            r"[^A-Za-z0-9._-]",
            "_",
            uploaded_file.name
        )

        file_name = f"{uuid4().hex}_{safe_name}"

        evidence_path = (
            f"{user_id}/{participant_id}/{file_name}"
        )

        supabase.storage.from_(
            EVIDENCE_BUCKET
        ).upload(
            evidence_path,
            uploaded_file.getvalue(),
            file_options={
                "content-type": uploaded_file.type,
                "upsert": "false",
            }
        )

    record = {
        "participant_id": participant_id,
        "user_id": user_id,
        "progress_amount": progress_amount,
        "description": description.strip(),
        "evidence_url": evidence_path,
        "status": "pending",
    }

    supabase.table(
        "challenge_submissions"
    ).insert(record).execute()


# =====================================================
# DISPLAY SUBMISSION HISTORY
# =====================================================

def render_submission_history(submissions):
    if not submissions:
        st.caption("You have not submitted any challenge progress yet.")
        return

    st.markdown("**Your submission history**")

    for submission in submissions:
        status = submission.get("status", "pending")
        amount = submission.get("progress_amount", 0)
        created = submission.get("created_at", "")

        with st.container(border=True):
            if status == "approved":
                st.success("Approved")

            elif status == "rejected":
                st.error("Rejected")

            else:
                st.info("Pending coordinator review")

            st.write(f"Submitted progress: {amount}")
            st.caption(f"Submitted: {created}")

            if submission.get("description"):
                st.write(submission["description"])

            if submission.get("review_feedback"):
                st.caption(
                    "Coordinator feedback: "
                    + submission["review_feedback"]
                )


# =====================================================
# MAIN CHALLENGES PAGE
# =====================================================

def render_challenges_page(supabase, user_id=None, is_admin=False):

    st.title("🌱 Environmental Challenges")

    st.caption(
        "Take action. Join a movement. "
        "Create measurable environmental impact."
    )

    if supabase is None:
        st.error("EcoLoop database connection is unavailable.")
        return

    # LOAD DATABASE RECORDS

    try:
        challenges = get_challenges(supabase)

        participations = get_my_participation(
            supabase, user_id
        )

        submissions = get_my_submissions(
            supabase, user_id
        ) if user_id else []

    except Exception as e:
        st.error("Could not load challenges.")
        st.exception(e)
        return

    participation_map = {
        str(item["challenge_id"]): item
        for item in participations
    }

    submissions_by_participant = {}

    for submission in submissions:
        participant_id = str(
            submission.get("participant_id")
        )

        submissions_by_participant.setdefault(
            participant_id, []
        ).append(submission)

    # SUMMARY

    completed_count = sum(
        1 for item in participations
        if item.get("completed") is True
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Available", len(challenges))
    col2.metric(
        "Joined",
        len(participations) if user_id else "—"
    )
    col3.metric(
        "Completed",
        completed_count if user_id else "—"
    )

    st.divider()

    # ADMIN PUBLISHING

    if is_admin:
        with st.expander("🌍 Publish starter challenges"):

            st.write(
                "Make the seven official EcoLoop starter "
                "challenges available to members."
            )

            if st.button(
                "Publish starter challenges",
                use_container_width=True
            ):
                try:
                    added = publish_starter_challenges(
                        supabase, user_id, challenges
                    )

                    st.success(
                        f"{added} new challenges published."
                    )
                    st.rerun()

                except Exception as e:
                    st.error("Could not publish challenges.")
                    st.exception(e)

    # GUEST INFORMATION

    if not user_id:
        st.info(
            "You can explore challenges as a guest. "
            "Log in or register to join them."
        )

    st.divider()

    # CHALLENGE DISCOVERY

    st.subheader("🌍 Explore Environmental Challenges")

    search = st.text_input(
        "Search challenges",
        placeholder="Search by challenge name or description..."
    )

    participation_filter = st.selectbox(
        "Participation type",
        ["All", "Individual", "Group", "Both"]
    )

    type_map = {
        "Individual": "individual",
        "Group": "group",
        "Both": "both",
    }

    filtered = []

    for challenge in challenges:
        title = challenge.get("title") or ""
        description = challenge.get("description") or ""

        search_match = (
            search.lower() in title.lower()
            or search.lower() in description.lower()
        )

        challenge_type = challenge.get("challenge_type")

        type_match = (
            participation_filter == "All"
            or challenge_type == type_map.get(
                participation_filter
            )
        )

        if search_match and type_match:
            filtered.append(challenge)

    if not filtered:
        st.info("No matching challenges found.")

    # DISPLAY CHALLENGES

    for challenge in filtered:
        challenge_id = str(challenge["id"])
        joined = participation_map.get(challenge_id)

        challenge_type = challenge.get(
            "challenge_type", "individual"
        )

        reward = challenge.get("points_reward", 0) or 0
        target = challenge.get("target_quantity")

        with st.container(border=True):
            st.subheader(
                "🌱 " + challenge.get(
                    "title", "Environmental Challenge"
                )
            )

            st.write(challenge.get("description") or "")

            st.caption(
                f"Participation: {challenge_type.title()} "
                f"· Reward: {reward} points"
            )

            st.caption(
                f"Starts: {challenge.get('start_date', 'Not specified')} "
                f"· Ends: {challenge.get('end_date', 'Not specified')}"
            )

            if target is not None:
                st.caption(f"Target: {target}")

            if not user_id:
                st.info("Log in to join this challenge.")

            elif joined:
                st.success("You have joined this challenge.")

                progress = joined.get("progress", 0) or 0

                if target and float(target) > 0:
                    progress_value = min(
                        float(progress) / float(target), 1.0
                    )

                    st.progress(progress_value)
                    st.write(f"Verified progress: {progress} / {target}")

                if joined.get("completed") is True:
                    st.success("🏆 Challenge completed!")

                else:
                    st.caption(
                        "Submit your progress below for "
                        "coordinator verification."
                    )

                    participant_id = str(joined["id"])

                    with st.expander(
                        "📤 Submit challenge progress"
                    ):
                        with st.form(
                            key=f"submission_form_{participant_id}"
                        ):
                            progress_amount = st.number_input(
                                "Progress achieved in this submission",
                                min_value=0.01,
                                value=1.0,
                                step=1.0
                            )

                            description = st.text_area(
                                "Describe what you accomplished",
                                placeholder=(
                                    "Explain the environmental "
                                    "activity you completed..."
                                )
                            )

                            uploaded_file = st.file_uploader(
                                "Upload photographic evidence (optional)",
                                type=["jpg", "jpeg", "png", "webp"],
                                help="Maximum file size: 5 MB."
                            )

                            submit_button = st.form_submit_button(
                                "Submit for verification",
                                use_container_width=True
                            )

                            if submit_button:
                                if not description.strip():
                                    st.error(
                                        "Please describe your activity."
                                    )

                                elif (
                                    uploaded_file is not None
                                    and len(uploaded_file.getvalue())
                                    > 5 * 1024 * 1024
                                ):
                                    st.error(
                                        "Your photograph exceeds "
                                        "the 5 MB limit."
                                    )

                                else:
                                    try:
                                        submit_challenge_progress(
                                            supabase,
                                            participant_id,
                                            user_id,
                                            progress_amount,
                                            description,
                                            uploaded_file
                                        )

                                        st.success(
                                            "Your progress has been "
                                            "submitted for coordinator review!"
                                        )

                                        st.rerun()

                                    except Exception as e:
                                        st.error(
                                            "Could not submit your progress."
                                        )
                                        st.exception(e)

                    history = submissions_by_participant.get(
                        participant_id, []
                    )

                    render_submission_history(history)

            elif challenge_type == "group":
                st.info(
                    "This challenge is for groups. "
                    "Group joining will be enabled after the "
                    "group participation database update."
                )

            else:
                if st.button(
                    "Join Challenge",
                    key=f"join_{challenge_id}",
                    use_container_width=True
                ):
                    try:
                        success, message = join_challenge(
                            supabase, challenge_id, user_id
                        )

                        if success:
                            st.success(message)
                        else:
                            st.info(message)

                        st.rerun()

                    except Exception as e:
                        st.error("Could not join this challenge.")
                        st.exception(e)

    # FOOTER

    st.divider()

    st.caption(
        "EcoLoop Node · Turning everyday environmental "
        "action into measurable community impact."
    )
