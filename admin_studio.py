import streamlit as st
from datetime import datetime, timezone
import uuid
import re

# ============================================================
# ECOLOOP NODE — ADMIN STUDIO
# ============================================================

ROLE_SUPER_ADMIN = "super_admin"
ROLE_SUPER_USER = "super_user"
ROLE_ADMIN = "admin"
ROLE_MEMBER = "user"

ROLE_LABELS = {
    ROLE_SUPER_ADMIN: "Super Admin",
    ROLE_SUPER_USER: "Super User",
    ROLE_ADMIN: "Administrator / Coordinator",
    ROLE_MEMBER: "Ordinary Member",
}

PRIMARY_SUPER_ADMIN_ID = str(
    st.secrets.get("PRIMARY_SUPER_ADMIN_ID", "")
).strip()

NGIH_PILLARS = [
    "Governance & Civic Education",
    "Climate Action & Environment",
    "Business & Entrepreneurship",
    "Technology, Innovation, Media & Arts",
]

COUNTRIES = {
    "Zimbabwe": "ZW",
    "South Africa": "ZA",
    "Botswana": "BW",
    "Zambia": "ZM",
    "Kenya": "KE",
    "Nigeria": "NG",
    "Ghana": "GH",
    "United States": "US",
    "United Kingdom": "GB",
    "Canada": "CA",
    "Australia": "AU",
    "Other": "XX",
}

MATERIALS = [
    "Plastic", "Paper", "Metal", "Glass",
    "Organic", "Electronic", "Textiles", "Other",
]

STATION_TYPES = [
    "EcoLoop-owned",
    "Partner station",
    "Community collection point",
]

METRIC_TABLES = {
    "Registered Members": "profiles",
    "Collection Stations": "collection_stations",
    "Waste Contributions": "waste_contributions",
    "Community Groups": "community_groups",
    "Reading Materials": "learning_resources",
    "Quiz Questions": "quiz_questions",
}


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
    supabase, actor_id, action, target_type,
    target_id=None, details=None
):
    """Best-effort audit insert; never broadens database permissions."""
    if not actor_id:
        return

    record = {
        "actor_id": actor_id,
        "action": action,
        "target_type": target_type,
        "target_id": str(target_id) if target_id else None,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _safe_execute(
        supabase.table("admin_audit_logs").insert(record),
        show_error=False,
    )


def _get_role(profile):
    return profile.get("role", ROLE_MEMBER) if isinstance(profile, dict) else ROLE_MEMBER


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
        and str(user_id) == PRIMARY_SUPER_ADMIN_ID
    )


def _can_manage_roles(role):
    return role in (ROLE_SUPER_ADMIN, ROLE_SUPER_USER)


def _can_manage_super_users(role, user_id):
    return role == ROLE_SUPER_ADMIN and _is_primary_super_admin(user_id)


def _can_manage_content(role):
    return role in (ROLE_SUPER_ADMIN, ROLE_SUPER_USER, ROLE_ADMIN)


def _can_manage_stations(role):
    return role in (ROLE_SUPER_ADMIN, ROLE_SUPER_USER, ROLE_ADMIN)


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

def _change_member_role(supabase, actor_id, actor_role, target, new_role):
    target_id = target.get("id")
    target_role = target.get("role", ROLE_MEMBER)

    if not target_id:
        st.error("This member has no valid account ID.")
        return

    if _is_primary_super_admin(target_id):
        st.error("The Primary Super Admin account is protected.")
        return

    if new_role not in (ROLE_SUPER_USER, ROLE_ADMIN, ROLE_MEMBER):
        st.error("Invalid role selected.")
        return

    if target_role == ROLE_SUPER_USER or new_role == ROLE_SUPER_USER:
        if not _can_manage_super_users(actor_role, actor_id):
            st.error("Only the Primary Super Admin can appoint or revoke Super Users.")
            return

    if actor_role not in (ROLE_SUPER_ADMIN, ROLE_SUPER_USER):
        st.error("You do not have permission to change member roles.")
        return

    result = _safe_execute(
        supabase.rpc(
            "manage_member_role",
            {"target_id": str(target_id), "new_role": new_role},
        )
    )

    if result is not None:
        st.success(f"Member role updated to {ROLE_LABELS[new_role]}.")
        st.rerun()


