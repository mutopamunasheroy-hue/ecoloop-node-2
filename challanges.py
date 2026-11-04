
import streamlit as st
from datetime import date


# =====================================================
# ECOLOOP NODE — ENVIRONMENTAL CHALLENGES
# =====================================================

STARTER_CHALLENGES = [
    {
        "title": "7-Day Recycling Challenge",
        "category": "Recycling",
        "description": (
            "Sort recyclable materials for seven days. "
            "Record your contributions and help reduce waste."
        ),
        "participation_type": "Both",
        "target_points": 100,
    },
    {
        "title": "Green Neighbourhood Challenge",
        "category": "Tree Planting",
        "description": (
            "Plant and care for suitable indigenous trees "
            "with permission and community support."
        ),
        "participation_type": "Both",
        "target_points": 150,
    },
    {
        "title": "Plastic-Free Week",
        "category": "Plastic Reduction",
        "description": (
            "Reduce your use of single-use plastics "
            "and record the reusable alternatives you choose."
        ),
        "participation_type": "Individual",
        "target_points": 100,
    },
    {
        "title": "Clean Community Challenge",
        "category": "Clean-up",
        "description": (
            "Organise or participate in a supervised "
            "community cleanup. Avoid hazardous waste."
        ),
        "participation_type": "Both",
        "target_points": 150,
    },
    {
        "title": "Eco-Education Challenge",
        "category": "Environmental Education",
        "description": (
            "Spread environmental awareness through "
            "posters, presentations and educational activities."
        ),
        "participation_type": "Both",
        "target_points": 100,
    },
    {
        "title": "Water Conservation Challenge",
        "category": "Water Conservation",
        "description": (
            "Practise responsible water use and identify "
            "everyday ways to reduce unnecessary waste."
        ),
        "participation_type": "Individual",
        "target_points": 100,
    },
    {
        "title": "Waste-to-Value Challenge",
        "category": "Waste Reuse",
        "description": (
            "Explore safe and creative ways to reuse "
            "materials or turn organic waste into compost."
        ),
        "participation_type": "Both",
        "target_points": 120,
    },
]


# =====================================================
# MAIN PAGE
# =====================================================

