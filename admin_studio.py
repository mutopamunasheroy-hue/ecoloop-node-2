import streamlit as st
from datetime import datetime, timezone
import uuid


# ============================================================
# ECOLOOP NODE — ADMIN STUDIO
# ============================================================

APP_NAME = "EcoLoop Node"

ROLE_SUPER_ADMIN = "super_admin"
ROLE_SUPER_USER = "super_user"
ROLE_ADMIN = "admin"
ROLE_MEMBER = "user"

ROLE_LABELS = {
    ROLE_SUPER_ADMIN: "Super Admin",
    ROLE_SUPER_USER: "Super User",
    ROLE_ADMIN: "Administrator / Coordinator",
    ROLE_MEMBER: "Ordinary Member"
}

PRIMARY_SUPER_ADMIN_ID = str(
    st.secrets.get("PRIMARY_SUPER_ADMIN_ID", "")
).strip()

METRIC_TABLES = {
    "Registered Members": "profiles",
    "Collection Stations": "collection_stations",
    "Waste Contributions": "waste_contributions",
    "Community Groups": "community_groups",
    "Environmental Actions": "environmental_actions",
    "Environmental Challenges": "community_challenges",
    "Collection Records": "collection_records",
    "Reading Materials": "reading_resources",
    "Quiz Questions": "quiz_questions"
}

NGIH_PILLARS = [
    "Governance & Civic Education",
    "Climate Action & Environment",
    "Business & Entrepreneurship",
    "Technology, Innovation, Media & Arts"
]


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_execute(query, show_error=True):
    try:
        return query.execute()
    except Exception as exc:
        if show_error:
            st.error(f"Database operation failed: {exc}")
        return None