def _render_role_management(supabase, actor_id, actor_role):
    st.subheader("Member Role Management")

    if not _can_manage_roles(actor_role):
        st.warning("You do not have permission to manage roles.")
        return

    members = _get_members(supabase)
    search = st.text_input(
        "Search members",
        placeholder="Search by name, username or email...",
    )

    filtered = []
    for member in members:
        searchable = " ".join([
            str(member.get("full_name", "")),
            str(member.get("username", "")),
            str(member.get("email", "")),
        ]).lower()
        if search.lower() in searchable:
            filtered.append(member)

    if not filtered:
        st.info("No matching accounts found.")
        return

    member_options = {}
    for member in filtered:
        name = member.get("full_name") or member.get("username") or "Unnamed Member"
        role = member.get("role", ROLE_MEMBER)
        label = f"{name} — {ROLE_LABELS.get(role, role)} — {str(member.get('id'))[:8]}"
        member_options[label] = member

    selected_label = st.selectbox(
        "Select an account",
        list(member_options.keys())
    )
    selected = member_options[selected_label]

    st.write(f"**Name:** {_get_name(selected)}")
    st.write(f"**Username:** {selected.get('username', 'Not available')}")
    st.write(f"**Email:** {selected.get('email', 'Not available')}")

    current_role = selected.get("role", ROLE_MEMBER)
    st.write(f"**Current role:** {ROLE_LABELS.get(current_role, current_role)}")

    if _is_primary_super_admin(selected.get("id")):
        st.success("Protected Primary Super Admin account.")
        return

    if _can_manage_super_users(actor_role, actor_id):
        available_roles = [ROLE_MEMBER, ROLE_ADMIN, ROLE_SUPER_USER]
    elif actor_role == ROLE_SUPER_USER:
        if current_role == ROLE_SUPER_USER:
            st.info("Super Users cannot change another Super User's appointment.")
            return
        available_roles = [ROLE_MEMBER, ROLE_ADMIN]
    else:
        return

    new_role = st.selectbox(
        "Assign account role",
        available_roles,
        format_func=lambda role: ROLE_LABELS[role],
        key="admin_studio_new_role",
    )

    if st.button("Save Role Changes", type="primary", use_container_width=True):
        if new_role == current_role:
            st.info("This account already has that role.")
        else:
            _change_member_role(
                supabase, actor_id, actor_role, selected, new_role
    )
# ============================================================
# LEARNING MATERIAL MANAGEMENT
# Actual table: learning_resources
# Actual bucket: learning-resources
# ============================================================