def render_challenges_page(supabase, user_id=None, is_admin=False):

    st.title("🌱 Environmental Challenges")

    st.caption(
        "Take action. Join a movement. "
        "Create measurable environmental impact."
    )

    if not supabase:
        st.error("EcoLoop database connection is unavailable.")
        return

    # -------------------------------------------------
    # DATABASE FUNCTIONS
    # -------------------------------------------------

    def get_challenges():
        response = (
            supabase.table("environmental_challenges")
            .select("*")
            .eq("status", "active")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def get_my_participation():
        if not user_id:
            return []

        response = (
            supabase.table("challenge_participants")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data or []

    # -------------------------------------------------
    # LOAD CHALLENGES
    # -------------------------------------------------

    try:
        challenges = get_challenges()
        participations = get_my_participation()

    except Exception as e:
        st.error("Could not load environmental challenges.")
        st.code(str(e))
        return

    participation_map = {
        str(item["challenge_id"]): item
        for item in participations
    }

    # -------------------------------------------------
    # SUMMARY
    # -------------------------------------------------

    completed = sum(
        1 for item in participations
        if item.get("status") == "completed"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Available", len(challenges))
    col2.metric(
        "Joined",
        len(participations) if user_id else "—"
    )
    col3.metric(
        "Completed",
        completed if user_id else "—"
    )

    st.divider()

    # -------------------------------------------------
    # ADMIN: PUBLISH STARTER CHALLENGES
    # -------------------------------------------------

    if is_admin:

        with st.expander("🌍 Publish starter challenges"):

            st.write(
                "Publish the seven EcoLoop starter challenges "
                "so members can discover and join them."
            )

            if st.button(
                "Publish starter challenges",
                use_container_width=True
            ):

                existing_titles = {
                    item.get("title")
                    for item in challenges
                }

                added = 0

                try:
                    for item in STARTER_CHALLENGES:

                        if item["title"] in existing_titles:
                            continue

                        record = {
                            **item,
                            "start_date": str(date.today()),
                            "end_date": None,
                            "created_by": user_id,
                            "status": "active",
                        }

                        supabase.table(
                            "environmental_challenges"
                        ).insert(record).execute()

                        added += 1

                    st.success(
                        f"Published {added} new starter challenges."
                    )
                    st.rerun()

                except Exception as e:
                    st.error("Could not publish starter challenges.")
                    st.code(str(e))

    # -------------------------------------------------
    # MEMBER: PROPOSE A CHALLENGE
    # -------------------------------------------------

    if user_id:

        with st.expander("💡 Propose a new challenge"):

            st.write(
                "Have an environmental idea? "
                "Submit it for administrator review."
            )

            with st.form("challenge_proposal_form"):

                proposal_title = st.text_input(
                    "Challenge title"
                )

                proposal_description = st.text_area(
                    "Describe your idea"
                )

                proposal_category = st.selectbox(
                    "Category",
                    [
                        "Recycling",
                        "Tree Planting",
                        "Clean-up",
                        "Plastic Reduction",
                        "Water Conservation",
                        "Environmental Education",
                        "Waste Reuse",
                        "Other",
                    ]
                )

                proposal_type = st.selectbox(
                    "Who can participate?",
                    ["Individual", "Team", "Both"]
                )

                proposal_submit = st.form_submit_button(
                    "Submit proposal",
                    use_container_width=True
                )

                if proposal_submit:

                    if not proposal_title.strip():
                        st.error("Enter a challenge title.")

                    elif not proposal_description.strip():
                        st.error("Describe your challenge.")

                    else:
                        try:
                            supabase.table(
                                "challenge_proposals"
                            ).insert({
                                "title": proposal_title.strip(),
                                "description": proposal_description.strip(),
                                "category": proposal_category,
                                "participation_type": proposal_type,
                                "proposed_by": user_id,
                                "status": "pending",
                            }).execute()

                            st.success(
                                "Your proposal has been submitted "
                                "for administrator review!"
                            )

                        except Exception as e:
                            st.error("Could not submit proposal.")
                            st.code(str(e))

    else:
        st.info(
            "You can explore challenges as a guest. "
            "Create an account or log in to participate "
            "and propose new challenges."
        )

    st.divider()

    # -------------------------------------------------
    # ADMIN: REVIEW PROPOSALS
    # -------------------------------------------------

    if is_admin:

        with st.expander("📋 Review member proposals"):

            try:
                proposals = (
                    supabase.table("challenge_proposals")
                    .select("*")
                    .eq("status", "pending")
                    .order("created_at", desc=False)
                    .execute()
                    .data or []
                )

                if not proposals:
                    st.info("No pending proposals.")

                for proposal in proposals:

                    with st.container(border=True):

                        st.subheader(proposal["title"])
                        st.write(proposal["description"])

                        st.caption(
                            f"{proposal['category']} · "
                            f"{proposal['participation_type']}"
                        )

                        col1, col2 = st.columns(2)

                        if col1.button(
                            "Approve",
                            key=f"approve_{proposal['id']}"
                        ):

                            supabase.table(
                                "environmental_challenges"
                            ).insert({
                                "title": proposal["title"],
                                "description": proposal["description"],
                                "category": proposal["category"],
                                "participation_type": proposal["participation_type"],
                                "target_points": 100,
                                "start_date": str(date.today()),
                                "created_by": user_id,
                                "status": "active",
                            }).execute()

                            supabase.table(
                                "challenge_proposals"
                            ).update({
                                "status": "approved"
                            }).eq(
                                "id", proposal["id"]
                            ).execute()

                            st.success("Proposal approved!")
                            st.rerun()

                        if col2.button(
                            "Reject",
                            key=f"reject_{proposal['id']}"
                        ):

                            supabase.table(
                                "challenge_proposals"
                            ).update({
                                "status": "rejected"
                            }).eq(
                                "id", proposal["id"]
                            ).execute()

                            st.rerun()

            except Exception as e:
                st.error("Could not load proposals.")
                st.code(str(e))

    # -------------------------------------------------
    # CHALLENGE DISCOVERY
    # -------------------------------------------------

    st.subheader("🌍 Explore Environmental Challenges")

    search = st.text_input(
        "Search challenges",
        placeholder="Search by name or category..."
    )

    categories = [
        "All",
        "Recycling",
        "Tree Planting",
        "Clean-up",
        "Plastic Reduction",
        "Water Conservation",
        "Environmental Education",
        "Waste Reuse",
        "Other",
    ]

    selected_category = st.selectbox(
        "Filter by category",
        categories
    )

    filtered = []

    for challenge in challenges:

        matches_search = (
            search.lower() in challenge.get("title", "").lower()
            or search.lower() in challenge.get("description", "").lower()
            or search.lower() in challenge.get("category", "").lower()
        )

        matches_category = (
            selected_category == "All"
            or challenge.get("category") == selected_category
        )

        if matches_search and matches_category:
            filtered.append(challenge)

    if not filtered:
        st.info("No matching challenges found.")

    # -------------------------------------------------
    # DISPLAY CHALLENGES
    # -------------------------------------------------

    for challenge in filtered:

        challenge_id = str(challenge["id"])

        joined = participation_map.get(challenge_id)

        with st.container(border=True):

            st.subheader(
                "🌱 " + challenge.get("title", "Challenge")
            )

            st.write(challenge.get("description", ""))

            st.caption(
                f"Category: {challenge.get('category', 'General')} "
                f"· Participation: "
                f"{challenge.get('participation_type', 'Both')}"
            )

            st.caption(
                f"Start: {challenge.get('start_date', 'Not specified')} "
                f"· End: {challenge.get('end_date') or 'Open-ended'}"
            )

            if not user_id:

                st.info(
                    "Log in or register to join this challenge."
                )

            elif joined:

                progress = int(joined.get("progress", 0) or 0)

                target = int(
                    challenge.get("target_points", 100) or 100
                )

                st.progress(
                    min(progress / max(target, 1), 1.0)
                )

                st.write(
                    f"Your progress: {progress} / {target}"
                )

                if joined.get("status") == "completed":
                    st.success("🏆 Challenge completed!")

                else:

                    st.caption(
                        "Progress is self-reported until evidence "
                        "is submitted and verified."
                    )

                    with st.form(
                        f"progress_form_{challenge_id}"
                    ):

                        new_progress = st.number_input(
                            "Update your progress",
                            min_value=0,
                            value=progress,
                            step=1
                        )

                        update_progress = st.form_submit_button(
                            "Save progress"
                        )

                        if update_progress:

                            try:
                                supabase.table(
                                    "challenge_participants"
                                ).update({
                                    "progress": int(new_progress)
                                }).eq(
                                    "id", joined["id"]
                                ).eq(
                                    "user_id", user_id
                                ).execute()

                                st.success("Progress saved!")
                                st.rerun()

                            except Exception as e:
                                st.error("Could not update progress.")
                                st.code(str(e))

            else:

                if st.button(
                    "Join Challenge",
                    key=f"join_{challenge_id}",
                    use_container_width=True
                ):

                    try:
                        supabase.table(
                            "challenge_participants"
                        ).insert({
                            "challenge_id": challenge_id,
                            "user_id": user_id,
                            "progress": 0,
                            "status": "active",
                        }).execute()

                        st.success("You joined the challenge!")
                        st.rerun()

                    except Exception as e:
                        st.error("Could not join challenge.")
                        st.code(str(e))

    # -------------------------------------------------
    # ADMIN: VERIFY SUBMISSIONS
    # -------------------------------------------------

    if is_admin:

        st.divider()

        with st.expander("🔍 Review challenge evidence"):

            try:
                submissions = (
                    supabase.table("challenge_submissions")
                    .select("*")
                    .eq("status", "pending")
                    .order("created_at", desc=False)
                    .execute()
                    .data or []
                )

                if not submissions:
                    st.info("No evidence awaiting review.")

                for submission in submissions:

                    with st.container(border=True):

                        st.write(
                            submission.get(
                                "description",
                                "Environmental activity submission"
                            )
                        )

                        if submission.get("evidence_url"):
                            st.link_button(
                                "View submitted evidence",
                                submission["evidence_url"]
                            )

                        col1, col2 = st.columns(2)

                        if col1.button(
                            "Verify",
                            key=f"verify_{submission['id']}"
                        ):

                            supabase.table(
                                "challenge_submissions"
                            ).update({
                                "status": "verified",
                                "verified_by": user_id,
                                "points_awarded": 10,
                            }).eq(
                                "id", submission["id"]
                            ).eq(
                                "status", "pending"
                            ).execute()

                            st.success("Submission verified.")
                            st.rerun()

                        if col2.button(
                            "Reject",
                            key=f"reject_evidence_{submission['id']}"
                        ):

                            supabase.table(
                                "challenge_submissions"
                            ).update({
                                "status": "rejected",
                                "verified_by": user_id,
                                "points_awarded": 0,
                            }).eq(
                                "id", submission["id"]
                            ).execute()

                            st.rerun()

            except Exception as e:
                st.error("Could not load evidence submissions.")
                st.code(str(e))

    st.divider()

    st.caption(
        "EcoLoop Node · Turning everyday environmental action "
        "into measurable community impact."
    )
