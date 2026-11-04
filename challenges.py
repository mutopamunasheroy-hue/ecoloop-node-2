
import streamlit as st
from datetime import date, timedelta


# =====================================================
# ECOLOOP NODE — ENVIRONMENTAL CHALLENGES
# =====================================================

STARTER_CHALLENGES = [
    {
        "title": "7-Day Recycling Challenge",
        "description": (
            "Sort recyclable materials for seven days. "
            "Record your contributions and help reduce waste."
        ),
        "challenge_type": "both",
        "target_quantity": 7,
        "points_reward": 100,
    },
    {
        "title": "Green Neighbourhood Challenge",
        "description": (
            "Plant and care for suitable indigenous trees "
            "with permission and community support."
        ),
        "challenge_type": "both",
        "target_quantity": 1,
        "points_reward": 150,
    },
    {
        "title": "Plastic-Free Week",
        "description": (
            "Reduce your use of single-use plastics "
            "and record reusable alternatives."
        ),
        "challenge_type": "individual",
        "target_quantity": 7,
        "points_reward": 100,
    },
    {
        "title": "Clean Community Challenge",
        "description": (
            "Participate in a supervised community cleanup. "
            "Avoid hazardous waste."
        ),
        "challenge_type": "both",
        "target_quantity": 1,
        "points_reward": 150,
    },
    {
        "title": "Eco-Education Challenge",
        "description": (
            "Spread environmental awareness through posters, "
            "presentations and educational activities."
        ),
        "challenge_type": "both",
        "target_quantity": 1,
        "points_reward": 100,
    },
    {
        "title": "Water Conservation Challenge",
        "description": (
            "Practise responsible water use and identify "
            "everyday ways to reduce unnecessary waste."
        ),
        "challenge_type": "individual",
        "target_quantity": 7,
        "points_reward": 100,
    },
    {
        "title": "Waste-to-Value Challenge",
        "description": (
            "Explore safe and creative ways to reuse "
            "materials or turn organic waste into compost."
        ),
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

    except Exception as e:
    st.error("Could not load challenges.")
    st.exception(e)
    return

    participation_map = {
        str(item["challenge_id"]): item
        for item in participations
    }

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
                        supabase,
                        user_id,
                        challenges
                    )

                    st.success(
                        f"{added} new challenges published."
                    )
                    st.rerun()

                except Exception:
                    st.error(
                        "Could not publish challenges. "
                        "Check the database permissions."
                    )

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

            st.subheader("🌱 " + challenge.get(
                "title", "Environmental Challenge"
            ))

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

                    st.write(
                        f"Progress: {progress} / {target}"
                    )

                if joined.get("completed") is True:
                    st.success("🏆 Challenge completed!")
                else:
                    st.caption(
                        "Your participation is registered. "
                        "Evidence verification and progress updates "
                        "will be enabled in the next setup."
                    )

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
                            supabase,
                            challenge_id,
                            user_id
                        )

                        if success:
                            st.success(message)
                        else:
                            st.info(message)

                        st.rerun()

                    except Exception:
                        st.error(
                            "Could not join this challenge. "
                            "Please check your account permissions."
                        )

    # FOOTER

    st.divider()

    st.caption(
        "EcoLoop Node · Turning everyday environmental "
        "action into measurable community impact."
    )