def _render_learning_materials(supabase, actor_id, actor_role):
    st.subheader("Learning Materials")

    if not _can_manage_content(actor_role):
        st.warning("You do not have permission to manage content.")
        return

    tab_pending, tab_add = st.tabs([
        "Pending Submissions",
        "Add Reading Material",
    ])

    with tab_pending:
        materials = _get_pending_content(supabase, "learning_resources")

        if not materials:
            st.info("There are no pending reading materials.")

        for index, material in enumerate(materials):
            material_id = material.get("id")
            with st.expander(material.get("title", "Untitled Material")):
                st.write(material.get("description", ""))
                st.write(f"**Category:** {material.get('category', 'Uncategorised')}")
                st.write(f"**Licence:** {material.get('licence', 'Not specified')}")
                st.write(f"**Submitted by:** {material.get('submitted_by', 'Unknown')}")
                st.write(f"**Resource URL:** {material.get('resource_url') or 'Not provided'}")
                st.write(f"**File path:** {material.get('file_path') or 'No uploaded file'}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_learning_{material_id}_{index}"):
                        result = _safe_execute(
                            supabase.table("learning_resources")
                            .update({"status": "approved"})
                            .eq("id", material_id)
                        )
                        if result is not None:
                            _record_audit(
                                supabase, actor_id, "learning_material_approved",
                                "learning_resources", material_id
                            )
                            st.success("Material approved.")
                            st.rerun()

                with col2:
                    if st.button("Reject", key=f"reject_learning_{material_id}_{index}"):
                        result = _safe_execute(
                            supabase.table("learning_resources")
                            .update({"status": "rejected"})
                            .eq("id", material_id)
                        )
                        if result is not None:
                            _record_audit(
                                supabase, actor_id, "learning_material_rejected",
                                "learning_resources", material_id
                            )
                            st.success("Material rejected.")
                            st.rerun()

    with tab_add:
        st.caption("Submit a PDF or an external learning-resource link for review.")

        with st.form("admin_add_reading_material"):
            title = st.text_input("Material title")
            description = st.text_area("Description")
            category = st.selectbox("Learning category", NGIH_PILLARS)
            licence = st.text_input(
                "Resource licence",
                placeholder="e.g. Creative Commons, Open Access",
            )
            resource_url = st.text_input("External resource URL (optional)")
            uploaded_file = st.file_uploader(
                "Upload reading material (optional)",
                type=["pdf", "doc", "docx", "ppt", "pptx"],
            )
            submitted = st.form_submit_button(
                "Submit Reading Material",
                use_container_width=True,
            )

        if submitted:
            if not title.strip():
                st.error("Enter a material title.")
            elif not licence.strip():
                st.error("Enter the resource licence.")
            elif not resource_url.strip() and not uploaded_file:
                st.error("Provide a resource URL or upload a file.")
            else:
                file_path = None
                upload_success = True

                if uploaded_file:
                    file_path = f"{actor_id}/{uuid.uuid4().hex}_{uploaded_file.name}"
                    try:
                        supabase.storage.from_("learning-resources").upload(
                            file_path,
                            uploaded_file.getvalue(),
                            {
                                "content-type": (
                                    uploaded_file.type or "application/octet-stream"
                                )
                            },
                        )
                    except Exception as exc:
                        upload_success = False
                        st.error(f"Storage upload failed: {exc}")
                        st.info(
                            "Storage permissions must be configured in Supabase. "
                            "This code does not bypass those permissions."
                        )

                if upload_success:
                    record = {
                        "title": title.strip(),
                        "description": description.strip(),
                        "category": category,
                        "licence": licence.strip(),
                        "resource_url": resource_url.strip() or None,
                        "file_path": file_path,
                        "submitted_by": actor_id,
                        "status": "pending",
                    }
                    result = _safe_execute(
                        supabase.table("learning_resources").insert(record)
                    )
                    if result is not None:
                        _record_audit(
                            supabase, actor_id, "learning_material_submitted",
                            "learning_resources"
                        )
                        st.success("Reading material submitted for review.")
                        st.rerun()


# ============================================================
# QUIZ MANAGEMENT
# Uses quiz_submissions and existing publication RPC.
# ============================================================

