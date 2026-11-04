"""
EcoLoop Node — Unified Points System
Powered by Next Gen Impact Hub (NGIH)
"""

import streamlit as st


def award_points(
    supabase,
    user_id,
    points,
    activity_type,
    description,
    contribution_id=None,
    quiz_attempt_id=None,
    group_id=None
):
    """
    Award points through the secure Supabase function.
    Only authorised administrators can execute awards.
    """

    try:
        result = supabase.rpc(
            "award_ecoloop_points",
            {
                "p_user_id": str(user_id),
                "p_points": int(points),
                "p_activity_type": str(activity_type),
                "p_description": str(description),
                "p_contribution_id": (
                    str(contribution_id) if contribution_id else None
                ),
                "p_quiz_attempt_id": (
                    str(quiz_attempt_id) if quiz_attempt_id else None
                ),
                "p_group_id": (
                    str(group_id) if group_id else None
                )
            }
        ).execute()

        return {
            "success": True,
            "transaction_id": result.data,
            "message": "Points awarded successfully."
        }

    except Exception as error:
        return {
            "success": False,
            "transaction_id": None,
            "message": str(error)
        }


def get_user_points(supabase, user_id):
    """Calculate one user's total points."""

    try:
        result = (
            supabase.table("point_transactions")
            .select("points")
            .eq("user_id", str(user_id))
            .execute()
        )

        total = sum(
            int(row.get("points") or 0)
            for row in (result.data or [])
        )

        return total

    except Exception as error:
        st.error(f"Could not load points: {error}")
        return 0


def get_points_transactions(supabase, user_id, limit=20):
    """Get a user's latest points transactions."""

    try:
        result = (
            supabase.table("point_transactions")
            .select(
                "activity_type, points, description, awarded_at"
            )
            .eq("user_id", str(user_id))
            .order("awarded_at", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data or []

    except Exception as error:
        st.error(f"Could not load points history: {error}")
        return []
