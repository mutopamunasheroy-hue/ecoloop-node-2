
import streamlit as st
from datetime import datetime, timezone
import uuid


# ============================================================
# ECOLOOP NODE — ADMIN STUDIO
# ============================================================
# Roles:
#   super_admin  = Primary Super Admin
#   super_user   = Additional Super User
#   admin        = Administrator / Coordinator
#   user         = Ordinary Member
#
# Database tables and security policies will be created
# separately in Supabase.
# ============================================================


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# GENERAL HELPERS
# ------------------------------------------------------------

def _safe_execute(query):
    try:
        return query.execute()
    except Exception as exc:
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
    """
    Records important administrative activity.
    The matching audit table will be created in Supabase.
    """

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
        supabase.table("admin_audit_logs").insert(record)
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
    return role in [
        ROLE_SUPER_ADMIN,
        ROLE_SUPER_USER
    ]


def _can_manage_super_users(role, user_id):
    return (
        role == ROLE_SUPER_ADMIN
        and _is_primary_super_admin(user_id)
    )


def _can_manage_admins(role):
    return role in [
        ROLE_SUPER_ADMIN,
        ROLE_SUPER_USER
    ]


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


# ------------------------------------------------------------
# DATA RETRIEVAL
# ------------------------------------------------------------

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

    except Exception:
        return []