def _render_quiz_management(supabase, actor_id, actor_role):
    st.subheader("Quiz Management")

    if not _can_manage_content(actor_role):
        st.warning("You do not have permission to manage quizzes.")
        return

    tab_create, tab_pending = st.tabs([
        "Submit Quiz Question",
        "Pending Quiz Submissions",
    ])

    with tab_create:
        st.caption(
            "Questions are submitted for review through the existing quiz workflow."
        )

        with st.form("admin_create_quiz_question"):
            quiz_title = st.text_input("Quiz title", value="NGIH Community Quiz")
            description = st.text_area(
                "Quiz description",
                value="Community learning question submitted for review.",
            )
            pillar = st.selectbox("NGIH Pillar", NGIH_PILLARS)
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            question = st.text_area("Question")
            option_a = st.text_input("Option A")
            option_b = st.text_input("Option B")
            option_c = st.text_input("Option C")
            option_d = st.text_input("Option D")
            correct_option = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
            explanation = st.text_area("Explanation")
            submitted = st.form_submit_button(
                "Submit Quiz Question",
                use_container_width=True,
            )

        if submitted:
            if not quiz_title.strip():
                st.error("Enter a quiz title.")
            elif not question.strip():
                st.error("Enter a question.")
            elif not all([
                option_a.strip(), option_b.strip(),
                option_c.strip(), option_d.strip()
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
                    "points": 1,
                }

                difficulty_value = {
                    "Easy": "beginner",
                    "Medium": "intermediate",
                    "Hard": "advanced",
                }[difficulty]

                submission_data = {
                    "user_id": actor_id,
                    "title": quiz_title.strip(),
                    "description": description.strip(),
                    "category": pillar,
                    "difficulty": difficulty_value,
                    "questions": [question_data],
                    "status": "pending",
                }

                result = _safe_execute(
                    supabase.table("quiz_submissions").insert(submission_data)
                )
                if result is not None:
                    _record_audit(
                        supabase, actor_id, "quiz_question_submitted",
                        "quiz_submissions"
                    )
                    st.success("Quiz question submitted for review.")
                    st.rerun()

    with tab_pending:
        if actor_role != ROLE_SUPER_ADMIN or not _is_primary_super_admin(actor_id):
            st.info(
                "Quiz publication and rejection are reserved for the "
                "configured Primary Super Admin."
            )
            return

        submissions = _get_pending_content(supabase, "quiz_submissions")

        if not submissions:
            st.info("There are no pending quiz submissions.")

        for index, item in enumerate(submissions):
            submission_id = item.get("id")
            with st.expander(item.get("title", "Untitled Quiz Submission")):
                st.write(f"**Description:** {item.get('description', '')}")
                st.write(f"**Pillar:** {item.get('category', 'Not specified')}")
                st.write(f"**Difficulty:** {item.get('difficulty', 'Not specified')}")
                st.write(f"**Submitted by:** {item.get('user_id', 'Unknown')}")

                questions = item.get("questions") or []
                if not isinstance(questions, list):
                    questions = []

                if not questions:
                    st.warning("This submission has no readable questions.")

                for q_index, q in enumerate(questions):
                    st.divider()
                    st.write(
                        f"**Question {q_index + 1}:** "
                        f"{q.get('question_text', '')}"
                    )
                    for option in ["a", "b", "c", "d"]:
                        st.write(
                            f"{option.upper()}: {q.get('option_' + option, '')}"
                        )
                    st.write(f"**Correct option:** {q.get('correct_option', '')}")
                    st.write(f"**Explanation:** {q.get('explanation', '')}")

                note = st.text_area(
                    "Review note",
                    key=f"quiz_review_note_{submission_id}_{index}",
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "Approve and Publish",
                        key=f"publish_quiz_{submission_id}_{index}",
                        type="primary",
                    ):
                        result = _safe_execute(
                            supabase.rpc(
                                "publish_quiz_submission",
                                {"p_submission_id": submission_id},
                            )
                        )
                        if result is not None:
                            _record_audit(
                                supabase, actor_id, "quiz_submission_published",
                                "quiz_submissions", submission_id
                            )
                            st.success("Quiz submission published successfully.")
                            st.rerun()

                with col2:
                    if st.button(
                        "Reject Submission",
                        key=f"reject_quiz_{submission_id}_{index}",
                    ):
                        if not note.strip():
                            st.warning("Provide a reason for rejection.")
                        else:
                            now = datetime.now(timezone.utc).isoformat()
                            result = _safe_execute(
                                supabase.table("quiz_submissions")
                                .update({
                                    "status": "rejected",
                                    "admin_feedback": note.strip(),
                                    "reviewed_by": actor_id,
                                    "reviewed_at": now,
                                    "updated_at": now,
                                })
                                .eq("id", submission_id)
                            )
                            if result is not None:
                                _record_audit(
                                    supabase, actor_id, "quiz_submission_rejected",
                                    "quiz_submissions", submission_id,
                                    {"reason": note.strip()}
                                )
                                st.success("Quiz submission rejected.")
                                st.rerun()
# ============================================================
# GLOBAL STATION MANAGEMENT
# Matches collection_stations schema supplied by user.
# ============================================================

def _station_prefix(country_code, city):
    city_code = re.sub(r"[^A-Z]", "", city.upper())[:3] or "GEN"
    return f"ECO-{country_code}-{city_code}"


def _create_admin_station(
    supabase, station_name, country, region, city, address,
    capacity_kg, accepted_materials, station_type,
    latitude=None, longitude=None
):
    try:
        country_code = COUNTRIES.get(country, "XX")
        prefix = _station_prefix(country_code, city)

        existing = (
            supabase.table("collection_stations")
            .select("station_code")
            .like("station_code", f"{prefix}-%")
            .execute()
        )

        existing_numbers = []
        for station in existing.data or []:
            code = station.get("station_code", "")
            try:
                existing_numbers.append(int(code.split("-")[-1]))
            except (ValueError, IndexError):
                continue

        next_number = max(existing_numbers, default=0) + 1
        station_code = f"{prefix}-{next_number:04d}"

        station_data = {
            "station_code": station_code,
            "station_name": station_name.strip(),
            "country": country,
            "country_code": country_code,
            "region": region.strip(),
            "city": city.strip(),
            "address": address.strip(),
            "capacity_kg": float(capacity_kg),
            "accepted_materials": accepted_materials,
            "station_type": station_type,
            "is_active": True,
            "qr_code": station_code,
            "qr_enabled": True,
            "sensor_enabled": False,
            "sensor_status": "not_installed",
            "fill_level": 0,
        }

        if latitude is not None:
            station_data["latitude"] = float(latitude)
        if longitude is not None:
            station_data["longitude"] = float(longitude)

        response = (
            supabase.table("collection_stations")
            .insert(station_data)
            .execute()
        )

        if not response.data:
            return False, "The database did not confirm station creation."

        return True, station_code

    except Exception as exc:
        return False, str(exc)


def _render_station_management(supabase, actor_id, actor_role):
    st.subheader("EcoLoop Node Station Management")

    if not _can_manage_stations(actor_role):
        st.warning("You do not have permission to manage stations.")
        return

    tab_add, tab_view = st.tabs(["Register Station", "Existing Stations"])

    with tab_add:
        with st.form("admin_add_global_station"):
            station_name = st.text_input("Station Name")
            station_type = st.selectbox("Station Type", STATION_TYPES)
            country = st.selectbox("Country", list(COUNTRIES.keys()))
            region = st.text_input("Region / Province")
            city = st.text_input("City")
            address = st.text_area("Physical Address")
            capacity = st.number_input(
                "Maximum Capacity (kg)",
                min_value=1.0,
                value=500.0,
                step=50.0,
            )
            accepted_materials = st.multiselect(
                "Accepted Materials", MATERIALS
            )
            add_coordinates = st.checkbox("Add GPS coordinates")

            latitude = None
            longitude = None
            if add_coordinates:
                latitude = st.number_input(
                    "Latitude", min_value=-90.0, max_value=90.0,
                    value=0.0, format="%.6f"
                )
                longitude = st.number_input(
                    "Longitude", min_value=-180.0, max_value=180.0,
                    value=0.0, format="%.6f"
                )

            submitted = st.form_submit_button(
                "Register Station", use_container_width=True
            )

        if submitted:
            if not station_name.strip():
                st.error("Enter a station name.")
            elif not region.strip():
                st.error("Enter the region or province.")
            elif not city.strip():
                st.error("Enter the city.")
            elif not address.strip():
                st.error("Enter the physical address.")
            elif not accepted_materials:
                st.error("Select at least one accepted material.")
            else:
                success, result = _create_admin_station(
                    supabase=supabase,
                    station_name=station_name,
                    country=country,
                    region=region,
                    city=city,
                    address=address,
                    capacity_kg=capacity,
                    accepted_materials=accepted_materials,
                    station_type=station_type,
                    latitude=latitude,
                    longitude=longitude,
                )

                if success:
                    _record_audit(
                        supabase, actor_id, "station_added",
                        "collection_stations", result
                    )
                    st.success(f"Station registered successfully: {result}")
                    st.rerun()
                else:
                    st.error(f"Station registration failed: {result}")

    with tab_view:
        try:
            response = (
                supabase.table("collection_stations")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            stations = response.data or []
        except Exception as exc:
            st.error(f"Could not load stations: {exc}")
            stations = []

        active_count = sum(
            1 for station in stations if station.get("is_active") is True
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Stations", len(stations))
        c2.metric("Active Stations", active_count)
        c3.metric("Inactive Stations", len(stations) - active_count)

        for index, station in enumerate(stations):
            station_code = station.get("station_code", "")
            station_name = station.get("station_name", "Unnamed Station")
            active = station.get("is_active", False)

            with st.expander(f"{station_name} — {station_code}"):
                st.write(f"**Country:** {station.get('country', '')}")
                st.write(f"**Region:** {station.get('region', '')}")
                st.write(f"**City:** {station.get('city', '')}")
                st.write(f"**Address:** {station.get('address', '')}")
                st.write(f"**Station Type:** {station.get('station_type', '')}")
                st.write(f"**Capacity:** {station.get('capacity_kg', 0)} kg")

                materials = station.get("accepted_materials") or []
                st.write("**Accepted Materials:** " + ", ".join(materials))
                st.write("**Status:** " + ("Active" if active else "Inactive"))
                st.write(
                    "**QR Enabled:** "
                    + ("Yes" if station.get("qr_enabled") else "No")
                )
                st.write(
                    f"**Sensor Status:** "
                    f"{station.get('sensor_status', 'not_installed')}"
                )

                if _can_manage_super_users(actor_role, actor_id):
                    if active:
                        if st.button(
                            "Deactivate Station",
                            key=f"deactivate_station_{station_code}_{index}",
                        ):
                            result = _safe_execute(
                                supabase.table("collection_stations")
                                .update({"is_active": False})
                                .eq("station_code", station_code)
                            )
                            if result is not None:
                                _record_audit(
                                    supabase, actor_id, "station_deactivated",
                                    "collection_stations", station_code
                                )
                                st.success("Station deactivated.")
                                st.rerun()
                    else:
                        if st.button(
                            "Activate Station",
                            key=f"activate_station_{station_code}_{index}",
                        ):
                            result = _safe_execute(
                                supabase.table("collection_stations")
                                .update({"is_active": True})
                                .eq("station_code", station_code)
                            )
                            if result is not None:
                                _record_audit(
                                    supabase, actor_id, "station_activated",
                                    "collection_stations", station_code
                                )
                                st.success("Station activated.")
                                st.rerun()

# ============================================================
# ADMINISTRATIVE ACTIVITY
# ============================================================

def _render_audit_logs(supabase, actor_role):
    st.subheader("Administrative Activity")

    if actor_role not in (ROLE_SUPER_ADMIN, ROLE_SUPER_USER, ROLE_ADMIN):
        st.warning("You cannot access administrative activity.")
        return

    st.info(
        "Administrative activity records are protected. "
        "Secure read access will be configured through a restricted "
        "database mechanism."
    )


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
        "Administrative actions are subject to the platform's role "
        "hierarchy and database security policies."
    )


# ============================================================
# MAIN ADMIN STUDIO PAGE
# ============================================================

def admin_studio_page(supabase, current_user_id, profile):
    if not current_user_id or not isinstance(profile, dict):
        st.error("Please sign in to access Admin Studio.")
        return

    actor_role = _get_role(profile)

    if actor_role not in (ROLE_SUPER_ADMIN, ROLE_SUPER_USER, ROLE_ADMIN):
        st.error("Access denied. Administrative permissions are required.")
        return

    if actor_role == ROLE_SUPER_ADMIN and not _is_primary_super_admin(current_user_id):
        st.error(
            "This Super Admin account is not registered as the protected "
            "Primary Super Admin."
        )
        return

    st.title("Admin Studio")
    st.caption(
        "Central administration and operational management for EcoLoop Node."
    )
    st.write(f"Welcome, **{_get_name(profile)}**")
    st.divider()

    pages = [
        "Platform Overview",
        "Member Role Management",
        "Learning Materials",
        "Quiz Management",
        "Node Station Management",
        "Administrative Activity",
    ]

    if actor_role == ROLE_ADMIN:
        pages.remove("Member Role Management")

    selected_page = st.radio(
        "Admin Studio Sections",
        pages,
        horizontal=False,
        label_visibility="collapsed",
    )

    st.divider()

    if selected_page == "Platform Overview":
        _render_overview(supabase, actor_role)
    elif selected_page == "Member Role Management":
        _render_role_management(supabase, current_user_id, actor_role)
    elif selected_page == "Learning Materials":
        _render_learning_materials(supabase, current_user_id, actor_role)
    elif selected_page == "Quiz Management":
        _render_quiz_management(supabase, current_user_id, actor_role)
    elif selected_page == "Node Station Management":
        _render_station_management(supabase, current_user_id, actor_role)
    elif selected_page == "Administrative Activity":
        _render_audit_logs(supabase, actor_role)
