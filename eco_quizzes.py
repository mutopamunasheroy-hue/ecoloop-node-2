
# ============================================================
# ECOLOOP NODE — ECO QUIZZES
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================

import streamlit as st
from datetime import datetime, timezone


NGIH_PILLARS = [
    "Governance & Civic Education",
    "Climate Action & Environment",
    "Business & Entrepreneurship",
    "Technology, Innovation, Media & Arts"
]

DIFFICULTIES = ["Easy", "Medium", "Hard"]


# ============================================================
# HELPERS
# ============================================================

def _profile_value(profile, key, default=None):
    if isinstance(profile, dict):
        return profile.get(key, default)
    return default


def _is_super_admin(profile):
    return _profile_value(profile, "role", "") == "super_admin"


def _safe_execute(query):
    try:
        response = (
            query.execute()
            if hasattr(query, "execute")
            else query
        )
        return response.data or []
    except Exception as error:
        st.error(f"Database operation failed: {error}")
        return None


def _get_quizzes(supabase):
    return _safe_execute(
        supabase.table("quizzes")
        .select("*")
        .eq("is_active", True)
        .execute()
    )


def _difficulty_badge(difficulty):
    colours = {
        "Easy": "🟢",
        "Medium": "🟠",
        "Hard": "🔴"
    }
    return colours.get(difficulty, "⚪")


def _get_member_name(profile):
    return (
        _profile_value(profile, "full_name")
        or "EcoLoop Member"
    )


# ============================================================
# QUIZ CENTRE
# ============================================================

def quiz_centre(supabase, user_id):

    st.subheader("📚 Quiz Centre")
    st.write(
        "Explore environmental and development knowledge "
        "quizzes from across the four NGIH pillars."
    )

    quizzes = _get_quizzes(supabase)

    if quizzes is None:
        return

    if not quizzes:
        st.info("No published quizzes are available yet.")
        return

    difficulty_filter = st.selectbox(
        "Filter by difficulty",
        ["All"] + DIFFICULTIES,
        key="eco_quiz_difficulty_filter"
    )

    pillar_filter = st.selectbox(
        "Filter by NGIH pillar",
        ["All"] + NGIH_PILLARS,
        key="eco_quiz_pillar_filter"
    )

    filtered = []

    for quiz in quizzes:
        if (
            difficulty_filter != "All"
            and quiz.get("difficulty") != difficulty_filter
        ):
            continue

        if (
            pillar_filter != "All"
            and quiz.get("category") != pillar_filter
        ):
            continue

        filtered.append(quiz)

    if not filtered:
        st.info("No quizzes match these filters.")
        return

    for quiz in filtered:

        title = quiz.get("title", "Untitled Quiz")
        difficulty = quiz.get("difficulty", "Not specified")

        with st.container(border=True):

            st.markdown(f"### {title}")

            st.caption(
                f"{_difficulty_badge(difficulty)} "
                f"{difficulty}  |  "
                f"{quiz.get('category', 'General')}"
            )

            st.write(
                quiz.get("description", "No description available.")
            )

            if st.button(
                "Start Quiz",
                key=f"start_quiz_{quiz['id']}",
                use_container_width=True
            ):
                st.session_state["eco_active_quiz"] = quiz
                st.session_state["eco_quiz_answers"] = {}
                st.session_state["eco_quiz_submitted"] = False
                st.rerun()


# ============================================================
# TAKE QUIZ
# ============================================================