# ------------------------------------------------------------
# MEMBER ROLE MANAGEMENT
# ------------------------------------------------------------

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

    # Protect the primary Super Admin.
    if _is_primary_super_admin(target_id):
        st.error("The Primary Super Admin account is protected.")
        return

    # Nobody can appoint another Primary Super Admin.
    if new_role == ROLE_SUPER_ADMIN:
        st.error(
            "The Primary Super Admin role cannot be assigned "
            "through ordinary member management."
        )
        return

    # Only the Primary Super Admin manages Super Users.
    if target_role == ROLE_SUPER_USER or new_role == ROLE_SUPER_USER:

        if not _can_manage_super_users(actor_role, actor_id):
            st.error(
                "Only the Primary Super Admin can appoint "
                "or revoke Super Users."
            )
            return

    # Super Users can appoint or revoke Administrators.
    if target_role == ROLE_ADMIN or new_role == ROLE_ADMIN:

        if not _can_manage_admins(actor_role):
            st.error(
                "You do not have permission to manage "
                "Administrators / Coordinators."
            )
            return

    # Administrators cannot manage account roles.
    if actor_role == ROLE_ADMIN:
        st.error("Administrators cannot change member roles.")
        return

    # Validate available role values.
    if new_role not in [
        ROLE_SUPER_USER,
        ROLE_ADMIN,
        ROLE_MEMBER
    ]:
        st.error("Invalid role selected.")
        return

    result = _safe_execute(
        supabase.table("profiles")
        .update({"role": new_role})
        .eq("id", target_id)
    )

    if result is not None:

        _record_audit(
            supabase,
            actor_id,
            "member_role_changed",
            "profiles",
            target_id,
            {
                "previous_role": target_role,
                "new_role": new_role
            }
        )

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

        member_id = member.get("id")

        name = (
            member.get("full_name")
            or member.get("username")
            or "Unnamed Member"
        )

        role = member.get("role", ROLE_MEMBER)

        member_options[
            f"{name} — {ROLE_LABELS.get(role, role)}"
        ] = member

    selected_label = st.selectbox(
        "Select an account",
        list(member_options.keys())
    )

    selected = member_options[selected_label]

    st.divider()

    st.write(
        f"**Name:** {_get_name(selected)}"
    )

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

    role_labels = {
        role: ROLE_LABELS[role]
        for role in available_roles
    }

    new_role = st.selectbox(
        "Assign account role",
        available_roles,
        format_func=lambda role: role_labels[role],
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


# ------------------------------------------------------------
# LEARNING MATERIAL MANAGEMENT
# ------------------------------------------------------------

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

            for material in materials:

                with st.expander(
                    material.get("title", "Untitled Material")
                ):

                    st.write(
                        material.get("description", "")
                    )

                    st.write(
                        f"Category: {material.get('category', 'Uncategorised')}"
                    )

                    st.write(
                        f"Submitted by: {material.get('uploaded_by', 'Unknown')}"
                    )

                    st.write(
                        f"File: {material.get('file_url', 'Not available')}"
                    )

                    review_note = st.text_input(
                        "Review note",
                        key=f"material_note_{material.get('id')}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Approve",
                            key=f"approve_material_{material.get('id')}"
                        ):

                            result = _safe_execute(
                                supabase.table("reading_resources")
                                .update({
                                    "status": "approved",
                                    "reviewed_by": actor_id,
                                    "review_note": review_note
                                })
                                .eq("id", material.get("id"))
                            )

                            if result is not None:

                                _record_audit(
                                    supabase,
                                    actor_id,
                                    "reading_material_approved",
                                    "reading_resources",
                                    material.get("id")
                                )

                                st.success("Material approved.")
                                st.rerun()

                    with col2:

                        if st.button(
                            "Reject",
                            key=f"reject_material_{material.get('id')}"
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
                                    .eq("id", material.get("id"))
                                )

                                if result is not None:

                                    _record_audit(
                                        supabase,
                                        actor_id,
                                        "reading_material_rejected",
                                        "reading_resources",
                                        material.get("id"),
                                        {"reason": review_note}
                                    )

                                    st.success("Material rejected.")
                                    st.rerun()

    with tab_add:

        st.write(
            "Administrators and senior administrators can "
            "contribute learning materials directly."
        )

        with st.form("admin_add_reading_material"):

            title = st.text_input("Material title")

            description = st.text_area(
                "Description"
            )

            category = st.selectbox(
                "Learning category",
                [
                    "Governance & Civic Education",
                    "Climate Action & Environment",
                    "Business & Entrepreneurship",
                    "Technology, Innovation, Media & Arts"
                ]
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

                    try:

                        file_name = (
                            f"reading-materials/"
                            f"{uuid.uuid4().hex}_{uploaded_file.name}"
                        )

                        upload_result = (
                            supabase.storage
                            .from_("learning-resources")
                            .upload(
                                file_name,
                                uploaded_file.getvalue(),
                                {
                                    "content-type": uploaded_file.type
                                }
                            )
                        )

                        file_url = (
                            supabase.storage
                            .from_("learning-resources")
                            .get_public_url(file_name)
                        )

                        result = _safe_execute(
                            supabase.table("reading_resources")
                            .insert({
                                "title": title,
                                "description": description,
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

                    except Exception as exc:
                        st.error(
                            f"Upload failed: {exc}"
                        )


# ------------------------------------------------------------
# QUIZ MANAGEMENT
# ------------------------------------------------------------

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
        "Create Quiz Question",
        "Pending Questions"
    ])

    with tab_create:

        with st.form("admin_create_quiz_question"):

            question = st.text_area("Question")

            pillar = st.selectbox(
                "NGIH Pillar",
                [
                    "Governance & Civic Education",
                    "Climate Action & Environment",
                    "Business & Entrepreneurship",
                    "Technology, Innovation, Media & Arts"
                ]
            )

            option_a = st.text_input("Option A")
            option_b = st.text_input("Option B")
            option_c = st.text_input("Option C")
            option_d = st.text_input("Option D")

            correct_answer = st.selectbox(
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

                if not question.strip():
                    st.error("Enter a question.")

                elif not all([
                    option_a.strip(),
                    option_b.strip(),
                    option_c.strip(),
                    option_d.strip()
                ]):
                    st.error("Complete all four answer options.")

                else:

                    result = _safe_execute(
                        supabase.table("quiz_questions")
                        .insert({
                            "question": question,
                            "pillar": pillar,
                            "option_a": option_a,
                            "option_b": option_b,
                            "option_c": option_c,
                            "option_d": option_d,
                            "correct_answer": correct_answer,
                            "explanation": explanation,
                            "created_by": actor_id,
                            "status": "pending"
                        })
                    )

                    if result is not None:

                        _record_audit(
                            supabase,
                            actor_id,
                            "quiz_question_submitted",
                            "quiz_questions"
                        )

                        st.success(
                            "Quiz question submitted for review."
                        )

    with tab_pending:

        questions = _get_pending_content(
            supabase,
            "quiz_questions"
        )

        if not questions:
            st.info("There are no pending quiz questions.")

        else:

            for item in questions:

                with st.expander(
                    item.get("question", "Untitled Question")
                ):

                    st.write(
                        f"Pillar: {item.get('pillar', 'Not specified')}"
                    )

                    for option in ["a", "b", "c", "d"]:
                        st.write(
                            f"{option.upper()}: "
                            f"{item.get('option_' + option, '')}"
                        )

                    st.write(
                        f"Correct answer: {item.get('correct_answer', '')}"
                    )

                    note = st.text_input(
                        "Review note",
                        key=f"quiz_note_{item.get('id')}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Approve Question",
                            key=f"approve_quiz_{item.get('id')}"
                        ):

                            result = _safe_execute(
                                supabase.table("quiz_questions")
                                .update({
                                    "status": "approved",
                                    "reviewed_by": actor_id,
                                    "review_note": note
                                })
                                .eq("id", item.get("id"))
                            )

                            if result is not None:

                                _record_audit(
                                    supabase,
                                    actor_id,
                                    "quiz_question_approved",
                                    "quiz_questions",
                                    item.get("id")
                                )

                                st.success("Question approved.")
                                st.rerun()

                    with col2:

                        if st.button(
                            "Reject Question",
                            key=f"reject_quiz_{item.get('id')}"
                        ):

                            if not note.strip():
                                st.warning(
                                    "Provide a rejection reason."
                                )
                            else:

                                result = _safe_execute(
                                    supabase.table("quiz_questions")
                                    .update({
                                        "status": "rejected",
                                        "reviewed_by": actor_id,
                                        "review_note": note
                                    })
                                    .eq("id", item.get("id"))
                                )

                                if result is not None:

                                    _record_audit(
                                        supabase,
                                        actor_id,
                                        "quiz_question_rejected",
                                        "quiz_questions",
                                        item.get("id"),
                                        {"reason": note}
                                    )

                                    st.success("Question rejected.")
                                    st.rerun()


# ------------------------------------------------------------
# ECOLOOP NODE STATION MANAGEMENT
# ------------------------------------------------------------

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

            capacity = st.number_input(
                "Station Capacity",
                min_value=1.0,
                value=50.0
            )

            submitted = st.form_submit_button(
                "Add EcoLoop Node Station",
                use_container_width=True
            )

            if submitted:

                if not station_code.strip() or not station_name.strip():
                    st.error("Station code and name are required.")

                else:

                    result = _safe_execute(
                        supabase.table("collection_stations")
                        .insert({
                            "station_code": station_code.upper(),
                            "station_name": station_name,
                            "location": location,
                            "capacity": capacity,
                            "is_active": True,
                            "created_by": actor_id
                        })
                    )

                    if result is not None:

                        _record_audit(
                            supabase,
                            actor_id,
                            "station_added",
                            "collection_stations",
                            station_code
                        )

                        st.success("Station added successfully.")
                        st.rerun()

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

        for station in stations:

            station_id = station.get("id")

            with st.expander(
                station.get("station_name", "Unnamed Station")
            ):

                st.write(
                    f"Code: {station.get('station_code', '')}"
                )

                st.write(
                    f"Location: {station.get('location', '')}"
                )

                st.write(
                    f"Capacity: {station.get('capacity', '')}"
                )

                st.write(
                    "Status: "
                    + (
                        "Active"
                        if station.get("is_active")
                        else "Inactive"
                    )
                )

                # Only the Primary Super Admin can revoke a station.
                if _can_manage_super_users(actor_role, actor_id):

                    if station.get("is_active"):

                        if st.button(
                            "Deactivate Station",
                            key=f"deactivate_station_{station_id}"
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


# ------------------------------------------------------------
# ADMINISTRATIVE ACTIVITY
# ------------------------------------------------------------

def _render_audit_logs(supabase, actor_role):

    st.subheader("Administrative Activity")

    if actor_role not in [
        ROLE_SUPER_ADMIN,
        ROLE_SUPER_USER,
        ROLE_ADMIN
    ]:
        st.warning("You cannot access administrative activity.")
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
        st.error(f"Could not retrieve activity records: {exc}")
        return

    if not logs:
        st.info("No administrative activity has been recorded.")
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


# ------------------------------------------------------------
# PLATFORM OVERVIEW
# ------------------------------------------------------------

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
        f"Your account role: **{ROLE_LABELS.get(actor_role, actor_role)}**"
    )

    st.caption(
        "Administrative actions are subject to the role hierarchy "
        "and database security policies."
    )


# ------------------------------------------------------------
# MAIN ADMIN STUDIO PAGE
# ------------------------------------------------------------

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

    # The primary Super Admin ID must be configured.
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

    # Administrators cannot appoint or revoke account roles.
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

