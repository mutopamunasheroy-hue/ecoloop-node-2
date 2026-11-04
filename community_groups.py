
import streamlit as st


# =====================================================
# ECOLOOP NODE — COMMUNITY GROUPS MODULE
# Powered by Next Gen Impact Hub (NGIH)
# =====================================================


def render_community_groups_page(supabase, user_id):

    st.title("🤝 Community Groups")

    st.write(
        "Connect with people, schools and organisations "
        "working towards environmental protection."
    )

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    if not user_id:
        st.warning("Please log in to access community groups.")
        return

    # -------------------------------------------------
    # CREATE A COMMUNITY GROUP
    # -------------------------------------------------

    st.subheader("🌱 Create a Community Group")

    with st.form("create_community_group_form"):

        group_name = st.text_input(
            "Group name",
            placeholder="e.g. Harare Green Champions"
        )

        description = st.text_area(
            "Group description",
            placeholder="What is your group working towards?"
        )

        create_group = st.form_submit_button(
            "Create Community Group",
            use_container_width=True
        )

        if create_group:

            if not group_name.strip():
                st.warning("Please enter a group name.")

            else:

                try:

                    supabase.table(
                        "community_groups"
                    ).insert({
                        "name": group_name.strip(),
                        "description": description.strip(),
                        "created_by": user_id
                    }).execute()

                    st.success(
                        "Your community group has been created!"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "The community group could not be created."
                    )

                    st.code(str(e))

    st.divider()

    # -------------------------------------------------
    # LOAD COMMUNITY GROUPS
    # -------------------------------------------------

    st.subheader("Explore Environmental Groups")

    try:

        group_response = (
            supabase
            .table("community_groups")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        groups = group_response.data or []

    except Exception as e:

        st.error("Community groups could not be loaded.")
        st.code(str(e))
        return

    # -------------------------------------------------
    # LOAD MEMBER'S MEMBERSHIPS
    # -------------------------------------------------

    try:

        membership_response = (
            supabase
            .table("group_memberships")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        memberships = membership_response.data or []

    except Exception as e:

        st.error("Membership information could not be loaded.")
        st.code(str(e))
        return

    membership_by_group = {
        membership.get("group_id"): membership
        for membership in memberships
        if membership.get("group_id")
    }

    # -------------------------------------------------
    # EMPTY STATE
    # -------------------------------------------------

    if not groups:

        st.info(
            "There are no community groups available yet. "
            "You can create the first one above!"
        )

        return

    st.caption(
        f"{len(groups)} registered community group(s)"
    )

    # -------------------------------------------------
    # DISPLAY COMMUNITY GROUPS
    # -------------------------------------------------

    for group in groups:

        group_id = group.get("id")

        if not group_id:
            continue

        group_name = (
            group.get("name")
            or "Environmental Community Group"
        )

        description = (
            group.get("description")
            or "A community working towards environmental action."
        )

        creator_id = group.get("created_by")

        membership = membership_by_group.get(group_id)

        is_creator = str(creator_id) == str(user_id)

        with st.container(border=True):

            st.subheader(f"🌱 {group_name}")

            st.write(description)

            if is_creator:

                st.success("You created this group.")

                st.caption("Group administrator")

            elif membership:

                status = membership.get("status", "unknown")

                if status == "approved":

                    st.success(
                        "You are an approved member of this group."
                    )

                elif status == "pending":

                    st.info(
                        "Your membership request is awaiting approval."
                    )

                elif status == "rejected":

                    st.warning(
                        "Your previous membership request was not approved."
                    )

                else:

                    st.caption(
                        f"Membership status: {status}"
                    )

            else:

                if st.button(
                    "Request to Join",
                    key=f"join_group_{group_id}",
                    use_container_width=True
                ):

                    try:

                        supabase.table(
                            "group_memberships"
                        ).insert({
                            "group_id": group_id,
                            "user_id": user_id,
                            "status": "pending"
                        }).execute()

                        st.success(
                            "Your membership request has been submitted."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "Your membership request could not be submitted."
                        )

                        st.code(str(e))

    # -------------------------------------------------
    # COMMUNITY INFORMATION
    # -------------------------------------------------

    st.divider()

    st.info(
        "Community groups bring people together to "
        "collaborate, exchange ideas and participate "
        "in environmental initiatives."
    )