def take_quiz(supabase, user_id):

    quiz = st.session_state.get("eco_active_quiz")

    if not quiz:
        return

    st.subheader(f"🧠 {quiz.get('title', 'Quiz')}")

    questions = _safe_execute(
        supabase.table("quiz_questions")
        .select("*")
        .eq("quiz_id", quiz["id"])
        .order("question_order")
    )

    if questions is None:
        return

    if not questions:
        st.warning("This quiz has no questions yet.")
        return

    if st.session_state.get("eco_quiz_submitted"):

        st.success("Quiz completed!")

        results = st.session_state.get(
            "eco_quiz_results", []
        )

        score = sum(
            1 for result in results
            if result["correct"]
        )

        st.metric(
            "Your score",
            f"{score} / {len(results)}"
        )

        st.progress(score / len(results))

        st.markdown("### Your results")

        for index, result in enumerate(results, 1):

            if result["correct"]:
                st.success(
                    f"Question {index}: Correct"
                )
            else:
                st.error(
                    f"Question {index}: Incorrect"
                )

            st.write(result["question"])

            st.write(
                f"Your answer: {result['selected'] or 'Not answered'}"
            )

            st.write(
                f"Correct answer: {result['correct_answer']}"
            )

            st.info(
                result["explanation"] or
                "No explanation has been provided."
            )

        if st.button(
            "Return to Quiz Centre",
            use_container_width=True
        ):
            _clear_active_quiz()
            st.rerun()

        return

    st.write(
        f"**Questions:** {len(questions)}"
    )

    answers = {}

    with st.form("eco_quiz_answer_form"):

        for index, question in enumerate(questions, 1):

            st.markdown(f"**Question {index}**")

            st.write(question["question_text"])

            options = {
                "A": question.get("option_a", ""),
                "B": question.get("option_b", ""),
                "C": question.get("option_c", ""),
                "D": question.get("option_d", "")
            }

            selected = st.radio(
                "Choose your answer:",
                options=list(options.keys()),
                format_func=lambda value, opts=options:
                    f"{value}. {opts[value]}",
                key=f"eco_answer_{question['id']}",
                index=None
            )

            answers[question["id"]] = selected

            st.divider()

        submitted = st.form_submit_button(
            "Submit Quiz",
            use_container_width=True
        )

    if submitted:

        answer_keys = _safe_execute(
            supabase.table("quiz_answer_keys")
            .select("*")
            .in_(
                "question_id",
                [q["id"] for q in questions]
            )
        )

        if answer_keys is None:
            return

        key_map = {
            item["question_id"]: item
            for item in answer_keys
        }

        results = []

        for question in questions:

            question_id = question["id"]
            selected = answers.get(question_id)

            answer_key = key_map.get(question_id, {})

            correct_answer = (
                answer_key.get("correct_option", "")
            )

            results.append({
                "question": question["question_text"],
                "selected": selected,
                "correct_answer": correct_answer,
                "correct": (
                    selected == correct_answer
                    and bool(correct_answer)
                ),
                "explanation": answer_key.get(
                    "explanation", ""
                )
            })

        score = sum(
            1 for result in results
            if result["correct"]
        )

        attempt_data = {
            "user_id": user_id,
            "quiz_id": quiz["id"],
            "score": score,
            "total_questions": len(questions),
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

        saved_attempt = _safe_execute(
            supabase.table("quiz_attempts")
            .insert(attempt_data)
        )

        if saved_attempt is None:
            return

        st.session_state["eco_quiz_results"] = results
        st.session_state["eco_quiz_submitted"] = True
        st.rerun()


def _clear_active_quiz():

    for key in [
        "eco_active_quiz",
        "eco_quiz_answers",
        "eco_quiz_submitted",
        "eco_quiz_results"
    ]:
        st.session_state.pop(key, None)


# ============================================================
# CREATE QUIZ
# ============================================================

def create_quiz(supabase, user_id):

    st.subheader("✍️ Create a Quiz")

    st.write(
        "Create a knowledge quiz and submit it "
        "for Super Admin review."
    )

    with st.form("eco_create_quiz_form"):

        title = st.text_input("Quiz title")

        description = st.text_area(
            "Quiz description"
        )

        category = st.selectbox(
            "NGIH pillar",
            NGIH_PILLARS
        )

        difficulty = st.selectbox(
            "Difficulty",
            DIFFICULTIES
        )

        question_count = st.number_input(
            "Number of questions",
            min_value=1,
            max_value=30,
            value=5,
            step=1
        )

        questions = []

        for index in range(int(question_count)):

            st.markdown(f"#### Question {index + 1}")

            question_text = st.text_input(
                "Question",
                key=f"create_question_{index}"
            )

            option_a = st.text_input(
                "Option A",
                key=f"create_a_{index}"
            )

            option_b = st.text_input(
                "Option B",
                key=f"create_b_{index}"
            )

            option_c = st.text_input(
                "Option C",
                key=f"create_c_{index}"
            )

            option_d = st.text_input(
                "Option D",
                key=f"create_d_{index}"
            )

            correct_option = st.selectbox(
                "Correct answer",
                ["A", "B", "C", "D"],
                key=f"create_correct_{index}"
            )

            explanation = st.text_area(
                "Explain why this answer is correct",
                key=f"create_explanation_{index}"
            )

            questions.append({
                "question_text": question_text,
                "option_a": option_a,
                "option_b": option_b,
                "option_c": option_c,
                "option_d": option_d,
                "correct_option": correct_option,
                "explanation": explanation,
                "question_order": index + 1,
                "points": 1
            })

        submitted = st.form_submit_button(
            "Submit Quiz for Review",
            use_container_width=True
        )

    if submitted:

        if not title.strip() or not description.strip():
            st.error("Enter a title and description.")
            return

        for index, question in enumerate(questions, 1):

            required_fields = [
                question["question_text"],
                question["option_a"],
                question["option_b"],
                question["option_c"],
                question["option_d"],
                question["explanation"]
            ]

            if not all(
                str(value).strip()
                for value in required_fields
            ):
                st.error(
                    f"Please complete all fields for Question {index}."
                )
                return

        st.info(
            "The quiz submission system requires the "
            "new submission database tables before it "
            "can save this quiz. We will connect those "
            "tables in the next setup step."
        )


# ============================================================
# MY QUIZ SUBMISSIONS
# ============================================================

def my_submissions(supabase, user_id):

    st.subheader("📋 My Quiz Submissions")

    submissions = _safe_execute(
        supabase.table("quiz_submissions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )

    if submissions is None:
        return

    if not submissions:
        st.info("You haven't submitted any quizzes yet.")
        return

    for submission in submissions:

        with st.container(border=True):

            st.markdown(
                f"### {submission.get('title', 'Untitled Quiz')}"
            )

            status = submission.get(
                "status", "pending"
            )

            st.write(f"**Status:** {status.title()}")

            st.write(
                submission.get("review_notes", "")
            )

            if status == "rejected":
                st.warning(
                    "This submission needs changes before "
                    "it can be reviewed again."
                )


# ============================================================
# SUPER ADMIN REVIEW
# ============================================================

def admin_review(supabase):

    st.subheader("🛡️ Super Admin — Quiz Review")

    submissions = _safe_execute(
        supabase.table("quiz_submissions")
        .select("*")
        .eq("status", "pending")
        .order("created_at")
    )

    if submissions is None:
        return

    if not submissions:
        st.success("There are no pending quiz submissions.")
        return

    for submission in submissions:

        with st.container(border=True):

            st.markdown(
                f"### {submission.get('title', 'Untitled Quiz')}"
            )

            st.write(
                submission.get("description", "")
            )

            st.caption(
                f"{submission.get('category', '')} | "
                f"{submission.get('difficulty', '')}"
            )

            notes = st.text_area(
                "Review notes",
                key=f"review_notes_{submission['id']}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Approve",
                    key=f"approve_{submission['id']}",
                    use_container_width=True
                ):
                    st.info(
                        "Publishing will be connected once "
                        "the submission database structure "
                        "is installed."
                    )

            with col2:
                if st.button(
                    "Reject",
                    key=f"reject_{submission['id']}",
                    use_container_width=True
                ):
                    result = _safe_execute(
                        supabase.table("quiz_submissions")
                        .update({
                            "status": "rejected",
                            "review_notes": notes
                        })
                        .eq("id", submission["id"])
                    )

                    if result is not None:
                        st.success("Submission rejected.")
                        st.rerun()


# ============================================================
# MAIN ECO QUIZZES PAGE
# ============================================================

def render_eco_quizzes(supabase, user_id, profile=None):

    st.title("🧠 Eco Quizzes")

    st.write(
        "Learn, test your knowledge, challenge yourself "
        "and contribute to environmental awareness."
    )

    if not user_id:
        st.warning("Please log in to access Eco Quizzes.")
        return

    # --------------------------------------------------------
    # ACTIVE QUIZ
    # --------------------------------------------------------

    if st.session_state.get("eco_active_quiz"):

        if st.button("← Back to Eco Quizzes"):
            _clear_active_quiz()
            st.rerun()

        take_quiz(supabase, user_id)
        return

    # --------------------------------------------------------
    # PAGE SECTIONS
    # --------------------------------------------------------

    is_admin = _is_super_admin(profile)

    tab_names = [
        "Quiz Centre",
        "Create a Quiz",
        "My Submissions"
    ]

    if is_admin:
        tab_names.append("Admin Review")

    tabs = st.tabs(tab_names)

    with tabs[0]:
        quiz_centre(supabase, user_id)

    with tabs[1]:
        create_quiz(supabase, user_id)

    with tabs[2]:
        my_submissions(supabase, user_id)

    if is_admin:
        with tabs[3]:
            admin_review(supabase)


# ============================================================
# END OF ECO QUIZZES
# ============================================================