def _record_audit(
    supabase,
    actor_id,
    action,
    target_type,
    target_id=None,
    details=None
):
    if not actor_id:
        return

    record = {
        "actor_id": actor_id,
        "action": action,
        "target_type": target_type,
        "target_id": str(target_id) if target_id else None,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    _safe_execute(
        supabase.table("admin_audit_logs").insert(record),
        show_error=False
    )


def _get_role(profile):
    if not isinstance(profile, dict):
        return ROLE_MEMBER

    return profile.get("role", ROLE_MEMBER)


def _get_name(profile):
    if not isinstance(profile, dict):
        return "EcoLoop Member"

    return (
        profile.get("full_name")
        or profile.get("username")
        or "EcoLoop Member"
    )


def _is_primary_super_admin(user_id):
    return bool(
        user_id
        and PRIMARY_SUPER_ADMIN_ID
        and str(user_id) == str(PRIMARY_SUPER_ADMIN_ID)
    )


def _can_manage_roles(role):
    return role in [ROLE_SUPER_ADMIN, ROLE_SUPER_USER]


def _can_manage_super_users(role, user_id):
    return (
        role == ROLE_SUPER_ADMIN
        and _is_primary_super_admin(user_id)
    )


def _can_manage_admins(role):
    return role in [ROLE_SUPER_ADMIN, ROLE_SUPER_USER]


def _can_manage_content(role):
    return role in [
        ROLE_SUPER_ADMIN,
        ROLE_SUPER_USER,
        ROLE_ADMIN
    ]


def _can_manage_stations(role):
    return role in [
        ROLE_SUPER_ADMIN,
        ROLE_SUPER_USER,
        ROLE_ADMIN
    ]


# ============================================================
# DATA RETRIEVAL
# ============================================================

def _get_platform_metrics(supabase):

    metrics = {}

    for label, table_name in METRIC_TABLES.items():

        try:
            response = (
                supabase.table(table_name)
                .select("*", count="exact")
                .limit(0)
                .execute()
            )

            metrics[label] = response.count or 0

        except Exception:
            metrics[label] = "Unavailable"

    return metrics


def _get_members(supabase):

    try:
        response = (
            supabase.table("profiles")
            .select("*")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )

        return response.data or []

    except Exception as exc:
        st.error(f"Could not retrieve members: {exc}")
        return []


def _get_pending_content(supabase, table_name):

    try:
        response = (
            supabase.table(table_name)
            .select("*")
            .eq("status", "pending")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        return response.data or []

    except Exception as exc:
        st.error(f"Could not retrieve pending content: {exc}")
        return []


# ============================================================
# MEMBER ROLE MANAGEMENT
# ============================================================

def _change_member_role(
    supabase,
    actor_id,
    actor_role,
    target,
    new_role
):

    target_id = target.get("id")

    if not target_id:
        st.error("This member has no valid account ID.")
        return

    target_role = target.get("role", ROLE_MEMBER)

    if _is_primary_super_admin(target_id):
        st.error("The Primary Super Admin account is protected.")
        return

    if new_role == ROLE_SUPER_ADMIN:
        st.error(
            "The Primary Super Admin role cannot be assigned "
            "through ordinary member management."
        )
        return

    if new_role not in [
        ROLE_SUPER_USER,
        ROLE_ADMIN,
        ROLE_MEMBER
    ]:
        st.error("Invalid role selected.")
        return

    if (
        target_role == ROLE_SUPER_USER
        or new_role == ROLE_SUPER_USER
    ):
        if not _can_manage_super_users(actor_role, actor_id):
            st.error(
                "Only the Primary Super Admin can appoint "
                "or revoke Super Users."
            )
            return

    if (
        target_role == ROLE_ADMIN
        or new_role == ROLE_ADMIN
    ):
        if not _can_manage_admins(actor_role):
            st.error(
                "You do not have permission to manage "
                "Administrators / Coordinators."
            )
            return

    if actor_role == ROLE_ADMIN:
        st.error("Administrators cannot change member roles.")
        return

    # IMPORTANT:
    # Do not update profiles.role directly.
    # The database protects this column.
    # Use the existing SECURITY DEFINER RPC instead.

    result = _safe_execute(
        supabase.rpc(
            "manage_member_role",
            {
                "target_id": str(target_id),
                "new_role": new_role
            }
        )
    )

    if result is not None:
        st.success(
            f"Member role updated to {ROLE_LABELS[new_role]}."
        )
        st.rerun()


def _render_role_management(
    supabase,
    actor_id,
    actor_role
):

    st.subheader("Member Role Management")

    st.caption(
        "Manage EcoLoop Node account appointments "
        "according to the platform's role hierarchy."
    )

    if not _can_manage_roles(actor_role):
        st.warning("You do not have permission to manage roles.")
        return

    members = _get_members(supabase)

    search = st.text_input(
        "Search members",
        placeholder="Search by name, username or email..."
    )

    filtered = []

    for member in members:

        searchable = " ".join([
            str(member.get("full_name", "")),
            str(member.get("username", "")),
            str(member.get("email", ""))
        ]).lower()

        if search.lower() in searchable:
            filtered.append(member)

    st.caption(f"{len(filtered)} matching accounts")

    if not filtered:
        st.info("No matching accounts found.")
        return

    member_options = {}

    for member in filtered:

        name = (
            member.get("full_name")
            or member.get("username")
            or "Unnamed Member"
        )

        role = member.get("role", ROLE_MEMBER)
        member_id = member.get("id")

        label = (
            f"{name} — "
            f"{ROLE_LABELS.get(role, role)} — "
            f"{str(member_id)[:8]}"
        )

        member_options[label] = member

    selected_label = st.selectbox(
        "Select an account",
        list(member_options.keys())
    )

    selected = member_options[selected_label]

    st.divider()

    st.write(f"**Name:** {_get_name(selected)}")

    st.write(
        f"**Username:** {selected.get('username', 'Not available')}"
    )

    st.write(
        f"**Email:** {selected.get('email', 'Not available')}"
    )

    current_role = selected.get("role", ROLE_MEMBER)

    st.write(
        f"**Current role:** "
        f"{ROLE_LABELS.get(current_role, current_role)}"
    )

    if _is_primary_super_admin(selected.get("id")):
        st.success("Protected Primary Super Admin account.")
        return

    if _can_manage_super_users(actor_role, actor_id):

        available_roles = [
            ROLE_MEMBER,
            ROLE_ADMIN,
            ROLE_SUPER_USER
        ]

    elif actor_role == ROLE_SUPER_USER:

        available_roles = [
            ROLE_MEMBER,
            ROLE_ADMIN
        ]

        if current_role == ROLE_SUPER_USER:
            st.info(
                "Super Users cannot change another "
                "Super User's appointment."
            )
            return

    else:
        return

    new_role = st.selectbox(
        "Assign account role",
        available_roles,
        format_func=lambda role: ROLE_LABELS[role],
        key="admin_studio_new_role"
    )

    if st.button(
        "Save Role Changes",
        type="primary",
        use_container_width=True
    ):

        if new_role == current_role:
            st.info("This account already has that role.")
        else:
            _change_member_role(
                supabase,
                actor_id,
                actor_role,
                selected,
                new_role
            )


# ============================================================
# LEARNING MATERIAL MANAGEMENT
# ============================================================

def _render_learning_materials(
    supabase,
    actor_id,
    actor_role
):

    st.subheader("Learning Materials")

    if not _can_manage_content(actor_role):
        st.warning("You do not have permission to manage content.")
        return

    tab_pending, tab_add = st.tabs([
        "Pending Submissions",
        "Add Reading Material"
    ])

    with tab_pending:

        materials = _get_pending_content(
            supabase,
            "reading_resources"
        )

        if not materials:
            st.info("There are no pending reading materials.")

        else:

            for index, material in enumerate(materials):

                material_id = material.get("id")
                title = material.get("title", "Untitled Material")

                with st.expander(title):

                    st.write(material.get("description", ""))

                    st.write(
                        f"Category: "
                        f"{material.get('category', 'Uncategorised')}"
                    )

                    st.write(
                        f"Submitted by: "
                        f"{material.get('uploaded_by', 'Unknown')}"
                    )

                    st.write(
                        f"File: "
                        f"{material.get('file_url', 'Not available')}"
                    )

                    review_note = st.text_input(
                        "Review note",
                        key=f"material_note_{material_id}_{index}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Approve",
                            key=f"approve_material_{material_id}_{index}"
                        ):

                            result = _safe_execute(
                                supabase.table("reading_resources")
                                .update({
                                    "status": "approved",
                                    "reviewed_by": actor_id,
                                    "review_note": review_note
                                })
                                .eq("id", material_id)
                            )

                            if result is not None:

                                _record_audit(
                                    supabase,
                                    actor_id,
                                    "reading_material_approved",
                                    "reading_resources",
                                    material_id
                                )

                                st.success("Material approved.")
                                st.rerun()

                    with col2:

                        if st.button(
                            "Reject",
                            key=f"reject_material_{material_id}_{index}"
                        ):

                            if not review_note.strip():
                                st.warning(
                                    "Please provide a reason for rejection."
                                )

                            else:

                                result = _safe_execute(
                                    supabase.table("reading_resources")
                                    .update({
                                        "status": "rejected",
                                        "reviewed_by": actor_id,
                                        "review_note": review_note
                                    })
                                    .eq("id", material_id)
                                )

                                if result is not None:

                                    _record_audit(
                                        supabase,
                                        actor_id,
                                        "reading_material_rejected",
                                        "reading_resources",
                                        material_id,
                                        {"reason": review_note}
                                    )

                                    st.success("Material rejected.")
                                    st.rerun()

    with tab_add:

        st.write(
            "Administrators and senior administrators can "
            "contribute learning materials."
        )

        with st.form("admin_add_reading_material"):

            title = st.text_input("Material title")

            description = st.text_area("Description")

            category = st.selectbox(
                "Learning category",
                NGIH_PILLARS
            )

            uploaded_file = st.file_uploader(
                "Upload reading material",
                type=["pdf", "doc", "docx", "ppt", "pptx"]
            )

            submitted = st.form_submit_button(
                "Submit Reading Material",
                use_container_width=True
            )

            if submitted:

                if not title.strip():
                    st.error("Enter a material title.")

                elif not uploaded_file:
                    st.error("Choose a file to upload.")

                else:

                    file_name = (
                        f"reading-materials/"
                        f"{uuid.uuid4().hex}_{uploaded_file.name}"
                    )

                    # Keep storage upload errors separate from
                    # reading_resources database errors.
                    try:

                        supabase.storage.from_(
                            "learning-resources"
                        ).upload(
                            file_name,
                            uploaded_file.getvalue(),
                            {
                                "content-type": (
                                    uploaded_file.type
                                    or "application/octet-stream"
                                )
                            }
                        )

                    except Exception as exc:

                        st.error(
                            "Storage upload failed. "
                            "The file could not be uploaded. "
                            f"Details: {exc}"
                        )

                        st.info(
                            "The Storage permission issue must be "
                            "corrected in Supabase. This code does "
                            "not bypass your Storage security policies."
                        )

                    else:

                        try:

                            file_url = (
                                supabase.storage
                                .from_("learning-resources")
                                .get_public_url(file_name)
                            )

                            if isinstance(file_url, dict):
                                file_url = (
                                    file_url.get("publicUrl")
                                    or file_url.get("publicURL")
                                    or ""
                                )

                            result = _safe_execute(
                                supabase.table("reading_resources")
                                .insert({
                                    "title": title.strip(),
                                    "description": description.strip(),
                                    "category": category,
                                    "file_url": file_url,
                                    "uploaded_by": actor_id,
                                    "status": "pending"
                                })
                            )

                            if result is not None:

                                _record_audit(
                                    supabase,
                                    actor_id,
                                    "reading_material_submitted",
                                    "reading_resources"
                                )

                                st.success(
                                    "Reading material submitted for review."
                                )

                                st.rerun()

                        except Exception as exc:

                            st.error(
                                "The file uploaded, but its reading "
                                f"material record could not be saved: {exc}"
                            )


# ============================================================
# QUIZ MANAGEMENT
# ============================================================

def _render_quiz_management(
    supabase,
    actor_id,
    actor_role
):

    st.subheader("Quiz Management")

    if not _can_manage_content(actor_role):
        st.warning("You do not have permission to manage quizzes.")
        return

    tab_create, tab_pending = st.tabs([
        "Submit Quiz Question",
        "Pending Quiz Submissions"
    ])

    # --------------------------------------------------------
    # SUBMIT A QUESTION THROUGH THE EXISTING SUBMISSION SYSTEM
    # --------------------------------------------------------

    with tab_create:

        st.caption(
            "Questions submitted here enter the existing quiz "
            "review process. They are not inserted directly into "
            "the published quiz question bank."
        )

        with st.form("admin_create_quiz_question"):

            quiz_title = st.text_input(
                "Quiz title",
                value="NGIH Community Quiz"
            )

            description = st.text_area(
                "Quiz description",
                value="Community learning question submitted for review."
            )

            pillar = st.selectbox(
                "NGIH Pillar",
                NGIH_PILLARS
            )

            difficulty = st.selectbox(
                "Difficulty",
                ["Easy", "Medium", "Hard"]
            )

            question = st.text_area("Question")

            option_a = st.text_input("Option A")
            option_b = st.text_input("Option B")
            option_c = st.text_input("Option C")
            option_d = st.text_input("Option D")

            correct_option = st.selectbox(
                "Correct Answer",
                ["A", "B", "C", "D"]
            )

            explanation = st.text_area(
                "Explanation"
            )

            submitted = st.form_submit_button(
                "Submit Quiz Question",
                use_container_width=True
            )

            if submitted:

                if not quiz_title.strip():
                    st.error("Enter a quiz title.")

                elif not question.strip():
                    st.error("Enter a question.")

                elif not all([
                    option_a.strip(),
                    option_b.strip(),
                    option_c.strip(),
                    option_d.strip()
                ]):
                    st.error("Complete all four answer options.")

                else:

                    question_data = {
                        "question_text": question.strip(),
                        "option_a": option_a.strip(),
                        "option_b": option_b.strip(),
                        "option_c": option_c.strip(),
                        "option_d": option_d.strip(),
                        "correct_option": correct_option,
                        "explanation": explanation.strip(),
                        "question_order": 1,
                        "points": 1
                    }

                    submission_data = {
                        "user_id": actor_id,
                        "title": quiz_title.strip(),
                        "description": description.strip(),
                        "category": pillar,
                        "difficulty": difficulty.lower(),
                        "questions": [question_data],
                        "status": "pending"
                    }

                    result = _safe_execute(
                        supabase.table("quiz_submissions")
                        .insert(submission_data)
                    )

                    if result is not None:

                        _record_audit(
                            supabase,
                            actor_id,
                            "quiz_question_submitted",
                            "quiz_submissions"
                        )

                        st.success(
                            "Quiz question submitted for review."
                        )

                        st.rerun()

    # --------------------------------------------------------
    # REVIEW PENDING SUBMISSIONS
    # --------------------------------------------------------

    with tab_pending:

        if actor_role != ROLE_SUPER_ADMIN:
            st.info(
                "Quiz submission review and publication are "
                "reserved for the Primary Super Admin."
            )
            return

        if not _is_primary_super_admin(actor_id):
            st.error(
                "Only the configured Primary Super Admin can "
                "review and publish quiz submissions."
            )
            return

        submissions = _get_pending_content(
            supabase,
            "quiz_submissions"
        )

        if not submissions:
            st.info("There are no pending quiz submissions.")

        else:

            for index, item in enumerate(submissions):

                submission_id = item.get("id")

                with st.expander(
                    item.get("title", "Untitled Quiz Submission")
                ):

                    st.write(
                        f"**Description:** "
                        f"{item.get('description', '')}"
                    )

                    st.write(
                        f"**Pillar:** "
                        f"{item.get('category', 'Not specified')}"
                    )

                    st.write(
                        f"**Difficulty:** "
                        f"{item.get('difficulty', 'Not specified')}"
                    )

                    st.write(
                        f"**Submitted by:** "
                        f"{item.get('user_id', 'Unknown')}"
                    )

                    questions = item.get("questions") or []

                    if not isinstance(questions, list):
                        questions = []

                    if not questions:
                        st.warning(
                            "This submission does not contain "
                            "a readable question list."
                        )

                    for question_index, question_item in enumerate(questions):

                        st.divider()

                        st.write(
                            f"**Question {question_index + 1}:** "
                            f"{question_item.get('question_text', '')}"
                        )

                        for option in ["a", "b", "c", "d"]:

                            st.write(
                                f"{option.upper()}: "
                                f"{question_item.get('option_' + option, '')}"
                            )

                        st.write(
                            f"**Correct option:** "
                            f"{question_item.get('correct_option', '')}"
                        )

                        st.write(
                            f"**Explanation:** "
                            f"{question_item.get('explanation', '')}"
                        )

                    note = st.text_area(
                        "Review note",
                        key=f"quiz_review_note_{submission_id}_{index}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Approve and Publish",
                            key=f"publish_quiz_{submission_id}_{index}",
                            type="primary"
                        ):

                            result = _safe_execute(
                                supabase.rpc(
                                    "publish_quiz_submission",
                                    {
                                        "p_submission_id": submission_id
                                    }
                                )
                            )

                            if result is not None:

                                _record_audit(
                                    supabase,
                                    actor_id,
                                    "quiz_submission_published",
                                    "quiz_submissions",
                                    submission_id
                                )

                                st.success(
                                    "Quiz submission published successfully."
                                )

                                st.rerun()

                    with col2:

                        if st.button(
                            "Reject Submission",
                            key=f"reject_quiz_{submission_id}_{index}"
                        ):

                            if not note.strip():
                                st.warning(
                                    "Provide a reason for rejection."
                                )

                            else:

                                result = _safe_execute(
                                    supabase.table("quiz_submissions")
                                    .update({
                                        "status": "rejected",
                                        "admin_feedback": note.strip(),
                                        "reviewed_by": actor_id,
                                        "reviewed_at": (
                                            datetime.now(timezone.utc).isoformat()
                                        ),
                                        "updated_at": (
                                            datetime.now(timezone.utc).isoformat()
                                        )
                                    })
                                    .eq("id", submission_id)
                                )

                                if result is not None:

                                    _record_audit(
                                        supabase,
                                        actor_id,
                                        "quiz_submission_rejected",
                                        "quiz_submissions",
                                        submission_id,
                                        {"reason": note.strip()}
                                    )

                                    st.success(
                                        "Quiz submission rejected."
                                    )

                                    st.rerun()


# ============================================================
# ECOLOOP NODE STATION MANAGEMENT
# ============================================================

def _render_station_management(
    supabase,
    actor_id,
    actor_role
):

    st.subheader("EcoLoop Node Station Management")

    if not _can_manage_stations(actor_role):
        st.warning("You do not have permission to manage stations.")
        return

    tab_add, tab_view = st.tabs([
        "Add Station",
        "Existing Stations"
    ])

    # --------------------------------------------------------
    # ADD STATION
    # --------------------------------------------------------

    with tab_add:

        with st.form("admin_add_station"):

            station_code = st.text_input(
                "Station Code",
                placeholder="ECO004"
            )

            station_name = st.text_input(
                "Station Name"
            )

            location = st.text_area(
                "Station Location"
            )

            submitted = st.form_submit_button(
                "Add EcoLoop Node Station",
                use_container_width=True
            )

            if submitted:

                if (
                    not station_code.strip()
                    or not station_name.strip()
                ):
                    st.error(
                        "Station code and name are required."
                    )

                else:

                    station_data = {
                        "station_code": station_code.strip().upper(),
                        "station_name": station_name.strip(),
                        "location": location.strip(),
                        "is_active": True,
                        "created_by": actor_id
                    }

                    result = _safe_execute(
                        supabase.table("collection_stations")
                        .insert(station_data)
                    )

                    if result is not None:

                        _record_audit(
                            supabase,
                            actor_id,
                            "station_added",
                            "collection_stations",
                            station_code.strip().upper()
                        )

                        st.success("Station added successfully.")
                        st.rerun()

    # --------------------------------------------------------
    # VIEW AND DEACTIVATE STATIONS
    # --------------------------------------------------------

    with tab_view:

        try:

            response = (
                supabase.table("collection_stations")
                .select("*")
                .order("station_code")
                .execute()
            )

            stations = response.data or []

        except Exception as exc:

            st.error(f"Could not load stations: {exc}")
            stations = []

        if not stations:
            st.info("No stations found.")

        for station_index, station in enumerate(stations):

            station_id = station.get("id")

            station_name = station.get(
                "station_name",
                "Unnamed Station"
            )

            with st.expander(station_name):

                st.write(
                    f"**Code:** {station.get('station_code', '')}"
                )

                st.write(
                    f"**Location:** {station.get('location', '')}"
                )

                st.write(
                    "**Status:** "
                    + (
                        "Active"
                        if station.get("is_active")
                        else "Inactive"
                    )
                )

                # Only the Primary Super Admin can deactivate stations.
                if _can_manage_super_users(actor_role, actor_id):

                    if station.get("is_active"):

                        if not station_id:
                            st.warning(
                                "This station has no valid database ID."
                            )

                        elif st.button(
                            "Deactivate Station",
                            key=(
                                f"deactivate_station_"
                                f"{station_id}_{station_index}"
                            )
                        ):

                            result = _safe_execute(
                                supabase.table("collection_stations")
                                .update({"is_active": False})
                                .eq("id", station_id)
                            )

                            if result is not None:

                                _record_audit(
                                    supabase,
                                    actor_id,
                                    "station_deactivated",
                                    "collection_stations",
                                    station_id
                                )

                                st.success("Station deactivated.")
                                st.rerun()


# ============================================================
# ADMINISTRATIVE ACTIVITY
# ============================================================

def _render_audit_logs(supabase, actor_role):

    st.subheader("Administrative Activity")

    if actor_role not in [
        ROLE_SUPER_ADMIN,
        ROLE_SUPER_USER,
        ROLE_ADMIN
    ]:
        st.warning(
            "You cannot access administrative activity."
        )
        return

    try:

        response = (
            supabase.table("admin_audit_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(200)
            .execute()
        )

        logs = response.data or []

    except Exception as exc:

        st.error(
            f"Could not retrieve activity records: {exc}"
        )
        return

    if not logs:
        st.info(
            "No administrative activity has been recorded."
        )
        return

    for log in logs:

        with st.container():

            st.write(
                f"**{log.get('action', 'Activity')}**"
            )

            st.caption(
                f"Actor: {log.get('actor_id', 'Unknown')} | "
                f"Target: {log.get('target_type', 'Unknown')} | "
                f"Date: {log.get('created_at', 'Unknown')}"
            )

            details = log.get("details")

            if details:
                st.json(details)

            st.divider()


# ============================================================
# PLATFORM OVERVIEW
# ============================================================

def _render_overview(supabase, actor_role):

    st.subheader("Platform Overview")

    metrics = _get_platform_metrics(supabase)

    items = list(metrics.items())

    for index in range(0, len(items), 2):

        col1, col2 = st.columns(2)

        with col1:

            label, value = items[index]
            st.metric(label, value)

        if index + 1 < len(items):

            with col2:

                label, value = items[index + 1]
                st.metric(label, value)

    st.divider()

    st.subheader("Administrative Authority")

    st.write(
        f"Your account role: "
        f"**{ROLE_LABELS.get(actor_role, actor_role)}**"
    )

    st.caption(
        "Administrative actions are subject to the role hierarchy "
        "and database security policies."
    )


# ============================================================
# MAIN ADMIN STUDIO PAGE
# ============================================================

def admin_studio_page(
    supabase,
    current_user_id,
    profile
):

    if not current_user_id or not isinstance(profile, dict):
        st.error("Please sign in to access Admin Studio.")
        return

    actor_role = _get_role(profile)

    if actor_role not in [
        ROLE_SUPER_ADMIN,
        ROLE_SUPER_USER,
        ROLE_ADMIN
    ]:
        st.error(
            "Access denied. Administrative permissions are required."
        )
        return

    # Verify the configured Primary Super Admin account.
    if actor_role == ROLE_SUPER_ADMIN:

        if not _is_primary_super_admin(current_user_id):
            st.error(
                "This Super Admin account is not registered as "
                "the protected Primary Super Admin."
            )
            return

    st.title("Admin Studio")

    st.caption(
        "Central administration and operational management "
        "for EcoLoop Node."
    )

    st.write(
        f"Welcome, **{_get_name(profile)}**"
    )

    st.divider()

    pages = [
        "Platform Overview",
        "Member Role Management",
        "Learning Materials",
        "Quiz Management",
        "Node Station Management",
        "Administrative Activity"
    ]

    if actor_role == ROLE_ADMIN:
        pages.remove("Member Role Management")

    selected_page = st.radio(
        "Admin Studio Sections",
        pages,
        horizontal=False,
        label_visibility="collapsed"
    )

    st.divider()

    if selected_page == "Platform Overview":

        _render_overview(
            supabase,
            actor_role
        )

    elif selected_page == "Member Role Management":

        _render_role_management(
            supabase,
            current_user_id,
            actor_role
        )

    elif selected_page == "Learning Materials":

        _render_learning_materials(
            supabase,
            current_user_id,
            actor_role
        )

    elif selected_page == "Quiz Management":

        _render_quiz_management(
            supabase,
            current_user_id,
            actor_role
        )

    elif selected_page == "Node Station Management":

        _render_station_management(
            supabase,
            current_user_id,
            actor_role
        )

    elif selected_page == "Administrative Activity":

        _render_audit_logs(
            supabase,
            actor_role
    )
